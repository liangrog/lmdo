"""
lmdo

Usage:
    lmdo init <project_name>
    lmdo init config
    lmdo bp fetch <url>
    lmdo cf (create|update|delete) [-c | --change_set] [-he | --hide-event] [--stack=<stackName>]
    lmdo lm (create|update|delete|package) [--function=<functionName>]
    lmdo cwe (create|update|delete)
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
    --function=<functioName>       Lambda function name
    --group-name=<groupName>       Cloudwatch log group name
    -he --hide-event               Hide CloudFormation event output

"""

from __future__ import print_function
from docopt import docopt

from . import __version__ as VERSION
from lmdo.oprint import Oprint
from lmdo.cmds.bp.bp_client import BpClient


def main():
    """Call Commands"""   

    args = docopt(__doc__, version=VERSION)

    # Project initalisation
    if args.get('init'):
        client_factory = BpClient(args)
        return client_factory.execute()

    from lmdo.lmdo_config import lmdo_config

    # Check if cli is at the right directory
    if not lmdo_config.if_lmdo_config_exist():
        Oprint.err('Please run lmdo command at the directory contains the lmdo config file')

    # Call the right client to handle
    if args.get('bp'):
        client_factory = BpClient(args)
    elif args.get('s3'):
        from lmdo.cmds.s3.s3_client import S3Client
        client_factory = S3Client(args)
    elif args.get('cf'):
        from lmdo.cmds.cf.cf_client import CfClient
        client_factory = CfClient(args)
    elif args.get('lm'):
        from lmdo.cmds.lm.lm_client import LmClient
        client_factory = LmClient(args)
    elif args.get('api'):
        from lmdo.cmds.api.api_client import ApiClient
        client_factory = ApiClient(args)
    elif args.get('cwe'):
        from lmdo.cmds.cwe.cwe_client import CweClient
        client_factory = CweClient(args)
    elif args.get('logs'):
        from lmdo.cmds.logs.logs_client import LogsClient
        client_factory = LogsClient(args)
    elif args.get('deploy'):
        from lmdo.cmds.deploy.deploy_client import DeployClient
        client_factory = DeployClient(args)
    elif args.get('destroy'):
        from lmdo.cmds.destroy.destroy_client import DestroyClient
        client_factory = DestroyClient(args)

    if client_factory:
        client_factory.execute()


