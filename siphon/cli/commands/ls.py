
from siphon.cli.utils.siphon import login_required
from siphon.cli.wrappers import Auth, Siphon

from siphon.cli.utils.mixpanel import mixpanel_event, MIXPANEL_EVENT_LIST

def print_usage():
    print('Usage: siphon ls [--help]')

@login_required
def print_apps():
    auth = Auth()
    mixpanel_event(MIXPANEL_EVENT_LIST)
    siphon = Siphon(auth.auth_token)
    for app in siphon.list_apps():
        print(app['name'])

def run(args):
    if args is None:
        args = []
    if '--help' in args or len(args) > 0:
        print_usage()
    else:
        print_apps()
