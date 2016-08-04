import os

from siphon.cli.constants import SIPHON_USER_DIR
from siphon.cli.wrappers.json_file import JSONFile

AUTH_PATH = os.path.join(SIPHON_USER_DIR, '.auth')

class Auth(JSONFile):
    KEY_USERNAME = 'username'
    KEY_AUTH_TOKEN = 'auth_token'

    def __init__(self):
        super(Auth, self).__init__(AUTH_PATH)

    @property
    def auth_token(self):
        return self.get(Auth.KEY_AUTH_TOKEN)

    @auth_token.setter
    def auth_token(self, value):
        self.set(Auth.KEY_AUTH_TOKEN, value)

    @property
    def username(self):
        return self.get(Auth.KEY_USERNAME)

    @username.setter
    def username(self, value):
        self.set(Auth.KEY_USERNAME, value)

    def logged_in(self):
        return self.username and self.auth_token

    def clear(self):
        # Delete the file
        try:
            os.remove(self._path)
        except FileNotFoundError:
            pass
