import os
import stat
import json

from siphon.cli.wrappers.json_file import JSONFile
from siphon.cli.constants import SIPHON_CONFIG, SIPHON_USER_CONFIG

class Config(JSONFile):
    KEY_APP_ID = 'app_id'

    def __init__(self, directory='.'):
        super(Config, self).__init__(os.path.join(directory, SIPHON_CONFIG))

    @property
    def app_id(self):
        return self.get(Config.KEY_APP_ID)

    @app_id.setter
    def app_id(self, value):
        self.set(Config.KEY_APP_ID, value)

    def is_ready(self):
        return self.app_id is not None

class UserConfig(JSONFile):
    def __init__(self, directory='.'):
        super(UserConfig, self).__init__(os.path.join(directory,
                                     SIPHON_USER_CONFIG))

    def set(self, k, v):
        obj = self._load()
        obj[k] = v
        with open(self._path, 'w') as f:
            os.chmod(self._path, stat.S_IWRITE | stat.S_IREAD)
            json.dump(obj, f, indent=4, sort_keys=True)
