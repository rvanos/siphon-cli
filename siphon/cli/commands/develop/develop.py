
import os
import re
import sys
from decimal import Decimal
from siphon.cli.utils.siphon import config_required
from siphon.cli.constants import DEVELOP_BASE_VERSIONS, MIN_OSX_VERSION
from siphon.cli.utils.platform import get_platform_name, PLATFORM_DARWIN
from siphon.cli.utils.platform import osx_version_supported
from siphon.cli.dependencies.apple import ensure_xcode_dependencies
from siphon.cli.dependencies.node import ensure_node
from siphon.cli.dependencies.base import ensure_base
from siphon.cli.commands.develop.sim import IOSSimulatorData
from siphon.cli.commands.develop.sim import SiphonSimulatorException
from siphon.cli.utils.input import get_input, yn
from siphon.cli.utils.system import cleanup_dir
from siphon.cli.wrappers import Build, Config, DevelopDir, UserConfig
from siphon.cli.wrappers import BaseConfig, BaseProject, Cache

from siphon.cli.utils.mixpanel import mixpanel_event, MIXPANEL_EVENT_DEVELOP

from clint.textui import colored, puts

def print_usage():
    print('Usage: siphon develop [--simulator <sim-name>] [--list-sims] ' \
        '[--help]\n\nRuns the React Native packager on your local machine ' \
        'and spins up an iOS simulator to run your app.')

def print_sims():
    ensure_xcode_dependencies()
    ios_sim_data = IOSSimulatorData()
    latest_platform_version = ios_sim_data.latest_platform_version()
    ios_sim_list = ios_sim_data.sim_list(latest_platform_version)
    print('Available simulator devices (iOS %s):' % latest_platform_version)
    default = ios_sim_data.default_sim()
    for s in ios_sim_list:
        if s.formatted_name == default.formatted_name:
            puts(colored.green('%s (default)' % s.formatted_name))
        else:
            print(s.formatted_name)

def log_filter(line):
    """
    If returns True if the log should be shown to the user
    """
    blacklist = [
        '(.*?backboardd).*?(SecTaskCopyDebugDescription)*?',
        '(.*?accountsd).*?(SecTaskCopyDebugDescription)*?',
        '(.*?webinspectord).*?(SecTaskCopyDebugDescription)*?',
        '(.*?: The regenerator/runtime module is deprecated; please import ' \
        'regenerator-runtime/runtime instead.)',
        '(.*?: Accelerometer not Available!)',
        '(.*?: Magnetometer not Available!)',
        '(.*?: Gyroscope not Available!)',
        '(.*?: JSC profiler is not supported.)',
        '(.*?: Accelerometer)',
        '(.*?: Magnetometer)',
        '(.*?: Gyroscope)',
        '(.*?CoreSimulatorBridge.*?)',
        '(.*?: assertion failed: *?)'
    ]
    black_listed = any(re.match(pattern, line) for pattern in blacklist)
    if black_listed or 'SiphonBase' not in line:
        return False
    else:
        return True

def archive(sim, arch_dir, project_dir):
    """
    Handle archiving in a user-friendly way
    """
    proceed = yn('A build is required for this app. ' \
                 'This step is needed if you haven\'t run this ' \
                 'app on this particular simulator before, ' \
                 'you have changed the name or base version, or ' \
                 'if an update has recently been performed. ' \
                 'This may take a few minutes. Proceed? ' \
                 '[Y/n]: ')
    if proceed:
        try:
            app = sim.archive(project_dir, arch_dir)
            return app
        except SiphonSimulatorException:
            cleanup_dir(arch_dir)
            sys.exit(1)
        except KeyboardInterrupt:
            puts(colored.red('\nArchiving interrupted'))
            cleanup_dir(arch_dir)
            sys.exit(1)
    else:
        sys.exit(1)

def start_processes(dev_dir, sim, app, bundle_id, global_watchman=False):
    # We need to coordinate the loading of the packager, booting of
    # the simulator and streaming the simulator logs
    puts(colored.green('Starting packager...'))
    pkg_process = dev_dir.start_packager(os.getcwd(), global_watchman)

    try:
        current_process = pkg_process
        logging = False  # enable when we have started logging
        packager_output = False
        while True:
            l = current_process.stdout.readline().decode()
            if not logging and '<START>' in l:
                packager_output = True
            if logging:
                if log_filter(l):
                    sys.stdout.write(l)
            elif packager_output:
                sys.stdout.write(l)

            if 'Building Dependency Graph' in l \
            and '<END>' in l:
                # We're ready to launch the simulator
                sim.run(app, bundle_id)
                current_process = sim.tail_logs()
                puts(colored.green('Streaming logs...'))
                logging = True

    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        print('Exiting...')
    finally:
        sim.quit()
        current_process.kill()

