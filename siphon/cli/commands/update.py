
from siphon.cli.utils.updates import check_for_updates


def print_usage():
    print('Usage: siphon update\n\nUpdates this command-line tool to the ' \
        'latest version.')

def run(args=None, prompt=True):
    if args is None:
        args = []
    if '--help' in args or len(args) > 0:
        print_usage()
    else:
        check_for_updates(force=True)
