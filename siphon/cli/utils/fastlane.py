import subprocess
import sys
import os

from siphon.cli.constants import CLI_DIR
from siphon.cli import SiphonClientException

from clint.textui import colored, puts

def siphon_fastlane(username, udid):
    try:
        siphon_fl = os.path.join(CLI_DIR,
                                 'siphon/cli/fastlane/bin/siphon-fastlane')
        env = dict(os.environ)
        if not env.get('FASTLANE_DIR'):
            env['FASTLANE_DIR'] = os.path.join(CLI_DIR, 'fastlane')
        subprocess.check_call(['ruby', siphon_fl, '--username',
                         username, '--udid', udid], env=env)
    except subprocess.CalledProcessError as e:
        output = e.output.decode()
        if 'Your account is in no teams' in output:
            puts(colored.red(
                'A problem occurred. Please check that your Apple Developer ' \
                'subscription has not expired.'
            ))
            sys.exit(1)
        else:
            puts(colored.red(output))
            sys.exit(1)
