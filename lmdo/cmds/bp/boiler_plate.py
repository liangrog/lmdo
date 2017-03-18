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
        self._pkg_dir = None

    def init(self):
        """Initiating the project and provide a sample lmdo.yaml file"""
        if self._args.get('<project_name>'):
            mkdir('./{}'.format(self._args.get('<project_name>')))

            """Copy lmdo.yaml over"""
            # Do not copy over unless it's a clearn dir
            if os.path.isfile(os.path.join(self._args.get('<project_name>'), PROJECT_CONFIG_FILE)):
                Oprint.err('Your have existing {} already, exiting...'.format(PROJECT_CONFIG_FILE), 'lmdo')

            pkg_dir = self.get_installed_path()
            if pkg_dir:
                copytree(os.path.join(pkg_dir, 'template'), './{}'.format(self._args.get('<project_name>')))
        elif self._args.get('config'):
           pkg_dir = self.get_installed_path()
           # Don't override existing lmdo.yaml
           if os.path.isfile(PROJECT_CONFIG_FILE):
               Oprint.warn('You have existing {} file, a copy will be created with name {}.copy'.format(PROJECT_CONFIG_FILE, PROJECT_CONFIG_FILE), 'lmdo')
               shutil.copyfile(os.path.join(pkg_dir, 'template', PROJECT_CONFIG_FILE), '{}.copy'.format(PROJECT_CONFIG_FILE))
           else:
               shutil.copyfile(os.path.join(pkg_dir, 'template', PROJECT_CONFIG_FILE), PROJECT_CONFIG_FILE)
    
    def get_installed_path(self):
        """Get lmdo site package installed path"""
        if not self._pkg_dir:
            pkg_dir = get_sitepackage_dirs()
            for pd in pkg_dir:
                if os.path.isdir(os.path.join(pd, 'lmdo')):
                    self._pkg_dir = os.path.join(pd, 'lmdo')                
                    return self._pkg_dir

        Oprint.err('You don\'t seem to have lmdo installed. Cannot find lmdo in your site packages')
        return False

    def fetch(self):
        """Fetch template repo to local"""
        try: 
            Oprint.info('Start downloading repo to your project from {}'.format(self._args.get('<url>')), 'lmdo')
            spinner.start()

            tmp = tempfile.mkdtemp()
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


