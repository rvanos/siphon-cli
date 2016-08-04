import os
import requests

from siphon.cli import SiphonAPIException, SiphonCommandException
from siphon.cli.utils.download import get_download_size
from siphon.cli.wrappers.cache import Cache

def error_to_string(obj):
    """ Formats API errors for human consumption. """
    vals = []
    for val in obj.values():
        if isinstance(val, list) or isinstance(val, tuple):
            vals.append(' '.join(map(str, val)))
        else:
            vals.append(str(val))
    return '\n'.join(vals)

class Siphon(object):
    TOKEN_HEADER_NAME = 'X-Siphon-Token'

    def __init__(self, auth_token):
        self._token = auth_token

    @staticmethod
    def make_root_url():
        url = '{scheme}://{host}%s'.format(
            scheme=os.environ.get('SP_SCHEME', 'https') or 'https',
            host=os.environ['SP_HOST']
        )

        port = str(os.environ.get('SP_PORT', 80) or 80)
        if port != '80':
            s = ':%s' % port
            return url % s
        else:
            return url % '' # port is implied by scheme

    @staticmethod
    def make_static_root_url():
        static_host = os.environ.get('SP_STATIC_HOST')

        if static_host:
            url = '{scheme}://{host}%s'.format(
                scheme=os.environ.get('SP_STATIC_SCHEME', 'https') or 'https',
                host=static_host
            )

            port = str(os.environ.get('SP_STATIC_PORT', 80) or '80')
            if port != '80':
                s = ':%s' % port
                return url % s
            else:
                return url % '' # port is implied by scheme
        else:
            return Siphon.make_root_url()

    @staticmethod
    def make_url(endpoint):
        extension = '/api/{version}{endpoint}'.format(
            version=os.environ.get('SP_API_VERSION', 'v1') or 'v1',
            endpoint=endpoint
        )

        url = '%s%s' % (Siphon.make_root_url(), extension)
        return url

    @staticmethod
    def base_package_url(version):
        extension = '/static/cli/siphon-base-%s.tar.gz' % version
        pkg_url = '%s%s' % (Siphon.make_static_root_url(), extension)
        return pkg_url

    @staticmethod
    def call(method, endpoint, data=None, token=None, timeout=None):
        if timeout is None:
            timeout = 10
        url = Siphon.make_url(endpoint)
        data = data or {}
        if token:
            headers = {Siphon.TOKEN_HEADER_NAME: token}
        else:
            headers = None
        try:
            response = requests.request(method, url, data=data,
                headers=headers, timeout=timeout)
        except requests.exceptions.RequestException as e:
            print('METHOD: %s' % method)
            print('URL: %s' % url)
            raise SiphonCommandException(str(e))
        try:
            obj = response.json()
        except ValueError as e:
            print('\nSTATUS: %s' % response.status_code)
            print('CONTENT:\n%s\n' % response.content.decode('utf-8'))
            raise SiphonAPIException('Expecting JSON for endpoint "%s".' %
                                     endpoint)
        if not response.ok:
            raise SiphonCommandException(error_to_string(obj))
        else:
            return obj

    @staticmethod
    def content_length_for_version(version):
        """
        Takes a base version string and returns the Content-Length of the
        remote package for this version, using a HEAD request.
        """
        url = Siphon.base_package_url(version)
        return get_download_size(url)

    def _call(self, method, endpoint, data=None, timeout=None):
        """ Always authenticated. """
        return Siphon.call(method, endpoint, data=data,
            token=self._token, timeout=timeout)

    @staticmethod
    def authenticate(username, password):
        """ Returns a token suitable for instantiating a Siphon object. """
        obj = Siphon.call('POST', '/accounts/login/', data={
            'username': username,
            'password': password
        })
        if 'token' not in obj:
            raise SiphonAPIException('The server failed to return a token.')
        return obj['token']

    def create(self, app_name):
        return self._call('POST', '/apps/', data={'name': app_name})

    def submit(self, app_id, platform, username=None, password=None):
        data = {'app_id': app_id, 'platform': platform}
        if username and password:
            data['platform_username'] = username
            data['platform_password'] = password
        return self._call('POST', '/submissions/', data=data, timeout=120)

    def list_apps(self):
        return self._call('GET', '/apps/')['results']

    def get_app(self, app_id):
        return self._call('GET', '/apps/%s' % app_id)

    def get_bundler_url(self, app_id, action):
        bundler_url = Cache.get_server_url('bundler', app_id)
        if bundler_url is None:
            obj = self._call('GET', '/bundlers/?app_id=%s&action=%s' % (
                app_id, action))
            bundler_url = obj['bundler_url']
            Cache.set_server_url('bundler', app_id, bundler_url)
        return bundler_url

    def get_streamer_url(self, app_id, stream_type):
        streamer_url = Cache.get_server_url('streamer', app_id)
        if streamer_url is None:
            obj = self._call('GET', '/streamers/?app_id=%s&type=%s' % (
                app_id, stream_type))
            streamer_url = obj['streamer_url']
            Cache.set_server_url('streamer', app_id, streamer_url)
        return streamer_url

    def get_base_version(self, app_id):
        obj = self.get_app()
        return obj['base_version']

    def get_account_info(self):
        return self._call('GET', '/accounts/info/')

    def get_sharing_status(self, app_id, permission_type='beta-tester'):
        return self._call('GET', '/permissions/?app_id=%s&permission_type=%s' \
            % (app_id, permission_type))

    def share(self, app_id, permission_type, email):
        return self._call('POST', '/permissions/', data={
            'app_id': app_id,
            'permission_type': permission_type,
            'email': email
        })

    def validate_app(self, app_id, platform):
        obj = self._call('GET',
              '/submissions/validate/?app_id=%s&platform=%s' % (app_id,
                                                                platform))
        return obj['status']

    def user_can_publish(self):
        obj = self.get_account_info()
        return obj['can_publish']

    def app_requires_hard_update(self, app_id, platform):
        obj = self._call('GET',
              '/submissions/check/?app_id=%s&platform=%s' % (app_id, platform))
        return obj['hard_update_required']
