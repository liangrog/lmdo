from abc import ABCMeta, abstractmethod


class Convertor:
    """Abstract resovler interface"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def convert(self, *args, **kwargs):
        pass


