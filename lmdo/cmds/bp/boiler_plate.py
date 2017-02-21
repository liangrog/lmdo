from __future__ import print_function
import sys
import os
import shutil
import fnmatch
import tempfile

from git import Repo

from lmdo.config import PROJECT_CONFIG_FILE
from lmdo.oprint import Oprint
from lmdo.utils import mkdir, get_sitepackage_dirs, copytree
from lmdo.spinner import spinner

class BoilerPlate(object):
    """Boiler plating handler"""
   
    def __init__(self, args):
        self._args = args

    def init(self):
        """Initiating the project and provide a sample lmdo.yml file"""
        mkdir('./{}'.format(self._args.get('<project_name>')))

        """Copy lmdo.yml over"""
        # Do not copy over unless it's a clearn dir
        if os.path.isfile('./{}'.format(PROJECT_CONFIG_FILE)):
            Oprint.err('Your have existing lmdo.yml already, exiting...', 'lmdo')

        pkg_dir = get_sitepackage_dirs()
        for pd in pkg_dir:
            if os.path.isdir(pd + '/lmdo'):
                src_dir = pd + '/lmdo/template'
                break
        if src_dir:
            copytree(src_dir, './{}'.format(self._args.get('<project_name>')))
        
    def fetch(self):
        """Fetch template repo to local"""
        try: 
            Oprint.info('Start downloading repo to your project from {}'.format(self._args.get('<url>')), 'lmdo')
            spinner.start()

            tmp = tempfile.gettempdir()
            self.git_clone(self._args.get('<url>'), tmp)
            copytree(tmp, './', ignore=shutil.ignore_patterns('*.git*'))
            shutil.rmtree(tmp)
            
            spinner.stop()
            Oprint.info('Complete downloading repo to your project from {}'.format(self._args.get('<url>')), 'lmdo')
        except Exception as e:
            spinner.stop()
            raise e

    def git_clone(self, url, local_dir, depth=1):
        """Clone a repo from url to local"""
        if os.path.isdir(local_dir):
            shutil.rmtree(local_dir)
        
        mkdir(local_dir)
        Repo.clone_from(url, local_dir, depth=depth)


