
from lmdo.cmds.api.apigateway import Apigateway
from lmdo.cmds.commands import Dispatcher, CreateCommand, UpdateCommand, DeleteCommand
from lmdo.cmds.client_factory_interface import ClientFactoryInterface

class ApiClient(ClientFactoryInterface):
    """Cloudformation command client"""
    def __init__(self, args):
        self._apigateway = Apigateway()
        self._dispatcher = Dispatcher()
        self._args = args

    def execute(self):
        if self._args.get('create'):
            self._dispatcher.run(CreateCommand(self._apigateway))
        elif self._args.get('update'):
            self._dispatcher.run(UpdateCommand(self._apigateway))
        elif self._args.get('delete'):
            self._dispatcher.run(DeleteCommand(self._apigateway))
        else:
            Oprint.err('create|update|delete command option is required', 'lmdo')


