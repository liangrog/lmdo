from __future__ import print_function
import sys
import os

from .base import Base
from .lm import Lm
from lmdo.config import cf_file, cf_dir
from lmdo.utils import mkdir

class Cf(Base):
    """
    Class upload cloudformation template to S3
    and create/update stack
    """
    
    def __init__(self, options={}, *args, **kwargs):
        super(Cf, self).__init__(options, *args, **kwargs)

        # Check if template exist
        self.cf_path = cf_dir + cf_file
        self.has_template = False
        if os.path.isfile(self.cf_path):
            self.has_template = True
        else:
            print('No cloud formation template found')
            sys.exit(0)
            
        self.cf = self.get_aws_client('cloudformation')

    def run(self):
        if self.has_template:
            self.create_cf()
            self.update_lambda_code()

    def get_stack_name(self):
        """
        Construct clound formation stack name
        """

        surfix = self.config_loader.get_value('Stage') + '-' + self.config_loader.get_value('Service') + '-service'
        return self.config_loader.get_value('User') + '-' + surfix

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
      
        #if not self.validate_cf(cf_str):
        #    sys.exit(0)

        self.update_stack(self.get_stack_name(), cf_str, **kwargs)

        return True

    def create_cf(self):
        """
        Create cloud formation
        """

        with open(self.cf_path, 'r') as outfile:
            template = outfile.read()

            parameters = []

            # Get Lambda package name and bucket name
            lm = Lm()

            parameters.append(self.get_param_dic('LambdaBucket', self.config_loader.get_value('LambdaBucketName')))
            parameters.append(self.get_param_dic('LambdaKey', lm.get_pkg_name()))
            parameters.append(self.get_param_dic('UserName', self.config_loader.get_value('User')))
            parameters.append(self.get_param_dic('StageName', self.config_loader.get_value('Stage')))
            parameters.append(self.get_param_dic('ServiceName', self.config_loader.get_value('Service')))

            params = self.config_loader.get_value('Parameters')

            if (params):
                for k, v in params.items():
                    parameters.append(self.get_param_dic(k, v))
            
            return self.put_cf(template, parameters=parameters)

    def update_lambda_code(self):
        """
        Update lambda code
        """

        lm = Lm()
        lmda = self.get_aws_client('lambda')
        for lfunc in self.config_loader.get_value('LambdaMapping'):
            func_name = self.config_loader.get_value('User') \
                + '-' + self.config_loader.get_value('Stage') \
                + '-' + self.config_loader.get_value('Service') \
                + '-' + lfunc
            try:
                 lmda.update_function_code(
                    FunctionName=func_name,
                    S3Bucket=self.config_loader.get_value('LambdaBucketName'),
                    S3Key=lm.get_pkg_name()
                    )
                 print('Lambda function ' + func_name + ' has been updated')
            except Exception as e:
                print(e)
                
        return True

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

    def destroy(self):
        """
        Destroy the stack
        """

        self.delete_bucket_object()
        self.remove_stack(self.get_stack_name())

    def delete_bucket_object(self):
        """
        Delete all object under a bucket so
        the bucket can be deleted during stack
        removal
        """

        if self.config_loader.get_value('BucketInStackToDestroy'):
            try:
                for bucket in self.config_loader.get_value('BucketInStackToDestroy'):
                    objects = self.s3.list_objects_v2(Bucket=bucket)
                    self.s3.delete_objects(Bucket=bucket, Delete={'Objects': objects['Contents']})
            except Exception as e:
                print(e)
                sys.exit(0)
                    