@config_required
def develop(sim, default_sim=True, global_watchman=False):
    """
    Takes a simulator object and runs the simulator
    """
    conf = Config()
    user_conf = UserConfig()
    app_id = conf.app_id

    mixpanel_props = {
        'app_id': app_id,
        'simulator': sim.formatted_name,
        'default_sim': default_sim
    }
    mixpanel_event(MIXPANEL_EVENT_DEVELOP, properties=mixpanel_props)

    # The app needs to be built (archived) if:
    #
    #   1. An archive for this base version doesn't exist
    #   2. An archive exists and the display name has changed
    #   3. An archive exists and the facebook app id has changed
    #
    # After each build, we cache the build info and use it for future
    # reference. If build info is not stored for this app and base version,
    # we build the app anyway and cache the build info.

    # Here we use the version in the Siphonfile since we are not pushing
    # the app.
    version = user_conf.get('base_version')
    # Ensure that node exists in our develop directory
    ensure_node(version)

    # Create a Build instance for the app
    build = Build(conf.app_id, version)

    # Make sure the correct base version is installed and the build
    # directory exists
    ensure_base(version)
    build.ensure_build_dir()

    # Get/set the display name
    display_name = user_conf.get('display_name')
    if not display_name:
        print('A display name for this app has not been set. ' \
              'Please enter a display name. This can be changed by ' \
              'modifying the "display_name" value in the app ' \
              'Siphonfile.')
        new_display_name = get_input('Display name: ')
        user_conf.set('display_name', new_display_name)
        display_name = new_display_name

    # Get the facebook_app_id
    facebook_app_id = user_conf.get('facebook_app_id')

    cache = Cache()
    build_info_updated = cache.build_info_updated(build.build_id,
                                                 display_name, facebook_app_id)

    # If the build info has been updated, we clear the old archives
    if build_info_updated:
        build.clean_archives()

    # Make sure our develop directory is populated with the latest node modules
    # and is generally Initialized
    dev_dir = DevelopDir(version)
    dev_dir.clean_old()
    dev_dir.ensure_develop_dir()

    bundle_id = 'com.getsiphon.%s' % conf.app_id

    # Initialize a BaseConfig instance that will be used to configure
    # the base project we're archiving.
    base_conf = BaseConfig(display_name, bundle_id,
                           facebook_app_id=facebook_app_id,
                           app_transport_exception='localhost')
    base = BaseProject(build.project_dir(sim.platform))

    platform_version = sim.platform_version
    arch_dir = build.archive_dir_path(sim.formatted_name, platform_version)

    if not build.archived(sim.formatted_name, platform_version):
        with base.configure(base_conf):
            app = archive(sim, arch_dir, build.project_dir())
    else:
        app = sim.app_path(arch_dir)

    # Update the cached app_info & run the app
    cache.set_build_info(build.build_id, display_name, facebook_app_id)
    start_processes(dev_dir, sim, app, bundle_id, global_watchman)

def run(args):
    if args is None:
        args = []
    if '--help' in args:
        print_usage()
        return

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

    sim_data = IOSSimulatorData()
    platform_version = sim_data.latest_platform_version()

    if len(args) == 1 and args[0] == '--list-sims':
        print_sims()
        return

    # Use the global installation of watchman if specified
    global_watchman = False
    if '--global-watchman' in args:
        global_watchman = True
        args.remove('--global-watchman')

    if len(args) == 2 and args[0] == '--simulator':
        sim_name = args[1]
        sim = sim_data.get_sim(sim_name, platform_version)
        if not sim:
            puts(colored.red('Invalid simulator name provided.'))
            print_sims()
            return
        develop(sim, default_sim=False, global_watchman=global_watchman)
        return
    elif len(args) > 0:
        print_usage()
        return

    sim = sim_data.default_sim()
    develop(sim, global_watchman=global_watchman)
