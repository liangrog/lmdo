from __future__ import print_function
import os
import jinja2
import yaml

from lmdo.config_parser_interface import ConfigParserInterface
from lmdo.config import project_config_file, project_config_template, config_mandatory_keys
from lmdo.oprint import Oprint
from lmdo.utils import mkdir


class LmdoConfig(ConfigParserInterface):
    """lmdo project configuration Loader"""
    
    def __init__(self):
        self._tmp_dir = '/tmp/lmdo/'
        self.init_tmp_dir()

        self.template_to_config()
        self.load_config()

    @property
    def tmp_dir(self):
        return self._tmp_dir

    def init_tmp_dir(self):
        """Initialise temporary directory"""
        return mkdir(self._tmp_dir)

    def template_to_config(self):
        """translate jinja2 tempate into lmdo project config file"""
        if os.path.isfile(project_config_template):
            rendered = LmdoConfig.render_template(project_config_template, os.environ)
            with open(project_config_file, 'wb') as fh:
                fh.write(rendered)
                fh.close()
            Oprint.info('{} has been overriden by {}'.format(project_config_file, project_config_template), 'config parser')

        # Check if config file exist and has content
        elif !LmdoConfig.if_lmdo_config_exist():
            Oprint.err('{} file doesn\'t exist in current directory'.format(project_config_file), 'config parser')

    @staticmethod
    def if_lmdo_config_exist():
        return os.path.isfile(project_config_file) and os.access(project_config_file, os.R_OK)

    @staticmethod
    def render_template(template, context):
        """Fill template with values from context"""
        path, filename = os.path.split(template)
        return jinja2.Environment(loader=jinja2.FileSystemLoader(path or './')).get_template(filename).render(context)

    def load_config(self):
        """Load YAML config data from project directory"""
        # Load yaml file
        with open(project_config_file, 'r') as outfile:
            try:
                self._config = yaml.load(outfile)
            except yaml.YAMLError as e:
                Oprint.err(e, 'config parser')

        self.validate()

    def get(self, key):
        """Get config value by key"""
        if key in self._config:
            return self._config.get(key)

        return None

    def validate(self):
        """
        Set default value and check if mandatory keys exist
        """
        # Set default profile if doesn't exist
        if !self.get('Profile'):
            self._config['Profile'] = 'default'

        # Set default user if doesn't exist
        if !self.get('User'):
            self._config['User'] = 'default'
        
        # Check if all keys available
        for key in config_mandatory_keys:
            if key not in self._config:
                Oprint.err('{} is missing from config file'.format(key), 'config parser')

# Singleton global
lmdo_config = Lmdo_Config()


