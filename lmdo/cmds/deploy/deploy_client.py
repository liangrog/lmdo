
from lmdo.cmds.cf.cloudformation import Cloudformation
from lmdo.cmds.lm.lambdaa import Lambda
from lmdo.cmds.api.apigateway import Apigateway
from lmdo.cmds.commands import Dispatcher, CreateCommand
from lmdo.cmds.client_factory_interface import ClientFactoryInterface
from lmdo.oprint import Oprint

class DeployClient(ClientFactoryInterface):
    """Cloudformation command client"""
    def __init__(self, args):
        self._cloudformation = Cloudformation()
        self._lambda = Lambda()
        self._apigateway = Apigateway(args)
        self._dispatcher = Dispatcher()
        self._args = args

    def execute(self):
        Oprint.info('Start deploying service', 'lmdo')
        self._dispatcher.run(CreateCommand(self._cloudformation))
        self._dispatcher.run(CreateCommand(self._lambda))
        self._dispatcher.run(CreateCommand(self._apigateway))
        Oprint.info('Complete deploying service', 'lmdo')


