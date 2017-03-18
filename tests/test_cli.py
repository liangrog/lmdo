
from subprocess import PIPE, Popen as popen
from unittest import TestCase

from docopt import docopt

from lmdo import __version__ as VERSION

class TestHelp(TestCase):
    """Test case"""
    def test_returns_usage_information(self):
        """Test usage"""
        output = popen(['lmdo', '-h'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output)

        output = popen(['lmdo', '--help'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output)

class TestVersion(TestCase):
    """Test version"""
    def test_returns_version_information(self):
        output = popen(['lmdo', '--version'], stdout=PIPE).communicate()[0]
        self.assertEqual(output.strip(), VERSION)

