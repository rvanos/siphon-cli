
import os
import sys

from siphon.cli.commands.push import push
from siphon.cli.wrappers import Auth, UserConfig, Config, Siphon
from siphon.cli import SiphonCommandException
from siphon.cli.utils.siphon import config_required, login_required
from siphon.cli.utils.input import get_input, yn
from siphon.cli.utils.platform import get_platform_name, PLATFORM_DARWIN
from siphon.cli.utils.system import bash, copyfile, ensure_dir_exists
from siphon.cli.constants import CLI_RESOURCES

from siphon.cli.utils.mixpanel import mixpanel_event, MIXPANEL_EVENT_PUBLISH

from clint.textui import colored, puts

PLATFORM_IOS = 'ios'
PLATFORM_ANDROID = 'android'
ALLOWED_PLATFORMS = (PLATFORM_IOS, PLATFORM_ANDROID)

PUBLISH_DIR = 'publish'

def prompt_for_upgrade():
    pricing_url = 'https://getsiphon.com/pricing/'
    print('Sorry, publishing is a paid feature and it appears that you do ' \
        'not have a paid subscription yet. Please visit our pricing page ' \
        'to find out how to upgrade:\n\n==> %s' % pricing_url)
    if get_platform_name() == PLATFORM_DARWIN:
        msg = '\nWould you like to open the pricing page now and ' \
            'upgrade? [Y/n]: '
        try:
            if get_input(colored.green(msg)) in ('Y', 'y', ''):
                bash('open %s' % pricing_url)
        except KeyboardInterrupt:
            print()
    else:
        print('\nAfter upgrading, try running this command again to ' \
            'publish your app.')

def prompt_for_platform_info(platform):
    platform_username = None
    platform_password = None
    if platform == PLATFORM_IOS:
        puts(colored.yellow('We need some details so that we can build and '\
            'upload your app to iTunes Connect on your behalf:'))
        try:
            while not platform_username:
                platform_username = get_input('Please enter your Apple ID ' \
                    'for iTunes Connect: ')
            while not platform_password:
                platform_password = get_input('Enter your password for ' \
                    'iTunes Connect: ', password=True)
        except KeyboardInterrupt:
            print()
            sys.exit(0)
    elif platform == PLATFORM_ANDROID:
        puts(colored.yellow('We need some details so that we can build and '\
            'upload your app to the Google Developer Console on your behalf:'))
        try:
            while not platform_username:
                platform_username = get_input('Please enter your username ' \
                    'for Google Play: ')
            while not platform_password:
                platform_password = get_input('Enter your password for ' \
                    'Google Play: ', password=True)
        except KeyboardInterrupt:
            print()
            sys.exit(0)
    else:
        raise RuntimeError('Platform "%s" is not configured!')
    return platform_username, platform_password

def validate_platform(platform):
    if platform not in ALLOWED_PLATFORMS:
        raise SiphonCommandException('Platform "%s" is not supported, try ' \
            'one of these: %s' % (platform, ', '.join(ALLOWED_PLATFORMS)))

    platform_entry = 'index.%s.js' % platform
    dir_contents = os.listdir()
    entry_found = False
    for entry in ('index.js', platform_entry):
        if entry in dir_contents:
            entry_found = True

    if not entry_found:
        raise SiphonCommandException('Platform "%s" is not supported by ' \
            'your app. Please make sure you either have an %s or ' \
            'an %s file in your app directory.' % (platform, 'index.js',
                                                  platform_entry))

def prompt_for_hard_update(platform):
    if platform == PLATFORM_IOS:
        puts(colored.yellow('\nThis submission requires a new binary to ' \
            'be built and submitted to the App Store for approval by ' \
            'the Apple review team. The approval process typically ' \
            'takes 5-7 working days.'))
    elif platform == PLATFORM_ANDROID:
        puts(colored.yellow('\nThis submission requires a new Android ' \
            'package to be compiled and submitted to the Play Store.'))
    else:
        raise SiphonCommandException('Unknown platform: %s' % platform)
    while 1:
        try:
            result = get_input('Would you like to continue anyway? [y/n]: ')
            if result in ('Y', 'y'):
                return True
            elif result in ('n', 'N'):
                return False
        except KeyboardInterrupt:
            return False

def print_usage():
    print('Usage: siphon publish --platform <platform> [--help] [--validate]')
    print('\nAvailable platforms:\n--------------------\n%s'
        % ', '.join(ALLOWED_PLATFORMS))
    print('\nPublish your app to the App Store or Play Store. \n' \
          '\n--platform ios: your app will be uploaded to iTunes Connect ' \
          'for release on the App Store.\n' \
          '\n--platform android: your app will be uploaded to ' \
          'your Google Developer Console for release on the Play Store.\n\n' \
          'If this app is already published and live, ' \
          'running this command again ' \
          'updates your app with any new changes you have pushed.\n\n' \
          '[--validate]: include this additional flag to check that ' \
          'you have provided all the information required for us ' \
          'to upload your app. If this flag is used without specifying ' \
          'a platform validation will take place for both platforms.\n\n')

