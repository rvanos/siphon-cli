import os

from siphon.cli.constants import CLI_DIR
from siphon.cli.utils.platform import get_platform_name, PLATFORM_DARWIN

# Note that the client watchman directory may only be used for installs
# located at /usr/local/siphon-cli
def local_watchman_dir():
    if os.environ.get('LOCAL_WATCHMAN') or \
            '/usr/local/siphon-cli' not in os.path.dirname(__file__):
        watchman_dir = None
    elif get_platform_name() == PLATFORM_DARWIN:
        watchman_dir = os.path.join(CLI_DIR, 'watchman', 'osx-64')
    else:
        watchman_dir = None
    return watchman_dir
