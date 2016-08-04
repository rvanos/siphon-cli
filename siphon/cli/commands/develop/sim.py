import subprocess
import re
import os
import json
import time
import sys
from decimal import Decimal
from siphon.cli.utils.packager import packager_endpoint
from siphon.cli.utils.system import bash, background_process, cd
from siphon.cli.utils.system import process_running

from siphon.cli import SiphonClientException

from siphon.cli.constants import (
    PACKAGER_HOST,
    PACKAGER_PORT,

    XCODE_PROJECT_WORKSPACE,
    XCODE_PROJECT_SCHEME,
    XCODE_PRODUCT_NAME,
    XCODE_BUNDLE_IDENTIFIER,
    XCTOOL_PATH
)
from clint.textui import colored, puts

SIMCTL_NUM_SERVICES = 130

class SiphonSimulatorException(SiphonClientException):
    pass

class BaseSimulator(object):
    """
    The base class from which simulator device objects inherit.
    """
    def __init__(self, name, formatted_name, platform, platform_version):
        self.name = name  # The
        self.formatted_name = formatted_name  # Siphon-formatted name
        self.platform = platform  # 'ios' or 'android'
        self.platform_version = platform_version

    @classmethod
    def from_name(cls, name, platform_version):
        """
        Factory method. Returns an instance from a given machine-formatted
        device name and platform version.
        """
        raise NotImplementedError

    @classmethod
    def from_formatted_name(cls, formatted_name, platform_version):
        """
        Factory method. Returns an instance from a given Siphon-formatted
        device name and platform version.
        """
        raise NotImplementedError

    @staticmethod
    def format_device_name(name):
        """
        Takes the device name that is formatted for the machine and returns
        the Siphon-formatted form.
        """
        raise NotImplementedError

    @staticmethod
    def platform_device_name(formatted_name):
        """
        Takes a formatted device name and returns the device name as expected
        by the machine.
        """
        raise NotImplementedError

    @staticmethod
    def run(app):
        """
        Takes a given app and run it
        """
        raise NotImplementedError

    @staticmethod
    def quit():
        """
        Quit the simulator if it's running.
        """
        raise NotImplementedError


class IOSSimulator(BaseSimulator):
    """
    Represents an iOS simulator device
    """
    def __init__(self, name, formatted_name, platform_version, device_category,
                 sdk, udid):
        """
        name: Xcode-formatted name (e.g. 'iPhone 6s')
        formatted_name: Name formatted for client input/output ' \
        '(e.g. 'iphone6s') ios: The version of iOS supported by ' \
        'the simulator (e.g. '9.2') device_category: Required by xc ' \
        '(e.g. 'iOS 9.2') \
        sdk: The sdk version required for xctool
        udid: UDID of simulator device
        """
        super().__init__(name, formatted_name, 'ios', platform_version)
        self.device_category = device_category
        self.sdk = sdk
        self.udid = udid

    @classmethod
    def from_name(cls, name, platform_version, udid):
        """
        Returns a new IOSSimulator instance.
        """
        formatted_name = IOSSimulator.format_device_name(name)
        category = 'iOS %s' % platform_version
        sdk = 'iphonesimulator%s' % platform_version
        return cls(name, formatted_name, platform_version, category, sdk, udid)

    @classmethod
    def from_formatted_name(cls, formatted_name, platform_version, udid):
        """
        Returns a new IOSSimulator instance.
        """
        name = IOSSimulator.platform_device_name(formatted_name)
        category = 'iOS %s' % platform_version
        sdk = 'iphonesimulator%s' % platform_version
        return cls(name, formatted_name, platform_version, category, sdk, udid)

    @staticmethod
    def format_device_name(name):
        formatted_name = name.replace(' ', '').lower().replace('plus', '+')
        return formatted_name

    @staticmethod
    def platform_device_name(formatted_name):
        match = re.match('(?P<device>(iphone|ipad))(?P<number>[0-9]+(s?))' \
                         '(?P<plus>+?)')
        device = match.group('device').replace('p', 'P')
        number = match.group('number')
        plus = match.group('plus')
        name = '%s %s' % (device, number)
        if plus:
            name = '%s Plus' % name
        return name

    @staticmethod
    def app_path(archive_dir):
        """
        Takes the directory containing the archive and returns the path to
        the .app file.
        """
        archive_path = os.path.join(archive_dir, 'archive.xcarchive')
        return os.path.join(
            archive_path,
            'Products/Applications',
            '%s.app' % XCODE_PRODUCT_NAME
        )

    @staticmethod
    def is_running():
        return process_running('Simulator')

    def run(self, app, bundle_identifier=XCODE_BUNDLE_IDENTIFIER):
        """
        Launch the Simulator if it's not already open and run the provided .app
        file.
        """
        self.boot_simulator()
        IOSSimulator.install_and_run(app, bundle_identifier)
        puts(colored.green('You can change the window scale of ' \
                           'the simulator by pressing, for example, ⌘ - 3.'))

    def archive(self, project_dir, output_dir):
        """
        :returns absolute path to SiphonBase.app ready to be installed.
        """
        derived_data_path = os.path.join(output_dir, 'derived-data')
        archive_path = os.path.join(output_dir, 'archive.xcarchive')

        # Command to set the preprocessor macro values
        preprocessor_defs = ["SIPHON_PACKAGER_ENDPOINT='%s'" % packager_endpoint(self.platform)]
        preprocessor_defs.append("SIPHON_PACKAGER_HOST='%s'" % PACKAGER_HOST)
        preprocessor_defs.append("SIPHON_PACKAGER_PORT='%s'" % PACKAGER_PORT)

        macro_cmd = " GCC_PREPROCESSOR_DEFINITIONS=" \
                    "'$GCC_PREPROCESSOR_DEFINITIONS %s'" % ' '.join(preprocessor_defs)

        dest = 'platform=iOS Simulator,OS=%s,name=%s' % (self.platform_version,
                                                         self.name)

        cmd = XCTOOL_PATH
        cmd += ' -workspace "./%s"' % XCODE_PROJECT_WORKSPACE
        cmd += ' -configuration Debug'
        cmd += ' -scheme "%s"' % XCODE_PROJECT_SCHEME
        cmd += ' -sdk %s' % self.sdk
        cmd += ' -destination "%s"' % dest
        cmd += ' -derivedDataPath "%s"' % derived_data_path
        cmd += macro_cmd
        cmd += ' clean archive -archivePath "%s"' % archive_path

        with cd(project_dir):
            puts(colored.yellow('Building app for the simulator...'))
            p = background_process(cmd, time_estimate=100)
            out, err = p.communicate()
            if p.returncode != 0:
                print(out)
                print(err.decode())
                sys.exit(1)

        return IOSSimulator.app_path(output_dir)

    def boot_simulator(self):
        # Note that we suppress error messages here since xctool raises a funny
        # 'template not specified error'.
        bash('xcrun instruments -w "%s"' % self.udid, hide_stderr=True)
        IOSSimulator.wait_for_ready()

    def tail_logs(self):
        # Returns a process the lines of which are the simulator logs
        log_path = os.path.join(os.path.expanduser('~'),
                    'Library/Logs/CoreSimulator/%s/system.log' % self.udid)
        cmd = [
            'tail',
            '-F',
            log_path
        ]
        log_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1)
        return log_process

    @staticmethod
    def wait_for_ready():
        """ Blocks until the simulator is ready. """
        while 1:
            print('Waiting for the simulator to startup...')
            cmd = 'xcrun simctl spawn booted launchctl list | wc -l'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            n = int(output.strip())
            if n >= SIMCTL_NUM_SERVICES:  # this is a hack!
                puts(colored.green('Ready!'))
                break
            time.sleep(3)

    @staticmethod
    def quit():
        bash('killall \'Simulator\'')

    @staticmethod
    def install_and_run(app_path, bundle_identifier=XCODE_BUNDLE_IDENTIFIER):
        bash('xcrun simctl install booted %s' % app_path)
        bash('xcrun simctl launch booted %s' % bundle_identifier)

    @staticmethod
    def uninstall_app(bundle_identifier=XCODE_BUNDLE_IDENTIFIER):
        bash('xcrun simctl uninstall booted %s' % bundle_identifier,
            hide_stderr=True)

