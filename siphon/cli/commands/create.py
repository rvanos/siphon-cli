
import os
import re
import shutil
import sys
import json

from clint.textui import colored, puts

from siphon.cli import SiphonCommandException
from siphon.cli.wrappers import Auth, Config, Siphon
from siphon.cli.utils.input import get_input
from siphon.cli.utils.node import node_module_version
from siphon.cli.utils.siphon import entry_file_required, login_required
from siphon.cli.utils.system import cd
from siphon.cli.constants import SIPHON_CONFIG, SIPHON_USER_CONFIG
from siphon.cli.constants import CLI_RESOURCES

from siphon.cli.utils.mixpanel import mixpanel_event, MIXPANEL_EVENT_CREATE

def print_usage():
    print('Usage: siphon create [app-name]\n\nCreates a new Siphon app and ' \
        'pushes the new files to our servers. Provide the [app-name] if you ' \
        'are starting from scratch. This will create a new Siphon app in ' \
        'a directory with the same name.\n\nIf you wish to convert an ' \
        'existing React Native project into ' \
        'a Siphon app, run \'siphon create\' in the app directory.')

def app_name_valid(app_name):
    if not re.match(r'[\w\-_]+$', app_name):
        return False
    else:
        return True

def copy_app_template(app_name, to_path):
    path = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(path, '../../../app-template/')
    ignore_func = shutil.ignore_patterns('.DS_Store', 'Thumbs.db')
    shutil.copytree(source_dir, to_path, ignore=ignore_func)

    # Replace the app name placeholder
    index_path = os.path.join(to_path, 'index.js')
    s = open(index_path, 'r').read().replace('{{app_name}}', app_name)
    with open(index_path, 'w') as fp:
        fp.write(s)

def print_app_registry_message(entry):
    with open(entry, 'r') as f:
        s = f.read()
    m = re.search('AppRegistry.registerComponent\([\'\"](?P<name>\w*?)' \
        '[\'\"],\s*?\(\)\s*?=>\s*?\w*?\s*?\)', s)
    if not m:
        return
    replacement = re.sub('AppRegistry.registerComponent\(\'(?P<name>\w*?)\'',
        'AppRegistry.registerComponent(\'App\'', m.group(0))
    puts(colored.yellow('[%s] Please replace "%s" with "%s"' % (
        entry, m.group(0), replacement)))

@entry_file_required(print_usage)
@login_required
def init():
    auth = Auth()
    # Create the app server-side
    siphon = Siphon(auth.auth_token)
    print('Please enter a name for your Siphon app.')

    try:
        name_valid = False
        while not name_valid:
            app_name = get_input('App name: ')
            name_valid = app_name_valid(app_name)
            if not name_valid:
                print('Siphon app names may only contain letters, numbers, ' \
                      'underscores and hyphens.')
    except KeyboardInterrupt:
        sys.exit(1)

    obj = siphon.create(app_name)
    app_id = obj['id']  # server gives us back our internal app ID

    # Write out a .siphon configuration to the new directory
    conf = Config()
    conf.app_id = app_id

    # Copy our .siphonignore file over
    siphon_ignore = os.path.join(CLI_RESOURCES, '.siphonignore')
    shutil.copyfile(siphon_ignore, '.siphonignore')

    puts(colored.green('Siphon app created.'))

    # Register Mixpanel event
    username = auth.username
    mixpanel_event(MIXPANEL_EVENT_CREATE, username, {'app_id': app_id,
                                                     'existing_app': True})

    # Write out the Siphonfile
    with open(SIPHON_USER_CONFIG, 'w') as fp:
        json.dump({'base_version': obj['base_version']}, fp, indent=2)

    # Implicitly do a push too
    from siphon.cli.commands.push import push
    push(track_event=False)
    puts(colored.green('Done.'))

    # Print warning about mismatched React Native versions
    project_rn_version = node_module_version('node_modules/react-native')
    siphon_rn_version = obj['react_native_version']
    if project_rn_version != siphon_rn_version:
        puts(colored.yellow('Note: Siphon app is using React Native %s but ' \
            'existing project is using React Native %s.\n'\
            'Please visit https://getsiphon.com/docs/base-version/ to learn ' \
            'more about base versions.\n' %
                            (siphon_rn_version, project_rn_version)))

    if os.path.isfile('index.js'):
        print('You must register your component with the name \'App\'' \
              'in your index.js file to use Siphon.\n')
        if os.path.isfile('index.js'):
            print_app_registry_message('index.js')
    else:
        print('You must register your component with the name \'App\'' \
              'in your index.ios.js and index.android.js files ' \
              ' to use Siphon.\n')
        if os.path.isfile('index.ios.js'):
            print_app_registry_message('index.ios.js')
        if os.path.isfile('index.android.js'):
            print_app_registry_message('index.android.js')

@login_required
def create(app_name, app_path):
    auth = Auth()

    # Create the app server-side
    siphon = Siphon(auth.auth_token)
    obj = siphon.create(app_name)
    app_id = obj['id']  # server gives us back our internal app ID

    # Populate our new directory with template files
    copy_app_template(app_name, app_path)

    # Write out a .siphon configuration to the new direcotry
    conf = Config(directory=app_name)
    conf.app_id = app_id

    # Copy our .siphonignore file over
    siphon_ignore = os.path.join(CLI_RESOURCES, '.siphonignore')
    shutil.copyfile(siphon_ignore, os.path.join(app_path, '.siphonignore'))
    puts(colored.green('Siphon app created at %s' % app_path))

    # Register Mixpanel event
    username = auth.username
    mixpanel_event(MIXPANEL_EVENT_CREATE, username, {'app_id': app_id,
                                                     'existing_app': False})

    # Write out the Siphonfile
    with open(os.path.join(app_name, SIPHON_USER_CONFIG), 'w') as fp:
        json.dump({'base_version': obj['base_version']}, fp, indent=2)

    # Implicitly do a push too
    with cd(app_path):
        from siphon.cli.commands.push import push
        push(track_event=False)
    puts(colored.green('Done.'))

def run(args):
    # Validate the arguments
    app_name = None
    if args is None:
        args = []
    if len(args) == 1:
        app_name = args[0]
    if '--help' in args or len(args) > 1:
        print_usage()
        return

    # Ensure the app name doesn't contain any bad characters, as we're going
    # to create a directory with this name.
    if app_name and not app_name_valid(app_name):
        raise SiphonCommandException(
            'Siphon app names may only contain letters, numbers, ' \
            'underscores and hyphens.'
        )

    if Config(directory='.').exists():
        raise SiphonCommandException(
            'This directory already contains a %s configuration file. ' \
            'Creating a new Siphon app here is not supported.' % SIPHON_CONFIG
        )

    # If an app name has been provided we create a new app an 'AppName'
    # directory. If we are not given one, we try to initialize one in the
    # current directory (there must be an entry file in this directory)
    if app_name:
        app_path = os.path.abspath(app_name)
        if os.path.isdir(app_name):
            raise SiphonCommandException('The directory %s already exists.' %
                                         app_path)
        create(app_name, app_path)
    else:
        init()
