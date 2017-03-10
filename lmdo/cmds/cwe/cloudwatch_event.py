from __future__ import print_function

import uuid
import os
import copy

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.lm.lambdaa import Lambda
from lmdo.cmds.iam.iam import IAM

from lmdo.oprint import Oprint


class CloudWatchEvent(AWSBase):
    NAME = 'cloudwatchevent'

    TARGET_DEFAULT = 'default'
    TARGET_LOCAL = 'local'
    TARGET_DISPATCHER = 'dispatcher'

    """CloudwatchEvent handler"""
    def __init__(self, args=None):
        super(CloudWatchEvent, self).__init__()
        self._client = self.get_client('events')
        self._lambda = Lambda()
        self._iam = IAM()
        self._args = args or {}

    @property
    def client(self):
        return self._client

    def create(self):
        self.process()

    def update(self):
        return self.create()

    def delete(self):
        if not self._config.get('CloudWatchEvent'):
            Oprint.info('No CloudWatch Events to process', self.NAME)
            return True

        rules, targets = self.get_deployment_data(self._config.get('CloudWatchEvent'))
    
        for rule in rules:
            self.delete_rule(name=rule['name'])

        self.delete_default_role()

        return True
            
    def process(self):
        """Process cloudwatch events"""
        if not self._config.get('CloudWatchEvent'):
            Oprint.info('No CloudWatch Events to process', self.NAME)
            return True

        rules, targets = self.get_deployment_data(self._config.get('CloudWatchEvent'))
        for rule in rules:
            self.upsert_rule(**rule)
            self.put_target(rule_name=rule['Name'], targets=targets.get(rule['Name']))

        return True

    def get_deployment_data(self, events):
        rule_list = []
        target_list = {}
        default_role_arn = None

        # create the rule list so that we know what rules to create
        for rule in events:
            rule_entry = {
                "Name": self.get_lmdo_format_name(rule['Name'], rule.get('DisablePrefix', False)),
                "State": 'ENABLED',
                "Description": rule.get('Description') or 'Rule deployed by lmdo'
            }

            if rule.get('ScheduleExpression'):
                rule_entry['ScheduleExpression'] = rule.get('ScheduleExpression')

            if rule.get('EventPatternFile') and os.path.isfile(rule.get('EventPatternFile')):
                with open(rule.get('EventPatternFile'), 'r') as outfile:
                    rule_entry['EventPattern'] = outfile.read()

            if rule.get('RoleArn'):
                rule_entry['RoleArn'] = rule.get('RoleArn')
            else:
                if not default_role_arn:
                    default_role_arn = self.create_default_role()

                rule_entry['RoleArn'] = default_role_arn

                    
            # Create target list so we can attach them to the rule
            if rule.get('Targets'):   
                target_entry = {
                    "rule_name": rule_entry['Name'],
                    "targets": []
                }
                counter = 0
                for target in rule.get('Targets'):
                    t_type = target.get('Type', self.TARGET_DEFAULT)
                    
                    if t_type == self.TARGET_DEFAULT:
                        if not target.get('Arn'):
                            Oprint.warn('No Arn given for target. Rule {}. Skipping target'.format(rule_entry['Name']), self.NAME)
                            continue
                        
                        target_entry["targets"].append({"Arn": target.get('Arn')})
                        counter += 1
                    elif t_type == self.TARGET_LOCAL:
                        if not target.get('FunctionName'):
                            Oprint.warn('No FunctionName given for target. Rule {}. Skiping target'.format(rule_entry['Name']), self.NAME)
                            continue
                       
                        arn = self.get_function_arn(function_name=target.get('FunctionName'))
                        if arn:
                            target_entry["targets"].append({"Arn": arn}) 
                        else:
                            Oprint.warn('No Arn found for given FunctionName {} of  target. Rule {}. Skiping target'.format(target.get('FunctionName'), rule_entry['Name']), self.NAME)
                        counter +=1
                    # the dispatcher type of target will create a new rule
                    # targeting the generic lmdo event dispatcher function
                    elif t_type == self.TARGET_DISPATCHER:
                        if not target.get('Handler'):
                            Oprint.warn('No handler given for target. Rule {}. Skipping target'.format(rule_entry['Name']), self.NAME)
                            continue

                        # Create a new rule that has name concat with handler
                        # so that the generic function knows which handler to call
                        d_rule_entry = copy.deepcopy(rule_entry)
                        d_rule_entry["Name"] = '{}--{}'.format(d_rule_entry['Name'], target.get('Handler'))
                        #d_rule_entry["dispatcher_function"] = True
                        rule_list.append(d_rule_entry)

                        d_target_entry = {
                            "rule_name": d_rule_entry["Name"],
                            "targets": [{'Arn': self._lambda.get_events_dispatcher_arn()}]
                        }
                      
                        target_list[d_rule_entry['Name']] = d_target_entry
                        continue

                    target_list[rule_entry['Name']] = target_entry
                
                if counter > 0:
                    rule_list.append(rule_entry)

        return rule_list, target_list
    
    def get_function_arn(self, function_name):
        """Get local function's arn"""
        info = self._lambda.get_function(self.get_lmdo_format_name(function_name))
        arn = info.get('Configuration').get('FunctionArn')
        if not arn:
            Oprint.warn('Cannot find local defined function {}\'s arn'.format(function_name), self.NAME)
            return False

        return arn

    def create_default_role(self):
        """Create a default event rule role"""
        role = self._iam.get_role(role_name=self.get_lmdo_format_name('default-events'))
        if not role:
            return self._iam.create_default_events_role(role_name=self.get_lmdo_format_name('default-events'))['Role']['Arn'] 
        
        return role['Role']['Arn']

    def delete_default_role(self):
        """Delete the defaul event rule role"""
        if self._iam.get_role(role_name=self.get_lmdo_format_name('default-events')):
            self._iam.delete_role_and_associated_policies(role_name=self.get_lmdo_format_name('default-events'))

        return True

    def upsert_rule(self, **kwargs):
        """Create or update rule"""
        try:
            Name = kwargs.get('Name')
            Oprint.info('Creating Cloudwatch Event rule {}'.format(Name), self.NAME)
            response = self._client.put_rule(**kwargs)
        except Exception as e:
            Oprint.err(e, self.NAME)

        return response['RuleArn']

    def delete_targets(self, rule_name, target_ids):
        """Deleting targets from rule"""
        success = True
        try:
            if target_ids:
                Oprint.info('Removing {} targets from Cloudwatch Event rule {}'.format(len(target_ids), rule_name), self.NAME)
                response = self._client.remove_targets(Rule=rule_name, Ids=target_ids)
                if response.get('FailedEntryCount') > 0:
                    success = False
                    Oprint.warn('{} target removal failed'.response.get('FailedEntryCount'), self.NAME)
        except Exception as e:
            Oprint.err(e, self.NAME)

        return success

    def delete_rule_targets(self, rule_name):
        """Delete all targes from a rule"""
        try:
            response = self._client.list_targets_by_rule(Rule=rule_name)
            target_ids = [target['Id'] for target in response.get('Targets')]
            d_response = self.delete_targets(rule_name=rule_name, target_ids=target_ids)
            if not d_response:
                return False
            while response.get('NextToken'):
                response = self._client.list_targets_by_rule(Rule=rule_name, NextToken=response.get('NextToken'))
                target_ids = [target['Id'] for target in response.get('Targets')]
                d_response = self.delete_targets(rule_name=rule_name, target_ids=target_ids)
                if not d_response:
                    return False
        except Exception as e:
            Oprint.err(e, self.NAME)

        return True

    def delete_rule(self, name):
        """Delete a cloudwatch event rule"""
        try:
            if not self.delete_rule_targets(rule_name=name):
                Oprint.err('Cannot delete rule {} due to deleting its targets failed'.format(name), self.NAME)
            response = self._client.delete_rule(Name=name)
        except Exception as e:
            Oprint.err(e, self.NAME)

        return True
    
    def format_targets(self, targets):
        """Formatting target list"""
        target_list = []
        if type(targets) is dict:
            for target in targets.get('targets'):
                t_tmp = {
                    'Id': str(uuid.uuid4()),
                    'Arn': target.get('Arn')
                }

                target_list.append(t_tmp)
        else:
            t_tmp = {
                'Id': str(uuid.uuid4()),
                'Arn': targets
            }
            target_list.append(t_tmp)
        
        return target_list
    
    def add_lambda_permission_to_targets(self, targets):
        """Enable event permission to lambda if it's function"""
        for target in targets.get('targets'):
            self._lambda.add_event_permission_to_lambda(target.get('Arn'))
        return True

    def put_target(self, rule_name, targets=None):
        """
        Add target to a rule
        Targets can be a single ARN or a list of ARNs
        """
        try:
            if not self.delete_rule_targets(rule_name=rule_name):
                Oprint.err('Cannot delete rule {} due to deleting its targets failed'.format(rule_name), self.NAME)
            
            response = self._client.put_targets(Rule=rule_name, Targets=self.format_targets(targets))
            if response['FailedEntryCount'] > 0:
                Oprint.err('Failed to update targets for rule {}'.format(rule_name), self.NAME)
            else:
                Oprint.info('Targets created for rule {}'.format(rule_name), self.NAME)

            self.add_lambda_permission_to_targets(targets)
        except Exception as e:
            Oprint.err(e, self.NAME)

        return True


