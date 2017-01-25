"""
lmdo

Usage:
    lmdo init <project_name>
    lmdo bp fetch <url>
    lmdo cf (create|update|delete) 
    lmdo lm (create|update|delete) [--function-name=<functionName>]
    lmdo api (create|update|delete)
    lmdo api create-stage <from_stage> <to_stage>
    lmdo api delete-stage <from_stage>
    lmdo api create-domain <domain_name> <cert_name> <cert_path> <cert_private_key_path> <cert_chain_path>
    lmdo api delete-domain <domain_name>
    lmdo api create-mapping <domain_name> <base_path> <api_name> <stage>
    lmdo api delete-mapping <domain_name> <base_path>
    lmdo s3 sync 
    lmdo logs tail function <function_name> [-f | --follow] [--day=<int>] [--start-date=<datetime>] [--end-date=<datetime>]
    lmdo logs tail <log_group_name> [-f | --follow] [--day=<int>] [--start-date=<datetime>] [--end-date=<datetime>]
    lmdo deploy
    lmdo destroy
    lmdo (-h | --help)
    lmdo --version

Options:
    -h --help                      Show this screen.
    --version                      Show version.
    --day=<int>                    Day to search e.g. 5, -10
    --start-date=<datetime>        Start date in format 1970-01-01
    --end-date=<datetime>          End date in format 1970-01-01
    -f --follow                    Follow entry
    --function-name=<functioName>  Lambda function name
    --group-name=<groupName>       Cloudwatch log group name

"""

from __future__ import print_function
from docopt import docopt

from . import __version__ as VERSION
from lmdo.lmdo_config import LmdoConfig
from lmdo.oprint import Oprint
from lmdo.cmds.cf.cf_client import CfClient
from lmdo.cmds.lm.lm_client import LmClient
from lmdo.cmds.api.api_client import ApiClient
from lmdo.cmds.s3.s3_client import S3Client
from lmdo.cmds.deploy.deploy_client import DeployClient
from lmdo.cmds.destroy.destroy_client import DestroyClient
from lmdo.cmds.bp.bp_client import BpClient
from lmdo.cmds.logs.logs_client import LogsClient


def main():
    """Call Commands"""   

    args = docopt(__doc__, version=VERSION)

    # Project initalisation
    if args.get('init'):
        client_factory = BpClient(args)
        return client_factory.execute()

    # Check if cli is at the right directory
    if not LmdoConfig.if_lmdo_config_exist():
        Oprint.err('Please run lmdo command at the directory contains the lmdo config file')

    # Call the right client to handle
    if args.get('bp'):
        client_factory = BpClient(args)
    elif args.get('s3'):
        client_factory = S3Client(args)
    elif args.get('cf'):
        client_factory = CfClient(args)
    elif args.get('lm'):
        client_factory = LmClient(args)
    elif args.get('api'):
        client_factory = ApiClient(args)
    elif args.get('logs'):
        client_factory = LogsClient(args)
    elif args.get('deploy'):
        client_factory = DeployClient(args)
    elif args.get('destroy'):
        client_factory = DestroyClient(args)

    if client_factory:
        client_factory.execute()


