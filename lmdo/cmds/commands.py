import sys


class CommandInterface(object):
    """The command interface"""
    def __init__(self, obj):
        self._obj = obj

    def run(self):
        raise NotImplementedError

class CreateCommand(CommandInterface):
    """Command for creation"""
    def run(self):
        self._obj.create()

class UpdateCommand(CommandInterface):
    """Command for update"""
    def run(self):
        self._obj.update()

class DeleteCommand(CommandInterface):
    """Command for delete"""
    def run(self):
        self._obj.delete()

class DeployCommand(CommandInterface):
    """Command for deployment"""
    def run(self):
        self._obj.deploy()

class TeardownCommand(CommandInterface):
    """Commmand for tear down"""
    def run(self):
        self._obj.teardown()

class Dispatcher(object):
    """Command invocation class"""
    def run(self, command):
        try:
            command.run()
        except Exception as e:
            print "Unexpected error:", sys.exc_info()[0]
            raise e


