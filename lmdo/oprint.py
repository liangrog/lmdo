from __future__ import print_function

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
    def infog(cls, msg, prefix='- '):
        if type(msg) is str:
            print(prefix + Oprint.OKGREEN + msg + Oprint.ENDC)
        else:
            print(msg)

    @classmethod
    def info(cls,  msg, prefix='- '):
        if type(msg) is str:
            print(prefix+ Oprint.OKBLUE + msg + Oprint.ENDC)
        else:
            print(msg)
    
    @classmethod
    def warn(cls, msg, prefix='- '):
        if type(msg) is str:
            print(prefix + Oprint.WARNING + msg + Oprint.ENDC)
        else:
            print(msg)
    
    @classmethod
    def err(cls, msg, prefix='- '):
        if type(msg) is str:
            print(prefix + Oprint.FAIL + msg + Oprint.ENDC)
        else:
            print(msg)


