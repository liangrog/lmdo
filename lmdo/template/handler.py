from __future__ import print_function
import sys
import os

# get this file's directory independent of where it's run from
file_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(file_path, "./"))
sys.path.append(os.path.join(file_path, "./vendored"))

import boto3
import json

def auth(event, context):
