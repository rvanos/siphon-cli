
import os

def packager_endpoint(platform):
    plat = platform.lower()
    if os.path.isfile('index.js'):
        entry = 'index'
    else:
        entry = 'index.%s' % plat
    return '%s.bundle?platform=%s' % (entry, plat)
