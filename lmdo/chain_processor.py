

class ChainProcessor(object):
    """Processor deal with chain of resposibility"""
    def __init__(self):
        self._successor = None
    
    @property
    def successor(self):
        return self._successor

    @successor.setter
    def successor(self, successor):
        self._successor = successor
    
    def process(self, data):
        """Interface for all children"""
        raise NotImplementedError

    def process_next(self, data):
        """Let the next successor process"""
        if self._successor:
            return self._successor.process_next(self.process(data))
        else:
            return self.process(data)


