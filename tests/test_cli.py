
from subprocess import PIPE, Popen as popen
from unittest import TestCase

from docopt import docopt

from inspect import getmembers, isclass
from lmdo import __version__ as VERSION
from lmdo import cli
from lmdo.cmds import LambdaFunc

"""
class TestHelp(TestCase):
    def test_returns_usage_information(self):
        output = popen(['lmdo', '-h'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output)

        output = popen(['lmdo', '--help'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output)

class TestVersion(TestCase):
    def test_returns_version_information(self):
        output = popen(['lmdo', '--version'], stdout=PIPE).communicate()[0]
        self.assertEqual(output.strip(), VERSION)
        """

class TestMain(TestCase):
    def test_main(self):
        t = LambdaFunc(['lm'])
        cls_commands = getmembers(t, isclass)
        c = [command[1] for command in cls_commands if command[0] != 'Base'][0]
        print(c)
        #for c in cls_commands:
        #    print(c);
        #print(command for command in cls_commands)
        #print(cls_commands)

        assert False
        """
        argvs = ['lm']
        args = docopt(__doc__, argv=argvs, version=VERSION)
    
        for k, v in arguments.iteritems():
            print(k, ":", v)   
            if hasattr(commands, k) and v:
                module = getattr(commands, k)
                cls_commands = getmembers(module, isclass)
                print(cls_commands)
                command = [command[1] for command in cls_commands if command[0] != 'Base'][0]
                command = command(args)
"""
