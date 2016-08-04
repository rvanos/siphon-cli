import sys
import subprocess

from siphon.cli.constants import MIN_OSX_VERSION

PLATFORM_WINDOWS = 'windows'
PLATFORM_LINUX = 'linux'
PLATFORM_BSD = 'bsd'
PLATFORM_DARWIN = 'darwin'
PLATFORM_UNKNOWN = 'unknown'

def get_platform_name():
    if sys.platform.startswith("win"):
        return PLATFORM_WINDOWS
    elif sys.platform.startswith('darwin'):
        return PLATFORM_DARWIN
    elif sys.platform.startswith('linux'):
        return PLATFORM_LINUX
    elif sys.platform.startswith('bsd'):
        return PLATFORM_BSD
    else:
        return PLATFORM_UNKNOWN

def version_supported(version, min_version):
    """
    Takes version numbers consisting of a string of ints separated by periods
    and returns True if the first one is higher than the second (False
    otherwise).
    """
    v1_nums = [int(x) for x in version.split('.')]
    v2_nums = [int(x) for x in min_version.split('.')]
    # The highest one is the one with the highest left-most character
    for i in range(len(v1_nums)):
        n1 = v1_nums[i]
        n2 = v2_nums[i]
        if n1 == n2:
            continue
        elif n1 > n2:
            return True
        else:
            return False
    # We have compared all the numbers and they are identical
    return True


def osx_version():
    """ Returns the version of osx that the user is running """
    version = subprocess.check_output(['sw_vers', '-productVersion']).decode()
    return version

def osx_version_supported():
    current_version = osx_version()
    return version_supported(current_version, MIN_OSX_VERSION)
