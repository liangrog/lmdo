from __future__ import print_function

from .base import Base
from .lm import Lm
from .cf import Cf
from .api import Api


class Deploy(Base):
    """
    Deploying AWS assets
    """

    def run(self):
        print('Assets deployment process start...')

        Lm().run()
        Cf().run()
        Api().run()

        print('Assets deployment process complete')


