import os
import json

from lmdo.convertors import Convertor
from lmdo.chain_processor import ChainProcessor


class EnvVarConvertor(Convertor, ChainProcessor):
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
        data_string = json.dumps(data)
        
        for key, value in self.replacement_data():
            data_string = data_string.replace(key, value)

        return json.loads(data_string)

    def replacement_data(self):
        """
        Return enviroment variable in a dict
        with a format of '$env|name': value
        """
        replacement = {}
        for key, value in os.environ.iteritems():
            key = '$env|{}'.format(key)
            replacement[key] = value

        return replacement
        

