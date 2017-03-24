import os
import re

from lmdo.convertors import Convertor
from lmdo.chain_processor import ChainProcessor
from lmdo.oprint import Oprint
from lmdo.file_loader import FileLoader

class EnvVarConvertor(ChainProcessor, Convertor):
    """
    Replace environment variable tags using enviroment variable
    tag format:
    $env|[name]
    """
    
    def process(self, data):
        return self.convert(data)

    def convert(self, data):
        """
        Convert all possible environment
        variable name to value
        """
        data_string, _ = data
        
        for key, value in self.replacement_data(data_string).iteritems():
            data_string = data_string.replace(key, value)
        
        return data_string, FileLoader.toJson(data_string)

    def replacement_data(self, content):
        """
        Return enviroment variable in a dict
        with a format of '$env|name': value
        """
        replacement = {}
        for name in self.get_env_names(content):
            key = '$env|{}'.format(name)
            value = os.environ.get(name)
            if not value:
                Oprint.warn('Environment variable {} has no value found'.format(name), 'lmdo')
                continue

            replacement[key] = value
        
        return replacement
        
    def get_pattern(self):
        """Environment variable pattern $env|[env_name]"""
        return r'(\$env\|[^"\', \r\n]+)+'

    def get_env_names(self, content):
        """Get all the stack names and keys need to query"""
        search_result = re.findall(self.get_pattern(), content)
        
        if search_result:
            result = []
            for item in search_result:
                header, env_name = item.split("|")
                if env_name not in result:
                    result.append(env_name)

            return result

        return []


