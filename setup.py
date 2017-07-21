"""Packaging settings."""

import os
from codecs import open
from subprocess import call

from setuptools import Command, find_packages, setup

from lmdo import __version__

# Set external files
try:
    from pypandoc import convert
    README = convert('README.md', 'rst')
except ImportError:
    README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


class RunTests(Command):

    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov=lmdo', '--cov-report=term-missing'])
        raise SystemExit(errno)


setup(
    name='lmdo',
    version=__version__,
    description='CLI tools for microservices automation using AWS Lambda function',
    url='https://github.com/liangrog/lmdo',
    author='Roger Liang',
    author_email='pinguroger@gmail.com',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='cli',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=[
        'docopt==0.6.2',
        'boto3>=1.4.2',
        'PyYAML==3.12',
        'jinja2==2.8',
        'gitpython',
        'lambda-packages==0.13.0',
    ],
    extras_require={
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'lmdo=lmdo.cli:main',
        ],
    },
    cmdclass={'test': RunTests},
)
