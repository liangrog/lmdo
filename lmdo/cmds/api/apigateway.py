from __future__ import print_function
import os
import sys
import site
import datetime
import json

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.iam.iam import IAM
from lmdo.cmds.lm.aws_lambda import AWSLambda
from lmdo.oprint import Oprint
from lmdo.config import SWAGGER_DIR, SWAGGER_FILE, PROJECT_CONFIG_FILE, APIGATEWAY_SWAGGER_WSGI
from lmdo.utils import update_template, get_template
from lmdo.convertors.stack_var_convertor import StackVarConvertor
from lmdo.convertors.apigateway_local_lambda_convertor import ApiGatewayLocalLambdaConvertor 
from lmdo.convertors.apigateway_local_lambda_role_convertor import ApiGatewayLocalLambdaRoleConvertor 


class Apigateway(AWSBase):
    """create/update APIGateway"""

    def __init__(self):
        super(Apigateway, self).__init__()
        self._client = self.get_client('apigateway')
        self.convert_config()

    @property
    def client(self):
        return self._client

    def convert_config(self):
        """converting stack var"""
        convertor = StackVarConvertor()
        apigateway_local_lambda_convertor = ApiGatewayLocalLambdaConvertor()
        apigateway_local_lambda_role_convertor = ApiGatewayLocalLambdaRoleConvertor()

        convertor.successor = apigateway_local_lambda_convertor
        apigateway_local_lambda_convertor.successor = apigateway_local_lambda_role_convertor

        # Convert stack output key value if there is any
        _, json_data = convertor.process_next((json.dumps(self._config.config), self._config.config))
        
        self._config.config = json_data

        return True

    def create(self):
        """Create"""
        if not self.get_apigateway_name():
            Oprint.info('No action for api gateway, skip...', 'apigateway')
            sys.exit(0)

        swagger_api = self.create_api_by_swagger()
        swagger_api = self.create_wsgi_api()
        if swagger_api:
            self.create_deployment(swagger_api.get('id'), self._config.get('Stage'), swagger_api.get('name'))

    def update(self):
        """Update"""
        self.create()

    def delete(self):
        """Delete"""
        self.delete_rest_api(self.get_apigateway_name())
        self.delete_wsgi_api_roles()

    def create_stage(self):
        """Create statge"""
        self.create_stage_from_stage(self._args.get('<from_stage>'), self._args.get('<to_stage>'), self.get_apigateway_name())

    def delete_stage(self):
        swagger_api = self.if_api_exist_by_name(self.get_apigateway_name())
        self.delete_api_stage(swagger_api.get('id'), self._args.get('<from_stage>'), swagger_api.get('name'))

    def create_domain(self):
        self.create_domain_name(self._args.get('<domain_name>'), self._args.get('<cert_name>'), self._args.get('<cert_path>'), self._args.get('<cert_private_key_path>'), self._args.get('<cert_chain_path>'))

    def delete_domain(self):
        self.delete_domain_name(self._args.get('<domain_name>'))

    def create_mapping(self):
        self.create_base_path_mapping(self._args.get('<domain_name>'), self._args.get('<base_path>'), self._args.get('<api_name>'), self._args.get('<stage>'))

    def delete_mapping(self):
        self.delete_base_path_mapping(self._args.get('<domain_name>'), self._args.get('<base_path>'))
 
    def get_swagger_template(self):
        """Return swagger template path"""
        return './{}/{}'.format(SWAGGER_DIR, SWAGGER_FILE)
    
    def get_apigateway_name(self):
        """Return config for swagger api name"""
        return self._config.get('ApiGatewayName')

    def import_rest_api(self, body, api_name=None):
        """Import rest api via Swagger"""
        try:
            Oprint.info('Start creating rest api definition via Swagger file for API {}'.format(api_name or self.get_apigateway_name()), 'apigateway')
            response = self._client.import_rest_api(body=body)
            Oprint.info('Finish creating rest api', 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def put_rest_api(self, api_id, body, mode='merge', api_name=None):
        """Update rest api via Swagger"""
        try:
            Oprint.info('Start updating rest api definition via Swagger file for API {}'.format(api_name or self.get_apigateway_name()), 'apigateway')
            response = self._client.put_rest_api(restApiId=api_id, mode=mode, body=body)
            Oprint.info('Finish updating rest api', 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def delete_rest_api(self, api_name):
        """Delete rest api by name"""
        api = self.if_api_exist_by_name(api_name)
        if not api:
            Oprint.warn('API {} doesn\'t exist, nothing to delete'.format(api_name), 'apigateway')
        else: 
            try:
                Oprint.info('Deleting rest API {}'.format(api_name), 'apigateway')
                response = self._client.delete_rest_api(restApiId=api.get('id'))
                Oprint.info('Complete deleting rest API {}'.format(api_name), 'apigateway')
            except Exception as e:
                Oprint.err(e, 'apigateway')

        return True


    def if_api_exist_by_name(self, api_name):
        """
        Check if an API exist by given name
        Note: APIGateway allows name to be duplicated, it uses internal ID 
        to identify the actual APIs. We won't consider using same name for
        APIs, hence return the first item which should be unique
        """
        try:
            limit = 100
            found = False
            pos = None
            while True:
                if pos:
                    response = self._client.get_rest_apis(position=pos, limit=limit)
                else: 
                    response = self._client.get_rest_apis(limit=limit)

                pos = response.get('position')
                if len(response.get('items')) > 0:
                    for api in response.get('items'):
                        if api_name == api.get('name'):
                            found = api
                            break

                if not pos:
                    break

            return found
        except Exception as e:
            Oprint.err(e, 'apigateway')
    
        return False

    def create_api_by_swagger(self):
        """Create/Update api definition by swagger"""
        # Exist if no swagger definition
        if not os.path.isfile(self.get_swagger_template()):
            return True

        api = self.if_api_exist_by_name(self.get_apigateway_name())
        with open(self.get_swagger_template(), 'r') as outfile:
            to_replace = {
                "$title": self.get_apigateway_name(),
                "$version": str(datetime.datetime.utcnow())
            }

            # Replace variable in swagger template with content in a file.
            var_to_file = self._config.get('ApiVarMapToFile')
            if (var_to_file):
                for var_name, file_name in var_to_file.iteritems():
                    with open('{}/{}'.format(SWAGGER_DIR, file_name), 'r') as ofile:
                        file_content = ofile.read()
                        to_replace[var_name] = file_content.replace('\n', '\\n').replace('"', '\\"')

            var_to_var = self._config.get('ApiVarMapToVar')
            if var_to_var:
                for var_name, replacement in var_to_var.iteritems():
                    to_replace[var_name] = replacement
                    
            body = update_template(outfile.read(), to_replace)

            if not api:
                return self.import_rest_api(body)
            else:
                # Always overwrite for update
                return self.put_rest_api(api.get('id'), body, 'overwrite')

        return False
            
    def create_deployment(self, api_id, stage_name='dev', api_name=None, **kwargs):
        """Create a stage deployment to internet"""
        try:
            Oprint.info('Deploying {} stage: {} to internet'.format(api_name or self.get_apigateway_name(), stage_name), 'apigateway')
            response = self._client.create_deployment(restApiId=api_id, stageName=stage_name, **kwargs)
            Oprint.info('Complete deploying {} stage: {}'.format(api_name or self.get_apigateway_name(), stage_name), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def delete_deployment(self, api_id, deployment_id, api_name=None):
        """Delete a deployments of an API"""
        try:
            Oprint.info('Deleting stage: {} for API {}'.format(stage_name, api_name or self.get_apigateway_name()), 'apigateway')
            response = self._client.delete_deployment(restApiId=api_id, deploymentId=deployment_id)
            Oprint.info('Complete deleting stage: {} for API {}'.format(stage_name, api_name or self.get_apigateway_name()), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def create_api_stage(self, api_id, stage_name, deployment_id, api_name=None, **kwargs):
        """Create a stage"""
        try:
            Oprint.info('Creating stage: {} for API {}'.format(stage_name, api_name or self.get_apigateway_name()), 'apigateway')
            response = self._client.create_stage(restApiId=api_id, stageName=stage_name, deploymentId=deployment_id, **kwargs)
            Oprint.info('Complete creating stage: {} for API {}'.format(stage_name, api_name or self.get_apigateway_name()), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def delete_api_stage(self, api_id, stage_name, api_name=None):
        """delete a stage"""
        try:
            Oprint.info('Deleting stage: {} deployment for API {}'.format(stage_name, api_name or self.get_apigateway_name()), 'apigateway')
            response = self._client.delete_stage(restApiId=api_id, stageName=stage_name)
            Oprint.info('Complete deleting stage: {} deployment for API {}'.format(stage_name, api_name or self.get_apigateway_name()), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return True

    def get_stage(self, api_id, stage_name):
        """Get stage information by name"""
        try:
            response = self._client.get_stage(restApiId=api_id, stageName=stage_name)
        except Exception as e:
            return False
            #Oprint.err(e, 'apigateway')

        return response

    def create_stage_from_stage(self, from_stage, new_stage, api_name=None):
        """Create a new stage by given existing stage"""
        # Get api_id 
        api = self.if_api_exist_by_name(api_name or self.get_apigateway_name())
        if not api:
            Oprint.err('API {} hasn\'t been created yet. Please create it first.'.format(api_name or self.get_apigateway_name()), 'apigateway')
        
        # Get deployment ID from source stage
        from_stage_info = self.get_stage(api.get('id'), from_stage)
        if len(from_stage_info.get('deploymentId')) <= 0:
            Oprint.warn('Stage: {} for API {} hasn\'t been deployed to internet yet, deploying...'.format(from_stage, api_name or self.get_apigateway_name()), 'apigateway')
            deployment_id = self.create_deployment(api.get('id'), from_stage)
        else:
            deployment_id = from_stage_info.get('deploymentId')

        to_stage_info = self.get_stage(api.get('id'), new_stage)
        if to_stage_info:
            # Delete new stage if exist
            Oprint.warn('Stage {} exists for API {}. Removing it now...'.format(new_stage, api_name or self.get_apigateway_name()), 'apigateway')
            self.delete_api_stage(api.get('id'), new_stage, api.get('name'))
        
        # Create new stage
        self.create_api_stage(api.get('id'), new_stage, deployment_id)

    def create_domain_name(self, domain_name, cert_name, cert_body, cert_private_key, cert_chain):
        """Create API custom domain name"""
        try:
            with open(cert_body, 'r') as outfile:
                cert_body_str = outfile.read()

            with open(cert_private_key, 'r') as outfile:
                cert_private_key_str = outfile.read()

            with open(cert_chain, 'r') as outfile:
                cert_chain_str = outfile.read()

            Oprint.info('Creating custom domain {}'.format(domain_name), 'apigateway')
            response = self._client.create_domain_name(
                    domainName=domain_name,
                    certificateName=cert_name,
                    certificateBody=cert_body_str,
                    certificatePrivateKey=cert_private_key_str,
                    certificateChain=cert_chain_str
            )
            Oprint.info('Complete creating custom domain {}'.format(domain_name), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

    def delete_domain_name(self, domain_name):
        """delete custom domain"""
        try:
            Oprint.info('Deleting custom domain {}'.format(domain_name), 'apigateway')
            response = self._client.delete_domain_name(domainName=domain_name)
            Oprint.info('Complete deleting custom domain {}'.format(domain_name), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return True

    def create_base_path_mapping(self, domain_name, base_path, api_name, stage_name):
        """Create API mapping to customer domain"""
        # Get API id
        api = self.if_api_exist_by_name(api_name)
        if not api:
            Oprint.err('API {} hasn\'t been created yet. Please create it first.'.format(api_name), 'apigateway')

        try:
            Oprint.info('Creating mapping to {} from {}, stage: {}'.format(domain_name, api_name, stage_name), 'apigateway')
            response = self._client.create_base_path_mapping(
                    domainName=domain_name,
                    basePath=base_path,
                    restApiId=api.get('id'),
                    stage=stage_name
            )
            Oprint.info('Complete creating mapping to {} from {}, stage: {}'.format(domain_name, api_name, stage_name), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def delete_base_path_mapping(self, domain_name, base_path):
        """Delete API mapping to customer domain"""
        try:
            Oprint.info('Deleting path {}  mapping to {}'.format(base_path, domain_name), 'apigateway')
            response = self._client.delete_base_path_mapping(
                    domainName=domain_name,
                    basePath=base_path,
            )
            Oprint.info('Complete deleting path {}  mapping to {}'.format(base_path, domain_name), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response
      
    def create_wsgi_api(self):
        """Create/Update api definition for wsgi app"""
        swagger_api = False
        # If there is already an exsiting swagger api template,
        # fetch it so we won't  duplicate it 
        #if os.path.isfile(self.get_swagger_template()) and self.get_apigateway_name():
        swagger_api = self.if_api_exist_by_name(self.get_apigateway_name())
        
        iam = IAM()

        for lm_func in self._config.get('Lambda'):
            if lm_func.get('Type') != AWSLambda.FUNCTION_TYPE_WSGI or lm_func.get('DisableApiGateway'):
                continue
            
            function_name = self.get_lmdo_format_name(lm_func.get('FunctionName'))

            role = iam.get_lambda_apigateway_default_role(function_name)
            
            Oprint.info('Create/Update API Gateway for wsgi function {}'.format(lm_func.get('FunctionName')), 'apigateway')

            to_replace = {
                "$title": self.get_apigateway_name(),
                "$version": str(datetime.datetime.utcnow()),
                "$basePath": lm_func.get('ApiBasePath') or '/res',
                "$apiRegion": self.get_region(),
                "$functionRegion": self.get_region(),
                "$accountId": self.get_account_id(),
                "$functionName": function_name,
                "$credentials": role['Role'].get('Arn')
            }

            # Enable cognito user pool as authorizer
            if lm_func.get('CognitoUserPoolId'):
                se_replace = {
                    "$apiRegion": self.get_region(),
                    "$accountId": self.get_account_id(),
                    "$userPoolId": lm_func.get('CognitoUserPoolId'),
                    "$CognitoUserPool": 'CognitoUserPool-{}'.format(lm_func.get('FunctionName'))
                }

                to_replace["$securityDefinitions"] = self.get_apigateway_authorizer(se_replace)
                to_replace["$authorizer"] = '{"' + str(se_replace['$CognitoUserPool'])+'":[]}'
            else:
                to_replace["$securityDefinitions"] = ''
                to_replace["$authorizer"] = ''

            template_dir = get_template(APIGATEWAY_SWAGGER_WSGI)
            if not template_dir:
                Oprint.err('Template {} for creating wsgi APIGateway hasn\'t been installed or missing'.format(APIGATEWAY_SWAGGER_WSGI), 'apigateway')
            
            with open(template_dir, 'r') as outfile:
                body = update_template(outfile.read(), to_replace)
                
                if not swagger_api:
                    swagger_api = self.import_rest_api(body)
                else:
                    # Always overwrite for update
                    self.put_rest_api(swagger_api.get('id'), body, 'merge')

        return swagger_api

    def get_apigateway_authorizer(self, to_replace):
        template = ',"securityDefinitions": {' \
              '"$CognitoUserPool": {' \
                  '"type": "apiKey",' \
                  '"name": "Authorization",'\
                  '"in": "header",' \
                  '"x-amazon-apigateway-authtype": "cognito_user_pools",' \
                  '"x-amazon-apigateway-authorizer": {' \
                    '"type": "cognito_user_pools",' \
                      '"providerARNs": [' \
                        '"arn:aws:cognito-idp:$apiRegion:$accountId:userpool/$userPoolId"' \
                      ']' \
                 '}' \
              '}' \
          '}' 

        return update_template(template, to_replace)

    def delete_wsgi_api_roles(self):
        """Remove IAM roles for wsgi"""
        iam = IAM()
        for lm_func in self._config.get('Lambda'):
            if lm_func.get('Type') == 'wsgi' and not lm_func.get('DisableApiGateway'):
                function_name = self.get_lmdo_format_name(lm_func.get('FunctionName'))
                iam.delete_role_and_associated_policies(self.get_apigateway_lambda_role_name(function_name))

    def get_authorizers(self, rest_api_id, filters=None, **kwargs):
        """Get authorizers for a rest api"""
        response = self._client.get_authorizers(restApiId=rest_api_id, **kwargs)
        authorizers = response.get('items')

        if filters:
            f = lambda x: x.get('type') == filters.get('type') or \
                          x.get('name') == filters.get('name') or \
                          x.get('authType') == filters.get('authType') or \
                          x.get('identitySource') == filters.get('identitySource')
            authorizers = list(filter(f, authorizers))

        return authorizers

    def create_userpool_authorizer(self, rest_api_id, userpool_id):
        """Create a userpool type authorizer"""
        name = self.get_lmdo_authorizer_name()
        userpool_arn = self.get_userpool_arn(userpool_id)
        identitySource = "method.request.header.Authorization"
        response = self._client.create_authorizer(
            restApiId=rest_api_id,
            name=name,
            type='COGNITO_USER_POOLS',
            providerARNs=[userpool_arn],
            identitySource=identitySource)

        Oprint.info('Authorizer {} for rest api {} has been created'.format(name, rest_api_id), self.NAME)

        return response

    def flush_rest_api(self, rest_api_id, stage_name):
        """Flush cache so to take changes"""
        self._client.flush_stage_authorizers_cache(restApiId=rest_api_id, stageName=stage_name)
        self._client.flush_stage_cache(restApiId=rest_api_id, stageName=stage_name)
        return True

