from __future__ import print_function
import os

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint


class BucketNotification(AWSBase):
    """S3 bucket notification handler"""
    NAME = 's3_notification'

    def __init__(self):
        super(BucketNotification, self).__init__()
        self._client = self.get_client('s3')
        self._notification_config_cache = {}

    def get_notification_id(self, name):
        """Create pre-defined notification id"""
        return "lmdo-{}".format(name)

    def get_lambda_configuration(self, event_config):
        """Return dict of lambda configuration"""
        config = {
            "Id": self.get_notification_id(event_config['FunctionName']),
            "LambdaFunctionArn": self.get_lambda_arn(event_config['FunctionName']),
            "Events": event_config.get('Events', ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"])
        }

        if event_config.get('FilterRules'):
            config['Filter'] = {
                "Key": {
                  "FilterRules": event_config.get('FilterRules')
                }
            }
        
        return config

    def update(self, event_config):
        """Update S3 event source"""
        if event_config.get('FunctionName'):
            self.update_lambda_configuration(event_config)
    
    def get_notifications(self, bucket_name, refresh=False):
        """Get s3 notification configuration"""
        if refresh or not self._notification_config_cache.get(bucket_name):
            self._notification_config_cache[bucket_name] = self._client.get_bucket_notification_configuration(Bucket=bucket_name)

        return self._notification_config_cache[bucket_name]

    def search_lambda_configuration(self, event_config):
        """Search lambda configuration, return the up-to-date version"""
        found = False
        delete = event_config.get('Delete', False)
        lambda_config = self.get_lambda_configuration(event_config)
        lambda_notifications = self.get_notifications(bucket_name=event_config['BucketName']).get('LambdaFunctionConfigurations', [])
       
        if lambda_notifications:
            for index, elm in enumerate(lambda_notifications):
                if elm.get('Id') == lambda_config.get('Id'):
                    found = index
                    break

        # If it has been deleted, no action required
        if delete and found is False:
            return False

        if found is not False:
            # Always delete for update or delete
            del lambda_notifications[found]

            if delete:
                return lambda_notifications
       
        if not lambda_notifications:
            lambda_notifications = []

        lambda_notifications.append(lambda_config)
         
        return lambda_notifications

    def update_lambda_configuration(self, event_config):
        """Update lambda configuration for S3 bucket"""
        configuration = self.get_notifications(bucket_name=event_config['BucketName'])
        del configuration['ResponseMetadata']

        lambda_configuration = self.search_lambda_configuration(event_config)
        if lambda_configuration is not False:
            configuration['LambdaFunctionConfigurations'] = lambda_configuration
            response = self._client.put_bucket_notification_configuration(Bucket=event_config['BucketName'], NotificationConfiguration=configuration)
            Oprint.info('S3 bucket {} notification for lambda function {} has been updated'.format(event_config['BucketName'], event_config['FunctionName']), self.NAME)

        return True


