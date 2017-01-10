
from lmdo.cmds.bp.boiler_plate import BoilerPlate
from lmdo.cmds.commands import Dispatcher, InitCommand, FetchCommand
from lmdo.cmds.client_factory_interface import ClientFactoryInterface


class InitClient(ClientFactoryInterface):
    """Init command client"""
    def __init__(self, args):
        self._boilder_plate = BoilerPlate(args)
        self._args = args

    def execute(self):
        if self._args.get('init'):
            self._dispatcher.run(InitCommand(self._boiler_plate))

        if self._args.get('bp'):
            if self._args.get('fetch'):
            self._dispatcher.run(FetchCommand(self._boiler_plate))


