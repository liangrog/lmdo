from __future__ import print_function

import os
import sys

import jinja2

import yaml

from .config import config_file, config_template, tmp_dir, config_mandatory_keys
from .oprint import Oprint
from .utils import mkdir


class CLoader:
    """
    Configuration Loader
    """

    def __init__(self):
        self.template_config()
        self.load_config()
        self.init_tmp_dir()

    @staticmethod
    def render(tpl_path, context):
        path, filename = os.path.split(tpl_path)
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(path or './')
        ).get_template(filename).render(context)

    def load_config(self):
        """
        Load YAML config file from project directory
        """

        # Check if config file exist and has content
        if not os.path.isfile(config_file) or not os.access(config_file, os.R_OK):
            Oprint.err(config_file + 'file doesn\'t exist in current directory', 'config loader')
            sys.exit(0)

        # Load yaml file
        with open(config_file, 'r') as outfile:
            try:
                self.config = yaml.load(outfile)
            except yaml.YAMLError as e:
                Oprint.err(e, 'config loader')
                sys.exit(0)

        error_msg = self.check_mandatory_keys()
        if error_msg:
            Oprint.err(error_msg, 'config loader')
            sys.exit(0)

    def template_config(self):
        if os.path.isfile(config_template):
            rendered = CLoader.render(config_template, os.environ)
            with open(config_file, 'wb') as fh:
                fh.write(rendered)
                fh.close()
            Oprint.info('%s has been overriden by %s' % (config_file, config_template), 'lmdo')

    def init_tmp_dir(self):
        """
        Initialise temporary directory
        """

        return mkdir(tmp_dir)

    def get_value(self, key):
        """
        Get config value by key
        """

        if key in self.config:
            return self.config[key]

        return None

    def check_mandatory_keys(self):
        """
        Set default value and check if mandatory keys exist
        """

        # Set default profile if doesn't exist
        if len(self.config['Profile']) <= 0:
            self.config['Profile'] = 'default'

        # Set default user if doesn't exist
        if len(self.config['User']) <= 0:
            self.config['User'] = 'default'

        errors = {}
        for k in config_mandatory_keys:
            if k not in self.config:
                errors[k] = 'Missing field'

        if (errors):
            return errors


