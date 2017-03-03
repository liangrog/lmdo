from abc import ABCMeta


class Convertor:
    """Abstract resovler interface"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def convert(self, *args, **kwargs):
        pass


