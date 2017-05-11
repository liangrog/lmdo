from __future__ import print_function

import os

import jinja2

from lmdo.cli import args
from lmdo.config_parser import ConfigParser
from lmdo.file_loader import FileLoader
from lmdo.config import PROJECT_CONFIG_FILE, PROJECT_CONFIG_TEMPLATE, CONFIG_MANDATORY_KEYS
from lmdo.oprint import Oprint
from lmdo.utils import mkdir
from lmdo.convertors.env_var_convertor import EnvVarConvertor


class LmdoConfig(ConfigParser):
    """lmdo project configuration Loader"""
    
    def __init__(self):
        self._args = args
        self.template_to_config()
        self.load_config()

    def get_config_file(self):
      """Get lmdo configuration file"""
      if self._args.get('--config'):
          return self._args.get('--config')
      
      return PROJECT_CONFIG_FILE

    def get_args_value(self, key):
        """Get command line input value"""
        return self._args.get(key, None)

    def template_to_config(self):
        """translate jinja2 tempate into lmdo project config file"""
        if os.path.isfile(PROJECT_CONFIG_TEMPLATE):
            rendered = LmdoConfig.render_template(PROJECT_CONFIG_TEMPLATE, os.environ)
            with open(PROJECT_CONFIG_FILE, 'wb') as fh:
                fh.write(rendered)
                fh.close()
            Oprint.info('{} has been overriden by {}'.format(PROJECT_CONFIG_FILE, PROJECT_CONFIG_TEMPLATE), 'lmdo')

        # Check if config file exist and has content
        elif not LmdoConfig.if_lmdo_config_exist(self._args):
            Oprint.err('{} file doesn\'t exist in current directory'.format(PROJECT_CONFIG_FILE), 'lmdo')

    @staticmethod
    def if_lmdo_config_exist(args):
        return (os.path.isfile(PROJECT_CONFIG_FILE) and os.access(PROJECT_CONFIG_FILE, os.R_OK)) \
            or (os.path.isfile(PROJECT_CONFIG_TEMPLATE) and os.access(PROJECT_CONFIG_TEMPLATE, os.R_OK)) \
            or args.get('--config')

    @staticmethod
    def render_template(template, context):
        """Fill template with values from context"""
        path, filename = os.path.split(template)
        return jinja2.Environment(loader=jinja2.FileSystemLoader(path or './')).get_template(filename).render(context)

    def load_config(self):
        """Load config data from project directory"""
        env_var_convertor = EnvVarConvertor()
        file_loader = FileLoader(file_path=self.get_config_file())
        file_loader.successor = env_var_convertor
        _, self._config = file_loader.process()
        
        self.validate()

    def get(self, key):
        """Get config value by key"""
        if key in self._config:
            return self._config.get(key)

        return None

    @property
    def config(self):
        """Get all config in json"""
        return self._config

    @config.setter
    def config(self, data):
        """Set config in json"""
        self._config = data

    def validate(self):
        """
        Set default value and check if mandatory keys exist
        """
        # Set default profile if doesn't exist
        if not self.get('Profile'):
            self._config['Profile'] = 'default'

        # Set default user if doesn't exist
        if not self.get('User'):
            self._config['User'] = 'default'
 
        # Set default service if doesn't exist
        if not self.get('Service'):
            self._config['Service'] = 'default'
   
        # Set default stage if doesn't exist
        if not self.get('Stage'):
            self._config['Stage'] = 'dev'
      
        # Check if all keys available
        for key in CONFIG_MANDATORY_KEYS:
            if key not in self._config:
                Oprint.err('{} is missing from config file'.format(key), 'lmdo')

lmdo_config = LmdoConfig()
