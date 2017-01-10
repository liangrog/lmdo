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

class InitCommand(CommandInterface):
    """Command for initialisation"""
    def run(self):
        self._obj.init()

class SyncCommand(CommandInterface):
    """Command for syncing"""
    def run(self):
        self._obj.sync()

class FetchCommand(CommandInterface):
    """Command for fetch"""
    def run(self):
        self._obj.fetch()

class Dispatcher(object):
    """Command invocation class"""
    def run(self, command):
        try:
            command.run()
        except Exception as e:
            print "Unexpected error:", sys.exc_info()[0]
            raise e


