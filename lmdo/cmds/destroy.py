from __future__ import print_function

from .base import Base
from .lm import Lm
from .cf import Cf
from .api import Api


class Destroy(Base):
    """
    Destroying all AWS assets deployed
    """

    def run(self):
        print('Assets removal process start...')

        Api().destroy()
        Cf().destroy()
        Lm().destroy()
        
        print('Assets removal process complete')


