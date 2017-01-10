"""
lmdo

Usage:
    lmdo init <project_name>
    lmdo bp fetch <url>
    lmdo cf (create|update|delete) 
    lmdo lm (create|update|delete)
    lmdo api (create|update|delete)
    lmdo api (create-domain|delete-domain) <domain_name> <cert_name> <cert_path> <cert_private_key_path> <cert_chain_path>
    lmdo api (create-mapping|delete-mapping) <base_path> <api_name> <stage>
    lmdo s3 sync 
    lmdo deploy
    lmdo destroy
    lmdo (-h | --help)
    lmdo --version

Options:
    -h --help     Show this screen.
    --version     Show version.
    --to          Relative Path installed to [default: ./]

"""

from __future__ import print_function
from docopt import docopt

from . import __version__ as VERSION
from lmdo.lmdo_config import LmdoConfig
from lmdo.cmds.cf.cf_client import CfClient
from lmdo.cmds.lm.lm_client import LmClient
from lmdo.cmds.api.api_client import ApiClient
from lmdo.cmds.deploy.deploy_client import DeployClient
from lmdo.cmds.destroy.destroy_client import DestroyClient
from lmdo.cmds.bp.bp_client import BpClient


def main():
    """Call Commands"""   

    args = docopt(__doc__, version=VERSION)

    # Check if cli is at the right directory
    if !args.get('init') and !LmdoConfig.if_lmdo_config_exist():
        Oprint.err('Please run lmdo command at the directory contains the lmdo config file')

    # Call the right client to handle
    if args.get('bp'):
        client_factory = BpClient(args)
    elif args.get('init'):
        client_factory = BpClient(args)
    elif args.get('cf'):
        client_factory = CfClient(args)
    elif args.get('lm'):
        client_factory = LmClient(args)
    elif args.get('api'):
        client_factory = ApiClient(args)
    elif args.get('deploy'):
        client_factory = DeployClient(args)
    elif args.get('destroy'):
        client_factory = DestroyClient(args)

    if client_factory:
        client_factory.execute()


