from __future__ import print_function

from .base import Base
from .lm import Lm
from .cf import Cf
from .api import Api
from lmdo.oprint import Oprint


class Destroy(Base):
    """
    Destroying all AWS assets deployed
    """

    def run(self):
        Oprint.info('Assets removal process start...')

        Api().destroy()
        Cf().destroy()
        Lm().destroy()
        
        Oprint.info('Assets removal process complete')


