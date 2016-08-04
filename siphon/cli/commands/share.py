
from clint.textui import colored, puts

from siphon.cli.utils.siphon import login_required
from siphon.cli.wrappers import Auth, Config, Siphon
from siphon.cli.utils.input import yn
from siphon.cli.commands.push import push
from siphon.cli.utils.mixpanel import (
    mixpanel_event,
    MIXPANEL_SHARE_BETA_TESTER,
    MIXPANEL_SHARE_TEAM_MEMBER
)

TEAM_SHARE_DOCS_URL = 'https://getsiphon.com/docs/team-sharing/'

def print_usage():
    print('Usage: siphon share <email> [--team] [--help]\n\n' \
        'Share your app with a beta tester or team member. This ' \
        'will trigger an invitation email to be sent to the given email ' \
        'address and the recipient must accept your invitation.\n\nTo ' \
        'share this app with a beta tester:\n\n' \
        '    $ siphon share someone@domain.com\n\n' \
        'To share this app with a team member:\n\n'
        '    $ siphon share someone@domain.com --team\n')

def prompt_team_share(shared_with):
    msg = 'This will share a special team copy of your app with the person ' \
        'who owns the email address that you specified. They will be sent ' \
        'an email with an explanation and a link to accept the invite.'
    msg += '\n\nPlease read this page before you continue: %s' % \
        TEAM_SHARE_DOCS_URL
    if shared_with:
        msg += '\n\nThe follow users are currently active team members for ' \
            'this app: \n\n'
        for obj in shared_with:
            msg += '    --> %s (%s)' % (obj['username'], obj['email'])
    msg += '\n\nContinue? [Y/n]: '
    return yn(msg)

def prompt_beta_share_for_specific_email(shared_with):
    msg = 'This will share a read-only copy of your app with the person who ' \
        'owns the email address that you specified.\n\nThey will be sent an ' \
        'email explaining how to download the Siphon Sandbox and run your ' \
        'app. If they do not yet have a Siphon account, they will be ' \
        'prompted to create one.'
    if shared_with:
        msg += '\n\nIn addition, the following active beta testers will '  \
            'receive the latest app changes:\n\n'
        for obj in shared_with:
            msg += '    --> %s (%s)' % (obj['username'], obj['email'])
    msg += '\n\nContinue? [Y/n]: '
    return yn(msg)

def prompt_beta_share_for_all(shared_with):
    msg = 'You are about to share the latest changes for this app. ' \
        'The following beta testers will be notified that there is an ' \
        'update available:\n\n'
    for obj in shared_with:
        msg += '    --> %s (%s)\n' % (obj['username'], obj['email'])
    msg += '\nContinue? [Y/n]: '
    return yn(msg)

@login_required
def share_with_team_member(email):
    auth = Auth()
    siphon = Siphon(auth.auth_token)
    conf = Config()

    # Prompt the user with implications before we do anything.
    puts(colored.yellow('Checking the sharing status for this app...'))
    sharing_status = siphon.get_sharing_status(conf.app_id)
    shared_with = sharing_status.get('shared_with', [])
    if not prompt_team_share(shared_with):
        return

    siphon.share(conf.app_id, 'team-member', email)
    puts(colored.green('Your app was shared successfully.'))
    mixpanel_event(MIXPANEL_SHARE_TEAM_MEMBER)

@login_required
def share_with_beta_tester(email=None):
    auth = Auth()
    siphon = Siphon(auth.auth_token)
    conf = Config()

    # Prompt the user with implications before we do anything.
    puts(colored.yellow('Checking the sharing status for this app...'))
    sharing_status = siphon.get_sharing_status(conf.app_id)
    shared_with = sharing_status.get('shared_with', [])
    if email:
        if not prompt_beta_share_for_specific_email(shared_with):
            return
    else:
        if len(shared_with) < 1:
            msg = 'Running the "siphon share" command without specifying ' \
                'an email address is only valid if you have one-or-more ' \
                'beta testers who already accepted an invitation.'
            puts(colored.red(msg))
            return
        if not prompt_beta_share_for_all(shared_with):
            return

    # Do a push to the *aliased* beta testing app.
    puts(colored.green('Pushing your local files for beta testing...'))
    aliased_app_id = sharing_status['aliased_app']['id']
    if not push(app_id=aliased_app_id, track_event=False):
        puts(colored.red('\nThe push failed so your beta testers were not ' \
            'notified.'))
        return

    # We only need to add a sharing permission if an email was specified,
    # because the push itself triggers notifications.
    if email is not None:
        siphon.share(conf.app_id, 'beta-tester', email)
    puts(colored.green('\nYour app was shared successfully.'))
    mixpanel_event(MIXPANEL_SHARE_BETA_TESTER)

def run(args):
    if args is None:
        args = []
    if '--help' in args or len(args) > 2:
        print_usage()
        return

    email = None
    if args:
        email = args[0]
        if '@' not in email:
            print_usage()
            return

    if '--team' in args:
        if not email:
            print_usage()
            return
        share_with_team_member(email)
    else:
        share_with_beta_tester(email=email)
