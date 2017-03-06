from abc import ABCMeta, abstractmethod


class ClientFactory:
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute(self):
        pass


