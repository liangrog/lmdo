"""
lmdo

Usage:
    lmdo tpl
    lmdo lm
    lmdo cf
    lmdo api
    lmdo deploy
    lmdo destroy
    lmdo (-h | --help)
    lmdo --version

Options:
    -h --help     Show this screen.
    --version     Show version.

"""
from __future__ import print_function
from inspect import getmembers, isclass

from docopt import docopt

from . import __version__ as VERSION
import lmdo.cmds as cmds

def main():
    """
    Command dispatcher
    """

    args = docopt(__doc__, version=VERSION)
    
    for k, v in args.iteritems():
        if hasattr(cmds, k) and v:
            module = getattr(cmds, k)
            cls_commands = getmembers(module, isclass)
            command = [command[1] for command in cls_commands if command[0] != 'Base' and command[0].lower() == k][0]
            command = command(args)
            command.run()
