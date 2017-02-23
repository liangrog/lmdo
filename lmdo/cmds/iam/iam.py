from __future__ import print_function
import os

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint
from lmdo.utils import get_template, update_template 
from lmdo.config import IAM_ROLE_APIGATEWAY_LAMBDA, IAM_POLICY_APIGATEWAY_LAMBDA_INVOKE, IAM_ROLE_LAMBDA_ASSUME, IAM_POLICY_LAMBDA_DEFAULT, LAMBDA_DEFAULT_ASSUME_ROLES 

class IAM(AWSBase):
    """create/update IAM properties"""

    def __init__(self):
        super(IAM, self).__init__()
        self._client = self.get_client('iam') 

    @property
    def client(self):
        return self._client
 
    def create_role(self, role_name, policy):
        """Create an IAM role"""
        try:
            Oprint.info('Creating role {}'.format(role_name), 'iam')
            response = self._client.create_role(RoleName=role_name, AssumeRolePolicyDocument=policy)
            Oprint.info('Complete creating role {}'.format(role_name), 'iam')
        except Exception as e:
            Oprint.err(str(e.response['Error']['Message']), 'iam')

        return response

    def delete_role(self, role_name):
        """Delete an IAM role"""
        try:
            # In case role doesn't exist
            response = False

            Oprint.info('Deleting role {}'.format(role_name), 'iam')
            response = self._client.delete_role(RoleName=role_name)
            Oprint.info('Complete deleting role {}'.format(role_name), 'iam')
        except Exception as e:
            Oprint.err(str(e.response['Error']['Message']), 'iam', exit=False)

        return response
 
    def get_role(self, role_name):
        """Get an IAM role"""
        try:
            response = self._client.get_role(RoleName=role_name)
        except Exception as e:
            return False

        return response
                   
    def create_apigateway_lambda_role(self, role_name):
        """Create APIGateway role that can invoke lambda"""
        try: 
            response = self.get_role(role_name)
            
            if response:
                Oprint.warn('Role {} exists, no action required'.format(role_name), 'iam')

            template = get_template(IAM_ROLE_APIGATEWAY_LAMBDA)
            if not template:
                return False

            if not response:
                with open(template, 'r') as outfile:
                    assume_policy = outfile.read()

                response = self.create_role(role_name, assume_policy)

            policy = self.create_apigateway_lambda_invoke_policy(role_name, self.create_policy_name(role_name, 'lambda-invoke'))
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def detach_role_managed_policies(self, role_name):
        """Detach managed policies that attache to a role"""
        try:
            response = self._client.list_attached_role_policies(RoleName=role_name)
            if not response:
                return False

            for policy in response.get('AttachedPolicies'):
                Oprint.info('Detaching managed IAM policy {}'.format(policy.get('PolicyName')), 'iam')
                
                self._client.detach_role_policy(RoleName=role_name, PolicyArn=policy.get('PolicyArn'))
                    
                Oprint.info('Managed IAM policy {} has been deteched'.format(policy.get('PolicyName')), 'iam')
        except Exception as e:
            Oprint.err(e.response['Error']['Message'], 'iam', exit=False)
        
        return True

    def delete_role_inline_policies(self, role_name):
        """Delete policies that inline to a role"""
        try:
            response = self._client.list_role_policies(RoleName=role_name)
            if not response:
                return False
            
            for name in response.get('PolicyNames'):
                Oprint.info('Deleting inline IAM policy {} for role {}'.format(name, role_name), 'iam')
                
                self._client.delete_role_policy(RoleName=role_name, PolicyName=name)
                    
                Oprint.info('Inline IAM policy {} has been deleted'.format(name), 'iam')
        except Exception as e:
            Oprint.err(e.response['Error']['Message'], 'iam', exit=False)
        
        return True

    def delete_role_and_associated_policies(self, role_name):
        """Delet a role and associated policies"""
        try:
            self.detach_role_managed_policies(role_name)
            self.delete_role_inline_policies(role_name)
            
            response = self.delete_role(role_name)
        except Exception as e:
            Oprint.err(e, 'iam', exit=False)

        return response
   
    def create_apigateway_lambda_invoke_policy(self, role_name, policy_name):
        """Create APIGateway role inline policy that can invoke lambda"""
        try:
            template = get_template(IAM_POLICY_APIGATEWAY_LAMBDA_INVOKE)
            if not template:
                return False

            with open(template, 'r') as outfile:
                policy_doc = outfile.read()

            return self._client.put_role_policy(RoleName=role_name, PolicyName=policy_name, PolicyDocument=policy_doc)
        except Exception as e:
            Oprint.err(e, 'iam')

    def delete_lambda_role(self, role_name):
        """wrapper"""
        return self.delete_role_and_associated_policies(role_name)

    def create_lambda_role(self, role_name, role_policy):
        """
            Create role for Lambda, all policies
            store in the assume role policy doc
            so that we can do update
            If not set, will using default
            which enables Lambda for invoking
            and logging
        """
        try:
            Oprint.info('Start creating role {} and policie for Lambda'.format(role_name), 'iam')
            
            roles = LAMBDA_DEFAULT_ASSUME_ROLES
            if role_policy and role_policy.get('AssumeRoles'):
                roles += role_policy.get('AssumeRoles')

            assume_template = get_template(IAM_ROLE_LAMBDA_ASSUME)
 
            # Default assum roles
            assume_roles = '"{}"'.format('","'.join(roles))
           
            to_replace = {
                "$services": assume_roles,
                "$region": self.get_region(),
                "$accountId": self.get_account_id()
            }

            with open(assume_template, 'r') as outfile:
                policy_doc = update_template(outfile.read(), to_replace)

            role = self.get_role(role_name)
            
            if not role:
                role = self._client.create_role(RoleName=role_name, AssumeRolePolicyDocument=policy_doc)
            else:
                self._client.update_assume_role_policy(RoleName=role_name, PolicyDocument=policy_doc)
            
            # If inline policy document provided
            policy_template = get_template(IAM_POLICY_LAMBDA_DEFAULT)

            if role_policy and role_policy.get('PolicyDocument'):
                with open(os.path.join(os.getcwd(), role_policy.get('PolicyDocument')), 'r') as outfile:
                    to_replace['$more'] = ',' + outfile.read()
            else:
                to_replace['$more'] = ''
            
            with open(policy_template, 'r') as outfile:
                policy_doc = update_template(outfile.read(), to_replace)

            # Do inline policy so that when deleting the role, it'll be deleted
            self._client.put_role_policy(RoleName=role_name, PolicyName='{}-policy'.format(role_name), PolicyDocument=policy_doc)

            if role_policy and role_policy is dict and role_policy.get('ManagedPolicyArns'):
                for m_policy_arn in role_policy.get('ManagedPolicyArns'):
                    self._client.attach_role_policy(RoleName=role_name, PolicyArn=m_policy_arn)

            Oprint.info('Complete creating role {} and policie for Lambda'.format(role_name), 'iam')
        except Exception as e:
            Oprint.err(e, 'iam')

        return role

    def create_policy_name(self, role_name, postfix):
        """Create policy name base on role name"""
        return '{}-{}-{}'.format(role_name, 'policy', postfix)

    def get_policy(self, policy_name):
        """Get policy information"""
        try:
            response = self._client.get_policy(PolicyArn=self.get_policy_arn(policy_name))
        except Exception as e:
            #Oprint.warn(e, 'iam')
            return False

        return response

    def create_policy(self, policy_name, policy_document, delete=True, **kwargs):
        """wrapper, check if policy exists before create"""
        try:
            Oprint.info('Creating IAM policy {}'.format(policy_name), 'iam')
           
            policy = self.get_policy(policy_name=policy_name)
            if policy and policy.get('Policy'):
                if not delete:
                    Oprint.info('Found existing IAM policy {}'.format(policy_name), 'iam')
                    return policy
                else:
                    # Can not delete a policy if it has been attached
                    if policy.get('Policy').get('AttachmentCount') > 0:
                        Oprint.warn('Policy {} already exists and has been attached to a role. Cannot delete'.format(policy.get('Policy').get('PolicyName')), 'iam')
                        return policy

                    self._client.delete_policy(PolicyArn=self.get_policy_arn(policy_name))
            
            policy = self._client.create_policy(PolicyName=policy_name, PolicyDocument=policy_document, **kwargs)

            Oprint.info('IAM policy {} has been created'.format(policy_name), 'iam')
        except Exception as e:
            Oprint.err(e, 'iam')

        return policy


