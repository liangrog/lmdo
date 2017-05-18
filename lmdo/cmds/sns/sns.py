from __future__ import print_function
import os

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint


class SNS(AWSBase):
    """SNS"""
    NAME = 'sns'

    def __init__(self):
        super(SNS, self).__init__()
        self._client = self.get_client('sns')

    def update_event_source(self, event_source):
        """Update lmdo lambda function event source"""
        if event_source.get('Delete'):
            self.unsubscribe_lambda(topic=event_source.get('Topic'), function_name=event_source.get('FunctionName'))
            return True

        self.subscribe_lambda(topic=event_source.get('Topic'), function_name=event_source.get('FunctionName'))
        return True

    def remove_event_source(self, event_source):
        """Remove lmdo lambda function event source"""
        self.unsubscribe_lambda(topic=event_source.get('Topic'), function_name=event_source.get('FunctionName'))
        return True
       
    def subscribe_lambda(self, topic, function_name):
        """Subscribing lambda to topic"""
        function_arn = self.get_lambda_arn(function_name)

        subscription = self.get_subscriptions_by_topic(topic=topic, filters={"Endpoint":function_arn})
        if len(subscription) == 0:
            self.subscribe(topic=topic, protocol='lambda', endpoint=function_arn)

        return True

    def unsubscribe_lambda(self, topic, function_name):
        """Unsubscribing lambda endpoint"""
        function_arn = self.get_lambda_arn(function_name)

        subscription = self.get_subscriptions_by_topic(topic=topic, filters={"Endpoint":function_arn})
        if len(subscription) > 0:
            self.unsubscribe(subscription[0].get('SubscriptionArn'))

        return True

    def subscribe(self, topic, protocol, endpoint):
        """Subscription"""
        topic_arn = self.get_sns_topic_arn(topic)
        self._client.subscribe(TopicArn=topic_arn, Protocol=protocol, Endpoint=endpoint)
        Oprint.info('Endpoint {} has subscribed to SNS topic {}'.format(endpoint, topic), self.NAME)
        return True
    
    def unsubscribe(self, sub_arn):
        """Unsubscribe endpoint"""
        self._client.unsubscribe(SubscriptionArn=sub_arn)
        Oprint.info('SNS topic unsubscription {} success'.format(sub_arn), self.NAME)
        return True

    def get_subscriptions_by_topic(self, topic, filters=None):
        """Get all topic subscriptions"""
        topic_arn = self.get_sns_topic_arn(topic)
        response = self._client.list_subscriptions_by_topic(TopicArn=topic_arn)
        subscriptions = response.get('Subscriptions')
        next_token = response.get('NextToken')
        if next_token:
            while next_token:
                response = self._client.list_subscriptions_by_topic(TopicArn=topic_arn, NextToken=next_token)
                subscriptions.append(response.get('Subscriptions'))
                next_token = response.get('NextToken')
        
        if filters:
            f = lambda x: filters.get('SubscriptionArn') == x.get('SubscriptionArn') or \
                          filters.get('Owner') == x.get('Owner') or \
                          filters.get('Protocol') == x.get('Protocol') or \
                          filters.get('Endpoint') == x.get('Endpoint')

            subscriptions = list(filter(f, subscriptions))

        return subscriptions

