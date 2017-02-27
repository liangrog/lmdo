from __future__ import print_function
import os
import fnmatch
import json
import datetime
import pprint

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.s3.s3 import S3
from lmdo.oprint import Oprint
from lmdo.config import CLOUDFORMATION_DIRECTORY, CLOUDFORMATION_TEMPLATE_ALLOWED_POSTFIX, CLOUDFORMATION_TEMPLATE, CLOUDFORMATION_PARAMETER_FILE, CLOUDFORMATION_STACK_LOCK_POLICY, CLOUDFORMATION_STACK_UNLOCK_POLICY
from lmdo.utils import find_files_by_postfix, find_files_by_name_only, get_template, sys_pause
from lmdo.waiters.cloudformation_waiters import CloudformationWaiterStackCreate, CloudformationWaiterStackUpdate, CloudformationWaiterStackDelete
from lmdo.cmds.cf.cf_status import CfStatus


class Cloudformation(AWSBase):
    """
    Class upload cloudformation template to S3
    and create/update stack
    Stack name is fixed with User-Stage-Servicename-Service
    """

    def __init__(self, args=None):
        super(Cloudformation, self).__init__()
        self._client = self.get_client('cloudformation') 
        self._s3 = S3()
        self._template = self.if_main_template_exist()
        self._args = args or {}

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
            if self._args.get('-c') or self._args.get('--change_set'):
                self.stack_update_via_change_set(self.get_stack_name, **func_params)
            else:
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

            self.lock_stack(stack_name=stack_name)
        except Exception as e:
            Oprint.err(e, 'cloudformation')
            return False
        
        self.verify_stack('create')

        return True

    def update_stack(self, stack_name, capabilities=['CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'], **kwargs):
        """Update a stack"""
        try:
            self.unlock_stack(stack_name=stack_name)
            waiter = CloudformationWaiterStackUpdate(self._client)
            response = self._client.update_stack(
                StackName=stack_name,
                Capabilities=capabilities,
                **kwargs
            )
            waiter.wait(stack_name)
            self.lock_stack(stack_name=stack_name)
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
            self.unlock_stack(stack_name=stack_name)
            waiter = CloudformationWaiterStackDelete(self._client)
            response = self._client.delete_stack(StackName=stack_name)
            waiter.wait(stack_name)
        except Exception as e:
            Oprint.err(e, 'cloudformation')
            return False

        self.verify_stack('delete', stack_info['Stacks'][0]['StackId']) 
        return True
    
    def get_stack_status(self, stack_id=None, status_niddle=None):
        stack_info = self.get_stack(stack_id or self.get_stack_name())
        status = stack_info['Stacks'][0]['StackStatus']

        if status_niddle == CfStatus.STACK_COMPLETE:
            return True if status.endswith('_COMPLETE') else False
        if status_niddle == CfStatus.STACK_FAILED::
            return True if status.endswith('_FAILED') or status.endswith('ROLLBACK_COMPLETE') else False
        if status_niddle == CfStatus._IN_PROGRESS:
            return True if status.endswith('_IN_PROGRESS') else False

        return status

    def verify_stack(self, mode, stack_id=None):
        """Check if stack action successful, deleted stack must provide stack id"""
        status = self.get_stack_status(stack_id)

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
   
    def list_existing_change_set(self, stack_name, *args, **kwargs):
        """List all existing stack"""
        try:
            response = self._client.list_change_sets(StackName=stack_name, *args, **kwargs)
        except Exception as e:
            Oprint.warn(e, 'cloudformation')
        
        return response

    def describe_change_set(self, change_set_name, *args, **kwargs):
        """Get change set information"""
        try:
            response = self_client.describe_change_set(ChangeSetName=change_set_name, *args, **kwargs)
        except Exception as e:
            Oprint.err(e, 'cloudformation')

        return response

    def create_change_set_name(self, stack_name):
        """Create uniformed change set name"""
        timestamp = '{:%Y-%m-%d-%H-%M-%S}'.format(datetime.datetime.now())
        return '{}-changeset-{}'.format(stack_name, timestamp)

    def delete_change_set(self, change_set_name, *args, **kwargs):
        """Delete existing change set"""
        try:
            response = self._client.delete_change_set(ChangeSetName=change_set_name, *args, **kwargs)
        except Exception as e:
            Oprint.warn(e, 'cloudformation')

        return True

    def create_change_set(self, stack_name, *args, **kwargs):
        """Creating change set"""
        try:
            change_set_name = create_change_set_name(stack_name)

            Oprint.info('Creating change set {} for stack {}'.format(change_set_name, stack_name), 'cloudformation')
            response = self._client.create_change_set(StackName=stack_name, ChangeSetName=change_set_name, *args, **kwargs)
        except Exception as e:
            Oprint.err(e, 'cloudformation')

        return change_set_name

    def excecute_change_set(self, change_set_name, stack_name, *args, **kwargs):
        """Run changeset to make it happen"""
        try:
            self.unlock_stack(stack_name=self.get_stack_name())
            waiter = CloudformationWaiterStackUpdate(self._client)
            Oprint.info('Executing change set {} for updating stack {}'.format(change_set_name, stack_name), 'cloudformation')
            response = self._client.execute_change_set(ChangeSetName=change_set_name, StackName=stack_name, *args, **kwargs)
            waiter.wait(stack_name)
            self.lock_stack(stack_name=self.get_stack_name())
        except Exception as e:
            Oprint.err(e, 'cloudformation')
        
        self.verify_stack('update')

        return response

    def lock_stack(self, stack_name):
        """Lock stack so no changes can be made accidentally"""
        try:
            lock_policy = get_template(CLOUDFORMATION_STACK_LOCK_POLICY)
            with open(lock_policy, 'r') as outfile:
                policy = outfile

            Oprint.info('Locking stack {} to prevent accidental changes'.format(stack_name), 'cloudformation')
            response = self._client.set_stack_policy(Stackname=stack_name, StackPolicyBody=policy)
        except Exception as e:
            Oprint.err(e, 'cloudformation')
        
        return True

    def unlock_stack(self, stack_name):
        """Unlock stack for update"""
        try:
            unlock_policy = get_template(CLOUDFORMATION_STACK_UNLOCK_POLICY)
            with open(unlock_policy, 'r') as outfile:
                policy = outfile

            Oprint.info('Unlocking stack {} for update'.format(stack_name), 'cloudformation')
            response = self._client.set_stack_policy(Stackname=stack_name, StackPolicyBody=policy)
        except Exception as e:
            Oprint.err(e, 'cloudformation')
        
        return True

    def get_stack_event(self, stack_name, *args, **kwargs):
        try:
            response = self._client.describe_stack_events(StackName=stack_name, *args, **kwargs)
        except Exception as e:
            Oprint.warn(e, 'cloudformation')
        return response
    
    def display_stack_event(self, stack_name, *args, **kwargs):
        """Displaying new stack event"""
        events = self.get_stack_event(stack_name=stack_name)['StackEvents']
        events.reverse()
        new_events = [event for event in events if (not self.current_event_timestamp) or (event["Timestamp"] > self.current_event_timestamp)]
        for event in new_events:
            prefix = 'Stack Event | '
            event_info = ' '.join([
                event['Timestamp'].replace(microsecond=0).isoformat(),
                event['LogicalResourceId'],
                event['ResourceType'],
                event['ResourceStatus'],
                event.get('ResourceStatusReason', '')
            ])
            Oprint.info('{}{}'.format(prefix, event_info), 'cloudformation')

    def stack_events_waiter(self):
        pass

    def display_change_set(self, change_set_name, stack_name):
        """Display change set infos"""
        change_set_info = self.describe_change_set(change_set_name=change_set_name, StackName=stack_name)
        pprint.pprint(change_set_info.get('Changes'))

        token = change_set_info.get('NextToken')
        if token:
            while token:
                change_set_info = self.describe_change_set(change_set_name=change_set_name, StackName=stack_name, NextToken=token)
                pprint.pprint(change_set_info.get('Changes'))
                token = change_set_info.get('NextToken')

        return True

    def stack_update_via_change_set(self, stack_name, *args, **kwargs):
        """Securely update a stack"""
        change_set_name = self.create_change_set(stack_name=stack_name, *args, **kwargs)
        self.display_change_set(change_set_name=change_set_name, stack_name=stack_name)
        
        sys_pause('Proceed to execute the change set?[yes/no]', 'yes')

        self.excecute_change_set(ChangeSetName=change_set_name, stack_ame=stack_name)

        return True

        





