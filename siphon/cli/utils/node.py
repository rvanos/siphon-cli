
import json
import os
import re
import subprocess
from decimal import Decimal
from siphon.cli.constants import MIN_NODE_VERSION, NODE_DESTINATION

def node_version_valid():
    try:
        verbose = str(subprocess.check_output(['node', '-v'],
                                            stderr=subprocess.STDOUT))
        m = re.search('v(?P<version>[0-9]+.[0-9]+)', verbose)
        if not m:
            return False

        version = m.group('version')
        if Decimal(version) >= Decimal(MIN_NODE_VERSION):
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        return False

def node_cmd(version):
    """
    Returns the command that we must use to invoke node.
    """
    local_path = os.path.join(NODE_DESTINATION, version, 'bin/node')
    if os.path.isfile(local_path):
        return local_path
    return None

def npm_cmd(version):
    """
    Returns the command that we must use to invoke npm
    """
    local_path = os.path.join(NODE_DESTINATION, version, 'bin/npm')
    if os.path.isfile(local_path):
        return local_path
    return None

def node_module_version(module_path):
    """
    Takes the path to a node module and returns its version.
    """
    pkg = os.path.join(module_path, 'package.json')
    try:
        with open(pkg, 'r') as f:
            pkg_obj = json.load(f)
        return pkg_obj.get('version')
    except FileNotFoundError:
        return None
