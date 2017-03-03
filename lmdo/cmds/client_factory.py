from abc import ABCMeta


class ClientFactory:
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute(self):
        pass


