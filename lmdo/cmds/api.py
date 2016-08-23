from __future__ import print_function
import sys
import os

from .base import Base
from .cf import Cf
from lmdo.config import swagger_file, swagger_dir

class Api(Base):
    """
    Class create, update API Gateway
    """
    
    def __init__(self, options={}, *args, **kwargs):
        super(Api, self).__init__(options, *args, **kwargs)

        self.api_path = swagger_dir + swagger_file
        
        if os.path.isfile(self.api_path):
            self.has_api = True

        self.api = self.get_aws_client('apigateway')

    def run(self):
        if self.has_api:
            self.import_swagger_api()
            self.deploy_api_stage()
    
    def if_api_exist(self, api_name, api_list):
        """
        check if api exist in api gateway
        """
        
        for api in api_list['items']:
            if api_name == api['name']:
                return api['id']

        return False

    def import_swagger_api(self):
        """
        Import swagger template
        """
        
        api_key = self.if_api_exist(self.config_loader.get_value('API'), self.api.get_rest_apis())
        with open(self.api_path, 'r+') as outfile:
            contents = outfile.read()
            mapping = self.config_loader.get_value('LambdaMapping')
            if (mapping):
                cf = Cf()
                cf_output = cf.get_stack_output()
                for funck, func in mapping.items():
                    if funck:
                        for k, v in func.items():
                            contents = contents.replace(v, cf.get_stack_output_value(k, cf_output))

            if not api_key:
                self.api.import_rest_api(body=contents)
            else:
                self.api.put_rest_api(restApiId=api_key, mode='overwrite', body=contents)

        return True

    def get_api_stage(self, api_id, stage):
        """
        Fetch API stage info
        """

        try:
            response = self.api.get_stage(restApiId=api_id, stageName=stage)
            return response
        except Exception as e:
            #print(e)
            return False

        return False

    def deploy_api_stage(self):
        """
        Deploy API to stage
        """
        
        api_key = self.if_api_exist(self.config_loader.get_value('API'), self.api.get_rest_apis())
        if not api_key:
            print('Can not find API ' + self.config_loader.get_value('API') + ' in AWS')
            sys.exit(0)

        try:
            api_stage = self.get_api_stage(api_key, self.config_loader.get_value('Stage'))
            print('Start deploying API Gateway stage ' + self.config_loader.get_value('Stage'))
            if api_stage:
                self.delete_api_stage(api_key, self.config_loader.get_value('Stage'))
                response = self.api.create_deployment(restApiId=api_key, stageName=self.config_loader.get_value('Stage'))
            else:
                response = self.api.create_deployment(restApiId=api_key, stageName=self.config_loader.get_value('Stage'))
            print('Finish deploying API Gateway stage ' + self.config_loader.get_value('Stage'))
        except Exception as e:
            print(e)
            sys.exit(0)

        return True
      
    def delete_api_stage(self, api_id, stage):
        """
        Delete API stage
        """

        try:
            self.api.delete_stage(restApiId=api_id, stageName=stage)
        except Exception as e:
            print(e)
            sys.exit(0)

        return True

    def delete_api_stages(self, api_id):
        """
        Delete all stages
        """

        try:
            stages = self.api.get_stages(restApiId=api_id)

            if stages['item']:
                for stage in stages['item']:
                    self.delete_api_stage(api_id, stage['stageName'])
                    print('Deleted rest API stage ' + stage['stageName'])

        except Exception as e:
            print(e)
            sys.exit(0)

    def destroy(self):
        """
        Destroy all API gateway assets
        """

        api_key = self.if_api_exist(self.config_loader.get_value('API'), self.api.get_rest_apis())

        if not api_key:
            print('No API Gateway assets to remove')
            sys.exit(0)

        try:
            self.delete_api_stages(api_key)        
            self.api.delete_rest_api(restApiId=api_key)
            print('Deleted rest API ' + self.config_loader.get_value('API'))
        except Exception as e:
            print(e)
            sys.exit(0)

        return True


