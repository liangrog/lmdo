import os
import re

from lmdo.convertors import Convertor
from lmdo.chain_processor import ChainProcessor
from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint
from lmdo.lmdo_config import lmdo_config
from lmdo.file_loader import FileLoader


class NestedTemplateUrlConvertor(ChainProcessor, Convertor):
    """
    Replace environment variable tags using enviroment variable
    """
    SEARCH_REGX = r'\$template\|[^"\', \r\n]+'
    SEARCH_REGX_STR = r'\$template\|[^"\', \r\n]+'

    @classmethod
    def match(cls, haystack):
        return re.findall(cls.SEARCH_REGX_STR, str(haystack))

    def process(self, data):
        return self.convert(data)

    def convert(self, data):
        """
        Convert all lmdo template url format '$template|[template name]'
        to its value AWS format "https://s3.amazonaws.com/[bucket name]/[service id]/[template name]"
        """
        data_string, _ = data
    
        for key, value in self.replacement_data(data_string).iteritems():
            data_string = data_string.replace(key, value)
        
        return data_string, FileLoader.toJson(data_string)

    def get_pattern(self):
        """Template URL variable pattern $template|[template_name]"""
        return self.SEARCH_REGX

    def get_template_names(self, content):
        """Get all the stack names and keys need to query"""
        search_result = re.findall(self.get_pattern(), content)
        
        if search_result:
            result = []
            for item in search_result:
                header, template_name = item[0:-1].split("|")
                if template_name not in result:
                    result.append(template_name)

            return result

        return []

    def replacement_data(self, content):
        """
        Return translated stack URL in a dict
        """
        aws = AWSBase()
        replacement = {}
        template_names = self.get_template_names(content)

        # Dont continue if there 
        if template_names and not lmdo_config.get('CloudFormation').get('S3Bucket'):
            Oprint.err('Nested stack requires S3 bucket, but found none', 'cloudformation')

        for template_name in template_names:
            url = aws.get_template_s3_url(template_name=template_name)
            from_str = '$template|{}'.format(template_name)
            replacement[from_str] = url                

        return replacement
        

