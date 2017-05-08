from __future__ import print_function

import uuid
import os
import copy
import random

from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.iam.iam import IAM
from lmdo.oprint import Oprint


class CloudWatchEvent(AWSBase):
    """CloudWatch Event class"""
    NAME = 'cloudwatchevent'

    TARGET_DEFAULT = 'default'
    TARGET_LOCAL = 'local'

    """CloudwatchEvent handler"""
    def __init__(self):
        super(CloudWatchEvent, self).__init__()
        self._client = self.get_client('events')
        # Not to depends on Lambda class
        self._lambda = self.get_client('lambda')
        self._iam = IAM()
        self._default_role_arn = None

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

        rules = self.get_deployment_data(self._config.get('CloudWatchEvent'))
       
        for rule in rules:
            self.delete_rule(name=rule['Name'])

        self.delete_default_role()

        return True
            
    def process(self):
        """Process cloudwatch events"""
        if not self._config.get('CloudWatchEvent'):
            Oprint.info('No CloudWatch Events to process', self.NAME)
            return True

        rules= self.get_deployment_data(self._config.get('CloudWatchEvent'))
        for rule in rules:
            targets = rule.pop('Targets')
            self.upsert_rule(**rule)
            self.upsert_targets(rule_name=rule['Name'], targets=targets)

        return True

    def get_deployment_data(self, events, delete=False):
        rule_list = []

        # create the rule list so that we know what rules to create
        for rule in events:
            if delete:
                rule_entry = {
                    "Name": self.get_lmdo_format_name(rule['Name'], rule.get('DisablePrefix', False))
                }

                rule_list.append(rule_entry)
                continue

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
                if not self._default_role_arn:
                    self._default_role_arn = self.create_default_role()

                rule_entry['RoleArn'] = self._default_role_arn

                    
            # Create target list so we can attach them to the rule
            if rule.get('Targets'):   
                targets = []               
                for target in rule.get('Targets'):
                    t_type = target.get('Type', self.TARGET_DEFAULT)
                   
                    # Any target ARN 
                    if t_type == self.TARGET_DEFAULT:
                        if not target.get('Arn'):
                            Oprint.warn('No Arn given for target. Rule {}. Skipping target'.format(rule_entry['Name']), self.NAME)
                            continue
                        
                        target_entry = {"Arn": target.get('Arn')}
    
                    # Local project lambda function
                    elif t_type == self.TARGET_LOCAL:
                        if not target.get('FunctionName'):
                            Oprint.warn('No FunctionName given for target. Rule {}. Skiping target'.format(rule_entry['Name']), self.NAME)
                            continue
                       
                        arn = self.get_lambda_arn(self.get_lmdo_format_name(target.get('FunctionName')))

                        if arn:
                            target_entry = {"Arn": arn}
                        else:
                            Oprint.warn('No Arn found for given FunctionName {} of  target. Rule {}. Skiping target'.format(target.get('FunctionName'), rule_entry['Name']), self.NAME)
                    
                    targets.append(target_entry)    
                rule_entry['Targets'] = targets                
            rule_list.append(rule_entry)

        return rule_list

    def create_default_role(self):
        """Create a default event rule role"""
        return self._iam.create_default_events_role(role_name=self.get_lmdo_format_name('default-events-cwe'))['Role']['Arn'] 

    def delete_default_role(self):
        """Delete the defaul event rule role"""
        self._iam.delete_default_events_role(role_name=self.get_lmdo_format_name('default-events-cwe'))

        return True

    def upsert_rule(self, **kwargs):
        """Create or update rule"""
        try:
            name = kwargs.get('Name')
            Oprint.info('Creating Cloudwatch Event rule {}'.format(name), self.NAME)
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
            self.delete_rule_targets(rule_name=name)
            response = self._client.delete_rule(Name=name)
            Oprint.info('CloudWatchEvent rule {} has been deleted'.format(name), self.NAME)
        except Exception as e:
            Oprint.err(e, self.NAME)

        return True
    
    def format_targets(self, targets):
        """Formatting target list"""
        target_list = []
        if type(targets) is list:
            for target in targets:
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
        for target in targets:
            if self.if_lambda_function(target.get('Arn')):
                stmt_id = 'Stmts-%s-lambda-%s' % (self.get_function_name_by_lambda_arn(target.get('Arn')), 'event')
               
                try:
                    self._lambda.remove_permission(
                        FunctionName=self.get_function_name_by_lambda_arn(target.get('Arn')),
                        StatementId=stmt_id
                    )
                except Exception as e:
                    pass

                response = self._lambda.add_permission(
                    FunctionName=self.get_function_name_by_lambda_arn(target.get('Arn')),
                    StatementId=stmt_id,
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com'
                )

        return True

    def upsert_targets(self, rule_name, targets=None):
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


