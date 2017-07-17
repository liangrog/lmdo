from __future__ import print_function
import os
import pip
import tarfile
import shutil
import tempfile
import subprocess
import glob
import copy
import random
import uuid
import json

from lambda_packages import lambda_packages

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.s3.s3 import S3
from lmdo.cmds.s3.bucket_notification import BucketNotification
from lmdo.cmds.sns.sns import SNS
from lmdo.cmds.iam.iam import IAM
from lmdo.cmds.cwe.cloudwatch_event import CloudWatchEvent
from lmdo.oprint import Oprint
from lmdo.config import LAMBDA_MEMORY_SIZE, LAMBDA_RUNTIME, LAMBDA_TIMEOUT, LAMBDA_EXCLUDE, PIP_VENDOR_FOLDER, PIP_REQUIREMENTS_FILE
from lmdo.utils import zipper, get_sitepackage_dirs, class_function_retry, copytree
from lmdo.spinner import spinner
from lmdo.convertors.stack_var_convertor import StackVarConvertor


class AWSLambda(AWSBase):
    """Class  create/update lambda function"""
    NAME = 'lambda'
    LMDO_HANDLER_DIR = 'lmdo_handlers'

    FUNCTION_TYPE_DEFAULT = 'default'
    FUNCTION_TYPE_WSGI = 'wsgi'
    FUNCTION_TYPE_CLOUDWATCHEVENTS = 'cron_dispatcher'
    FUNCTION_TYPE_HEATER = 'heater'
    FUNCTION_TYPE_GO = 'go'

    HANDLER_WSGI = 'lmdo_wsgi_handler.handler'
    HANDLER_GO = 'go_handler.handler'

    NAME_EVENTS_DISPATCHER = 'lmdo_events_dispatcher'
    HANDLER_EVENTS_DISPATCHER_HANDLER = 'events_dispatcher_handler.handler'

    NAME_HEATER = 'lmdo_heater'
    HANDLER_HEATER_HANDLER = 'heater_handler.handler'

    VIRTUALENV_ZIP_EXCLUDES = [
        '*.exe', '*.DS_Store', '*.Python', '*.git', '.git/*', '*.zip', '*.tar.gz',
        '*.hg', '*.egg-info', 'pip', 'docutils*', 'setuputils*', 'lmdo', 
        'lambda_packages', 'mock', 'boto3', 'botocore', 'git', 'gitdb',
    ]

    VIRTUALENV_EXCLUDE_PACKAGE = [
        "boto3", "lmdo", "lambda-packages", "dateutil", "botocore",
        "s3transfer", "six.py", "jmespath", "concurrent"
    ]

    EVENT_SOURCE_TYPE_S3 = 's3'
    EVENT_SOURCE_TYPE_SNS = 'sns'

    def __init__(self):
        super(AWSLambda, self).__init__()
        self._client = self.get_client('lambda') 
        self._s3 = S3()
        self._bucket_notification = BucketNotification()
        self._sns = SNS()
        self._iam = IAM()
        self._event = CloudWatchEvent()
        self._events_dispatcher_arn = {}
        self._heater_arn = None
        self._default_event_role_arn = None

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
        self.process()

    def package(self):
        self.process()

    def delete(self):
        """Delete lambda functions"""
        # Dont run if doesn't exist
        if not self._config.get('Lambda'):
            Oprint.info('No Lambda function configured, skip', 'lambda')
            return True

        # delete  all functions
        for lm in self._config.get('Lambda'):
            # Delete event source
            self.process_event_source(function_config=lm, delete=True)
            break
            # If user specify a function
            specify_function = self.if_specify_function()
            if specify_function and specify_function != lm.get('FunctionName'):
                continue
 
            # Get function info before being deleted
            info = self.get_function(self.get_lmdo_format_name(lm.get('FunctionName')))
            if info:
                # If it's a dispatcher
                self.delete_rules_for_dispatcher(lm)

                self.delete_function(info.get('Configuration').get('FunctionName'))

                # Remove container heater
                self.heat_down(lm)

                # Delete role if it's created by lmdo
                if not lm.get('RoleArn') or len(lm.get('RoleArn')) <= 0:
                    self.delete_role(info.get('Configuration').get('Role'))
            else:
                Oprint.warn('Cannot find function {} to delete in AWS'.format(self.get_lmdo_format_name(lm.get('FunctionName'))), 'lambda')
            
    def update(self):
        """Wrapper, same action as create"""
        self.create()

    def get_role_name(self, func_name):
        """get defined function name"""
        return "lmdo-{}-{}".format(self.get_name_id(), func_name)

    def get_zip_name(self, func_name):
        """get defined function name"""
        return "{}-{}.zip".format(self.get_name_id(), func_name)

    def get_statement_id(self, func_name, principal_id):
        """get defined function permission statement ID"""
        return "stmt-{}-{}".format(self.get_lmdo_format_name(func_name), principal_id)

    def add_permission(self, func_name, principal, principal_id, action='lambda:InvokeFunction'):
        """Add permission to Lambda function"""
        try:
            response = self._client.add_permission(
                FunctionName=self.get_lmdo_format_name(func_name),
                StatementId=self.get_statement_id(func_name, principal_id),
                Action=action,
                Principal=principal
            )
            Oprint.info('Permission {} has been added for {} with principal {}'.format(action, self.get_lmdo_format_name(func_name), principal), 'lambda')
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
            Oprint.info('Permission has been removed for {}'.format(self.get_lmdo_format_name(func_name)), 'lambda')
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
                FunctionName=self.get_lmdo_format_name(func_name),
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
            Oprint.info('Lambda function {} codes has been updated'.format(func_name), 'lambda')
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
    
    def add_init_file_to_root(self, tmp_path):
        """Make sure we have a __init__.py"""
        init_file = os.path.join(tmp_path, '__init__.py')
        if not os.path.isfile(init_file):
            open(init_file, 'a').close()

    def get_zipped_package(self, function_config):
        """Packaging lambda"""
        func_name = function_config.get('FunctionName')
        func_type = function_config.get('Type')

        # Create packaging temp dir
        lambda_temp_dir = tempfile.mkdtemp()
        # Create zip file temp dir
        target_temp_dir = tempfile.mkdtemp()
        target = '{}/{}'.format(target_temp_dir, self.get_zip_name(func_name))

        self.add_init_file_to_root(lambda_temp_dir)
 
        if func_type == self.FUNCTION_TYPE_WSGI:
            self.pip_wsgi_install(lambda_temp_dir)
      
        # Heater is one file only from lmdo. don't need packages
        if func_type != self.FUNCTION_TYPE_HEATER:
            # Go only need executables
            if func_type == self.FUNCTION_TYPE_GO:
                if not function_config.get('ExecutableName'):
                    Oprint.err('ExecutableName is not defined in lmdo config, function {} won\'t be deployed'.format(func_name), self.NAME)
                    return False, False
                
                # We only have on executable needed 
                shutil.copy(os.path.join(os.getcwd(), function_config.get('ExecutableName')), lambda_temp_dir)
            else: 
                # Copy project files
                copytree(os.getcwd(), lambda_temp_dir, ignore=shutil.ignore_patterns('*.git*'))

            # Installing package
            self.dependency_packaging(lambda_temp_dir)
            
            replace_path = [
                {
                   'from_path': lambda_temp_dir,
                   'to_path': '.'
                }
            ]

            # Zip what we've got so far
            zipper(lambda_temp_dir, target, LAMBDA_EXCLUDE, False, replace_path)

       
        # Default type function doesn't need lmdo's lambda wrappers
        if func_type != self.FUNCTION_TYPE_DEFAULT:
            # Don't load lmdo __init__.py
            if LAMBDA_EXCLUDE.get('LAMBDA_EXCLUDE'):
                LAMBDA_EXCLUDE['file_with_path'].append('*{}/{}/__init__.py'.format(self.LMDO_HANDLER_DIR, func_type))
            else:
                LAMBDA_EXCLUDE['file_with_path'] = ['*{}/{}/__init__.py'.format(self.LMDO_HANDLER_DIR, func_type)]

            replace_path = [
                {
                   'from_path': self.get_lmdo_function_dir(func_type),
                   'to_path': '.'
                }
            ]
            
            # Zip extra lmdo function handler
            zipper(self.get_lmdo_function_dir(func_type), target, LAMBDA_EXCLUDE, False, replace_path)

        shutil.rmtree(lambda_temp_dir)
        return (target_temp_dir, target)

    def get_lmdo_function_dir(self, func_type):
        """Get different function directory"""
        pkg_dir = get_sitepackage_dirs()
        for pd in pkg_dir:
            if os.path.isdir(os.path.join(pd, 'lmdo', self.LMDO_HANDLER_DIR)):
                function_dir = os.path.join(pd, 'lmdo', self.LMDO_HANDLER_DIR, func_type)
                break
        
        return function_dir

    def if_wsgi_exist(self):
        """Checking if wsgi lambda exist in config"""
        exist = False
        for lm in self._config.get('Lambda'):
            if lm.get('Type') == self.FUNCTION_TYPE_WSGI:
                exist = True
                break
        return exist

    def convert_config(self):
        config = self._config.get('Lambda')
        if config:
            # Convert stack output key value if there is any
            _, json_data = StackVarConvertor().process((json.dumps(config), config))
            return json_data

        return False

    def process(self, package_only=False):
        """Prepare function before creation/update"""
        config_data = self.convert_config()
        
        # Dont run if doesn't exist
        if not config_data:
            Oprint.info('No Lambda function configured, skip...', 'lambda')
            return True

        # Create all functions
        for lm in config_data:
            self.function_update_or_create(lm, package_only)

        return True

    def function_update_or_create(self, function_config, package_only=False, ignore_cmd=False):
        """Create/update function based on config"""
        # If user specify a function
        specify_function = self.if_specify_function()
        if not ignore_cmd and specify_function and specify_function != function_config.get('FunctionName'):
            return True
 
        function_config = self.update_function_config(function_config)
        
        params = {
            'FunctionName': self.get_lmdo_format_name(function_config.get('FunctionName')),
            'Code': {
                'S3Bucket': function_config.get('S3Bucket'),
                'S3Key': self.get_zip_name(function_config.get('FunctionName'))
            },
            'Handler': function_config.get('Handler'),
            'MemorySize': function_config.get('MemorySize') or LAMBDA_MEMORY_SIZE,
            'Runtime': function_config.get('Runtime') or LAMBDA_RUNTIME,
            'Timeout': function_config.get('Timeout') or LAMBDA_TIMEOUT,
            'Description': function_config.get('Description') or 'Function deployed for service {} by lmdo'.format(self._config.get('Service'))
        }
        
        if function_config.get('VpcConfig'):                
            params['VpcConfig'] = function_config.get('VpcConfig')

        if function_config.get('EnvironmentVariables'):
            ev = function_config.get('EnvironmentVariables')
            # Convert all value to string
            nev = {}
            for k, v in ev.iteritems():
                nev[k] = str(v)

            params['Environment'] = {'Variables': nev}

        tmp_path, zip_package = self.get_zipped_package(function_config)
        
        if zip_package:
            # Only package up lambda function
            if self._args.get('package'):
                Oprint.info('Generated zipped lambda package {}'.format(zip_package), 'lambda')
                return True

            if self._s3.upload_file(function_config.get('S3Bucket'), zip_package, self.get_zip_name(function_config.get('FunctionName'))):
                # If function exists
                info = self.get_function(self.get_lmdo_format_name(function_config.get('FunctionName')))
                if info:
                    role_arn = function_config.get('RoleArn') or self.create_role(self.get_role_name(function_config.get('FunctionName')), function_config.get('RolePolicy'))
                    self.update_function_code(info.get('Configuration').get('FunctionName'), function_config.get('S3Bucket'), self.get_zip_name(function_config.get('FunctionName')))
                   
                    params.pop('Code')
                    self._client.update_function_configuration(**params)
                    Oprint.info('Updated lambda function configuration', 'lambda')
                else:
                    # User configured role or create a new on based on policy document
                    role_arn = function_config.get('RoleArn') or self.create_role(self.get_role_name(function_config.get('FunctionName')), function_config.get('RolePolicy'))
                    params['Role'] = role_arn
                    self.create_function(**params)

            # Clean up
            shutil.rmtree(tmp_path)
        
        # Add container heater
        self.heat_up(function_config)
        # If it's a dispatcher
        self.create_dispatcher_and_rules(function_config)

        # If it has event source configuration
        self.process_event_source(function_config)

    def update_function_config(self, function_config):
        """Update function config value based on types"""
        # Set default if not set
        function_type = function_config.get('Type', self.FUNCTION_TYPE_DEFAULT)
        function_config['Type'] = function_type

        if function_type == self.FUNCTION_TYPE_WSGI:
            function_config['Handler'] = self.HANDLER_WSGI
            function_config['Description'] = 'Lmdo WSGI function deployed for service {} by lmdo'.format(self._config.get('Service'))

        if function_type == self.FUNCTION_TYPE_CLOUDWATCHEVENTS:
            function_config['Handler'] = self.HANDLER_EVENTS_DISPATCHER_HANDLER
            function_config['Description'] = 'Lmdo cloudwatch event function deployed for service {} by lmdo'.format(self._config.get('Service'))
 
        if function_type == self.FUNCTION_TYPE_GO:
            function_config['Handler'] = self.HANDLER_GO
            env_var = {"GO_EXE": function_config.get('ExecutableName')}
            function_config['EnvironmentVariables'] = dict(env_var, **function_config.get('EnvironmentVariables', {}))

        return function_config

    def create_role(self, role_name, role_policy):
        """Create role for lambda from policy doc"""
        # If not policy document created, create
        # default role that can invoke lambda and logging
        role = self._iam.create_lambda_role(role_name, role_policy)
        return role.get('Role').get('Arn')

    def delete_role(self, role_arn):
        """Delete role for lambda"""
        self._iam.delete_lambda_role(self.get_role_name_by_arn(role_arn))

    def dependency_packaging(self, tmp_path):
        """Packaging dependencies"""
        if self._config.get('VirtualEnv'):
            self.venv_package_install(tmp_path)
        else:
            self.package_install(tmp_path)

    def package_install(self, tmp_path):
        """Install requirement"""
        if os.path.isfile('{}/{}'.format(tmp_path, os.getenv('PIP_REQUIREMENTS_FILE', PIP_REQUIREMENTS_FILE))):
            with open('{}/{}'.format(tmp_path, os.getenv('PIP_REQUIREMENTS_FILE', PIP_REQUIREMENTS_FILE))) as f:
                requirements = [item.strip().lower() for item in f.read().splitlines() if item.strip()]
            try:
                lambda_pkg_to_install = {}
                
                # Filter function to find package should 
                # be fetched from lambda package
                def find_lambda_pkg(item):
                    found = False
                    for name, detail in lambda_packages.items(): 
                        if item.startswith(name.lower()):
                            lambda_pkg_to_install[name.lower()] = detail
                            return False
                        else:
                            continue

                    return True

                requirements = filter(find_lambda_pkg, requirements)
                # always install setup tool
                requirements.append('setuptools')
   
                for name, detail in lambda_pkg_to_install.iteritems():
                    Oprint.info('Installing Amazon Linux AMI bianry package {} to {}'.format(name, tmp_path), 'pip')
                    
                    tar = tarfile.open(detail['path'], mode="r:gz")
                    for member in tar.getmembers():
                        if member.isdir():
                            shutil.rmtree(os.path.join(tmp_path, member.name), ignore_errors=True)
                            continue

                        #tar.extract(member, os.getenv('PIP_VENDOR_FOLDER', PIP_VENDOR_FOLDER))
                        tar.extract(member, tmp_path)
           
                tmp_requirements = tempfile.NamedTemporaryFile(delete=False)
                for line in requirements:                     
                    tmp_requirements.write(line + '\n')
                tmp_requirements.close()

                Oprint.info('Installing python package dependancies to {}'.format(tmp_path), 'pip')
                spinner.start()
                os.system('pip install -t {} -r {} &>/dev/null'.format(tmp_path, tmp_requirements.name))
                spinner.stop()
            except Exception as e:
                spinner.stop()
                Oprint.err(e, 'pip')
        else:
            Oprint.warn('{} could not be found, no dependencies will be installed'.format(os.getenv('PIP_REQUIREMENTS_FILE', PIP_REQUIREMENTS_FILE)), 'pip')

    def pip_wsgi_install(self, tmp_path):
        """Install requirement for wsgi"""
        try:
            Oprint.info('Installing python package dependancies for wsgi', 'pip')

            spinner.start()
            os.system('pip install werkzeug base58 wsgi-request-logger -t {} &>/dev/null'.format(tmp_path))
            spinner.stop()

            #Oprint.info('Wsgi python package installation complete', 'pip')
        except Exception as e:
            spinner.stop()
            raise e
    
    def venv_package_install(self, tmp_path):
        """Install virtualenv packages"""
        import pip
        venv = self.get_current_venv_path()
        
        cwd = os.getcwd()

        def splitpath(path):
            parts = []
            (path, tail) = os.path.split(path)
            while path and tail:
                parts.append(tail)
                (path, tail) = os.path.split(path)
            parts.append(os.path.join(path, tail))
            return map(os.path.normpath, parts)[::-1]
        split_venv = splitpath(venv)
        split_cwd = splitpath(cwd)

        # Ideally this should be avoided automatically,
        # but this serves as an okay stop-gap measure.
        if split_venv[-1] == split_cwd[-1]:  # pragma: no cover
            Oprint.warn("Warning! Your project and virtualenv have the same name! You may want to re-create your venv with a new name, or explicitly define a 'project_name', as this may cause errors.", 'lambda')

        # Then, do site site-packages..
        egg_links = []
        
        site_packages = os.path.join(venv, 'lib', 'python2.7', 'site-packages')
        egg_links.extend(glob.glob(os.path.join(site_packages, '*.egg-link')))
        Oprint.info('Copying lib packages over', 'pip')
        copytree(site_packages, tmp_path, symlinks=False, ignore=shutil.ignore_patterns(*self.VIRTUALENV_ZIP_EXCLUDES))
       
        # We may have 64-bin specific packages too.
        site_packages_64 = os.path.join(venv, 'lib64', 'python2.7', 'site-packages')
        if os.path.exists(site_packages_64):
            egg_links.extend(glob.glob(os.path.join(site_packages_64, '*.egg-link')))
            Oprint.info('Copying lib64 packages over', 'pip')
            copytree(site_packages_64, tmp_path, symlinks=False, ignore=shutil.ignore_patterns(*self.VIRTUALENV_ZIP_EXCLUDES))

        if egg_links:
            self.copy_editable_packages(egg_links, tmp_path)

        package_to_keep = []
        if os.path.isdir(site_packages):
            package_to_keep += os.listdir(site_packages)
        if os.path.isdir(site_packages_64):
            package_to_keep += os.listdir(site_packages_64)
        
        installed_packages_name_set = self.get_virtualenv_installed_package()
        # First, try lambda packages
        for name, details in lambda_packages.iteritems():
            if name.lower() in installed_packages_name_set:
                Oprint.info('Installing Lambda_package Amazon Linux AMI bianry package {} to {}'.format(name, tmp_path), 'pip')
                tar = tarfile.open(details['path'], mode="r:gz")
                for member in tar.getmembers():
                    # If we can, trash the local version.
                    if member.isdir():
                        shutil.rmtree(os.path.join(tmp_path, member.name), ignore_errors=True)
                        continue

                    tar.extract(member, tmp_path)

                installed_packages_name_set.remove(name.lower())

        # Then try to use manylinux packages from PyPi..
        # Related: https://github.com/Miserlou/Zappa/issues/398
        try:
            Oprint.info('Installing virtualenv python package dependancies to {}'.format(tmp_path), 'pip')
            spinner.start()
            for installed_package_name in installed_packages_name_set:
                wheel_url = self.get_manylinux_wheel(installed_package_name)
                if wheel_url:
                    resp = requests.get(wheel_url, timeout=2, stream=True)
                    resp.raw.decode_content = True
                    zipresp = resp.raw
                    with zipfile.ZipFile(BytesIO(zipresp.read())) as zfile:
                        zfile.extractall(tmp_path)
            spinner.stop()
        except Exception as e:
            spinner.stop()
            Oprint.warn(e, 'pip')
    
    def get_virtualenv_installed_package(self):
        """Call freeze from shell to get the list of installed packages"""
        command = ['pip', 'freeze']
        return [pkg.split('==')[0].lower() for pkg in subprocess.check_output(command).decode('utf-8').splitlines() if pkg.split('==')[0].lower() not in self.VIRTUALENV_EXCLUDE_PACKAGE]

    def copy_editable_packages(self, egg_links, temp_package_path):
        """Copy editable packages"""
        Oprint.info('Copying editable packages over', 'pip')
        for egg_link in egg_links:
            with open(egg_link) as df:
                egg_path = df.read().decode('utf-8').splitlines()[0].strip()
                pkgs = {x.split(".")[0] for x in find_packages(egg_path, exclude=['test', 'tests'])}
                for pkg in pkgs:
                    copytree(os.path.join(egg_path, pkg), os.path.join(temp_package_path, pkg), symlinks=False)

        if temp_package_path:
            # now remove any egg-links as they will cause issues if they still exist
            for link in glob.glob(os.path.join(temp_package_path, "*.egg-link")):
                os.remove(link)

    def get_current_venv_path(self):
        """
        Returns the path to the current virtualenv
        """
        Oprint.info('Identifying current virtualenv path', 'pip')
        if 'VIRTUAL_ENV' in os.environ:
            venv = os.environ['VIRTUAL_ENV']
        elif os.path.exists('.python-version'):  # pragma: no cover
            try:
                subprocess.check_output('pyenv', stderr=subprocess.STDOUT)
            except OSError:
                Oprint.err("This directory seems to have pyenv's local venv but pyenv executable was not found.", 'pip')
            with open('.python-version', 'r') as f:
                env_name = f.read()[:-1]
            bin_path = subprocess.check_output(['pyenv', 'which', 'python']).decode('utf-8')
            venv = bin_path[:bin_path.rfind(env_name)] + env_name
        else:  # pragma: no cover
            Oprint.err("An active virtual environment is not found", 'lambda')

        return venv

    def get_manylinux_wheel(self, package):
        """
        For a given package name, returns a link to the download URL,
        else returns None.
        """
        url = 'https://pypi.python.org/pypi/{}/json'.format(package)
        try:
            res = requests.get(url, timeout=1.5)
            data = res.json()
            version = data['info']['version']
            for f in data['releases'][version]:
                if f['filename'].endswith('cp27mu-manylinux1_x86_64.whl'):
                    return f['url']
        except Exception, e: # pragma: no cover
            return None
        return None

    def if_specify_function(self):
        """If user specify a function to process"""
        return False if not self._args.get('--function') else self._args.get('--function')
   
    def get_events_dispatcher_arn(self, function_name):
        """Fetch lmdo events dispatcher arn"""
        # Return cache
        if not self._events_dispatcher_arn.get(function_name):
            # Return arn if exist otherwise create a new one
            info = self.get_function(self.get_lmdo_format_name(function_name))
            if not info or not info.get('Configuration').get('FunctionArn'):
                Oprint.err('You have not config lmdo event dispatch lambda function', self.NAME)
                
            self._events_dispatcher_arn[function_name] = info.get('Configuration').get('FunctionArn')
            
        return self._events_dispatcher_arn.get(function_name)

    def add_event_permission_to_lambda(self, lambda_arn, unique_code):
        """
        Add permission to Lambda function so that
        the topic can trigger Lambda
        """
        if not self.if_lambda_function(lambda_arn):
            return False

        function_name = self.get_function_name_by_lambda_arn(lambda_arn)
        stmt_id = 'Stmts-%s-lambda-%s' % (function_name, unique_code)

        response = self._client.add_permission(
            FunctionName=function_name,
            StatementId=stmt_id,
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com'
        )

        if response.get('Statement') is None:
            raise ValueError('Create lambda permission for Event topic failed')

        return stmt_id

    def delete_event_permission_to_lambda(self, lambda_arn, unique_code):
        """
        Delete permission to Lambda function
        """
        if not self.if_lambda_function(lambda_arn):
            return False
        try: 
            function_name = self.get_function_name_by_lambda_arn(lambda_arn)
            stmt_id = 'Stmts-%s-lambda-%s' % (function_name, unique_code)

            response = self._client.remove_permission(
                FunctionName=function_name,
                StatementId=stmt_id
            )
        except Exception as e:
            pass 

        return True

    def get_default_event_role_arn(self):
        """Get default event role"""
        if not self._default_event_role_arn:
            self._default_event_role_arn = self._iam.create_default_events_role(role_name=self.get_lmdo_format_name('default-events-lambda'))['Role']['Arn']

        return self._default_event_role_arn

    def delete_default_event_role_arn(self):
        """Get default event role"""
        self._default_event_role_arn = None 
        self._iam.delete_default_events_role(role_name=self.get_lmdo_format_name('default-events-lambda'))

        return True

    def delete_rules_for_dispatcher(self, function_config):
        """Delete rules for associated dispatcher"""
        if function_config.get('Type') != self.FUNCTION_TYPE_CLOUDWATCHEVENTS:
            return True
    
        rule_data = self.get_rule_data_for_dispatcher(function_config=function_config, delete=False)
        for rule in rule_data:
            self._event.delete_rule(name=rule.get('Name'))

        return True

    def create_dispatcher_and_rules(self, function_config):
        """Create rules for associated dispatcher"""
        if function_config.get('Type') != self.FUNCTION_TYPE_CLOUDWATCHEVENTS:
            return True
        
        rule_data = self.get_rule_data_for_dispatcher(function_config=function_config)
        if not rule_data:
            return True
        
        for rule in rule_data:
            target = rule.pop("Target")
            self._event.upsert_rule(**rule)
            self._event.upsert_targets(rule_name=rule.get('Name'), targets=target)

        return True

    def get_rule_data_for_dispatcher(self, function_config, delete=False):
        """Prepare rule data for dispatcher function"""
        if not function_config.get('RuleHandlers'):
            return False

        rule_data = []
        for handler in function_config.get('RuleHandlers'):
            # We only need the name for delete
            if delete:
                rule = {
                    "Name": '{}--{}'.format(self.get_lmdo_format_name(function_config['FunctionName']), handler.get('Handler'))
                }
            else:    
                rule = {
                    "Name": '{}--{}'.format(self.get_lmdo_format_name(function_config['FunctionName']), handler.get('Handler')),
                    "ScheduleExpression": handler.get('Rate'),
                    "State": 'ENABLED',
                    "Description": 'Lmdo dispatcher function',
                    "RoleArn": self.get_default_event_role_arn(),
                    "Target": [
                        {
                            'Id': str(uuid.uuid4()),
                            'Arn': self.get_events_dispatcher_arn(function_config.get('FunctionName'))
                        }
                     ]
                }
                rule_data.append(rule)

        return rule_data

    def heat_up(self, function_config):
        """Setup scheduled event to heat up the function by invoking it"""
        # if no heatup or rule exists
        if not function_config.get('HeatUp'):
            return False

        self.create_heater(function_config.get('S3Bucket'))
        rule_name = '{}--{}'.format(self.NAME_HEATER, self.get_lmdo_format_name(function_config.get('FunctionName'))) 

        rule = self._event.upsert_rule(
            Name=rule_name,
            ScheduleExpression=function_config.get('HeatRate', 'rate(4 minutes)'),
            State='ENABLED',
            Description='Lmdo heating function',
            RoleArn=self.get_default_event_role_arn()
        )

        target = self._event.upsert_targets(    
            rule_name=rule_name,
            targets=[
                {
                    'Id': str(uuid.uuid4()),
                    'Arn': self._heater_arn,
                }
            ]
        )

    def heat_down(self, function_config):
        """Setup scheduled event to heat up the function by invoking it"""
        rule_name = '{}--{}'.format(self.NAME_HEATER, self.get_lmdo_format_name(function_config.get('FunctionName')))
        
        response = None
        try: 
            response = self._event.client.describe_rule(Name=rule_name)
        except Exception as e:
            pass

        # if no heatup or rule exists
        if not function_config.get('HeatUp') or not response:
            return False
        
        self._event.delete_rule(name=rule_name)

        self.delete_heater()

    def create_heater(self, s3_bucket):
        """Create lmdo heater function"""
        function_config = {
            'FunctionName': self.NAME_HEATER,
            'Type': self.FUNCTION_TYPE_HEATER,
            'S3Bucket': s3_bucket,
            'Handler': self.HANDLER_HEATER_HANDLER,
            'Description': 'Lmdo heating function deployed for service {} by lmdo'.format(self._config.get('Service'))
        }

        if not self._heater_arn:
            info = self.get_function(self.get_lmdo_format_name(self.NAME_HEATER))
            if not info:
                self.function_update_or_create(function_config=function_config, ignore_cmd=True)
            
            info = self.get_function(self.get_lmdo_format_name(self.NAME_HEATER))
            self._heater_arn = info.get('Configuration').get('FunctionArn')
            self.delete_event_permission_to_lambda(self._heater_arn, self.NAME_HEATER)
            self.add_event_permission_to_lambda(self._heater_arn, self.NAME_HEATER)

        return self._heater_arn

    def delete_heater(self):
        # Get function info before being deleted
        info = self.get_function(self.get_lmdo_format_name(self.NAME_HEATER))
        if info:
            self.delete_function(info.get('Configuration').get('FunctionName'))
            self.delete_role(info.get('Configuration').get('Role'))

    def add_permission_to_lambda(self, function_name, unique_code, principal, source_arn):
        """
        Add permission to Lambda function so that
        the s3 can trigger Lambda
        """
        stmt_id = 'Stmts-{}'.format(unique_code)

        response = self._client.add_permission(
            FunctionName=function_name,
            StatementId=stmt_id,
            Action='lambda:InvokeFunction',
            Principal=principal,
            SourceArn=source_arn
        )

        if response.get('Statement') is None:
            raise ValueError('Create lambda permission for s3 failed')

        return stmt_id

    def delete_permission_to_lambda(self, function_name, unique_code):
        """
        Delete s3 permission to Lambda function
        """
        try: 
            stmt_id = 'Stmts-{}'.format(unique_code)

            response = self._client.remove_permission(
                FunctionName=function_name,
                StatementId=stmt_id
            )
        except Exception as e:
            pass 

        return True

    def process_event_source(self, function_config, delete=False):
        """Updating event source"""
        for event in function_config.get('EventSource', []):
            event['FunctionName'] = self.get_lmdo_format_name(function_config['FunctionName'])                
            # S3 event
            if event['Type'] == self.EVENT_SOURCE_TYPE_S3:
                # Always delete first
                self.delete_permission_to_lambda(function_name=event['FunctionName'], unique_code=event['BucketName'].replace('.', '-'))

                if not delete:
                    self.add_permission_to_lambda(function_name=event['FunctionName'], unique_code=event['BucketName'].replace('.', '-'), principal='s3.amazonaws.com', source_arn=self.get_s3_arn(event['BucketName']))
                else:
                    event['Delete'] = True

                self._bucket_notification.update(event)
            # SNS event
            if event['Type'] == self.EVENT_SOURCE_TYPE_SNS:
                # Always delete first
                self.delete_permission_to_lambda(function_name=event['FunctionName'], unique_code=event['Topic'])

                if not delete:
                    self.add_permission_to_lambda(function_name=event['FunctionName'], unique_code=event['Topic'], principal='sns.amazonaws.com', source_arn=self.get_sns_topic_arn(event['Topic']))

                if not delete:
                    self._sns.update_event_source(event)
                else:
                    self._sns.remove_event_source(event)


