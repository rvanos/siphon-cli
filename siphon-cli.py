
import sys
import os
import importlib

from clint.textui import colored, puts

from siphon.cli.wrappers.cache import Cache
from siphon.cli.utils.updates import get_remote_source_length, \
    check_for_updates
from siphon.cli import SiphonAPIException, SiphonCommandException, \
    SiphonBundlerException

def dispatch(command, args):
    try:
        module = importlib.import_module('siphon.cli.commands.%s' % command)
        module.run(args)
    except ImportError:
        if os.environ.get('SP_LOCAL_CLI'):
            raise
        else:
            print_usage()

def print_usage():
    s = 'Usage: siphon COMMAND [command-options]\n\nList of commands:\n\n'
    s += '  create   # create a new Siphon app\n'
    s += '  push     # push an app\'s latest changes (updates simulator' \
        '/device/sandbox)\n'
    s += '  play     # run an app on your developer device\n'
    s += '  develop  # run an app locally in the simulator (installs/runs ' \
        'the packager)\n'
    s += '  logs     # stream the console logs from your app (simulator' \
        '/device/sandbox)\n'
    s += '  ls       # list all of your apps\n'
    s += '  publish  # publish your app to the stores (or update an ' \
        'existing live app)\n'
    s += '  share    # share your app with a beta tester or team member\n'
    s += '  login    # set the current Siphon user\n'
    s += '  update   # update this command-line tool to the latest version\n'
    print(s)

def print_version():
    version = 'dev'
    try:
        import siphon_config
        version = siphon_config.VERSION
    except (ImportError, AttributeError):
        pass
    print('siphon-cli %s' % version)

def init_installation():
    """
    This is called when `siphon --init` is run. We use it to set the current
    Content-Length of the remote installation archive (siphon-cli.tar.gz)
    in the cache so that we can use it to check for updates going forward.
    """
    # Cache the current Content-Length.
    length = get_remote_source_length()
    Cache.set_installation_length(length)

def setup_env():
    try:
        import siphon_config
        os.environ['SP_HOST'] = siphon_config.HOST
        os.environ['SP_PORT'] = siphon_config.PORT
        os.environ['SP_STATIC_HOST'] = siphon_config.STATIC_HOST
        os.environ['SP_STATIC_PORT'] = siphon_config.STATIC_PORT
        os.environ['SP_REMOTE_SOURCE'] = siphon_config.REMOTE_SOURCE
    except ImportError:
        pass
    for k in ('SP_HOST', 'SP_REMOTE_SOURCE'):
        if k not in os.environ:
            puts(colored.red('%s environment variable is not set.' % k))
            sys.exit(1)

if __name__ == '__main__':
    if '--init-installation' in sys.argv:
        setup_env()
        init_installation()
    elif '--version' in sys.argv or '-v' in sys.argv:
        print_version()
    elif len(sys.argv) < 2:
        print_usage()
    else:
        setup_env()
        command = sys.argv[1]
        args = sys.argv[2:]
        if command != 'update':
            check_for_updates()
        try:
            dispatch(command, args)
        except SiphonCommandException as e:
            puts(colored.red('Error: %s' % e))
        except (SiphonAPIException, SiphonBundlerException) as e:
            puts(colored.red('Error calling the Siphon API: %s' % e))
