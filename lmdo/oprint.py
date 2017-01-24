from __future__ import print_function
import os
import sys

def lmdo_output(func):
    """lmdo output message decorator"""

    def __wrapper(cls, msg, src='lmdo', *args, **kwargs):
        if type(msg) is str:
            msg = '==> [{}]: {}'.format(src, msg).lower()

        output = func(cls, msg, *args, **kwargs)
        return output
    return __wrapper

    
class Oprint(object):
    """Printing class for output formatting"""

    # Colour codes
    header = '\033[95m'
    okblue = '\033[94m'
    okgreen = '\033[92m'
    warning = '\033[93m'
    fail = '\033[91m'
    endc = '\033[0m'
    bold = "\033[1m"

    def disable(self):
        header = ''
        okblue = ''
        okgreen = ''
        warning = ''
        fail = ''
        endc = ''

    @classmethod
    @lmdo_output
    def infog(cls, msg):
        if type(msg) is str:
            print(Oprint.okgreen + msg + Oprint.endc)
        else:
            print(msg)

    @classmethod
    @lmdo_output
    def info(cls, msg):
        if type(msg) is str:
            print(Oprint.okblue + msg + Oprint.endc)
        else:
            print(msg)
    
    @classmethod
    @lmdo_output
    def warn(cls, msg):
        if type(msg) is str:
            print(Oprint.warning + msg + Oprint.endc)
        else:
            print(msg)
    
    @classmethod
    @lmdo_output
    def err(cls, msg, exit=True):
        if type(msg) is str:
            print(Oprint.fail + msg + Oprint.endc)
        else:
            print(msg)
        
        # Exit if error. It's anti-pattern here (seperation
        # of responsibility) but hate to put this everywhere
        # in the code, so a compromise
        if exit:
            sys.exit(0)


