import logging
import json
import subprocess
import os
import shutil

# Set up logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Only in tmp you can run executables for lambda
BIN_DIR = '/tmp/bin'
ENV_DEBUG = 'DEBUG'
ENV_GO_EXE = 'GO_EXE'

GO_EXE = os.path.join(BIN_DIR, os.getenv(ENV_GO_EXE))

# Make sure we have go executable ready to use
# This will be only run once. Subsequent calls
# will go through handler directly
if not os.path.exists(BIN_DIR):
    os.makedirs(BIN_DIR)

shutil.copy2(os.getenv('GO_EXE'), GO_EXE)
os.chmod(GO_EXE, 0775)

def dump(obj):
    """Dumping context"""
    if hasattr(obj, '__slots__'):
        return {slot: getattr(obj, slot) for slot in obj.__slots__}
    return obj.__dict__

def handler(event, context):  
    error_msg = {'error': True}

    # debug mode
    debug = False
    if os.getenv(ENV_DEBUG, 'False').lower() == 'true':
        debug = True

    if debug:
        logger.info(event)
 
    if not os.getenv(ENV_GO_EXE):
        logger.error('No handler executable found from the environment variable {}'.format(ENV_GO_EXE))
        return error_msg
   
    # Run go executable
    cmd = [GO_EXE, json.dumps(event), json.dumps(context, default=dump)]
    output, error = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    if error:
        logger.error(error)
        return error_msg

    try:
        json_obj = json.loads(output)

        if debug:
            logger.info(json_obj)

        return json_obj
    except ValueError:
        if debug:
            logger.info(output)
        
        return output


