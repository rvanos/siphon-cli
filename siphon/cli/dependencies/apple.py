import subprocess
import sys
import time

from siphon.cli.utils.xcode import command_line_tools_installed
from siphon.cli.utils.xcode import xcode_is_installed, xcode_version_valid
from siphon.cli.utils.input import yn
from siphon.cli.utils.certificate import valid_wwdr_cert_installed
from siphon.cli.utils.certificate import add_wwdr_cert

from siphon.cli.constants import MIN_XCODE_VERSION
from clint.textui import colored, puts

def open_mac_app_store():
    subprocess.call([
        'open',
        'macappstores://itunes.apple.com/gb/app/xcode/id497799835'
    ])

def wait_for_tools_install():
    try:
        installed = False
        while not installed:
            installed = command_line_tools_installed()
            time.sleep(2)
    except KeyboardInterrupt:
        sys.exit(1)

def ensure_xcode_dependencies():
    """
    Ensure that a valid version of Xcode and command line tools are installed.
    """
    msg_intro = 'Running your app in the simulator or on a developer device ' \
                'requires Xcode to be installed on your machine (version ' \
                '%s or higher).' % MIN_XCODE_VERSION

    install_instruct = 'We couldn\'t find an installation, would you like ' \
                       'to open the Mac App Store and install it now? [Y/n]: '

    upgrade_instruct = 'You must upgrade your version of Xcode. Would you ' \
                       'like to open the Mac App Store and install it now?' \
                       ' [Y/n]: '

    if not command_line_tools_installed():
        install_tools = yn('We need to install the Xcode command line tools. ' \
                           'Continue? [Y/n]: ')
        if install_tools:
            subprocess.call(['xcode-select', '--install'])
            wait_for_tools_install()
        else:
            sys.exit(1)

    # Check if xcode build is installed
    if not xcode_is_installed():
        if yn('%s %s' % (msg_intro, install_instruct)):
            open_mac_app_store()
        sys.exit(1)

    if not xcode_version_valid():
        if yn('%s %s' % (msg_intro, upgrade_instruct)):
            open_mac_app_store()
        sys.exit(1)

def ensure_wwdr_cert():
    valid_cert_installed = valid_wwdr_cert_installed()
    if not valid_cert_installed:
        puts(colored.red('No valid WWDR certificate detected.'))
        proceed = yn('We need to download and install a new one '  \
          'in your keychain ' \
          '(See https://developer.apple.com/support/certificates/expiration/ ' \
          'for more details).\n'
          'Proceed? [Y/n]: ')
        if proceed:
            try:
                print('Downloading and installing new certificate...')
                add_wwdr_cert()
                print('Certificate installed successfully')
                return True
            except KeyboardInterrupt:
                return False
    else:
        return True
