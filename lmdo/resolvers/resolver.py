from abc import ABCMeta


class Resolver:
    """Abstract resovler interface"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def resolve(self, *args, **kwargs):
        pass


