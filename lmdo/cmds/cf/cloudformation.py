from __future__ import print_function
import os
import fnmatch
import json

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.s3.s3 import S3
from lmdo.oprint import Oprint
from lmdo.config import CLOUDFORMATION_DIRECTORY, CLOUDFORMATION_TEMPLATE_ALLOWED_POSTFIX, CLOUDFORMATION_TEMPLATE, CLOUDFORMATION_PARAMETER_FILE
from lmdo.utils import find_files_by_postfix, find_files_by_name_only
from lmdo.waiters.cloudformation_waiters import CloudformationWaiterStackCreate, CloudformationWaiterStackUpdate, CloudformationWaiterStackDelete


class Cloudformation(AWSBase):
    """
    Class upload cloudformation template to S3
    and create/update stack
    Stack name is fixed with User-Stage-Servicename-Service
    """

    def __init__(self):
        super(Cloudformation, self).__init__()
        self._client = self.get_client('cloudformation') 
        self._s3 = S3()
        self._template = self.if_main_template_exist()

    @property
    def client(self):
        return self._client
 
    @property
    def s3(self):
        return self._s3
    
    def get_stack_name(self):
        """get defined stack name"""
        return self._config.get('StackName') if self._config.get('StackName') else "{}-service".format(self.get_name_id())

    def create(self):
        """Create/Update stack"""
        # Don't run if we don't have templates
        if not self._template:
            return True
        
        self.process(self.prepare())

    def delete(self):
        """Delete stack"""
        self.delete_stack(self.get_stack_name())

    def update(self):
        """Wrapper, same action as create"""
        self.create()

    def find_main_template(self):
        """Get the main template file"""
        return find_files_by_name_only("./{}".format(CLOUDFORMATION_DIRECTORY), CLOUDFORMATION_TEMPLATE, CLOUDFORMATION_TEMPLATE_ALLOWED_POSTFIX)

    def find_template_files(self):
        """find all files end with .json or .templates"""
        return find_files_by_postfix("./{}".format(CLOUDFORMATION_DIRECTORY), CLOUDFORMATION_TEMPLATE_ALLOWED_POSTFIX)

    def if_main_template_exist(self):
        """Check if we have only one main template defined, allow .json or .template"""
        found_files = self.find_main_template()
        if len(found_files) > 1:
            Oprint.err("You cannot define more than one {} template".format(CLOUDFORMATION_TEMPLATE))
        
        if len(found_files) < 1:
            return False

        # return the main template file name
        return found_files.pop()

    def prepare(self):
        is_local = False
        bucket_name = self._config.get('CloudformationBucket')

        templates = self.find_template_files()

        # Validate syntax of the template
        for template in templates:
            with open("./{}/{}".format(CLOUDFORMATION_DIRECTORY, template), 'r') as outfile: 
                tpl = outfile.read()
                self.validate_template(tpl)

        # If bucket provided, we upload 
        # all templates into the subfolder 
        if bucket_name:
            # Don't upload parameter file
            for f in templates:
                if not fnmatch.fnmatch(f, CLOUDFORMATION_PARAMETER_FILE):
                    self._s3.upload_file(bucket_name, "./{}/{}".format(CLOUDFORMATION_DIRECTORY, f), "{}/{}".format(self.get_stack_name(), f))
        else:
            # Put local prepare here
            is_local = True

        return is_local

    def validate_template(self, template_body):
        """Validate template via content"""
        try:
            result = self._client.validate_template(TemplateBody=template_body)
        except Exception as e:
            Oprint.err(e, 'cloudformation')
        return True

    def get_stack(self, stack_name):
        """Check get stack info"""
        try:
            info = self._client.describe_stacks(StackName=stack_name)
        except Exception as e:
            return False

        return info

    def process(self, is_local):
        """Creating/updating stack"""
        to_update = False
        stack_info = self.get_stack(self.get_stack_name())

        if stack_info:
            # You cannot update a stack with status ROLLBACK_COMPLETE during creation
            if stack_info['Stacks'][0]['StackStatus'] == 'ROLLBACK_COMPLETE':
                Oprint.warn('Stack {} exits with bad state ROLLBACK_COMPLETE. Required to be removed first'.format(self.get_stack_name()), 'cloudformation')
                self.delete_stack(self.get_stack_name())
            else:
                to_update = True

        if is_local:
            # Read template data into cache
            if os.path.isfile("./{}/{}".format(CLOUDFORMATION_DIRECTORY, self._template)):
                with open("./{}/{}".format(CLOUDFORMATION_DIRECTORY, self._template), 'r') as outfile:
                    template_body = outfile.read()
 
            func_params = {
                "TemplateBody": template_body,
            }
        else:
            func_params = {
                "TemplateURL": "{}/{}/{}".format(self._s3.get_bucket_url(self._config.get('CloudformationBucket')), self.get_stack_name(), self._template)
            }

        # If parameters file exist
        if os.path.isfile("./{}/{}".format(CLOUDFORMATION_DIRECTORY, CLOUDFORMATION_PARAMETER_FILE)):
            with open("./{}/{}".format(CLOUDFORMATION_DIRECTORY, CLOUDFORMATION_PARAMETER_FILE), 'r') as outfile:
                func_params['Parameters'] = json.loads(outfile.read())
       
        if to_update:
            self.update_stack(self.get_stack_name(), **func_params)
        else:
            self.create_stack(self.get_stack_name(), **func_params)

    def create_stack(self, stack_name, capabilities=['CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'], **kwargs):
        """Create stack""" 
        try:
            waiter = CloudformationWaiterStackCreate(self._client)            
            response = self._client.create_stack(
                StackName=stack_name,
                Capabilities=capabilities,
                **kwargs
            )
            waiter.wait(stack_name)
        except Exception as e:
            Oprint.err(e, 'cloudformation')
            return False
        
        self.verify_stack('create')

        return True

    def update_stack(self, stack_name, capabilities=['CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'], **kwargs):
        """Update a stack"""
        try:
            waiter = CloudformationWaiterStackUpdate(self._client)
            response = self._client.update_stack(
                StackName=stack_name,
                Capabilities=capabilities,
                **kwargs
            )
            waiter.wait(stack_name)
        except Exception as e:
            Oprint.err(e, 'cloudformation')
            return False

        self.verify_stack('update')

        return True

    def delete_stack(self, stack_name):
        """Remove a stack by given name"""
        # Don't do anything if doesn't exist
        stack_info = self.get_stack(stack_name)
        if not stack_info:
            return True

        try:
            waiter = CloudformationWaiterStackDelete(self._client)
            response = self._client.delete_stack(StackName=stack_name)
            waiter.wait(stack_name)
        except Exception as e:
            Oprint.err(e, 'cloudformation')
            return False

        self.verify_stack('delete', stack_info['Stacks'][0]['StackId']) 
        return True

    def verify_stack(self, mode, stack_id=None):
        """Check if stack action successful, deleted stack must provide stack id"""
        stack_info = self.get_stack(stack_id or self.get_stack_name())
        status = stack_info['Stacks'][0]['StackStatus']

        if mode == 'create':
            if status != 'CREATE_COMPLETE':
                Oprint.err("Create stack failed with status {}".format(status), 'cloudformation')

        if mode == 'update':
            if status != 'UPDATE_COMPLETE':
                Oprint.err("Update stack failed with status {}".format(status), 'cloudformation')

        if mode == 'delete':
            if status != 'DELETE_COMPLETE':
                Oprint.warn("Delete stack failed with status {} (most likely caused by your S3 buckets have contents)".format(status), 'cloudformation')

    def get_output_value(self, stack_name, key):
        """get a specific stack output value"""
        stack_info = self.get_stack(stack_name)
        outputs = stack_info['Stacks'][0]['Outputs']

        for opts in outputs:
            if opts['OutputKey'] == key:
                return opts['OutputValue']
       
        return None
                   

