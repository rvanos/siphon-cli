
from mixpanel import Mixpanel
from mixpanel_async import AsyncBufferedConsumer

from siphon.cli.utils.platform import get_platform_name
from siphon.cli.wrappers import Auth

MIXPANEL_TOKEN = 'c3a111fe44df4fa1df943af18dd2464b'

MIXPANEL_EVENT_CREATE = 'CLI: Create'
MIXPANEL_EVENT_INIT = 'CLI: Init'
MIXPANEL_EVENT_PUSH = 'CLI: Push'
MIXPANEL_EVENT_PUSH_ERROR = 'CLI: Push/Error'
MIXPANEL_EVENT_PLAY = 'CLI: Play'
MIXPANEL_EVENT_DEVELOP = 'CLI: Develop'
MIXPANEL_EVENT_LOGS = 'CLI: Logs'
MIXPANEL_EVENT_LIST = 'CLI: List'
MIXPANEL_EVENT_PUBLISH = 'CLI: Publish'
MIXPANEL_EVENT_LOGIN = 'CLI: Login'
MIXPANEL_SHARE_BETA_TESTER = 'CLI: Share/Beta tester'
MIXPANEL_SHARE_TEAM_MEMBER = 'CLI: Share/Team member'

def mixpanel_event(name, username=None, properties=None):
    """
    Takes an event name and a dict of args and registers it with Mixpanel.
    If the username is None, it will assumed that it can be found in a
    .siphon file in the directory.
    """
    # Use AsyncBufferedConsumer to avoid blocking the main thread
    mp = Mixpanel(MIXPANEL_TOKEN, consumer=AsyncBufferedConsumer())
    if not username:
        auth = Auth()
        username = auth.username

    props = {'user_platform': get_platform_name()}
    if properties:
        props.update(properties)

    mp.track(username, name, props)
