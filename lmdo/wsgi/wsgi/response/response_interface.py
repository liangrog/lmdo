

class ResponseInterface(object):
    """wsgi response interface"""

    def translate(self):
        raise NotImplementedError