def ensure_publish_dir():
    # Make sure that a publish directory exists. If it does not, ask the
    # user if they would like to create one. After running the function
    # we should exit - we don't want to proceed with a publish if the
    # icons are dummy ones
    dir_exists = os.path.exists(PUBLISH_DIR)
    if not dir_exists:
        proceed = yn('A \'publish\' directory does not exist for this app. ' \
        'This folder will contain the icons for your app and is required ' \
        'for publishing. Would you like to create one now? [Y/n]: ')
        if not proceed:
            sys.exit(1)

        # Copy the icons over from our resources dir
        for platform in ALLOWED_PLATFORMS:
            icon_dir = os.path.join(PUBLISH_DIR, platform, 'icons')
            ensure_dir_exists(icon_dir)
            icon = os.path.join(CLI_RESOURCES, 'icons', platform, 'index.png')
            icon_dest = os.path.join(icon_dir, 'index.png')
            copyfile(icon, icon_dest)

        puts(colored.yellow('A \'publish\' directory has been created. ' \
            'This contains placeholder icons for your app. Please make ' \
            'sure you replace these with your own icons.'))
        sys.exit(0)

def ensure_platform_keys():
    # Ensure that there are skeleton ios and android keys in the Siphonfile
    siphonfile = UserConfig()
    if not siphonfile.get('ios'):
        siphonfile.set('ios', {'store_name': '', 'language': 'en'})
    if not siphonfile.get('android'):
        siphonfile.set('android', {'store_name': '', 'language': 'en-US'})

@login_required
@config_required
def validate_app(platforms):
    push_successful = push(track_event=False)
    if not push_successful:
        # The push failed, so no point in validating the app
        sys.exit(1)

    # Ensure that a publish directory exists
    ensure_publish_dir()
    ensure_platform_keys()

    # Load the app config and wrapper
    auth = Auth()
    conf = Config()
    siphon = Siphon(auth.auth_token)

    # Send a request to out validation endpoint to make sure we
    # have the required details
    for p in platforms:
        if p == 'ios':
            formatted_platform = 'iOS'
        else:
            formatted_platform = 'Android'

        puts(colored.yellow('Validating your app for %s publishing...' % \
            formatted_platform))
        status = siphon.validate_app(conf.app_id, p)
        if status == 'ok':
            puts(colored.green('OK.'))
        else:
            return False
    return True

@login_required
@config_required
def publish(platform):
    # Ensure that a publish directory exists
    ensure_publish_dir()
    ensure_platform_keys()

    # Load the app config and wrapper
    auth = Auth()
    conf = Config()
    siphon = Siphon(auth.auth_token)

    mixpanel_props = {
        'upgrade_required': False,
        'platform': platform
    }

    # We first check that the user has a valid subscription, because we're
    # going to do an implicit push before submitting, and it would otherwise
    # be confusing.
    puts(colored.yellow('Checking your account...'))
    if not siphon.user_can_publish():
        mixpanel_props['upgrade_required'] = True
        mixpanel_event(MIXPANEL_EVENT_PUBLISH, properties=mixpanel_props)
        prompt_for_upgrade()
        sys.exit(1)
    else:
        puts(colored.green('Your account is ready for publishing.'))

    mixpanel_event(MIXPANEL_EVENT_PUBLISH, properties=mixpanel_props)
    # It looks like the user can publish, so we do an implicit push
    # and validate the app.
    app_valid = validate_app([platform])
    if not app_valid:
        # The last push before publishing should be a successful one
        sys.exit(1)

    # Check if this submission requires a hard update, and if so then
    # prompt the user before going ahead with the submit so they understand.
    hard_update = siphon.app_requires_hard_update(conf.app_id, platform)
    if hard_update:
        if not prompt_for_hard_update(platform):
            return
    else:
        puts(colored.green('This update can be published without changing ' \
            'the app binary. It will be available straight away.'))

    # Prompt for platform info and do the actual submission
    user, password = None, None
    if hard_update:
        user, password = prompt_for_platform_info(platform)

    if hard_update:
        if not yn('Your app is about to be processed and submitted to the ' \
        'store. Are you sure you want to continue? [Y/n]: '):
            sys.exit(0)
    else:
        if not yn('Your app update is about to be submitted and the users ' \
        'of your app will receive it as an over-the-air update. Are you ' \
        'sure you want to continue? [Y/n]: '):
            sys.exit(0)

    puts(colored.yellow('Submitting...'))
    siphon.submit(conf.app_id, platform, username=user, password=password)

    puts(colored.green('\nThanks! Your app is in the queue. We will send ' \
        'status updates to your registered email address.'))
    print('Please note that after this submission has been released, you ' \
        'can push instant updates to your users by running the ' \
        '"siphon publish" command again.')

def run(args):
    # Validate the arguments
    if args is None:
        args = []

    validate = False
    try:
        args.pop(args.index('--validate'))
        validate = True
    except ValueError:
        pass

    if '--help' in args:
        print_usage()
    elif len(args) == 0 and validate:
        validate_app(list(ALLOWED_PLATFORMS))
    elif len(args) == 2 and args[0] == '--platform':
        platform = args[1]
        validate_platform(platform)
        if not validate:
            publish(platform)
        else:
            validate_app([platform])
    else:
        print_usage()
