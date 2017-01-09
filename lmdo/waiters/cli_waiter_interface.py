

class CliWaiterInterface(object):
    """Waiter interface for cli"""
    def wait(self, *args, **kwargs):
        raise NotImplementedError

    def get_waiter(self, *args, **kwargs):
        raise NotImplementedError


