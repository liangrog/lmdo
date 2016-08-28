from __future__ import print_function

def lmdo_output(func):
    """
    lmdo output message decorator
    """

    def __wrapper(cls, msg, src='lmdo', *args, **kwargs):
        if type(msg) is str:
            msg = '==> [{}]: {}'.format(src, msg).lower()

        output = func(cls, msg, *args, **kwargs)
        return output
    return __wrapper

    
class Oprint:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = "\033[1m"

    def disable(self):
        HEADER = ''
        OKBLUE = ''
        OKGREEN = ''
        WARNING = ''
        FAIL = ''
        ENDC = ''

    @classmethod
    @lmdo_output
    def infog(cls, msg):
        if type(msg) is str:
            print(Oprint.OKGREEN + msg + Oprint.ENDC)
        else:
            print(msg)

    @classmethod
    @lmdo_output
    def info(cls, msg):
        if type(msg) is str:
            print(Oprint.OKBLUE + msg + Oprint.ENDC)
        else:
            print(msg)
    
    @classmethod
    @lmdo_output
    def warn(cls, msg):
        if type(msg) is str:
            print(Oprint.WARNING + msg + Oprint.ENDC)
        else:
            print(msg)
    
    @classmethod
    @lmdo_output
    def err(cls, msg):
        if type(msg) is str:
            print(Oprint.FAIL + msg + Oprint.ENDC)
        else:
            print(msg)


