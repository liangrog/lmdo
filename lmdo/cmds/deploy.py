from __future__ import print_function

from .base import Base
from .lm import Lm
from .cf import Cf
from .api import Api
from lmdo.oprint import Oprint


class Deploy(Base):
    """
    Deploying AWS assets
    """

    def run(self):
        Oprint.info('Assets deployment process start...', 'default')

        Lm().run()
        Cf().run()
        Api().run()

        Oprint.info('Assets deployment process complete', 'default')


