import os
import json
import re

from lmdo.convertors import Convertor
from lmdo.chain_processor import ChainProcessor
from lmdo.cmds.cf.cloudformation import Cloudformation

class StackVarConvertor(Convertor, ChainProcessor):
    """
    Replace environment variable tags using enviroment variable
    tag format:
    $stack|[name]::[key]
    """

    def process(self, data):
        return self.convert(data)

    def convert(self, data):
        """
        Convert all possible stack output
        variable name to its value
        """
        data_string = json.dumps(data)
    
        for key, value in self.replacement_data(data_string):
            data_string = data_string.replace(key, value)

        return json.loads(data_string)

    def get_pattern(self):
        """Stack variable pattern $stack|[stack_name]::[key]"""
        return r'"\$stack\|.*?"'

    def get_stack_names_and_keys(self, content):
        """Get all the stack names and keys need to query"""
        search_result = re.findall(self.get_pattern(), content)
        
        if search_result:
            result = {}
            for item in search_result:
                header, body = item[1,-1].split("|")
                stack_name, key = body.split("::")
                if not result.get(stack_name):
                    result[stack_name] = [key]
                else:
                    result[stack_name].append(key)
            return result

        return []

    def replacement_data(self, content):
        """
        Return enviroment variable in a dict
        with a format of '$env|name': value
        """
        cf = Cloudformation()
        replacement = {}
        for stack_name, keys in self.get_stack_names_and_keys(content):
            for key in keys:
                value = cf.get_output_value(stack_name=stack_name, key=key, cached=True)
                from_str = '$stack|{}::{}'.format(stack_name, key)
                replacement[from_str] = value                

        return replacement
        

