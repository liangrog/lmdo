from abc import ABCMeta, abstractmethod


class ConfigParser:
    """Configuration file parser ABC"""
    __metaclass__ = ABCMeta

    """
    Config parser interface
    All parsers for configuaration will
    need to comply with this interface
    so lmdo can understand it
    """
    @abstractmethod
    def get(self, *args, **kwargs):
        """Get value from config file"""
        pass

    @abstractmethod
    def validate(self, *args, **kwargs):
        """Validate config file"""
        pass


