
from lmdo.cmds.s3.s3 import S3
from lmdo.cmds.commands import Dispatcher, SyncCommand
from lmdo.cmds.client_factory import ClientFactory


class S3Client(ClientFactory):
    """Cloudformation command client"""
    def __init__(self, args):
        self._s3 = S3()
        self._dispatcher = Dispatcher()
        self._args = args

    def execute(self):
        if self._args.get('sync'):
            self._dispatcher.run(SyncCommand(self._s3))
        else:
            Oprint.err('sync command option is required', 'lmdo')

