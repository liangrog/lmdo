

class ChainProcessor(object):
    """Processor deal with chain of resposibility"""
    def __init__(self):
        self.successor = None
    
    @property
    def successor(self):
        return self.successor

    @successor.setter
    def successor(self, successor):
        self.successor = successor
    
    def process(self, data):
        """Interface for all children"""
        raise NotImplementedError

    def process_next(self, data):
        """Let the next successor process"""
        if self.successor:
            self.successor.process_next(self.process(data))
        else:
            return self.process(data)


