import boto3

from lmdo.cli import args
from lmdo.lmdo_config import lmdo_config
from lmdo.oprint import Oprint

class AWSBase(object):
    """base AWS delegator class"""

    def __init__(self):
        self._args = args
        self._config = lmdo_config
        self._profile_name = ''

    @classmethod
    def init_with_parser(cls, config_parser):
        """alternative constructor taking custom parser"""
        alt_cls = cls()
        alt_cls.config = config_parser
        return alt_cls

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config_parser):
        self._config = config_parser

    def get_session(self):
        """Fetch AWS session based on AWS CLI credential setup"""
        kw = {}
        if self._config.get('AWSKey') and self._config.get('AWSSecret') and self._config.get('Region'):
            kw['aws_access_key_id'] = self._config.get('AWSKey')
            kw['aws_secret_access_key'] = self._config.get('AWSSecret')
            kw['region_name'] = self._config.get('Region')
        else:
            # User 'default' if no specified profile
            self._profile_name = 'default'
            if self._config.get('Profile'):
                self._profile_name = self._config.get('Profile')

            kw['profile_name'] = self._profile_name

        return boto3.Session(**kw)

    def get_region(self):
        """Get region name from AWS profile"""
        return self.get_session().region_name

    def get_account_id(self):
        """Get account ID"""
        return self.get_session().client('sts').get_caller_identity()['Account']

    def get_client(self, client_type):
        """Fetch AWS service client"""
        return self.get_session().client(client_type)

    def get_resource(self, resource_type):
        """Fetch AWS service resource"""
        return self.get_session().resource(resource_type)

    def get_name_id(self):
        return "{}-{}-{}".format(
            self._config.get('User'),
            self._config.get('Stage'),
            self._config.get('Service')
        ).lower()

    def get_lmdo_format_name(self, name, prefix_disabled=False):
        """Get lmdo name format prefixed with get_name_id"""
        if prefix_disabled == True:
            return name.lower()
        
        return "{}-{}".format(self.get_name_id(), name.lower())

    def get_template_s3_url(self, template_name):
        """Construct the template URL for nested stack"""
        return 'https://s3.amazonaws.com/{}/{}/{}'.format(self._config.get('CloudFormation').get('S3Bucket'), self.get_name_id(), template_name)

    def get_policy_arn(self, policy_name):
        """Fetch policy arn"""
        return 'arn:aws:iam::{}:policy/{}'.format(
            self.get_account_id(), policy_name)

    def get_role_arn(self, role_name):
        """Fetch role arn"""
        return 'arn:aws:iam::{}:role/{}'.format(self.get_account_id(), role_name)

    def get_role_name_by_arn(self, role_arn):
        """Fetch role name"""
        return role_arn.split('/').pop()

    def get_lambda_arn(self, func_name):
        """Return invokeable function url"""
        return 'arn:aws:lambda:{}:{}:function:{}'.format(self.get_region(), self.get_account_id(), func_name)

    def get_lmdo_lambda_arn(self, func_name):
        """Return lambda arn for created in lmdo"""
        return self.get_lambda_arn(self.get_lmdo_format_name(func_name))

    def if_lambda_function(self, arn):
        """Check if arn is function"""
        arns = arn.split(':')
        if 'function' in arns:
            return True

        return False

    def get_function_name_by_lambda_arn(self, arn):
        """
        Strip function number from ARN
        """
        arn_list = arn.split(':')
        return arn_list.pop()

    def get_apigateway_lambda_role_name(self, function_name):
        """Get apigateway for lambda default role name"""
        return "APIGateway-{}".format(function_name)

    def get_s3_arn(self, bucket_name):
        """Get s3 arn format"""
        return "arn:aws:s3:::{}".format(bucket_name)

    def get_sns_topic_arn(self, topic):
        """Get sns topic arn format"""
        return "arn:aws:sns:{}:{}:{}".format(self.get_region(), self.get_account_id(), topic)


