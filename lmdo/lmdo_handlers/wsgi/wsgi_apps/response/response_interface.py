

class ResponseInterface(object):
    """wsgi response interface"""

    def translate(self, *args, **kwargs):
        raise NotImplementedError


