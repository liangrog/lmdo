import os
import re

from lmdo.convertors import Convertor
from lmdo.chain_processor import ChainProcessor
from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint
from lmdo.file_loader import FileLoader

class StackVarConvertor(ChainProcessor, Convertor):
    """
    Replace environment variable tags using enviroment variable
    tag format:
    $stack|[name]::[key]
    """
    SEARCH_REGX = r'(\$stack\|[^"\', \r\n]+)+'

    def __init__(self):
        self._stack_info_cache = {}

    def process(self, data):
        return self.convert(data)

    def convert(self, data):
        """
        Convert all possible stack output
        variable name to its value
        """
        data_string, _ = data
        
        for key, value in self.replacement_data(data_string).iteritems():
            data_string = data_string.replace(key, value)
        
        return data_string, FileLoader.toJson(data_string)

    def get_pattern(self):
        """Stack variable pattern $stack|[stack_name]::[key]"""
        return self.SEARCH_REGX

    def get_stack_names_and_keys(self, content):
        """Get all the stack names and keys need to query"""
        search_result = re.findall(self.get_pattern(), content)
        
        if search_result:
            result = {}
            for item in search_result:
                header, body = item.split("|")
                stack_name, key = body.split("::")
                if not result.get(stack_name):
                    result[stack_name] = [key]
                else:
                    result[stack_name].append(key)
            return result

        return {}

    def replacement_data(self, content):
        """
        Return enviroment variable in a dict
        with a format of '$env|name': value
        """
        replacement = {}
        for stack_name, keys in self.get_stack_names_and_keys(content).iteritems():
            for key in keys:
                value = self.get_stack_output(stack_name=stack_name, key=key)
                from_str = '$stack|{}::{}'.format(stack_name, key)
                replacement[from_str] = value                
        
        return replacement
        
    def get_stack_output(self, stack_name, key):
        """
        Duplicate function to cloudformation due to avoiding circular
        condition as cloudformation import this module as well
        """
        try:
            if not self._stack_info_cache.get(stack_name):
                self._stack_info_cache[stack_name] = AWSBase().get_client('cloudformation').describe_stacks(StackName=stack_name)

            outputs = self._stack_info_cache[stack_name]['Stacks'][0]['Outputs']
      
            for opts in outputs:
                if opts['OutputKey'] == key:
                    return opts['OutputValue']
            Oprint.warn('Cannot find key {} output from stack {}'.format(key, stack_name), 'lmdo')
        except Exception:
            Oprint.warn('Error while retrieving output from {}'.format(stack_name), 'lmdo')

        return None
 
