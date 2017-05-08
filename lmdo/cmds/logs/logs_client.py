
from lmdo.cmds.logs.logs import Logs
from lmdo.cmds.commands import Dispatcher, TailCommand
from lmdo.cmds.client_factory import ClientFactory


class LogsClient(ClientFactory):
    """Cloudformation command client"""
    def __init__(self):
        self._logs = Logs(args)
        self._dispatcher = Dispatcher()

    def execute(self):
        if self._args.get('tail'):
            self._dispatcher.run(TailCommand(self._logs))
        else:
            Oprint.err('Command option is required', 'lmdo')

