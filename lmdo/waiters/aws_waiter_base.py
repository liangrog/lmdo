
from lmdo.waiters.cli_waiter_interface import CliWaiterInterface
from lmdo.cmds.aws_base import AWSBase


class AWSWaiterBase(AWSBase):
    """Cloudformation waiter base"""
    def __init__(self, client_type, client=None):
        super(AWSWaiterBase, self).__init__()
        if client:
            self._client = client
        else:
            self._client = self.get_client(client_type)

    @property
    def client(self):
        return self._client


