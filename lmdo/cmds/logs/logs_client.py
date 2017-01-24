
from lmdo.cmds.logs.logs import Logs
from lmdo.cmds.commands import Dispatcher, TailCommand
from lmdo.cmds.client_factory_interface import ClientFactoryInterface


class LogsClient(ClientFactoryInterface):
    """Cloudformation command client"""
    def __init__(self, args):
        self._logs = Logs(args)
        self._dispatcher = Dispatcher()
        self._args = args

    def execute(self):
        if self._args.get('tail'):
            self._dispatcher.run(TailCommand(self._logs))
        else:
            Oprint.err('Command option is required', 'lmdo')

