import os

INSTALLER_FILE = 'install.sh'
SOURCE_FILE = 'siphon-cli.tar.gz'
CLI_DIR = os.path.dirname(os.path.abspath(__file__))  # root of siphon-cli/
TEMPLATES_DIR = os.path.join(CLI_DIR, 'installer-templates')
PYRUN_BINARIES_DIR = os.path.join(CLI_DIR, 'pyrun-binaries')

# For generating the source archive
INCLUDE_ROOT_FILES = ('siphon-cli.py')
INCLUDE_ROOTS = ('app-template', 'siphon', 'packager-resources', 'resources')
IGNORE_EXTENSIONS = ('.pyc', '.DS_Store', '.siphon')

REPOS = {
    'xctool': {
        'repo': 'https://github.com/facebook/xctool.git',
        'repo_name': 'xctool',
        'commit': 'fdd74e0',
        'files': ('xctool.sh',),
        'directories': (
            'scripts',
            'xctool.xcworkspace',
            'xctool',
            'xcodebuild-shim',
            'Configurations',
            'Common',
            'reporters',
        ),
        'root': 'xctool'
    },
    'fastlane': {
        'repo': 'https://github.com/fastlane/fastlane',
        'repo_name': 'fastlane',
        'commit': '2cdbfd6',
        'files': [],
        'directories': (
            'credentials_manager/lib',
            'fastlane_core/lib',
            'spaceship/lib'
        ),
        'root': 'fastlane/fastlane',
    },
    'multi_xml': {
        'repo': 'https://github.com/sferik/multi_xml',
        'repo_name': 'multi_xml',
        'commit': '60f9773',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/multi_xml'
    },
    'plist': {
        'repo': 'https://github.com/bleything/plist',
        'repo_name': 'plist',
        'commit': '666a785',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/plist'
    },
    'faraday': {
        'repo': 'https://github.com/lostisland/faraday',
        'repo_name': 'faraday',
        'commit': '80c0e66',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/faraday'
    },
    'faraday_middleware': {
        'repo': 'https://github.com/lostisland/faraday_middleware',
        'repo_name': 'faraday_middleware',
        'commit': 'c5836ae',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/faraday_middleware'
    },
    'faraday-cookie_jar': {
        'repo': 'https://github.com/miyagawa/faraday-cookie_jar',
        'repo_name': 'faraday-cookie_jar',
        'commit': '7e6ee6a',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/faraday-cookie_jar'
    },
    'http-cookie': {
        'repo': 'https://github.com/sparklemotion/http-cookie',
        'repo_name': 'http-cookie',
        'commit': '405a48b',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/http-cookie',
    },
    'unf': {
        'repo': 'https://github.com/knu/ruby-unf',
        'repo_name': 'ruby-unf',
        'commit': '571395d',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/ruby-unf'
    },
    'domain_name': {
        'repo': 'https://github.com/knu/ruby-domain_name',
        'repo_name': 'ruby-domain_name',
        'commit': 'a804f1c',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/ruby-domain_name'
    },
    'colored': {
        'repo': 'https://github.com/defunkt/colored',
        'repo_name': 'colored',
        'commit': '829bde0',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/colored'
    },
    'fastimage': {
        'repo': 'https://github.com/sdsykes/fastimage',
        'repo_name': 'fastimage',
        'commit': '9c7ada1',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/fastimage'
    },
    'addressable': {
        'repo': 'https://github.com/sporkmonger/addressable',
        'repo_name': 'addressable',
        'commit': '295d7ba',
        'files': [],
        'directories': ('lib', 'data', 'spec'),
        'root': 'fastlane/dependencies/addressable'
    },
    # fastlane_core dependencies
    'json': {
        'repo': 'https://github.com/flori/json',
        'repo_name': 'json',
        'commit': '7082732',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/json'
    },
    'highline': {
        'repo': 'https://github.com/JEG2/highline',
        'repo_name': 'highline',
        'commit': '60d8eb0',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/highline'
    },
    'multi_json': {
        'repo': 'https://github.com/intridea/multi_json',
        'repo_name': 'multi_json',
        'commit': '1ba3be4',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/multi_json'
    },
    'commander': {
        'repo': 'https://github.com/commander-rb/commander',
        'repo_name': 'commander',
        'commit': 'b253670',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/commander'
    },
    'babosa': {
        'repo': 'https://github.com/norman/babosa',
        'repo_name': 'babosa',
        'commit': 'b5204d8',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/babosa'
    },
    'excon': {
        'repo': 'https://github.com/excon/excon',
        'repo_name': 'excon',
        'commit': '878e0bb',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/excon'
    },
    'rubyzip': {
        'repo': 'https://github.com/rubyzip/rubyzip',
        'repo_name': 'rubyzip',
        'commit': '3ec40d8',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/rubyzip'
    },
    'terminal-table': {
        'repo': 'https://github.com/tj/terminal-table',
        'repo_name': 'terminal-table',
        'commit': '87556a7',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/terminal-table'
    },
    'sentry-raven': {
        'repo': 'https://github.com/getsentry/raven-ruby',
        'repo_name': 'raven-ruby',
        'commit': '310309e',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/sentry-raven'
    },
    'multipart-post': {
        'repo': 'https://github.com/nicksieger/multipart-post',
        'repo_name': 'multipart-post',
        'commit': '5080876',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/multipart-post'
    },
    'security': {
        'repo': 'https://github.com/mattt/security',
        'repo_name': 'security',
        'commit': 'ceb3c7c',
        'files': [],
        'directories': ('lib',),
        'root': 'fastlane/dependencies/security',
    }
}

# Set the directories that the repos should live in when run locally (these
# are relative to $TMPDIR)
FASTLANE_COMMIT_SUM = sum(int(REPOS[k]['commit'], 16) for k in REPOS)

def generate_local_roots():
    local_roots = {}
    for k, v in REPOS.items():
        if k == 'xctool':
            local_roots[k] = 'siphon-xctool-%s' % v['commit']
        else:
            ext = v['root'].replace('fastlane/', '')
            root = 'siphon-fastlane-%x/%s' % (FASTLANE_COMMIT_SUM, ext)
            local_roots[k] = root
    return local_roots

LOCAL_ROOTS = generate_local_roots()
LOCAL_FASTLANE = 'siphon-fastlane-%x' % FASTLANE_COMMIT_SUM
