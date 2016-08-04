
import os
import json
import shutil
import time
import plistlib
import subprocess

from siphon.cli.utils.system import ensure_dir_exists
from siphon.cli.constants import SIPHON_USER_DIR

CACHE_DIR = os.path.join(SIPHON_USER_DIR, 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'cache.json')
IOS_CACHE_DIR = os.path.join(CACHE_DIR, 'ios')
PROVISIONING_PROFILE = os.path.join(IOS_CACHE_DIR, 'SiphonDev.mobileprovision')
BASE_VERSION_PREFIX = 'base-version'
UPDATE_CHECK_KEY = 'update-check'
INSTALLATION_LENGTH = 'installation-length'

SERVER_URL_PREFIX = 'server-url'
SERVER_URL_TIMEOUT = 3600 * 24


class Cache(object):
    @staticmethod
    def base_package_path(version):
        package_name = 'siphon-base-%s.tar.gz' % version
        return os.path.join(CACHE_DIR, package_name)

    @staticmethod
    def base_package_installed(version):
        return os.path.isfile(Cache.base_package_path(version))

    @staticmethod
    def set_length_for_base_version(version, val):
        Cache.set_key('%s/%s' % (BASE_VERSION_PREFIX, version), val)

    @staticmethod
    def get_length_for_base_version(version):
        return Cache.get_key('%s/%s' % (BASE_VERSION_PREFIX, version))

    @staticmethod
    def get_update_check_timestamp():
        """
        Returns a Unix timestamp that records the last time we checked
        for a CLI update.
        """
        return Cache.get_key(UPDATE_CHECK_KEY)

    @staticmethod
    def set_update_check_timestamp():
        """ Sets it to the current time. """
        timestamp = int(time.time())
        Cache.set_key(UPDATE_CHECK_KEY, timestamp)

    @staticmethod
    def set_installation_length(val):
        Cache.set_key(INSTALLATION_LENGTH, val)

    @staticmethod
    def get_installation_length():
        return Cache.get_key(INSTALLATION_LENGTH) or 0

    @staticmethod
    def get_server_url(server_type, app_id):
        assert server_type in ('bundler', 'streamer'), server_type
        k = '%s/%s/%s' % (SERVER_URL_PREFIX, app_id, server_type)
        obj = Cache.get_key(k)
        if obj is None:
            return None
        now = int(time.time())
        if obj['modified'] <= (now - SERVER_URL_TIMEOUT):
            return None  # value is too old
        else:
            return obj['url']

    @staticmethod
    def set_server_url(server_type, app_id, url):
        assert server_type in ('bundler', 'streamer'), server_type
        k = '%s/%s/%s' % (SERVER_URL_PREFIX, app_id, server_type)
        Cache.set_key(k, {
            'url': url,
            'modified': int(time.time())
        })

    @staticmethod
    def clear_urls():
        prefix = 'server-url'
        url_keys = []
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
            for k in list(data.keys()):
                if k.startswith(prefix):
                    url_keys.append(k)

            for k in url_keys:
                Cache.remove_key(k)
        except FileNotFoundError:
            return

    @staticmethod
    def set_apple_username(uname):
        Cache.set_key('apple_username', uname)

    @staticmethod
    def get_apple_username():
        return Cache.get_key('apple_username')

    @staticmethod
    def set_build_profile(build_id, uuid):
        """
        provisioning_profiles: {<app_id>: <uuid>}
        """
        profiles = Cache.get_key('provisioning_profiles')
        if not profiles:
            profiles = {}
        profiles[build_id] = uuid
        Cache.set_key('provisioning_profiles', profiles)

    @staticmethod
    def get_build_profile(build_id):
        profiles = Cache.get_key('provisioning_profiles')
        try:
            return profiles.get(build_id)
        except AttributeError:
            return None

    @staticmethod
    def get_app_profile(app_id):
        profiles = Cache.get_key('provisioning_profiles')
        try:
            return profiles.get(app_id)
        except AttributeError:
            return None

    @staticmethod
    def set_build_info(build_id, display_name, facebook_app_id):
        """
        We need to cache build info to check for changes and determine if
        rebuilds are required.

        Build info is structured in the following way:

        {
            "build_info": {
                "<build_id>": {
                    "display_name": "<display_name>",
                    "facebook_app_id": "<facebook_app_id>",
                }
            }
        }

        Note that the build ID corresponds to the name of the build
        directory and is of the form build-<app_id>-<base_version>.
        """
        build_info = Cache.get_key('build_info')
        if not build_info:
            build_info = {}

        build_info[build_id] = {
            'display_name': display_name,
            'facebook_app_id': facebook_app_id,
        }
        Cache.set_key('build_info', build_info)

    @staticmethod
    def get_build_info(build_id):
        build_info = Cache.get_key('build_info')
        try:
            return build_info.get(build_id)
        except AttributeError:
            return None

    @staticmethod
    def build_info_updated(build_id, display_name, facebook_app_id):
        """
        True if the provided info differs from our stored info; False
        otherwise.
        """
        cached_info = Cache().get_build_info(build_id)
        if not cached_info:
            return True

        updated = False
        if (display_name != cached_info.get('display_name')):
            updated = True
        if (facebook_app_id != cached_info.get('facebook_app_id')):
            updated = True

        return updated

    @staticmethod
    def set_key(k, val):
        ensure_dir_exists(CACHE_DIR)
        try:
            with open(CACHE_FILE, 'r') as fp:
                data = json.load(fp)
        except ValueError:
            data = {}
        except FileNotFoundError:
            data = {}
        data[k] = val
        with open(CACHE_FILE, 'w') as fp:
            json.dump(data, fp)

    @staticmethod
    def get_key(k):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                return data.get(k)
        except FileNotFoundError:
            return None
        except ValueError:
            return None

    @staticmethod
    def remove_key(k):
        # Remove the key from the file
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
            data.pop(k, None)

            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)

        except (FileNotFoundError, ValueError):
            return

    @staticmethod
    def get_provisioning_profile_id():
        try:
            profile = subprocess.check_output(['security', 'cms', '-D', '-i',
                                              PROVISIONING_PROFILE],
                                              stderr=subprocess.STDOUT)
            plist = plistlib.loads(profile)
            return plist['UUID']
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def device_in_profile(udid):
        try:
            profile = subprocess.check_output(['security', 'cms', '-D', '-i',
                                              PROVISIONING_PROFILE])
            plist = plistlib.loads(profile)
            return udid in plist['ProvisionedDevices']

        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def clear_ios():
        try:
            shutil.rmtree(IOS_CACHE_DIR)
        except OSError:
            pass

    @staticmethod
    def clear():
        """ Remove the cache directory. """
        shutil.rmtree(CACHE_DIR)
