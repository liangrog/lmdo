from __future__ import print_function

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint
from lmdo.waiters.s3_waiters import S3WaiterBucketCreate, S3WaiterBucketDelete, S3WaiterObjectCreate


class Logs(AWSBase):
    """Cloudwatch logs handler"""
    def __init__(self, args):
        super(Logs, self).__init__()
        self._client = self.get_client('logs') 
        self._args = args

    @property
    def client(self):
        return self._client


