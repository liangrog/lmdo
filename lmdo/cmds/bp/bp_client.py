
from lmdo.cmds.bp.boiler_plate import BoilerPlate
from lmdo.cmds.commands import Dispatcher, InitCommand, FetchCommand
from lmdo.cmds.client_factory import ClientFactory


class BpClient(ClientFactory):
    """Init command client"""
    def __init__(self, args):
        self._boiler_plate = BoilerPlate(args)
        self._dispatcher = Dispatcher()
        self._args = args

    def execute(self):
        if self._args.get('init'):
            self._dispatcher.run(InitCommand(self._boiler_plate))

        if self._args.get('bp'):
            if self._args.get('fetch'):
                self._dispatcher.run(FetchCommand(self._boiler_plate))