class IOSSimulatorData(object):
    """
    A wrapper around 'xcrun simctl list' that gives detailed info about
    the availability of various devices for the simulator
    """
    def __init__(self):
        self._data = self._fetch_device_data()

    def _fetch_device_data(self):
        cmd = 'xcrun simctl list --json'
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        obj = json.loads(output)
        return obj

    def platform_versions(self):
        """
        Returns a list of iOS versions for which simulators are available.
        """
        data_keys = list(self._data['devices'])
        platform_versions = []
        for k in data_keys:
            match = re.match('iOS (?P<version>[0-9]+.[0-9]+)', k)
            if match:
                platform_versions.append(match.group('version'))
        platform_versions.sort(key=lambda f: Decimal(f), reverse=True)
        return platform_versions

    def latest_platform_version(self):
        """
        Returns the latest iOS version
        """
        versions = self.platform_versions()
        if versions:
            return self.platform_versions()[0]
        else:
            return None

    def sim_list(self, os_version, format=True):
        """
        Returns a list of devices that are availble for the given os version.
        os_version is a decimal string.
        """
        sims = []
        category = 'iOS ' + os_version
        for device in self._data['devices'][category]:
            s = IOSSimulator.from_name(device['name'], os_version,
                                       device['udid'])
            sims.append(s)
        return sims

    def get_sim(self, formatted_name, platform_version):
        """
        Takes a formatted name and returns a corresponding simulator object.
        """
        sims = self.sim_list(platform_version)
        for s in sims:
            if s.formatted_name == formatted_name:
                return s
        return None

    def default_sim(self):
        """
        Returns the simulator model we set as a default. Returns the latest
        non-plus size version of the iPhone if available; otherwise return
        anything.
        """
        sims = self.sim_list(self.latest_platform_version())

        # Get all non-s, non-plus size iphones
        r = re.compile('iphone[0-9]+')
        iphones = [s for s in sims if r.match(s.formatted_name)]
        r = re.compile('iphone[0-9]+s')
        s_models = [s for s in sims if r.match(s.formatted_name)]
        if iphones:
            ordered = sorted(iphones, key=lambda s: s.formatted_name[6],
                             reverse=True)
            last = ordered[0]
            if s_models:
                ordered_s = sorted(s_models, key=lambda s: s.formatted_name[6],
                                   reverse=True)
                last_s = ordered_s[0]
                if last.formatted_name[:7] == last_s.formatted_name[:7]:
                    return last_s
                else:
                    return last
        elif sims:
            return sims[0]
        else:
            return None
