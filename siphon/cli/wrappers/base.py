
import json
import plistlib
import os

from contextlib import contextmanager

class BaseConfig(object):
    """
    Holds the configuration data for a given base project.
    """
    def __init__(self, display_name, bundle_id,
                 app_transport_exception=None, facebook_app_id=None):
        self.display_name = display_name
        self.bundle_id = bundle_id
        self.app_transport_exception = app_transport_exception
        self.facebook_app_id = facebook_app_id

    def to_dict(self):
        config_dict = {
            'display_name': self.display_name,
            'bundle_id': self.bundle_id,
            'app_transport_exception': self.app_transport_exception,
            'facebook_app_id': self.facebook_app_id
        }
        return config_dict

    def to_json(self):
        return json.dumps(self.to_dict())

class BaseProject(object):
    """
    Initialize with a directory path to a base project.
    """
    def __init__(self, directory):
        self.directory = directory
        self.info = os.path.join(self.directory, 'SiphonBase', 'Info.plist')

    @contextmanager
    def configure(self, config):
        """
        Temporarily configure a base project
        """
        with open(self.info, 'r') as f:
            info = f.read()
        try:
            self.set_bundle_id(config.bundle_id)
            self.set_display_name(config.display_name)
            self.set_facebook_sdk_info(config.facebook_app_id,
                                       config.display_name)
            self.set_app_transport_exception(config.app_transport_exception)
            yield
        finally:
            with open(self.info, 'w') as f:
                f.write(info)

    def set_bundle_id(self, bundle_id):
        self.set_info('CFBundleIdentifier', bundle_id)

    def set_display_name(self, display_name):
        self.set_info('CFBundleDisplayName', display_name)

    def set_app_transport_exception(self, domain):
        key = 'NSAppTransportSecurity'
        value = {'NSAllowsArbitraryLoads': False}
        if domain:
            value['NSExceptionDomains'] = {
                domain: {
                    'NSTemporaryExceptionAllowsInsecureHTTPLoads': True
                }
            }
        self.set_info(key, value)

    def set_facebook_sdk_info(self, fb_app_id, fb_display_name):
        # If the app id is not set, do nothing
        if not fb_app_id:
            return

        with open(self.info, 'r') as f:
            contents = f.read()

        # Handle updated template variables
        processed = contents.replace('{{facebook-app-id}}', fb_app_id)
        processed = contents.replace('facebook.app.id.placeholder', fb_app_id)
        processed = processed.replace('{{facebook-display-name}}',
                                     fb_display_name)
        processed = processed.replace('facebook.display.name.placeholder',
                                     fb_display_name)

        with open(self.info, 'w') as f:
            # Replace our template vars {{facebook-app-id}} and
            # {{facebook-display-name}}
            f.write(processed)

    def set_info(self, k, v):
        """
        Set a value for a given key in an app's base project info.plist
        """
        info = self.get_info()

        with open(self.info, 'wb') as f:
            # Note that we have to write the entire contents to the file.
            # so we load the current data, add whatever we need to it then
            info[k] = v
            plistlib.dump(info, f)

    def get_info(self, k=None):
        """
        Get the value for a key in the an app's base project info.plist
        """
        info = None
        with open(self.info, 'rb') as f:
            info = plistlib.load(f)
        if k:
            return info.get(k)
        else:
            return info
