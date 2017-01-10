from __future__ import print_function

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint


class IAM(AWSBase):
    """create/update IAM properties"""

    def __init__(self):
        super(IAM, self).__init__()
        self._client = self.get_client('iam') 

    @property
    def client(self):
        return self._client
 
    def create_role(self, role_name, policy):
        """Create an IAM role"""
        try:
            Oprint.info('Creating role {}'.format(role_name), 'iam')
            response = self._client.create_role(RoleName=role_name, AssumeRolePolicyDocument=policy)
            Oprint.info('Complete creating role {}'.format(role_name), 'iam')
        except Exception as e:
            Oprint.err(e, 'iam')

        return response

    def delete_role(self, role_name):
        """Delete an IAM role"""
        try:
            Oprint.info('Deleting role {}'.format(role_name), 'iam')
            response = self._client.delete_role(RoleName=role_name)
            Oprint.info('Complete deleting role {}'.format(role_name), 'iam')
        except Exception as e:
            Oprint.err(e, 'iam')

        return response
                   

