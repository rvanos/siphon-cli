import subprocess
import os
import sys

from siphon.cli import SiphonClientException
from siphon.cli.wrappers import Cache
from siphon.cli.utils.input import get_input
from siphon.cli.utils.xcode import provisioning_profile_installed
from siphon.cli.utils.fastlane import siphon_fastlane
from siphon.cli.utils.system import bash, background_process, cd

from clint.textui import colored, puts

from siphon.cli.constants import (
    IOS_DEPLOY,
    XCODE_PROJECT_WORKSPACE,
    XCODE_PROJECT_SCHEME,
    XCODE_PRODUCT_NAME,
    XCTOOL_PATH
)

class SiphonDeviceException(SiphonClientException):
    pass

class IOSDevice(object):
    def __init__(self, udid):
        self.udid = udid
        self.formatted_name = 'device'

    @staticmethod
    def get_device():
        udid = subprocess.check_output('system_profiler SPUSBDataType | ' \
         ' grep -A 11 -w "iPad\|iPhone\|iPad" | grep "Serial Number" | ' \
        'awk \'{ print $3 }\'', shell=True).decode().strip()

        if udid:
            return IOSDevice(udid)
        else:
            return None

    def archive(self, project_dir, output_dir, app_id, auth_token,
                provisioning_profile, dev_mode=False):
        """
        :returns absolute path to SiphonBase.app ready to be installed.
        """
        derived_data_path = os.path.join(output_dir, 'derived-data')
        archive_path = os.path.join(output_dir, 'archive.xcarchive')

        # Command to set the preprocessor macro values
        preprocessor_defs = ["SIPHON_APP_ID='%s'" % app_id]
        if auth_token:
            preprocessor_defs.append("SIPHON_AUTH_TOKEN='%s'" % auth_token)

        host = os.environ.get('SP_HOST')
        if host:
            preprocessor_defs.append("SIPHON_HOST='%s'" % host)

        if dev_mode:
            preprocessor_defs.append("SIPHON_DEV_MODE='%s'" % 'ON')

        macro_cmd = " GCC_PREPROCESSOR_DEFINITIONS="\
                    "'$GCC_PREPROCESSOR_DEFINITIONS %s'" % ' '.join(preprocessor_defs)

        cmd = XCTOOL_PATH
        cmd += ' -workspace "./%s"' % XCODE_PROJECT_WORKSPACE
        cmd += ' -scheme "%s"' % XCODE_PROJECT_SCHEME
        cmd += ' -sdk iphoneos'
        cmd += ' PROVISIONING_PROFILE=%s' % provisioning_profile
        cmd += ' -derivedDataPath "%s"' % derived_data_path
        cmd += macro_cmd
        cmd += ' clean archive -archivePath "%s"' % archive_path

        with cd(project_dir):
            puts(colored.yellow('Building app for the device...'))
            # bash(cmd)
            # sys.exit(0)
            p = background_process(cmd, time_estimate=100)
            out, err = p.communicate()
            if p.returncode != 0:
                print(out)
                print(err.decode())
                sys.exit(1)
        return IOSDevice.app_path(output_dir)

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

    def update_requirements(self):
        cache = Cache()
        uname = cache.get_apple_username()
        if not uname:
            print('Please enter your Apple Developer account username. ' \
                  'We need to use your credentials to ensure that a valid ' \
                  'development certificate and provisioning profile ' \
                  'are installed on your machine. Existing certificates ' \
                  'will not be revoked.\n' \
                  'Change the username using: siphon play ' \
                  '--set-apple-username <username>. ' \
                  'Your password will be stored in your keychain.')
            uname = get_input('Username: ')
        siphon_fastlane(uname, self.udid)
        cache.set_apple_username(uname)

    def profile_synchronised(self):
        """
        Check that we have an provisioning profile installed
        and that it is compatible with the device udid.
        """
        cache = Cache()
        in_sync = False
        profile_id = cache.get_provisioning_profile_id()
        if profile_id:
            profile_installed = provisioning_profile_installed(profile_id)
            device_in_profile = cache.device_in_profile(self.udid)
            if profile_installed and device_in_profile:
                in_sync = True
        return in_sync

    @staticmethod
    def build_profile_ok(build_id):
        """
        Return True if the previous build was completed using the current
        provisioning profile. An archive is required if not.
        """
        cache = Cache()
        build_profile = cache.get_build_profile(build_id)
        current_profile = cache.get_provisioning_profile_id()
        if build_profile == current_profile:
            return True
        else:
            return False

    @staticmethod
    def run(app):
        print('Launching app...')
        try:
            subprocess.check_output([IOS_DEPLOY, '--justlaunch',
                                '--bundle',
                                app])
            print('Launched.')
        except subprocess.CalledProcessError as e:
            if 'Device Locked' in e.output.decode():
                puts(colored.red(
                    'Your device is locked. Please unlock it and try again.'
                ))
            else:
                puts(colored.red(
                    'Unable to launch app. Please make sure your device is ' \
                    'connected.'
                ))
