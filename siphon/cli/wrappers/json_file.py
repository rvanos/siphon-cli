
import json
import stat
import os

class JSONFile(object):
    def __init__(self, path):
        self._path = path

    def _load(self):
        try:
            with open(self._path, 'r') as f:
                s = f.read()
                if not s:
                    return {}
                else:
                    return json.loads(s)
        except FileNotFoundError:
            return {}

    def exists(self):
        return os.path.isfile(self._path)

    def get(self, k):
        obj = self._load()
        return obj.get(k)

    def set(self, k, v):
        obj = self._load()
        obj[k] = v
        with open(self._path, 'w') as f:
            os.chmod(self._path, stat.S_IWRITE | stat.S_IREAD)
            json.dump(obj, f)

    def remove(self, k):
        # Remove the key from the file
        obj = self._load()
        obj.pop(k, None)
        with open(self._path, 'w') as f:
            os.chmod(self._path, stat.S_IWRITE | stat.S_IREAD)
            json.dump(obj, f)
