from __future__ import print_function
import sys
import os
import shutil
import site

class Tpl:
    """
    Copy templates
    """

    def __init__(self, options):
        pass

    def run(self):
        pkg_dir = site.getsitepackages()
        for pd in pkg_dir:
            if os.path.isdir(pd + '/lmdo'):
                src_dir = pd + '/lmdo/template'
                break
        if src_dir:
            self.copytree(src_dir, './')

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
                    print(e)
                    os.unlink(d)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)


