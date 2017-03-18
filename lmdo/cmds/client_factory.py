from abc import ABCMeta, abstractmethod


class ClientFactory:
    """Command client ABC"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute(self):
        pass


