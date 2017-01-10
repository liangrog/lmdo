from __future__ import print_function
import sys
import os
import shutil
import site

from lmdo.config import project_config_file
from lmdo.oprint import Oprint
from lmdo.utils import mkdir

class BoilerPlate(object):
    """Boiler plating handler"""
   
    def __init__(self, args):
        self._args = args

    def init(self):
        mkdir(self._args.get('project_name'))

        """Copy lmdo.yml over"""
        # Do not copy over unless it's a clearn dir
        if os.path.isfile('./{}'.format(project_config_file)):
            Oprint.err('Your have existing lmdo.yml already, exiting...', 'lmdo')

        pkg_dir = site.getsitepackages()
        for pd in pkg_dir:
            if os.path.isdir(pd + '/lmdo'):
                src_dir = pd + '/lmdo/template'
                break
        if src_dir:
            self.copytree(src_dir, './{}'.format(self._args.get('project_name')))

    def fetch(self):
        pass
        self.clone_boilerplate_to_tmp()
        self.cp_boilerplate_to_project()

    def copytree(self, src, dst, symlinks=False, ignore=None):
        """
        Copy content to new destination
        """

        for item in os.listdir(src):
            # Ignore .pyc
            if item.endswith('.pyc'):
                continue

            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.exists(d):
                try:
                    shutil.rmtree(d)
                except Exception as e:
                    Oprint.err(e, 'lmdo')
                    os.unlink(d)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

    def clone_boilerplate_to_tmp(self):
        pass

    def cp_boilerplate_to_project(self, from_dir, to_dir):
        pass


