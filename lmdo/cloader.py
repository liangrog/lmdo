from __future__ import print_function
import json
import sys
import os

import yaml

from .config import config_file, tmp_dir, config_mandatory_keys, profile
from .utils import mkdir

class CLoader:
    """
    Configuration Loader
    """

    def __init__(self):
        self.load_config()
        self.init_tmp_dir()

    def load_config(self):
        """
        Load YAML config file from project directory
        """
       
        # Check if config file exist and has content
        if not os.path.isfile(config_file) or not os.access(config_file, os.R_OK):
            print(config.config_file, 'file doesn\'t exist in current directory')
            sys.exit(0)
        
        # Load yaml file
        with open(config_file, 'r') as outfile:
            try:
                self.config = yaml.load(outfile)
            except yaml.YAMLError as e:
                print(e)
                sys.exit(0)

        error_msg = self.check_mandatory_keys(self.config)
        if error_msg:
            print(error_msg)
            sys.exit(0)

        print(self.config)
        sys.exit(0)

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

    def check_mandatory_keys(self, config_str):
        """
        Set default value and check if mandatory keys exist
        """

        # Set default profile if doesn't exist
        if len(config_str['Profile']) <= 0:
            config_str['Profile'] = profile
        
        errors = {}
        for k in config_mandatory_keys:
            if k not in config_str:
                errors[k] = 'Missing field'

        if (errors):
            return errors


