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

from lambda_packages import lambda_packages

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.s3.s3 import S3
from lmdo.cmds.iam.iam import IAM
from lmdo.oprint import Oprint
from lmdo.config import LAMBDA_MEMORY_SIZE, LAMBDA_RUNTIME, LAMBDA_TIMEOUT, LAMBDA_EXCLUDE, PIP_VENDOR_FOLDER, PIP_REQUIREMENTS_FILE
from lmdo.utils import zipper, get_sitepackage_dirs, class_function_retry, copytree
from lmdo.spinner import spinner


class Lambda(AWSBase):
    """Class  create/update lambda function"""
    NAME = 'lambda'
    LMDO_HANDLER_DIR = 'lmdo_handlers'

    FUNCTION_TYPE_DEFAULT = 'default'
    FUNCTION_TYPE_WSGI = 'wsgi'
    FUNCTION_TYPE_CLOUDWATCHEVENTS = 'cloudwatch_events'

    HANDLER_WSGI = 'lmdo_wsgi_handler.handler'

    NAME_EVENTS_DISPATCHER = 'lmdo_events_dispatcher'
    HANDLER_EVENTS_DISPATCHER_HANDLER = 'events_dispatcher_handler.handler'

    VIRTUALENV_ZIP_EXCLUDES = [
        '*.exe', '*.DS_Store', '*.Python', '*.git', '.git/*', '*.zip', '*.tar.gz',
        '*.hg', '*.egg-info', 'pip', 'docutils*', 'setuputils*', 'lmdo', 
        'lambda_packages', 'mock', 'boto3', 'botocore', 'git', 'gitdb',
    ]

    VIRTUALENV_EXCLUDE_PACKAGE = [
        "boto3", "lmdo", "lambda-packages", "dateutil", "botocore",
        "s3transfer", "six.py", "jmespath", "concurrent"
    ]

    def __init__(self, args=None):
        super(Lambda, self).__init__()
        self._client = self.get_client('lambda') 
        self._s3 = S3()
        self._iam = IAM()
        self._args = args or {}
        self._events_dispatcher_arn = None

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
            
            # If user specify a function
            specify_function = self.if_specify_function()
            if specify_function and specify_function != lm.get('FunctionName'):
                continue
 
            # Get function info before being deleted
            info = self.get_function(self.get_lmdo_format_name(lm.get('FunctionName')))
            if info:
                self.delete_function(info.get('Configuration').get('FunctionName'))

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

    def get_zipped_package(self, func_name, func_type):
        """Packaging lambda"""
        # Copy project file to temp
        lambda_temp_dir = tempfile.mkdtemp()
        copytree(os.getcwd(), lambda_temp_dir, ignore=shutil.ignore_patterns('*.git*'))
        self.add_init_file_to_root(lambda_temp_dir)

        # Installing packages
        self.dependency_packaging(lambda_temp_dir)
        
        if func_type == self.FUNCTION_TYPE_WSGI:
            self.pip_wsgi_install(lambda_temp_dir)

        target_temp_dir = tempfile.mkdtemp()
        target = '{}/{}'.format(target_temp_dir, self.get_zip_name(func_name))
        replace_path = [
            {
               'from_path': lambda_temp_dir,
               'to_path': '.'
            }
        ]

        # Zip what we'v got so far
        zipper(lambda_temp_dir, target, LAMBDA_EXCLUDE, False, replace_path)

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

    def process(self, package_only=False):
        """Prepare function before creation/update"""
        # Dont run if doesn't exist
        if not self._config.get('Lambda'):
            Oprint.info('No Lambda function configured, skip...', 'lambda')
            return True

        # Create all functions
        for lm in self._config.get('Lambda'):
            self.function_update_or_create(lm, package_only)

        return True

    def function_update_or_create(self, function_config, package_only=False):
        """Create/update function based on config"""
        # If user specify a function
        specify_function = self.if_specify_function()
        if specify_function and specify_function != function_config.get('FunctionName'):
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
            params['Environment'] = {'Variables': function_config.get('EnvironmentVariables')}

        tmp_path, zip_package = self.get_zipped_package(function_config.get('FunctionName'), function_config.get('Type'))
        
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
            function_config['FunctionName'] = self.NAME_EVENTS_DISPATCHER
            function_config['Description'] = 'Lmdo cloudwatch event function deployed for service {} by lmdo'.format(self._config.get('Service'))
        
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
                Oprint.warn(installed_package_name)
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
                pkgs = set([x.split(".")[0] for x in find_packages(egg_path, exclude=['test', 'tests'])])
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
   
    def get_events_dispatcher_name(self):
        """lmdo events dispatcher function name"""
        return self.get_lmdo_format_name(self.NAME_EVENTS_DISPATCHER)

    def get_events_dispatcher_arn(self):
        """Fetch lmdo events dispatcher arn"""
        # Return cache
        if self._events_dispatcher_arn:
            return self._events_dispatcher_arn

        # Return arn if exist otherwise create a new one
        info = self.get_function(self.get_events_dispatcher_name())
        if not info.get('Configuration').get('FunctionArn'):
            Oprint.err('You have not config lmdo event dispatch lambda function', self.NAME)

        self._events_dispatcher_arn = info.get('Configuration').get('FunctionArn')
        
        return self._events_dispatcher_arn

    def get_function_name_by_lambda_arn(self, arn):
        """
        Strip function number from ARN
        """
        arn_list = arn.split(':')
        return arn_list.pop()

    def if_lambda_function(self, arn):
        """Check if arn is function"""
        arns = arn.split(':')
        if 'function' in arns:
            return True

        return False

    def add_event_permission_to_lambda(self, lambda_arn):
        """
        Add SNS permission to Lambda function so that
        the topic can trigger Lambda
        """
        if not self.if_lambda_function(lambda_arn):
            return False

        function_name = self.get_function_name_by_lambda_arn(lambda_arn)
        stmt_id = 'Stmts-%s-sns-%s' % (function_name, str(random.randrange(1000000, 10000000)))

        response = self._client.add_permission(
            FunctionName=function_name,
            StatementId=stmt_id,
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com'
        )

        if response.get('Statement') is None:
            raise ValueError('Create lambda permission for SNS topic failed')

        return stmt_id


