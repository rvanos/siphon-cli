import re
import subprocess
import os

from decimal import Decimal
from siphon.cli.constants import MIN_XCODE_VERSION

def xcode_is_installed():
    try:
        subprocess.check_output(['which', 'xcodebuild'],
                                stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False

def command_line_tools_installed():
    try:
        subprocess.check_output(['xcode-select', '-p'],
                                stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False

def xcode_version_valid():
    try:
        verbose = str(subprocess.check_output(['xcodebuild', '-version'],
                                            stderr=subprocess.STDOUT))
        m = re.search('Xcode (?P<version>[0-9]+.[0-9]+)', verbose)
        if not m:
            return False

        version = m.group('version')
        if Decimal(version) >= Decimal(MIN_XCODE_VERSION):
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        return False

def provisioning_profile_installed(uuid):
    """
    Takes a provisioning profile uuid and determines whether it has been
    installed
    """
    home_dir = os.path.expanduser('~')
    profiles_path = os.path.join(home_dir,
                                 'Library/MobileDevice/Provisioning Profiles')
    installed_profiles = [f for f in os.listdir(profiles_path) \
                          if os.path.isfile(os.path.join(profiles_path, f))]
    installed = any(uuid in f for f in installed_profiles)
    return installed
