from __future__ import print_function

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint
from lmdo.utils import get_template 

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
            Oprint.err(e, 'iam')

        return response

    def delete_role(self, role_name):
        """Delete an IAM role"""
        try:
            Oprint.info('Deleting role {}'.format(role_name), 'iam')
            response = self._client.delete_role(RoleName=role_name)
            Oprint.info('Complete deleting role {}'.format(role_name), 'iam')
        except Exception as e:
            Oprint.err(e, 'iam')

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

            template = get_template('apigateway_lambda_role.json')
            if not template:
                return False

            if not response:
                with open(template, 'r') as outfile:
                    assume_policy = outfile.read()

                response = self.create_role(role_name, assume_policy)

            policy = self.create_lambda_invoke_policy(self.create_policy_name(role_name, 'lambda-invoke'))

            self._client.attach_role_policy(RoleName=response['Role'].get('RoleName'), PolicyArn=policy['Policy'].get('Arn'))
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def delete_apigateway_lambda_role(self, role_name):
        """Delete APIGateway role that can invoke lambda"""
        try: 
            policy_name = self.create_policy_name(role_name, 'lambda-invoke')    
            response = self.get_policy(policy_name)
            if response.get('Policy'):
                Oprint.info('Deleting IAM policy {}'.format(policy_name), 'iam')
                self._client.detach_role_policy(RoleName=role_name, PolicyArn=response['Policy'].get('Arn'))
                self._client.delete_policy(PolicyArn=response['Policy'].get('Arn'))
                Oprint.info('IAM policy {} has been deleted'.format(policy_name), 'iam')
            
            response = self.delete_role(role_name)
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def create_lambda_invoke_policy(self, policy_name):
        """Create APIGateway role that can invoke lambda"""
        exists = self.get_policy(policy_name)
        
        if exists:
            Oprint.warn('Policy {} exists, no action required'.format(policy_name), 'iam')
            return exists

        template = get_template('iam_policy_lambda_invoke.json')
        if not template:
            return False

        with open(template, 'r') as outfile:
            policy = outfile.read()

        return self._client.create_policy(PolicyName=policy_name, PolicyDocument=policy)

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


