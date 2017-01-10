from __future__ import print_function
import sys
import os
import shutil
import site
from git import Repo

from lmdo.config import PROJECT_CONFIG_FILE, TMP_DIR
from lmdo.oprint import Oprint
from lmdo.utils import mkdir

class BoilerPlate(object):
    """Boiler plating handler"""
   
    def __init__(self, args):
        self._args = args

    def init(self):
        """Initiating the project and provide a sample lmdo.yml file"""
        mkdir(self._args.get('project_name'))

        """Copy lmdo.yml over"""
        # Do not copy over unless it's a clearn dir
        if os.path.isfile('./{}'.format(PROJECT_CONFIG_FILE)):
            Oprint.err('Your have existing lmdo.yml already, exiting...', 'lmdo')

        pkg_dir = site.getsitepackages()
        for pd in pkg_dir:
            if os.path.isdir(pd + '/lmdo'):
                src_dir = pd + '/lmdo/template'
                break
        if src_dir:
            self.copytree(src_dir, './{}'.format(self._args.get('project_name')))

    def fetch(self):
        """Fetch template repo to local"""
        tmp = '{}/{}'.format(TMP_DIR, 'git_tmp')
        self.git_clone(self._args.get('url'), tmp)
        self.cp_clean_repo(tmp, './')
        shutil.rmtree(tmp)

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

    def git_clone(self, url, local_dir):
        """Clone a repo from url to local"""
        if os.path.isdir(local_dir):
            shutil.rmtree(local_dir)
        
        mkdir(local_dir)

        repo = Repo.init(local_dir)
        origin = repo.create_remote('origin', url)
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
         
    def cp_clean_repo(self, from_path, to_path):
        """Copy repo to dir without git"""
        self.copytree(from_path, to_path, ignore=shutil.ignore_patterns('*.git', '.gitignore'))


