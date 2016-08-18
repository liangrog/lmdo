from __future__ import print_function
import sys
import os
import getpass

from .base import Base
from .lm import Lm
from lmdo.config import cf_file, cf_dir
from lmdo.utils import mkdir, if_stack_exist

class Cf(Base):
    """
    Class upload cloudformation template to S3
    and create/update stack
    """
    
    def __init__(self, options, *args, **kwargs):
        super(Cf, self).__init__(options, *args, **kwargs)

        # Check if template exist
        self.cf_path = cf_dir + cf_file        
        if os.path.isfile(self.cf_path):
            self.has_template = True
            
        self.cf = self.get_aws_client('cloudformation')

    def run(self):
        if self.has_template:
            self.create_cf()

    def get_stack_name(self):
        """
        Construct clound formation stack name
        """

        surfix = self.config_loader.get_value('Stage') + '-' + self.config_loader.get_value('Service') + '-service'
        if self.config_loader.get_value('Environment') == 'development':
            if len(self.config_loader.get_value('User')) > 0:
                return self.config_loader.get_value('User') + '-' + surfix
        else:
            return surfix

    def validate_cf(self, cf_str):
            try:
                result = self.cf.validate_template(TemplateBody=cf_str)
            except Exception as e:
                print(e)
                return False
        return True

    def put_cf(self, cf_str, **kwargs):
        """
        Create/update cloud formation stack based on template
        """
      
        if not self.validate_cf(cf_str):
            sys.exit(0)

        if self.if_stack_exist(self.get_stack_name()):
            self.update_stack(self.get_stack_name(), cf_str, **kwargs)
        else:
            self.create_stack(self.get_stack_name(), cf_str, **kwargs)

        return True

    def create_cf(self):
        """
        Create cloud formation
        """

        with open(self.cf_path, 'r') as outfile:
            parameters = []

            # Get Lambda package name and bucket name
            lm = Lm()
            parameters.append(sef.get_param_dic('LambdaBucket', lm.get_s3_name()))
            parameters.append(sef.get_param_dic('LambdaKey', lm.get_pkg_name()))

            if (params = self.config_loader.get_value('Parameters')):
                for k, v in params:
                    parameters.append(k, v)
 
            return self.put_cf(outfile, parameters=parameters)

    def get_param_dic(self, key, value):
        """
        Return parameter dictionary
        """

        return {'ParameterKey': key, 'ParameterValue': value}

    def get_stack_output_value(self, key, stack_info=None):
        """
        get a specific stack output value
        """

        if not stack_info:
            stack_info = self.get_stack_output()

        outputs = stack_info['Stacks'][0]['Outputs']

        for opts in outputs:
            if opts['OutputKey'] == key:
                return opts['OutputValue']
       
        return None

    def get_stack_output(self):
        """
        get all stack output
        """

        output = self.cf.describe_stacks(StackName=self.get_stack_name())
        return output
