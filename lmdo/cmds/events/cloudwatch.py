from __future__ import print_function

import uuid
from lmdo.cmds.aws_base import AWSBase
from lmdo.cmds.lm.lambdaa import Lambda
from lmdo.cmds.iam.iam import IAM

from lmdo.oprint import Oprint


class CloudWatchEvent(AWSBase):
    """CloudwatchEvent handler"""
    def __init__(self):
        super(CloudWatchEvent, self).__init__()
        self._client = self.get_client('events')
        self._lambda = Lambda()
        self._iam = IAM()

    @property
    def client(self):
        return self._client

    def get_rule_name(self, func_name, func_path):
        return '{func_name}.{function}'.format(
            func_name=self._lambda.get_function_name(func_name),
            function=func_path
        )

    def create_rule(self, rule_name, event, lambda_iam_arn):
        # Create CloudWatch events rule
        rule_arn = self.client.put_rule(
            Name=rule_name,
            ScheduleExpression=event.get('expression'),
            # EventPattern='string',
            State='ENABLED',
            Description=event.get('function'),
            RoleArn=lambda_iam_arn
        )['RuleArn']
        Oprint.info('Cloudwatch rule created: {}'.format(rule_arn))
        return rule_arn

    def add_lambda_permission(self, func_name, rule_arn):
        return self._lambda.client.add_permission(
            FunctionName=self._lambda.get_function_name(func_name),
            StatementId=self._lambda.get_statement_id(
                func_name, str(uuid.uuid4())
            ),
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_arn
        )

    def attach_to_lambda(self, rule_name, lambda_arn):
        # Add lambda to above rule
        target_response = self.client.put_targets(
            Rule=rule_name,
            Targets=[{
                'Id': str(uuid.uuid4()),
                'Arn': lambda_arn,
            }]
        )
        if target_response['ResponseMetadata']['HTTPStatusCode'] == 200:
            Oprint.info('Scheduled: {} on Lambda {}'.format(
                rule_name, lambda_arn
            ))
        return target_response

    def create_event(self, func_name, event):
        lambda_iam_arn = self._iam.get_role(
            self._lambda.get_role_name(func_name)
        )['Role']['Arn']
        lambda_name = self._lambda.get_function_name(func_name)
        lambda_arn = self.get_lambda_arn(lambda_name)
        rule_name = self.get_rule_name(
            func_name=func_name,
            func_path=event.get('function')
        )
        rule_arn = self.create_rule(rule_name, event, lambda_iam_arn)
        self.add_lambda_permission(func_name, rule_arn)
        self.attach_to_lambda(rule_name, lambda_arn)

    def delete_event(self, func_name, event):
        rule_name = self.get_rule_name(
            func_name=func_name,
            func_path=event.get('function')
        )
        targets = self.client.list_targets_by_rule(Rule=rule_name)
        Oprint.info(targets)
        if 'Targets' in targets and targets['Targets']:
            self.client.remove_targets(
                Rule=rule_name, Ids=[x['Id'] for x in targets['Targets']]
            )
            Oprint.info('Targets removed from %s' % rule_name)
        resp = self.client.delete_rule(Name=rule_name)
        Oprint.info(resp)

    def add_events(self):
        for lm in self._config.get('Lambda'):
            events = lm.get('Events', [])
            for event in events:
                self.delete_event(lm.get('FunctionName'), event)
                self.create_event(lm.get('FunctionName'), event)


cwe = CloudWatchEvent()
cwe.add_events()