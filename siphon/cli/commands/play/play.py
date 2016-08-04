
import sys

from clint.textui import colored, puts

from siphon.cli.commands.push import push

from siphon.cli.wrappers import Build, BaseConfig, BaseProject
from siphon.cli.wrappers import Auth, Cache, Config, Siphon

from siphon.cli.commands.play.device import IOSDevice
from siphon.cli.commands.play.device import SiphonDeviceException
from siphon.cli.utils.input import yn
from siphon.cli.utils.siphon import config_required
from siphon.cli.utils.system import cleanup_dir
from siphon.cli.constants import MIN_OSX_VERSION
from siphon.cli.utils.platform import get_platform_name, PLATFORM_DARWIN
from siphon.cli.utils.platform import osx_version_supported
from siphon.cli.dependencies.apple import ensure_xcode_dependencies
from siphon.cli.dependencies.apple import ensure_wwdr_cert
from siphon.cli.dependencies.base import ensure_base

from siphon.cli.utils.mixpanel import mixpanel_event, MIXPANEL_EVENT_PLAY

def print_usage():
    print('Usage: siphon play ' \
        '[--set-apple-username <username>] [--help]\n\nRun ' \
        'an app on your iOS developer device.')

@config_required
def clear_builds():
    """
    Wipe any build directories for the app.
    """
    proceed = yn('This operation will remove any builds for this app. ' \
                 'The app will need to be rebuilt to run it again. ' \
                 'Proceed? [Y/n]: ')
    if proceed:
        conf = Config()
        build = Build(conf.app_id, '')
        build.clean_builds()
    else:
        return

@config_required
def play(device, dev_mode=False, platform='ios'):
    """
    Takes a device object and runs an app
    """
    conf = Config()
    auth = Auth()
    siphon = Siphon(auth.auth_token)

    # Mixpanel tracking
    current_app_data = siphon.get_app(conf.app_id)
    mixpanel_props = {
        'app_id': conf.app_id,
        'app_name': current_app_data['name'],
    }
    mixpanel_event(MIXPANEL_EVENT_PLAY, properties=mixpanel_props)

    # The app needs to be built (archived) if:
    #
    #   1. An archive for this base version doesn't exist
    #   2. An archive exists and the display name has changed
    #   3. An archive exists and the facebook app id has changed
    #   4. An archive exists and the provisioning profile used to create it
    #      is not installed or is not compatible with the connected device.
    #      (device.profile_synchronised() is False.)
    #
    # After each build, we cache the build info and use it for future
    # reference. If build info is not stored for this app and base version,
    # we build the app anyway and cache the build info.

    # Push the app and fetch the updated settings if successful
    push(track_event=False)
    updated_app_data = siphon.get_app(conf.app_id)
    version = updated_app_data['base_version']

    # Create a Build instance for the app
    build = Build(conf.app_id, version, dev_mode)

    # Make sure the correct base version is installed and the build
    # directory exists
    ensure_base(version)
    build.ensure_build_dir()

    # The new display name defaults to the app name if it is not set
    display_name = updated_app_data.get('display_name')
    if not display_name:
        display_name = updated_app_data.get('name')

    facebook_app_id = updated_app_data.get('facebook_app_id')

    bundle_id = 'com.getsiphon.%s' % conf.app_id

    # Initialize a BaseConfig instance that will be used to configure
    # the base project we're archiving.
    base_conf = BaseConfig(display_name, bundle_id,
                           facebook_app_id=facebook_app_id)

    # Get the cached build info for the previous build
    cache = Cache()
    build_info_updated = cache.build_info_updated(build.build_id,
                                                display_name, facebook_app_id)

    # If the build info has been updated, we clear the old archives
    if build_info_updated:
        build.clean_archives()

    # If the provisioning profile needs updating, then we clear the archive
    # of the device build only. (The profile doesn't affect
    # other builds for the simulator).

    # Is the installed profile compatible with the connected device?
    profile_synchronised = device.profile_synchronised()
    if not profile_synchronised:
        build.clean_archive(device.formatted_name)
        # Sort out a new provisioning profile that includes the device
        device.update_requirements()

    # Was previous build performed with the installed profile? If we're
    # here then a compatible profile is installed.
    build_profile_ok = device.build_profile_ok(build.build_id)
    if not build_profile_ok:
        build.clean_archive(device.formatted_name)

    # If an archive doesn't exist at this point (perhaps it never existed,
    # or was deleted when invalidated above) we need to rebuild.
    if not build.archived(device.formatted_name):
        archive = True
    else:
        archive = False

    arch_dir = build.archive_dir_path(device.formatted_name)

    # Archiving takes a while, so prompt the user
    if archive:
        proceed = yn('A build is required for this app. ' \
                     'This step is needed if you haven\'t run this ' \
                     'app on the device before, ' \
                     'you have changed the name or base version, or ' \
                     'if an update has recently been performed. ' \
                     'This may take a few minutes. Proceed? ' \
                     '[Y/n]: ')
        if proceed:
            try:
                provisioning_profile = cache.get_provisioning_profile_id()
                base = BaseProject(build.project_dir(platform))

                with base.configure(base_conf):
                    app = device.archive(
                        base.directory,
                        arch_dir,
                        conf.app_id,
                        auth.auth_token,
                        provisioning_profile,
                        dev_mode
                    )

                # Update the cached build info
                cache.set_build_info(build.build_id, display_name,
                                     facebook_app_id)
                # Record the provisioning profile used to archive this app
                cache.set_build_profile(build.build_id, provisioning_profile)
            except SiphonDeviceException:
                cleanup_dir(arch_dir)
                sys.exit(1)
            except KeyboardInterrupt:
                puts(colored.red('\nArchiving interrupted'))
                cleanup_dir(arch_dir)
                sys.exit(1)
        else:
            sys.exit(1)
    else:
        app = device.app_path(arch_dir)

    device.run(app)

def run(args):
    # Check that we're on a mac
    if get_platform_name() != PLATFORM_DARWIN:
        print('You must run the Siphon client on OS X in order to use this ' \
              'feature. Please use our Sandbox app, which is available on ' \
              'the App Store.')
        return

    if not osx_version_supported():
        print('OS X %s or higher is required to run this command. Please ' \
              'visit the App Store and upgrade you operating system. '
              % MIN_OSX_VERSION)
        return

    # Make sure the required dependencies are installed
    ensure_xcode_dependencies()
    dev_mode = False

    if len(args) == 1 and args[0] == '--help':
        print_usage()
        return
    elif len(args) == 2 and args[0] == '--set-apple-username':
        cache = Cache()
        cache.set_apple_username(args[1])
        cache.clear_ios()
        return
    elif len(args) == 1 and args[0] == '--clear-builds':
        clear_builds()
        return
    elif len(args) == 1 and args[0] == '--dev':
        dev_mode = True
    elif args:
        print_usage()
        return

    if not dev_mode:
        puts(colored.yellow('## Run your app with dev mode enabled for ' \
            'more detailed logs and warning messages: siphon play --dev'))

    device = IOSDevice.get_device()
    if not device:
        puts(colored.red('No device detected. Please connect your ' \
        'device and try again.'))
        return
    cert_installed = ensure_wwdr_cert()
    if cert_installed:
        play(device, dev_mode)
