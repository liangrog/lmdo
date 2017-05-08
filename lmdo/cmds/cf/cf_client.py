
from lmdo.cmds.cf.cloudformation import Cloudformation
from lmdo.cmds.commands import Dispatcher, CreateCommand, UpdateCommand, DeleteCommand
from lmdo.cmds.client_factory import ClientFactory

class CfClient(ClientFactory):
    """Cloudformation command client"""
    def __init__(self, args):
        self._cloudformation = Cloudformation()
        self._dispatcher = Dispatcher()
        self._args = args

    def execute(self):
        if self._args.get('create'):
            self._dispatcher.run(CreateCommand(self._cloudformation))
        elif self._args.get('update'):
            self._dispatcher.run(UpdateCommand(self._cloudformation))
        elif self._args.get('delete'):
            self._dispatcher.run(DeleteCommand(self._cloudformation))
        else:
            Oprint.err('create|update|delete command option is required', 'lmdo')

