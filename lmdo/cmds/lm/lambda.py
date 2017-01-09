from __future__ import print_function
import os
import pip

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.s3.s3 import S3
from lmdo.cmds.iam.iam import IAM
from lmdo.oprint import Oprint
from lmdo.config import tmp_dir, lambda_memory_size, lambda_runtime, lambda_timeout, lambda_exclude
from lmdo.utils import zipper
from lmdo.spinner import spinner

class Lambda(AWSBase):
    """Class  create/update lambda function"""

    def __init__(self):
        super(Lambda, self).__init__()
        self._client = self.get_client('lambda') 
        self._s3 = S3()
        self._iam = IAM()

    @property
    def client(self):
        return self._client
 
    @property
    def s3(self):
        return self._s3
    
    @property
    def iam(self):
        return self._iam

    def create(self):
        """Create/Update Lambda functions"""
        self.pip_install()
        self.process()

    def delete(self):
        """Delete lambda functions"""
        # Dont run if doesn't exist
        if !self._config.get('Lambda'):
            Oprint.info('No Lambda function configured, skip', 'lambda')
            return True

        # Create all functions
        for lm in self._config.get('Lambda').iteritem():
            # Get function info before being deleted
            info = self.get_function(lm.get('FunctionName'))
            self.delete_function(lm.get('FunctionName'))

            # Delete role if it's created by lmdo
            if !lm.get('Role'):
                self.delete_role(info.get('Configuration').get('Role'))

    def update(self):
        """Wrapper, same action as create"""
        self.create()

    def get_function_name(self, func_name):
        """get defined function name"""
        return "{}-{}".format(self.get_name_id(), func_name)

    def get_role_name(self, func_name):
        """get defined function name"""
        return "lmdo-{}-{}".format(self.get_name_id(), func_name)

    def get_zip_name(self, func_name):
        """get defined function name"""
        return "{}-{}.zip".format(self.get_name_id(), func_name)

    def get_statement_id(self, func_name, principal_id):
        """get defined function permission statement ID"""
        return "stmt-{}-{}".format(self.get_function_name(func_name), principal_id)

    def add_permission(self, func_name, principal, principal_id, action='lambda:InvokeFunction'):
        """Add permission to Lambda function"""
        try:
            response = self._client.add_permission(
                FunctionName=self.get_function_name(func_name),
                StatementId=self.get_statement_id(func_name, principal_id),
                Action=action,
                Principal=principal
            )
            Oprint.info('Permission {} has been added for {} with principal {}'.format(action, self.get_function_name(func_name), principal), 'lambda')
        except Exception as e:
            Oprint.err(e, 'lambda')

        if response.get('Statement') is None:
            Oprint.err('Create lambda permission {} for {}'.format(action, principal), 'lambda')

        return response

    def remove_permission(self, func_name, principal_id):
        """Remove permission from Lambda function"""
        try:
            response = self._client.remove_permission(
                FunctionName=func_name,
                StatementId=self.get_statement_id(func_name,  principal_id)
            )
            Oprint.info('Permission has been removed for {}'.format(self.get_function_name(func_name)), 'lambda')
        except Exception as e:
            Oprint.err(e, 'lambda')

        return response

    def create_function(self, func_name, role, handler, code, runtime, **kwargs):
        """Wrapper for create lambda function"""
        try:
            response = self._client.create_function(
                FunctionName=self.get_function_name(func_name),
                Runtime=runtime,
                Role=role,
                Handler=handler,
                Code=code,
                **kwargs
            )
            Oprint.info('Lambda function {} has been created'.format(self.get_function_name(func_name)), 'lambda')
        except Exception as e:
            Oprint.err(e, 'lambda')

        return response

    def delete_function(self, func_name, **kwargs):
        """Wrapper to delete lambda function"""
        try:
            response = self._client.delete_function(FunctionName=self.get_function_name(func_name), **kwargs)
            Oprint.info('Lambda function {} has been deleted'.format(self.get_function_name(func_name)), 'lambda')
        except Exception as e:
            Oprint.err(e, 'lambda')

        return response

    def invoke(self, func_name, **kwargs):
        """Wrapper for invoke"""
        try:
            response = self._client.invoke(
                FunctionName=self.get_function_name(func_name),
                **kwargs
            )
        except Exception as e:
            Oprint.err(e, 'lambda')

        return response

    def list_functions(self, **kwargs):
        """Wrapper for listing functions"""
        try:
            response = self._client.list_functions(**kwargs)
        except Exception as e:
            Oprint.err(e, 'lambda')

        return response

    def update_function_code(self, func_name, bucket_name):
        """Update lambda code"""
        try:
            response = self._client.update_function_code(
                FunctionName=self.get_function_name(func_name),
                S3Bucket=bucket_name,
                S3Key=self.get_zip_name(func_name)
            )
            Oprint.info('Lambda function {} has been updated'.format(func_name), 'lambda')
        except Exception as e:
            Oprint.err(e, 'lambda')
                
        return response

    def get_arn(self, func_name):
        """Return invokeable function url"""
        return 'arn:aws:lambda:{}:{}:function:{}'.format(self.get_region(), self.get_account_id(), self.get_function_name(func_name))

    def get_function(self, func_name, **kwargs):
        """Get function info"""
        try:
            response = self._client.get_function(FunctionName=func_name, **kwargs)
        except Exception as e:
            Oprint.err(e, 'lambda')

        return response if response.get('Configuration') else False

    def zip_function(self, func_name):
        """Packaging lambda"""
        target = tmp_dir + self.get_zip_name(func_name)
        if zipper('./', target, lambda_exclude):
            return target

        return False

    def remove_zip(self, func_name):
        """Remove lambda package from local"""
        try:
            target = tmp_dir + self.get_zip_name(func_name)
            os.remove(target)
        except OSError:
            pass

    def process(self):
        """Prepare function before creation/update"""
        # Dont run if doesn't exist
        if !self._config.get('Lambda'):
            Oprint.info('No Lambda function configured, skip', 'lambda')
            return True

        # Create all functions
        for lm in self._config.get('Lambda').iteritem():
            params = {
                'FunctionName': self.get_function_name(lm.get('FunctionName')),
                'S3Bucket': lm.get('S3Bucket'),
                'Handler': lm.get('Handler'),
                'MemorySize': lm.get('MemorySize') or lambda_memory_size,
                'Runtime': lm.get('Runtime') or lambda_runtime,
                'Timeout': lm.get('Timeout') or lambda_timeout
            }

            if lm.get('VpcConfig'):                
                params['VpcConfig'] = lm.get('VpcConfig')

            if lm.get('EnvironmentVariables'):
                params['Environment'] = {'Variables': lm.get('EnvironmentVariables')}

            # Clean up before create a new one
            self.remove_zip(lm.get('FunctionName'))
            file_path = self.zip_function(lm.get('FunctionName'))
            
            if file_path and self._s3.upload_file(lm.get('S3Bucket'), self.get_zip_name, file_path):
                # If function exists
                if self.get_function(lm.get('FunctionName')):
                    self.update_function_code(lm.get('FunctionName'), lm.get('S3Bucket'))
                else:
                    # User configured role or create a new on based on policy document
                    role = lm.get('Role') or self.create_role(lm.get('RolePolicyDocument'))
                    params['Role'] = role
                    self.create_function(**params)
            # Clean up
            self.remove_zip(lm.get('FunctionName'))

    def create_role(self, role_name, policy_path):
        """Create role for lambda from policy doc"""
        with open(policy_path, 'r') as outfile: 
            policy = outfile.read()
            self._iam.create_role(role_name, policy)

    def delete_role(self, role):
        """Delete role for lambda"""
        self._iam.delete_role(role)

    def pip_install(self):
        """Install requirement"""
        if os.path.isfile('./{}'.format(os.getenv('PIP_REQUIREMENTS_FILE', pip_requirements_file))):
            Oprint.info('Installing python package dependancies if there is any missing', 'pip')

            spinner.start()
            pip.main(['install', '-t', os.getenv('PIP_VENDOR_FOLDER', pip_vendor_folder), '-r', os.getenv('PIP_REQUIREMENTS_FILE', pip_requirements_file), '&>/dev/null'])
            spinner.stop()

            Oprint.info('Python package installation complete', 'pip')
        else:
            Oprint.warn('{} could not be found, no dependencies will be installed'.format(os.getenv('PIP_REQUIREMENTS_FILE', pip_requirements_file)), 'pip')

                   
