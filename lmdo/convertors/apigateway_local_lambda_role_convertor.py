import os
import re

from lmdo.convertors import Convertor
from lmdo.chain_processor import ChainProcessor
from lmdo.oprint import Oprint
from lmdo.cmds.iam.iam import IAM
from lmdo.file_loader import FileLoader


class ApiGatewayLocalLambdaRoleConvertor(ChainProcessor, Convertor):
    """
    Replace variable tags using lambda arn
    tag format:
    $lmdo-lambda-role|[lmdo lambda name]
    """
    SEARCH_REGX = r'(\$lmdo-lambda-role\|[^"\', \r\n]+)+'

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
        with a format of '$lmdo-lambda-role\|name': value
        """
        replacement = {}

        search_result = re.findall(self.get_pattern(), content)
        iam = IAM()
        for item in search_result:
            header, lambda_name = item.split("|")
            role = iam.get_lambda_apigateway_default_role(function_name=lambda_name, lmdo_lambda=True)
            replacement[item] = role['Role'].get('Arn') 
        
        return replacement
        
    def get_pattern(self):
        """Get variable pattern"""
        return self.SEARCH_REGX


