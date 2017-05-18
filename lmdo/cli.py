"""
lmdo

Usage:
    lmdo init <project_name>
    lmdo init config
    lmdo env export
    lmdo bp fetch <url> [--config=<config-file.yaml>]
    lmdo cf (create|update|delete) [-c | --change_set] [-he | --hide-event] [--stack=<stackName>] [--config=<config-file.yaml>]
    lmdo lm (create|update|delete|package) [--function=<functionName>] [--config=<config-file.yaml>]
    lmdo cwe (create|update|delete) [--config=<config-file.yaml>]
    lmdo api (create|update|delete) [--config=<config-file.yaml>]
    lmdo api create-stage <from_stage> <to_stage> [--config=<config-file.yaml>]
    lmdo api delete-stage <from_stage> [--config=<config-file.yaml>]
    lmdo api create-domain <domain_name> <cert_name> <cert_path> <cert_private_key_path> <cert_chain_path> [--config=<config-file.yaml>]
    lmdo api delete-domain <domain_name> [--config=<config-file.yaml>]
    lmdo api create-mapping <domain_name> <base_path> <api_name> <stage> [--config=<config-file.yaml>]
    lmdo api delete-mapping <domain_name> <base_path> [--config=<config-file.yaml>]
    lmdo s3 sync [--config=<config-file.yaml>]
    lmdo logs tail function <function_name> [-f | --follow] [--day=<int>] [--start-date=<datetime>] [--end-date=<datetime>] [--config=<config-file.yaml>]
    lmdo logs tail <log_group_name> [-f | --follow] [--day=<int>] [--start-date=<datetime>] [--end-date=<datetime>] [--config=<config-file.yaml>]
    lmdo deploy [--config=<config-file.yaml>]
    lmdo destroy [--config=<config-file.yaml>]
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
    --config=<config-file.yaml>    Custom lmdo configuration file                  
"""

from __future__ import print_function
from docopt import docopt

from . import __version__ as VERSION
from lmdo.oprint import Oprint
from lmdo.cmds.bp.bp_client import BpClient


args = docopt(__doc__, version=VERSION)

def main():
    """Call Commands"""   

    # Project initalisation
    if args.get('init'):
        client_factory = BpClient(args)
        return client_factory.execute()

    from lmdo.lmdo_config import lmdo_config

    # Check if cli is at the right directory
    if not lmdo_config.if_lmdo_config_exist(args):
        Oprint.err('Please run lmdo command at the directory contains the lmdo config file')

    # Call the right client to handle
    if args.get('bp'):
        client_factory = BpClient(args)
    if args.get('env'):
        from lmdo.cmds.env.env_client import EnvClient
        client_factory = EnvClient(args)
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


