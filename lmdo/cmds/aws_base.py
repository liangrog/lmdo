import boto3

from lmdo.lmdo_config import lmdo_config


class AWSBase(object):
    """base AWS delegator class"""

    def __init__(self):
        self._config = lmdo_config

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
        # User 'default' if no specified profile
        profile = 'default'
        if self._config.get('Profile'):
            profile = self._config.get('Profile')

        return boto3.Session(profile_name=profile)

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
