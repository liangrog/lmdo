from __future__ import print_function
import sys
import getpass

from .base import Base
from .lm import Lm
from .cf import Cf
from .api import Api


class Deploy(Base):
    """
    Class packaging Lambda function codes and
    upload it to S3
    """

    def run(self):
        Lm().run()
        Cf().run()
        Api().run()


