from __future__ import print_function
import os

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint
from lmdo.config import SWAGGER_DIR, SWAGGER_FILE


class Apigateway(AWSBase):
    """create/update APIGateway"""

    def __init__(self):
        super(Apigateway, self).__init__()
        self._client = self.get_client('apigateway') 

    @property
    def client(self):
        return self._client

    def create(self):
        self.create_api_by_swagger()

    def update(self):
        self.create_api_by_swagger()

    def delete(self):
        self.delete_rest_api(self.get_api_name())

    def get_swagger_template(self):
        """Return swagger template path"""
        return './{}/{}'.format(SWAGGER_DIR, SWAGGER_FILE)
    
    def get_api_name(self):
        """Create API name structure"""
        return '{}-{}'.format(self.get_name_id(), self._config.get('Service'))

    def import_rest_api(self, body):
        """Import rest api via Swagger"""
        try:
            Oprint.info('Start creating rest api definition via Swagger file for API {}'.format(self.get_api_name()), 'apigateway')
            response = self._client.import_rest_api(body=body)
            Oprint.info('Finish creating rest api', 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def put_rest_api(self, api_id, body, mode='merge'):
        """Update rest api via Swagger"""
        try:
            Oprint.info('Start updating rest api definition via Swagger file for API {}'.format(self.get_api_name()), 'apigateway')
            response = self._client.put_rest_api(restApiId=api_id, mode=mode, body=body)
            Oprint.info('Finish updating rest api', 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def delete_rest_api(self, api_name):
        """Delete rest api by name"""
        api = self.if_api_exist_by_name(api_name)
        if !api:
            Oprint.err('API {} doesn\'t exist, nothing to delete'.format(api_name), 'apigateway')

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
            response = self._client.get_api_keys(nameQuery=api_name)
        except Exception as e:
            Oprint.err(e, 'apigateway')
    
        return response.get('items').pop(0) if response.get('items') and len(response.get('items')) > 0 else False

    def create_api_by_swagger(self):
        """Create/Update api definition by swagger"""
        # Exist if no swagger definition
        if !os.path.isfile(self.get_swagger_template()):
            return True

        api = self.if_api_exist_by_name(self.get_api_name())
        with open(self.get_swagger_template(), 'r') as outfile:
            body = outfile.read()
            if !api:
                self.import_rest_api(body)
            else:
                # Always overwrite for update
                self.put_rest_api(api.get('id'), body, 'overwrite')

        return True
            
    def create_deployment(self, api_id, stage_name='dev', **kwargs):
        """Create a stage deployment to internet"""
        try:
            Oprint.info('Deploying {} stage: {} to internet'.format(self.get_api_name(), stage_name), 'apigateway')
            response = self._client.create_deployment(restApiId=api_id, stageName=stage_name, **kwargs)
            Oprint.info('Complete deploying {} stage: {}'.format(self.get_api_name(), stage_name), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def delete_deployment(self, api_id, deployment_id):
        """Delete a deployments of an API"""
        try:
            Oprint.info('Deleting stage: {} deployment for API {}'.format(stage_name, self.get_api_name()), 'apigateway')
            response = self._client.delete_deployment(restApiId=api_id, deploymentId=deployment_id)
            Oprint.info('Complete deleting stage: {} deployment for API {}'.format(stage_name, self.get_api_name()), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def create_stage(self, api_id, stage_name, deployment_id, **kwargs):
        """Create a stage"""
        try:
            Oprint.info('Creating stage: {} deployment for API {}'.format(stage_name, self.get_api_name()), 'apigateway')
            response = self._client.create_stage(restApiId=api_id, stageName=stage_name, deployment_id=deployment_id, **kwargs)
            Oprint.info('Complete creating stage: {} deployment for API {}'.format(stage_name, self.get_api_name()), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def delete_stage(self, api_id, stage_name):
        """delete a stage"""
        try:
            Oprint.info('Deleting stage: {} deployment for API {}'.format(stage_name, self.get_api_name()), 'apigateway')
            response = self._client.delete_stage(restApiId=api_id, stageName=stage_name)
            Oprint.info('Complete deleting stage: {} deployment for API {}'.format(stage_name, self.get_api_name()), 'apigateway')
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return True

    def get_stage(self, api_id, stage_name):
        """Get stage information by name"""
        try:
            response = self._client.get_stage(restApiId=api_id, stageName=stage_name)
        except Exception as e:
            Oprint.err(e, 'apigateway')

        return response

    def create_stage_from_stage(self, from_stage, new_stage):
        """Create a new stage by given existing stage"""
        # Get api_id 
        api = self.if_api_exist_by_name(self.get_api_name())
        if !api:
            Oprint.err('API {} hasn\'t been created yet. Please create it first.'.format(self.get_api_name()), 'apigateway')

        # Get deployment ID from source stage
        from_stage_info = self.get_stage(api.get('id'), from_stage)
        if len(from_stage_info.get('deploymentId')) <= 0:
            Oprint.warn('Stage: {} for API {} hasn\'t been deployed to internet yet, deploying...'.format(from_stage, self.get_api_name()), 'apigateway')
            deployment_id = self.create_deployment(api.get('id'), from_stage)
        else:
            deployment_id = from_stage_info.get('deploymentId')

        to_stage_info = self.get_stage(api.get('id'), new_stage)
        if to_stage_info:
            # Delete new stage if exist
            Oprint.warn('Stage {} exists for API {}. Removing it now...'.format(new_stage, self.get_api_name()), 'apigateway')
            self.delete_stage(api.get('id'), new_stage)
        else:
            # Create new stage
            self.create_stage(api.get('id'), new_stage, deployment_id)

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
        except Exception as e
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
        if !api:
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


