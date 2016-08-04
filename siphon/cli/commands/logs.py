
from siphon.cli.utils.siphon import config_required, login_required
from siphon.cli.wrappers import Auth, Config, Siphon

from siphon.cli.utils.mixpanel import mixpanel_event, MIXPANEL_EVENT_LOGS

from clint.textui import colored, puts

import websocket

def print_usage():
    print('Usage: siphon logs [--help]\n\nStream the console logs from your ' \
        'app. It must be running in the simulator, developer device or in ' \
        'the Siphon Sandbox.')

@login_required
@config_required
def stream_logs():
    conf = Config()
    # Request the correct streamer URL from siphon-web
    auth = Auth()
    siphon = Siphon(auth.auth_token)

    # Track
    mixpanel_event(MIXPANEL_EVENT_LOGS, properties={'app_id': conf.app_id})

    streamer_url = siphon.get_streamer_url(conf.app_id, 'log_reader')

    puts(colored.yellow('Connecting...'))
    ws = websocket.create_connection(streamer_url)
    puts(colored.green('Streaming logs and errors... (ctrl-c to stop)\n'))
    try:
        for line in ws:
            print(line)
    except KeyboardInterrupt:
        puts(colored.yellow('\nClosing the connection.'))
        ws.close()

def run(args):
    if args is None:
        args = []
    if '--help' in args or len(args) > 0:
        print_usage()
    else:
        stream_logs()
