from __future__ import print_function
import sys
import os
import shutil
import site
import fnmatch
from git import Repo

from lmdo.config import PROJECT_CONFIG_FILE, TMP_DIR
from lmdo.oprint import Oprint
from lmdo.utils import mkdir
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

        pkg_dir = site.getsitepackages()
        for pd in pkg_dir:
            if os.path.isdir(pd + '/lmdo'):
                src_dir = pd + '/lmdo/template'
                break
        if src_dir:
            self.copytree(src_dir, './{}'.format(self._args.get('<project_name>')))
        
    def fetch(self):
        """Fetch template repo to local"""
        try: 
            Oprint.info('Start downloading repo to your project from {}'.format(self._args.get('<url>')), 'lmdo')
            spinner.start()

            tmp = '{}/{}'.format(TMP_DIR, 'git_tmp')
            self.git_clone(self._args.get('<url>'), tmp)
            self.copytree(tmp, './', ignore=shutil.ignore_patterns('*.git*'))
            shutil.rmtree(tmp)
            
            spinner.stop()
            Oprint.info('Complete downloading repo to your project from {}'.format(self._args.get('<url>')), 'lmdo')
        except Exception as e:
            spinner.stop()
            raise e

    def copytree(self, src, dst, symlinks=False, ignore=None):
        """Copy content to new destination"""
        names = os.listdir(src)

        if ignore is not None:
            ignored_names = ignore(src, names)
        else:
            ignored_names = set()

        errors = []
        for name in names:
            if name.endswith('.pyc'):
                continue

            if name in ignored_names:
                continue

            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)

            # Delete if exists
            if os.path.exists(dstname):
                try:
                    shutil.rmtree(dstname)
                except Exception as e:
                    os.unlink(dstname)

            try:
                if symlinks and os.path.islink(srcname):
                    linkto = os.readlink(srcname)
                    os.symlink(linkto, dstname)
                elif os.path.isdir(srcname):
                    shutil.copytree(srcname, dstname, symlinks, ignore)
                else:
                    shutil.copy2(srcname, dstname)
            except (IOError, os.error) as why:
                errors.append((srcname, dstname, str(why)))
            # catch the Error from the recursive copytree so that we can
            # continue with other files
            except Exception as err:
                errors.extend(str(err))
        try:
            shutil.copystat(src, dst)
        except WindowsError:
            # can't copy file access times on Windows
            pass
        except OSError as why:
            errors.extend((src, dst, str(why)))
        if errors:
            raise Exception(errors)

    def git_clone(self, url, local_dir, depth=1):
        """Clone a repo from url to local"""
        if os.path.isdir(local_dir):
            shutil.rmtree(local_dir)
        
        mkdir(local_dir)
        Repo.clone_from(url, local_dir, depth=depth)


