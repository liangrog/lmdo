from __future__ import print_function
import os
import fnmatch
import json

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint


class IAM(AWSBase):
    """
    Class upload cloudformation template to S3
    and create/update stack
    Stack name is fixed with User-Stage-Servicename-Service
    """
    def __init__(self):
        super(IAM, self).__init__()
        self._client = self.get_client('iam') 

    @property
    def client(self):
        return self._client
 
    def create_role(self, role_name, policy):
        pass

    def delete_role(self, role_name):
        pass
                   

