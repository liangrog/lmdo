from __future__ import print_function
import os
import pip
import tarfile
import shutil

from lambda_packages import lambda_packages

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.s3.s3 import S3
from lmdo.cmds.iam.iam import IAM
from lmdo.oprint import Oprint
from lmdo.config import TMP_DIR, LAMBDA_MEMORY_SIZE, LAMBDA_RUNTIME, LAMBDA_TIMEOUT, LAMBDA_EXCLUDE, PIP_VENDOR_FOLDER, PIP_REQUIREMENTS_FILE 
from lmdo.utils import zipper, get_sitepackage_dirs, class_function_retry
from lmdo.spinner import spinner

class Lambda(AWSBase):
    """Class  create/update lambda function"""

    def __init__(self, args=None):
        super(Lambda, self).__init__()
        self._client = self.get_client('lambda') 
        self._s3 = S3()
        self._iam = IAM()
        self._args = args or {}

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
        #self.pip_install()
        #if self.if_wsgi_exist():
        #    self.pip_wsgi_install()

        self.process()

    def delete(self):
        """Delete lambda functions"""
        # Dont run if doesn't exist
        if not self._config.get('Lambda'):
            Oprint.info('No Lambda function configured, skip', 'lambda')
            return True

        # delete  all functions
        for lm in self._config.get('Lambda'):
            # Get function info before being deleted
            info = self.get_function(self.get_function_name(lm.get('FunctionName')))
            if info:
                self.delete_function(info.get('Configuration').get('FunctionName'))

                # Delete role if it's created by lmdo
                if not lm.get('RoleArn') or len(lm.get('RoleArn')) <= 0:
                    self.delete_role(info.get('Configuration').get('Role'))
            else:
                Oprint.warn('Cannot find function {} to delete in AWS'.format(self.get_function_name(lm.get('FunctionName'))), 'lambda')

    def update(self):
        """Wrapper, same action as create"""
        self.create()

    def get_function_name(self, func_name):
        """get defined function name"""
        return "{}-{}".format(self.get_name_id(), func_name)

    @classmethod
    def fetch_function_name(cls, prefix, postfix):
        """
        Wrapper for access outside object context
        Uggly, but quick work around...
        """
        return "{}-{}".format(prefix, postfix)

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
    
    @class_function_retry(aws_retry_condition=['InvalidParameterValueException'], tries=10, delay=2)
    def create_function(self, FunctionName, Role, Handler, Code, Runtime, **kwargs):
        """
        Wrapper for create lambda function
        Don't catch the exceptions as we want 
        the decorator to do that job
        """
        Oprint.info('Start creating Lambda function {}'.format(FunctionName), 'lambda')
        response = self._client.create_function(
            FunctionName=FunctionName,
            Runtime=Runtime,
            Role=Role,
            Handler=Handler,
            Code=Code,
            **kwargs
        )
        Oprint.info('Lambda function {} has been created'.format(FunctionName), 'lambda')

        return response

    def delete_function(self, func_name, **kwargs):
        """Wrapper to delete lambda function"""
        try:
            Oprint.info('Start deleting Lambda function {}'.format(func_name), 'lambda')
            response = self._client.delete_function(FunctionName=func_name, **kwargs)
            Oprint.info('Lambda function {} has been deleted'.format(func_name), 'lambda')
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

    def update_function_code(self, func_name, bucket_name, s3_key):
        """Update lambda code"""
        try:
            response = self._client.update_function_code(
                FunctionName=func_name,
                S3Bucket=bucket_name,
                S3Key=s3_key
            )
            Oprint.info('Lambda function {} has been updated'.format(func_name), 'lambda')
        except Exception as e:
            Oprint.err(e, 'lambda')
                
        return response

    def get_function(self, func_name, **kwargs):
        """Get function info"""
        try:
            return self._client.get_function(FunctionName=func_name, **kwargs)
        except Exception as e:
            pass
            #Oprint.err(e, 'lambda')

        return False

    def zip_function(self, func_name, func_type='default'):
        """Packaging lambda"""
        target = TMP_DIR + self.get_zip_name(func_name)
        if zipper('./', target, LAMBDA_EXCLUDE) \
            and (not func_type or func_type == 'default'):
            return target

        # zip lmdo wsgi function
        if func_type == 'wsgi':
            # Don't load lmdo __init__.py
            if LAMBDA_EXCLUDE.get('LAMBDA_EXCLUDE'):
                LAMBDA_EXCLUDE['file_with_path'].append('*wsgi/__init__.py')
            else:
                LAMBDA_EXCLUDE['file_with_path'] = ['*wsgi/__init__.py']

            replace_path = [
                {
                   'from_path': '/usr/lib/python2.7/site-packages/lmdo/wsgi',
                   'to_path': '.'
                }
            ]

            if zipper(self.get_wsgi_dir(), target, LAMBDA_EXCLUDE, False, replace_path):
                return target

        return False

    def remove_zip(self, func_name):
        """Remove lambda package from local"""
        try:
            target = TMP_DIR + self.get_zip_name(func_name)
            os.remove(target)
        except OSError:
            pass

    def get_wsgi_dir(self):
        pkg_dir = get_sitepackage_dirs()
        for pd in pkg_dir:
            if os.path.isdir(pd + '/lmdo'):
                wsgi_dir = pd + '/lmdo/wsgi'
                break
        
        return wsgi_dir

    def if_wsgi_exist(self):
        """Checking if wsgi lambda exist in config"""
        exist = False
        for lm in self._config.get('Lambda'):
            if lm.get('Type') == 'wsgi':
                exist = True
                break
        return exist

    def process(self):
        """Prepare function before creation/update"""
        # Dont run if doesn't exist
        if not self._config.get('Lambda'):
            Oprint.info('No Lambda function configured, skip...', 'lambda')
            return True

        # Create all functions
        for lm in self._config.get('Lambda'):

            # If user specify a function
            specify_function = self.if_specify_function()
            if specify_function and specify_function != lm.get('FunctionName'):
                continue
            
            params = {
                'FunctionName': self.get_function_name(lm.get('FunctionName')),
                'Code': {
                    'S3Bucket': lm.get('S3Bucket'),
                    'S3Key': self.get_zip_name(lm.get('FunctionName'))
                },
                'Handler': lm.get('Handler'),
                'MemorySize': lm.get('MemorySize') or LAMBDA_MEMORY_SIZE,
                'Runtime': lm.get('Runtime') or LAMBDA_RUNTIME,
                'Timeout': lm.get('Timeout') or LAMBDA_TIMEOUT,
                'Description': 'Function deployed for service {} by lmdo'.format(self._config.get('Service'))
            }

            if lm.get('Type') == 'wsgi':
                params['Handler'] = 'lmdo_wsgi_handler.handler'

            if lm.get('VpcConfig'):                
                params['VpcConfig'] = lm.get('VpcConfig')
       
            if lm.get('EnvironmentVariables'):
                params['Environment'] = {'Variables': lm.get('EnvironmentVariables')}

            # Clean up before create a new one
            self.remove_zip(lm.get('FunctionName'))
            file_path = self.zip_function(lm.get('FunctionName'), lm.get('Type'))
            
            if file_path:
                if self._s3.upload_file(lm.get('S3Bucket'), file_path, self.get_zip_name(lm.get('FunctionName'))):
                    # If function exists
                    info = self.get_function(self.get_function_name(lm.get('FunctionName')))
                    if info:
                        self.update_function_code(info.get('Configuration').get('FunctionName'), lm.get('S3Bucket'), self.get_zip_name(lm.get('FunctionName')))
                    else:
                        # User configured role or create a new on based on policy document
                        role_arn = lm.get('RoleArn') or self.create_role(self.get_role_name(lm.get('FunctionName')), lm.get('RolePolicy'))
                        params['Role'] = role_arn
                        self.create_function(**params)
                # Clean up
                self.remove_zip(lm.get('FunctionName'))

    def create_role(self, role_name, role_policy):
        """Create role for lambda from policy doc"""
        # If not policy document created, create
        # default role that can invoke lambda and logging
        role = self._iam.create_lambda_role(role_name, role_policy)
        return role.get('Role').get('Arn')

    def delete_role(self, role_arn):
        """Delete role for lambda"""
        self._iam.delete_lambda_role(self.get_role_name_by_arn(role_arn))

    def pip_install(self):
        """Install requirement"""
        if os.path.isfile('./{}'.format(os.getenv('PIP_REQUIREMENTS_FILE', PIP_REQUIREMENTS_FILE))):
            with open('./{}'.format(os.getenv('PIP_REQUIREMENTS_FILE', PIP_REQUIREMENTS_FILE))) as f:
                requirements = f.read().splitlines()

            try:
                for name, detail in lambda_packages.items():
                    if name.lower() in requirements:
                        Oprint.info('Installing Amazon Linux AMI bianry package {}'.format(name), 'pip')
                        
                        tar = tarfile.open(detail['path'], mode="r:gz")
                        for member in tar.getmembers():
                            if member.isdir():
                                shutil.rmtree(os.path.join(os.getenv('PIP_VENDOR_FOLDER', PIP_VENDOR_FOLDER), member.name), ignore_errors=True)
                                continue

                            tar.extract(member, os.getenv('PIP_VENDOR_FOLDER', PIP_VENDOR_FOLDER))
                        
                        Oprint.info('Complete installing Amazon Linux AMI bianry package{}'.format(name), 'pip')
                        requirements.remove(name.lower())

                requirements = ' '.join(requirements)

                Oprint.info('Installing python package dependancies if there is any missing', 'pip')

                spinner.start()
                #pip.main(['install', '-t', os.getenv('PIP_VENDOR_FOLDER', PIP_VENDOR_FOLDER), '-r', os.getenv('PIP_REQUIREMENTS_FILE', PIP_REQUIREMENTS_FILE), '&>/dev/null'])
                os.system('pip install --upgrade -t {} {} &>/dev/null'.format(os.getenv('PIP_VENDOR_FOLDER', PIP_VENDOR_FOLDER), requirements))
                spinner.stop()

                Oprint.info('Python package installation complete', 'pip')


            except Exception as e:
                spinner.stop()
                raise e

        else:
            Oprint.warn('{} could not be found, no dependencies will be installed'.format(os.getenv('PIP_REQUIREMENTS_FILE', PIP_REQUIREMENTS_FILE)), 'pip')

    def pip_wsgi_install(self):
        """Install requirement for wsgi"""
        try:
            Oprint.info('Installing python package dependancies for wsgi', 'pip')

            spinner.start()
            os.system('pip install werkzeug base58 wsgi-request-logger --upgrade -t {} &>/dev/null'.format(os.getenv('PIP_VENDOR_FOLDER', PIP_VENDOR_FOLDER)))
            spinner.stop()

            Oprint.info('Wsgi python package installation complete', 'pip')
        except Exception as e:
            spinner.stop()
            raise e

    def if_specify_function(self):
        """If user specify a function to process"""
        return False if not self._args.get('--function-name') else self._args.get('--function-name')
           
                  
