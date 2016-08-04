from siphon.cli.wrappers import Auth
from siphon.cli.utils.mixpanel import mixpanel_event, MIXPANEL_EVENT_LOGIN
from siphon.cli.utils.siphon import request_login

def print_usage():
    print('Usage: siphon [--help]\n\nSet the current user.')

def run(args):
    # Generate/retrieve the user's auth token
    credentials = request_login()
    username = credentials['username']
    auth_token = credentials['auth_token']

    # Update our .auth file
    auth = Auth()
    auth.username = username
    auth.auth_token = auth_token

    mixpanel_event(MIXPANEL_EVENT_LOGIN)
