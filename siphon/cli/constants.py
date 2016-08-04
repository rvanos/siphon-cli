
import os

from decimal import Decimal

DEVELOP_BASE_VERSIONS = [
    Decimal('0.3'),
    Decimal('0.4'),
    Decimal('0.5')
]

SIPHON_CONFIG = '.siphon'
SIPHON_USER_CONFIG = 'Siphonfile'
CLI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

CLI_RESOURCES = os.path.join(CLI_DIR, 'resources')
PACKAGER_RESOURCES = os.path.join(CLI_DIR, 'packager-resources')
XCTOOL_DIR = os.path.join(CLI_DIR, 'xctool')
XCTOOL_PATH = os.environ.get('XCTOOL_PATH',
    os.path.join(XCTOOL_DIR, 'xctool.sh'))
XCODE_PROJECT_WORKSPACE = 'SiphonBase.xcworkspace'
XCODE_PROJECT_SCHEME = 'SiphonBase'
XCODE_PRODUCT_NAME = 'SiphonBase'
XCODE_BUNDLE_IDENTIFIER = 'com.getsiphon.SiphonBase'

HOME_DIR = os.path.expanduser('~')
SIPHON_USER_DIR = os.path.join(HOME_DIR, '.siphon')
SIPHON_TMP = os.path.join(SIPHON_USER_DIR, 'tmp')

SIPHON_IGNORE = '.siphonignore'

NODE_BINARIES = {
    '0.3': {
        'darwin-64': {
            'url': 'https://nodejs.org/download/release/v4.2.1/node-v4.2.1' \
            '-darwin-x64.tar.gz',
            'content': 'node-v4.2.1-darwin-x64'
        }
    },
    '0.4': {
        'darwin-64': {
            'url': 'https://nodejs.org/dist/v4.4.3/node-v4.4.3-darwin' \
            '-x64.tar.gz',
            'content': 'node-v4.4.3-darwin-x64'
        }
    },
    '0.5': {
        'darwin-64': {
            'url': 'https://nodejs.org/dist/v4.4.3/node-v4.4.3-darwin' \
            '-x64.tar.gz',
            'content': 'node-v4.4.3-darwin-x64'
        }
    }
}

NODE_DESTINATION = os.path.join(SIPHON_TMP, 'node')

PACKAGER_HOST = 'localhost'
PACKAGER_PORT = '8081'

IOS_DEPLOY = os.environ.get('IOS_DEPLOY_PATH',
    os.path.join(CLI_DIR, 'ios-deploy'))

IGNORE_PATHS = (
    '.git',
    '.gitignore',
    '.siphon',
    '.DS_Store',
    '*.swp',
    'node_modules/react-native',
)

MIN_XCODE_VERSION = '7.2'
MIN_NODE_VERSION = '4.2'
MIN_NVM_VERSION = '0.28'
MIN_OSX_VERSION = '10.10.5'
