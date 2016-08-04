
import sys
import os
import time

import requests
from clint.textui import colored, puts

from siphon.cli.utils.system import bash
from siphon.cli.utils.input import get_input
from siphon.cli.wrappers.cache import Cache


def get_remote_source_length():
    url = os.environ.get('SP_REMOTE_SOURCE')
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
    except requests.exceptions.RequestException as e:
        puts(colored.red('[HEAD] %s' % url))
        puts(colored.red('Failed to get remote installation size: %s' % e))
        sys.exit(1)
    size = response.headers.get('content-length')
    if not size:
        size = response.headers.get('Content-Length')
    if not size or not size.isdigit():
        puts(colored.red('Could not fetch the remote Content-Length.'))
        sys.exit(1)
    try:
        size = int(size)
    except ValueError:
        pass
    return size

def check_for_updates(force=False):
    # Don't check for updates in local dev mode.
    if os.environ.get('SP_LOCAL_CLI'):
        if force is True:
            print('[dev mode, skipping]')
        return

    # Skip this check if less than 24-hours has passed since the last check.
    if force is False:
        timestamp = Cache.get_update_check_timestamp()
        now = int(time.time())
        threshold = 3600 * 48
        if timestamp and timestamp > (now - threshold):
            return  # already checked for an update recently, so skip this one

    # If we got this far we'll check for an update.
    puts(colored.yellow('Checking for updates...'))
    if get_remote_source_length() != Cache.get_installation_length():
        # Length mis-match, we need to do an update
        msg = 'There is an update available for the Siphon command-line ' \
            'tools. Would you like to install it now? [y/N]: '
        try:
            resp = get_input(colored.green(msg))
            if resp in ('y', 'Y'):
                puts(colored.yellow('Updating your local installation of ' \
                    'the Siphon command-line tools...\n'))
                url = 'https://%s/install.sh' % os.environ['SP_HOST']
                bash('curl %s | sh' % url)
        except KeyboardInterrupt:
            pass
    elif force is True:
        puts(colored.green('You are fully up-to-date.'))

    # Bump the timestamp so that we don't check again for 24-hours.
    Cache.set_update_check_timestamp()
