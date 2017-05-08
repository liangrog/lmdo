
from lmdo.cmds.cf.cloudformation import Cloudformation
from lmdo.cmds.lm.aws_lambda import AWSLambda
from lmdo.cmds.api.apigateway import Apigateway
from lmdo.cmds.cwe.cloudwatch_event import CloudWatchEvent
from lmdo.cmds.commands import Dispatcher, CreateCommand
from lmdo.cmds.client_factory import ClientFactory
from lmdo.oprint import Oprint

class DeployClient(ClientFactory):
    """Cloudformation command client"""
    def __init__(self, args):
        self._cloudformation = Cloudformation()
        self._lambda = AWSLambda()
        self._apigateway = Apigateway()
        self._cloudwatchevent = CloudWatchEvent()
        self._dispatcher = Dispatcher()
        self._args = args

    def execute(self):
        Oprint.info('Start deploying service', 'lmdo')
        self._dispatcher.run(CreateCommand(self._cloudformation))
        self._dispatcher.run(CreateCommand(self._lambda))
        self._dispatcher.run(CreateCommand(self._apigateway))
        self._dispatcher.run(CreateCommand(self._cloudwatchevent))
        Oprint.info('Complete deploying service', 'lmdo')


