

class ConfigParserInterface(object):
    """
    Config parser interface
    All parsers for configuaration will
    need to comply with this interface
    so lmdo can understand it
    """
    def get(self, *args, **kwargs):
        """Get value from config file"""
        raise NotImplementedError

    def validate(self, *args, **kwargs):
        """Validate config file"""
        raise NotImplementedError


