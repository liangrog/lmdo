

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

class CreateStageCommand(CommandInterface):
    """Command for fetch"""
    def run(self):
        self._obj.create_stage()

class DeleteStageCommand(CommandInterface):
    """Command for fetch"""
    def run(self):
        self._obj.delete_stage()

class CreateDomainCommand(CommandInterface):
    """Command for fetch"""
    def run(self):
        self._obj.create_domain()

class DeleteDomainCommand(CommandInterface):
    """Command for fetch"""
    def run(self):
        self._obj.delete_domain()

class CreateMappingCommand(CommandInterface):
    """Command for fetch"""
    def run(self):
        self._obj.create_mapping()

class DeleteMappingCommand(CommandInterface):
    """Command for fetch"""
    def run(self):
        self._obj.delete_mapping()

class TailCommand(CommandInterface):
    """Command for tail"""
    def run(self):
        self._obj.tail()

class PackageCommand(CommandInterface):
    """Command for package"""
    def run(self):
        self._obj.package()

class ExportCommand(CommandInterface):
    """Command for package"""
    def run(self):
        self._obj.export()

class Dispatcher(object):
    """Command invocation class"""
    def run(self, command):
        #try:
            command.run()
        #except Exception as exc:
        #    raise exc


