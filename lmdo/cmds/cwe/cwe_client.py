
from lmdo.cmds.cwe.cloudwatch_event import CloudWatchEvent
from lmdo.cmds.commands import Dispatcher, CreateCommand, UpdateCommand, DeleteCommand
from lmdo.cmds.client_factory import ClientFactory

class CweClient(ClientFactory):
    """Cloudwatch command client"""
    def __init__(self, args=None):
        self._cloudwatchevent = CloudWatchEvent()
        self._dispatcher = Dispatcher()
        self._args = args

    def execute(self):
        if self._args.get('create'):
            self._dispatcher.run(CreateCommand(self._cloudwatchevent))
        elif self._args.get('update'):
            self._dispatcher.run(UpdateCommand(self._cloudwatchevent))
        elif self._args.get('delete'):
            self._dispatcher.run(DeleteCommand(self._cloudwatchevent))
        else:
            Oprint.err('create|update|delete command option is required', 'lmdo')

