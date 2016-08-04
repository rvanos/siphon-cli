
import functools
import sys

from os.path import isfile
from getpass import getpass
from clint.textui import colored, puts

from siphon.cli.utils.input import get_input
from siphon.cli.wrappers import Auth, Cache, Config, Siphon
from siphon.cli.constants import SIPHON_CONFIG

def login_required(func):
    """
    This decorator asserts that the user is logged in (that there is an
    auth token in the ~/.siphon/.auth file). If one doesn't exist, prompt
    the user to log in.
    """
    def wrapper(*args, **kwargs):
        auth = Auth()
        if auth.logged_in():
            return func(*args, **kwargs)
        else:
            credentials = request_login()
            username = credentials['username']
            auth_token = credentials['auth_token']

            auth.username = username
            auth.auth_token = auth_token
            return func(*args, **kwargs)
    return wrapper

def config_required(func):
    """
    This decorator asserts that a Siphon config file exists in the current
    working directory and it contains at least an authentication token and
    Siphon app name.
    """
    def wrapper(*args, **kwargs):
        conf = Config()
        # Remove the username & auth_token keys if they exist (now found in
        # .auth file)
        conf.remove('username')
        conf.remove('auth_token')
        if conf.is_ready():
            return func(*args, **kwargs)
        else:
            puts(colored.red(
                'This directory does not contain a %s file. You need to ' \
                'create an app before running this command.' % SIPHON_CONFIG
            ))
            sys.exit(1)
    return wrapper

def logout():
    # Cached bundler urls should be cleared and .auth removed
    cache = Cache()
    auth = Auth()
    cache.clear_urls()
    auth.clear()

def request_login():
    puts('Please enter your Siphon credentials to continue.\n')
    try:
        username = get_input('Username or email: ')
        password = getpass('Password: ')
    except KeyboardInterrupt:
        print('')  # newline
        sys.exit(0)

    auth_token = Siphon.authenticate(username, password)
    puts(colored.green('Logged in successfully.'))
    logout()  # Make sure we're logged out
    return {'auth_token': auth_token, 'username': username}

def entry_file_required(on_no_entry=None):
    """
    This decorator asserts that an entry file/entry files are in directory
    from which the decorated function is called.
    """
    def real_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if isfile('index.js') or isfile('index.ios.js') \
                                  or isfile('index.android.js'):
                return func(*args, **kwargs)
            else:
                puts(colored.red(
                    'This directory does not contain an index.js, index.ios.js ' \
                    'or index.android.js file.'
                ))
                # Run the on_no_entry function
                if on_no_entry:
                    on_no_entry()
                sys.exit(1)
        return wrapper
    return real_decorator
