from __future__ import print_function
import os
import fnmatch
import json
import datetime
import time
import shutil

from botocore.exceptions import ClientError

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.s3.s3 import S3
from lmdo.oprint import Oprint
from lmdo.config import CLOUDFORMATION_STACK_LOCK_POLICY, CLOUDFORMATION_STACK_UNLOCK_POLICY
from lmdo.utils import find_files_by_postfix, find_files_by_name_only, get_template, sys_pause
from lmdo.waiters.cloudformation_waiters import CloudformationWaiterStackCreate, CloudformationWaiterStackUpdate, CloudformationWaiterStackDelete, CloudformationWaiterChangeSetCreateComplete
from lmdo.cmds.cf.cf_status import CfStatus
from lmdo.utc import utc
from lmdo.resolvers import ParamsResolver, TemplatesResolver


class Cloudformation(AWSBase):
    """
    Class upload cloudformation template to S3
    and create/update stack
    """
    
    NAME = 'cloudformation'

    def __init__(self):
        super(Cloudformation, self).__init__()
        self._client = self.get_client('cloudformation')
        self._s3 = S3()
        self._stack_info_cache = {}
        self.current_event_timestamp = (datetime.datetime.now(utc) - datetime.timedelta(seconds=3))
    
    @property
    def client(self):
        return self._client

    @property
    def s3(self):
        return self._s3

    def get_stack_name(self, stack_name):
        """get defined stack name"""
        return self._config.get('StackName') if self._config.get('StackName') else "{}-{}".format(self.get_name_id(), stack_name.lower())

    def create(self):
        """Create/Update stack"""
        # Don't run if we don't have templates
        if not self._config.get('CloudFormation'):
            Oprint.info('No cloudformation found, skip', self.NAME)
            return True

        self.process()

    def delete(self):
        """Delete stack"""
        if not self._config.get('CloudFormation'):
            Oprint.info('No cloudformation found, skip', self.NAME)
            return True

        for stack in self._config.get('CloudFormation').get('Stacks'):
            # If only for specified stack
            specified_stack = self.if_specify_stack()
            if specified_stack and specified_stack != stack.get('Name'):
                continue

            stack_name = self.get_lmdo_format_name(stack.get('Name'), stack.get('DisablePrefix', False))
            self.delete_stack(stack_name)

    def update(self):
        """Wrapper, same action as create"""
        self.create()

    def if_specify_stack(self):
        """If user specify a stack to process"""
        return False if not self._args.get('--stack') else self._args.get('--stack')

    def prepare(self, templates, bucket=None):
        """Prepare all templates/validate/upload before create and update"""
        if len(templates['children']) > 0 and not bucket:
            Oprint.err('S3 bucket hasn\'t been provided for nested template', self.NAME)

        # Validate syntax of the template
        with open(templates['master'], 'r') as outfile:
            self.validate_template(outfile.read())

        for child_template in templates['children']:
            with open(child_template, 'r') as outfile:
                self.validate_template(outfile.read())

        # If bucket provided, we upload
        # all templates into the subfolder
        if bucket:
            path, template_name = os.path.split(templates['master'])
            self._s3.upload_file(bucket, templates['master'], "{}/{}".format(self.get_name_id(), template_name))

            for child_template in templates['children']:
                path, template_name = os.path.split(child_template)
                self._s3.upload_file(bucket, child_template, "{}/{}".format(self.get_name_id(), template_name))

        return True

    def validate_template(self, template_body):
        """Validate template via content"""
        try:
            result = self._client.validate_template(TemplateBody=template_body)
        except Exception as e:
            Oprint.err(e, self.NAME)
        return True

    def get_stack(self, stack_name, cached=False):
        """Check get stack info"""
        try:
            if not self._stack_info_cache.get(stack_name) or not cached:
                self._stack_info_cache[stack_name] = self._client.describe_stacks(StackName=stack_name)
        except Exception as e:
            return False

        return self._stack_info_cache[stack_name]

    def process(self):
        """Creating/updating stack"""
        if self._config.get('CloudFormation'):
            s3_bucket = self._config.get('CloudFormation').get('S3Bucket')
            repo_path = self._config.get('CloudFormation').get('TemplateRepoPath')

            specified_stack_found = False
            for stack in self._config.get('CloudFormation').get('Stacks'):
                # If only for specified stack
                specified_stack = self.if_specify_stack()
                if specified_stack and specified_stack != stack.get('Name'):
                    continue
                else:
                    specified_stack_found = True

                func_params = {}

                params_path = stack.get('ParamsPath')
                if params_path:
                    func_params['Parameters'] = ParamsResolver(params_path=params_path).resolve()
                
                stack_name = self.get_lmdo_format_name(stack.get('Name'), stack.get('DisablePrefix', False))
                
                templates = TemplatesResolver(template_path=stack.get('TemplatePath'), params_path=params_path, repo_path=repo_path).resolve()
                
                self.prepare(templates=templates, bucket=s3_bucket)

                to_update = False
                stack_info = self.get_stack(stack_name=stack_name)

                if stack_info:
                    # You can't do much with UPDATE_ROLLBACK_FAILED state
                    if stack_info['Stacks'][0]['StackStatus'] == 'UPDATE_ROLLBACK_FAILED':
                        Oprint.warn('State {} is in a very bad state, lmdo cannot do anything. Please refer to {} for action you can take'.format(
                          stack_name,
                          'https://aws.amazon.com/blogs/devops/continue-rolling-back-an-update-for-aws-cloudformation-stacks-in-the-update_rollback_failed-state/'), 
                          self.NAME)

                        continue

                    # You cannot update a stack with status ROLLBACK_COMPLETE during creation
                    if stack_info['Stacks'][0]['StackStatus'] == 'ROLLBACK_COMPLETE':
                        Oprint.warn('Stack {} exited with bad state ROLLBACK_COMPLETE during last attempt to create. Required to be removed first'.format(stack_name), self.NAME)
                        self.delete_stack(stack_name, no_policy=True)
                    else:
                        to_update = True

                if not s3_bucket:
                    # Read master template data into cache
                    with open(templates['master'], 'r') as outfile:
                        template_body = outfile.read()

                    func_params['TemplateBody'] = template_body
                else:
                    path, template_name = os.path.split(templates['master'])
                    func_params['TemplateURL'] = self.get_template_s3_url(template_name)

                if to_update:
                    if self._args.get('-c') or self._args.get('--change_set'):
                        self.stack_update_via_change_set(stack_name=stack_name, **func_params)
                    else:
                        self.update_stack(stack_name, **func_params)
                else:
                    self.create_stack(stack_name, **func_params)

                # Remove temporary template dir
                shutil.rmtree(templates['tmp_dir'])
            
            # If specified stack name and none matched
            if self.if_specify_stack() and not specified_stack_found:
                Oprint.warn('Cannot find specified stack {} in lmdo config'.format(self.if_specify_stack()), self.NAME)

    def create_stack(self, stack_name, capabilities=None, **kwargs):
        """Create stack"""
        try:
            capabilities = capabilities or ['CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM']
            if self._args.get('-he') or self._args.get('--hide-event'):
                waiter = CloudformationWaiterStackCreate(self._client)
                response = self._client.create_stack(
                    StackName=stack_name,
                    Capabilities=capabilities,
                    **kwargs
                )
                waiter.wait(stack_name)
            else:
                response = self._client.create_stack(
                    StackName=stack_name,
                    Capabilities=capabilities,
                    **kwargs
                )
                self.stack_events_waiter(stack_name=stack_name)

            self.lock_stack(stack_name=stack_name)
        except Exception as e:
            Oprint.err(e, self.NAME)
            return False

        self.verify_stack(mode='create', stack_id=response.get('StackId'))

        return True

    def update_stack(self, stack_name, capabilities=None, **kwargs):
        """Update a stack"""
        try:
            capabilities = capabilities or ['CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM']
            self.unlock_stack(stack_name=stack_name)

            if self._args.get('-he') or self._args.get('--hide-event'):
                waiter = CloudformationWaiterStackUpdate(self._client)
                response = self._client.update_stack(
                    StackName=stack_name,
                    Capabilities=capabilities,
                    **kwargs
                )
                waiter.wait(stack_name)
            else:
                response = self._client.update_stack(
                    StackName=stack_name,
                    Capabilities=capabilities,
                    **kwargs
                )
                self.stack_events_waiter(stack_name=stack_name)

            self.lock_stack(stack_name=stack_name)
        except ClientError as ce:
            if str(ce.response['Error']['Message']) == 'No updates are to be performed.':
                Oprint.warn('AWS Validation Error: {} (If purely there isn\'t any changes to your cloudformation, you can safely ignore it)'.format(str(ce.response['Error']['Message'])), self.NAME)
                return True
            else:
                Oprint.err(str(ce.response['Error']['Message']), self.NAME)
        except Exception as e:
            Oprint.err(e, self.NAME)
            return False

        self.verify_stack(mode='update', stack_id=response.get('StackId'))

        return True

    def delete_stack(self, stack_name, no_policy=False):
        """Remove a stack by given name"""
        # Don't do anything if doesn't exist
        stack_info = self.get_stack(stack_name=stack_name)
        if not stack_info:
            return True

        try:
            if not no_policy:
                self.unlock_stack(stack_name=stack_name)

            if self._args.get('-he') or self._args.get('--hide-event'):
                waiter = CloudformationWaiterStackDelete(self._client)
                response = self._client.delete_stack(StackName=stack_name)
                waiter.wait(stack_name)   
            else:
                response = self._client.delete_stack(StackName=stack_name)
                self.stack_events_waiter(stack_name=stack_name)
        except Exception as e:
            Oprint.err(e, self.NAME)
            return False

        self.verify_stack(mode='delete', stack_id=stack_info['Stacks'][0]['StackId'])

        return True

    def get_stack_status(self, stack_id=None, status_niddle=None):
        stack_info = self.get_stack(stack_name=stack_id)
        status = stack_info['Stacks'][0]['StackStatus']

        if status_niddle == CfStatus.STACK_COMPLETE:
            return True if status.endswith('_COMPLETE') else False
        if status_niddle == CfStatus.STACK_FAILED:
            return True if status.endswith('_FAILED') or status.endswith('ROLLBACK_COMPLETE') else False
        if status_niddle == CfStatus.STACK_IN_PROGRESS:
            return True if status.endswith('_IN_PROGRESS') else False

        return status

    def verify_stack(self, mode, stack_id=None):
        """Check if stack action successful, deleted stack must provide stack id"""
        status = self.get_stack_status(stack_id=stack_id)

        if mode == 'create':
            if status != 'CREATE_COMPLETE':
                Oprint.err("Create stack failed with status {}".format(status), self.NAME)

        if mode == 'update':
            if status != 'UPDATE_COMPLETE':
                Oprint.err("Update stack failed with status {}".format(status), self.NAME)

        if mode == 'delete':
            if status != 'DELETE_COMPLETE':
                Oprint.warn("Delete stack failed with status {} (most likely caused by your S3 buckets have contents)".format(status), self.NAME)

    def get_output_value(self, stack_name, key, cached=False):
        """get a specific stack output value"""
        stack_info = self.get_stack(stack_name=stack_name, cached=cached)
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
            Oprint.warn(e, self.NAME)

        return response

    def describe_change_set(self, change_set_name, *args, **kwargs):
        """Get change set information"""
        try:
            response = self._client.describe_change_set(ChangeSetName=change_set_name, *args, **kwargs)
        except Exception as e:
            Oprint.err(e, self.NAME)

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
            Oprint.warn(e, self.NAME)

        return True

    def create_change_set(self, stack_name, capabilities=None, *args, **kwargs):
        """Creating change set"""
        try:
            waiter = CloudformationWaiterChangeSetCreateComplete(self._client)

            change_set_name = self.create_change_set_name(stack_name)

            #Oprint.info('Creating change set {} for stack {}'.format(change_set_name, stack_name), self.NAME)
            capabilities = capabilities or ['CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'] 
            response = self._client.create_change_set(StackName=stack_name, ChangeSetName=change_set_name, Capabilities=capabilities, *args, **kwargs)

            waiter.wait(change_set_name=change_set_name, stack_name=stack_name)
        except Exception as e:
            Oprint.err(e, self.NAME)

        return change_set_name

    def excecute_change_set(self, change_set_name, stack_name, *args, **kwargs):
        """Run changeset to make it happen"""
        try:
            self.unlock_stack(stack_name=stack_name)

            if self._args.get('-he') or self._args.get('--hide-event'):
                waiter = CloudformationWaiterStackUpdate(self._client)
                Oprint.info('Executing change set {} for updating stack {}'.format(change_set_name, stack_name), self.NAME)
                response = self._client.execute_change_set(ChangeSetName=change_set_name, StackName=stack_name, *args, **kwargs)
                waiter.wait(stack_name)
            else:
                Oprint.info('Executing change set {} for updating stack {}'.format(change_set_name, stack_name), self.NAME)
                response = self._client.execute_change_set(ChangeSetName=change_set_name, StackName=stack_name, *args, **kwargs)

                self.stack_events_waiter(stack_name=stack_name)

            self.lock_stack(stack_name=stack_name)
        except Exception as e:
            Oprint.err(e, self.NAME)

        self.verify_stack(mode='update', stack_id=stack_name)

        return response

    def can_update_stack_policy(self, stack_name):
        """Check if we can update stack policy"""
        stack_info = self.get_stack(stack_name=stack_name)
       
        # If stack doesn't exist anymore, ignore
        if not stack_info:
            return True

        not_in_status = ['ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_FAILED']
        if stack_info.get('Stacks') and stack_info['Stacks'][0]['StackStatus'] not in not_in_status:
            return True

        Oprint.warn('Can not update stack policy due to stack in the state of {}'.format(stack_info['Stacks'][0]['StackStatus']), self.NAME)

        return False

    def lock_stack(self, stack_name):
        """Lock stack so no changes can be made accidentally"""
        try:
            if not self.can_update_stack_policy(stack_name=stack_name):
                return True

            lock_policy = get_template(CLOUDFORMATION_STACK_LOCK_POLICY)
            with open(lock_policy, 'r') as outfile:
                policy = outfile.read()

            Oprint.info('Locking stack {} to prevent accidental changes'.format(stack_name), self.NAME)
            response = self._client.set_stack_policy(StackName=stack_name, StackPolicyBody=policy)
        except ClientError as ce:
            Oprint.err(str(ce.response['Error']['Message']), self.NAME)
        except Exception as e:
            Oprint.err(e, self.NAME)

        return True

    def unlock_stack(self, stack_name):
        """Unlock stack for update"""
        try:
            if not self.can_update_stack_policy(stack_name=stack_name):
                return True

            unlock_policy = get_template(CLOUDFORMATION_STACK_UNLOCK_POLICY)
            with open(unlock_policy, 'r') as outfile:
                policy = outfile.read()

            Oprint.info('Unlocking stack {} for update'.format(stack_name), self.NAME)
            response = self._client.set_stack_policy(StackName=stack_name, StackPolicyBody=policy)
        except Exception as e:
            Oprint.err(e, self.NAME)

        return True

    def get_stack_event(self, stack_name, *args, **kwargs):
        try:
            response = self._client.describe_stack_events(StackName=stack_name, *args, **kwargs)
        except Exception as e:
            Oprint.warn(e, self.NAME)
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
            Oprint.info('{}{}'.format(prefix, event_info), self.NAME)

            # Update timestamp
            if not self.current_event_timestamp:
                self.current_event_timestamp = event['Timestamp']
            elif event['Timestamp'] > self.current_event_timestamp:
                self.current_event_timestamp = event['Timestamp']

    def stack_events_waiter(self, stack_name):
        """Event waiter"""
        in_progress = True
        while in_progress:
            try:
                in_progress = self.get_stack_status(stack_id=stack_name, status_niddle=CfStatus.STACK_IN_PROGRESS)
                self.display_stack_event(stack_name=stack_name)
                time.sleep(3)
            except Exception:
                in_progress = False

        return in_progress

    def display_change_set(self, change_set_name, stack_name):
        """Display change set infos"""
        change_set_info = self.describe_change_set(change_set_name=change_set_name, StackName=stack_name)
        # If no changes, skip
        if not change_set_info.get('Changes'):
            Oprint.warn('There is no changes in change set, abort', self.NAME)
            return False

        self.pretty_change_set_changes(change_set_info.get('Changes'))

        token = change_set_info.get('NextToken')
        if token:
            while token:
                change_set_info = self.describe_change_set(change_set_name=change_set_name, StackName=stack_name, NextToken=token)
                self.pretty_change_set_changes(change_set_info.get('Changes'))
                token = change_set_info.get('NextToken')

        return True

    def pretty_change_set_changes(self, changes):
        """Display changes in a pretty format"""
        Oprint.infog('Proposed changes', self.NAME)
        for item in changes:
            change = item['ResourceChange']
            Oprint.infog('========================', self.NAME)
            Oprint.infog('Type: {}'.format(item.get('Type')), self.NAME)
            Oprint.infog('Action: {}'.format(change.get('Action')), self.NAME)
            Oprint.infog('Replacement: {}'.format(change.get('Replacement')), self.NAME)
            Oprint.infog('Scope: {}'.format(', '.join(change.get('Scope') or [])), self.NAME)
            Oprint.infog('ResourceType: {}'.format(change.get('ResourceType')), self.NAME)
            Oprint.infog('LogicalResourceId: {}'.format(change.get('LogicalResourceId')), self.NAME)
            Oprint.infog('PhysicalResourceId: {}'.format(change.get('PhysicalResourceId')), self.NAME)
            Oprint.infog('Details:', self.NAME)

            for detail in change['Details']:
                Oprint.infog('    ChangeSource: {}'.format(detail.get('ChangeSource')), self.NAME)
                Oprint.infog('    Evaluation: {}'.format(detail.get('Evaluation')), self.NAME)
                Oprint.infog('    CausingEntity: {}'.format(detail.get('CausingEntity')), self.NAME)
                Oprint.infog('    Target:', self.NAME)
                Oprint.infog('        Attribute: {}'.format(detail.get('Target').get('Attribute')), self.NAME)
                Oprint.infog('        Name: {}'.format(detail.get('Target').get('Name')), self.NAME)
                Oprint.infog('        RequiresRecreation: {}'.format(detail.get('Target').get('RequiresRecreation')), self.NAME)
                Oprint.infog('        -------------------------', self.NAME)

    def stack_update_via_change_set(self, stack_name, *args, **kwargs):
        """Securely update a stack"""
        change_set_name = self.create_change_set(stack_name=stack_name, *args, **kwargs)

        if not self.display_change_set(change_set_name=change_set_name, stack_name=stack_name):
            return False

        sys_pause('Proceed to execute the change set?[yes/no]', 'yes')

        self.excecute_change_set(change_set_name=change_set_name, stack_name=stack_name)

        return True
