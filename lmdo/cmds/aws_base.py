import boto3

from lmdo.lmdo_config import LmdoConfig


class AWSBase(object):
    """base AWS delegator class"""

    def __init__(self):
        self._config = LmdoConfig()

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
        if self._config.get('AWSKey') and self._config.get('AWSSecret'):
            kw['aws_access_key_id'] = self._config.get('AWSKey')
            kw['aws_secret_access_key'] = self._config.get('AWSSecret')
        else:
            # User 'default' if no specified profile
            profile = 'default'
            if self._config.get('Profile'):
                profile = self._config.get('Profile')
            kw['profile_name'] = profile

        return boto3.Session(**kw)

    def get_region(self):
        """Get region name from AWS profile"""
        return self.get_session().region_name

    def get_account_id(self):
        """Get account ID"""
        return boto3.client('sts').get_caller_identity()['Account']

    def get_client(self, client_type):
        """Fetch AWS service client"""
        return self.get_session().client(client_type)

    def get_resource(self, resource_type):
        """Fetch AWS service resource"""
        return self.get_session().resource(resource_type)

    def get_name_id(self):
        return "{}-{}-{}".format(self._config.get('User'), self._config.get('Stage'), self._config.get('Service'))

    def get_policy_arn(self, policy_name):
        """Fetch policy arn"""
        return 'arn:aws:iam::{}:policy/{}'.format(self.get_account_id(), policy_name)
    
    def get_role_arn(self, role_name):
        """Fetch role arn"""
        return 'arn:aws:iam::{}:role/{}'.format(self.get_account_id(), role_name)

    def get_lambda_arn(self, func_name):
        """Return invokeable function url"""
        return 'arn:aws:lambda:{}:{}:function:{}'.format(self.get_region(), self.get_account_id(), func_name)

