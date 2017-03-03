from abc import ABCMeta


class ConfigParserInterface:
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
        raise NotImplementedError

    @abstractmethod
    def validate(self, *args, **kwargs):
        """Validate config file"""
        raise NotImplementedError


