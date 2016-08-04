
import os
import zipfile
import fnmatch
import hashlib
import json
import sys
import time
from io import BytesIO

import requests
import watchdog
from clint.textui import colored, puts

import warnings; warnings.filterwarnings('ignore', module='watchdog')
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

from siphon.cli.wrappers import Auth, Config, Siphon
from siphon.cli import SiphonCommandException, SiphonBundlerException
from siphon.cli.utils.siphon import config_required, login_required
from siphon.cli.utils.download import ProgressReader
from siphon.cli.utils.siphon_ignore import get_ignored, keep

from siphon.cli.utils.mixpanel import mixpanel_event, MIXPANEL_EVENT_PUSH
from siphon.cli.utils.mixpanel import MIXPANEL_EVENT_PUSH_ERROR

def print_usage():
    print('Usage: siphon push [--watch] \n\nRun this command inside a Siphon ' \
        'app directory to push the app\'s latest changes to our servers. ' \
        'Note that this updates the simulator/device/sandbox in real-time ' \
        'if they are running, but it does not update a published app.')

def get_hashes(bundler_url):
    """ Get the currently stored server-side hashes for this app. """
    puts(colored.yellow('Fetching remote hashes...'))
    response = requests.get(bundler_url, timeout=10)
    try:
        obj = response.json()
    except ValueError as e:
        s = response.content.decode('utf-8')
        if len(s) > 500:
            s = s[:500] + '... [truncated]'
        raise SiphonBundlerException('Expecting JSON response from the ' \
            'bundler, received: %s' % s)
    if not response.ok or not isinstance(obj, dict) or 'hashes' not in obj:
        raise SiphonCommandException('Bad bundler response: %s' % str(obj))
    else:
        return obj['hashes']

def sha256(local_path):
    """
    Efficiently (memory-wise) calculates the SHA-256 hash of a file on disk.
    """
    hasher = hashlib.sha256()
    with open(local_path, 'rb') as fp:
        for chunk in iter(lambda: fp.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def should_push(sha, remote_path, server_hashes):
    """
    Generates a SHA-256 hash for the file at `local_path` and compares it to
    the hash in `hashes`. If this file doesn't exist in `hashes` (i.e. the
    server does not have it yet) or the hash is not equal, returns True to
    indicate that this file *should* be written into the /push zip archive.
    """
    remote_sha = server_hashes.get(remote_path)
    if remote_sha is None:
        return True # no need to generate local hash unless we have to
    return sha != remote_sha

def should_ignore(s, ignore_patterns=None):
    ignored = False
    if not ignore_patterns:
        ignore_patterns = get_ignored()
    for p in ignore_patterns:
        if fnmatch.fnmatch(s, p):
            ignored = True
    return ignored

def post_archive(bundler_url, server_hashes):
    puts(colored.yellow('Hashing...'))
    # Generate a .zip archive for our payload, writing out a listing file, and
    # any new/changed files into the diffs/ directory.
    fp = BytesIO()
    ignore_patterns = get_ignored()

    with zipfile.ZipFile(fp, 'w') as zf:
        listing = {}
        for root, dirs, files in os.walk('.'):
            if root == '.':
                prefix = ''
            elif root.startswith('./'):
                prefix = root[2:] + '/'
            else:
                raise RuntimeError('Unexpected root "%s"' % root)
            dirs[:] = keep(dirs, ignore_patterns, prefix)

            for fil in keep(files, ignore_patterns, prefix):
                local_path = root + '/' + fil # relative to current directory
                remote_path = prefix + fil # relative to app root
                zip_path = 'diffs/' + remote_path # path within .zip archive

                # Generate SHA-256 for this file and record it in the listing
                sha = sha256(local_path)
                listing[remote_path] = sha
                # Only write this file into diffs/ if we need to
                if should_push(sha, remote_path, server_hashes):
                    zf.write(local_path, zip_path)
        # Write out the listing file JSON
        zf.writestr('listing.json', json.dumps(listing))
    # Wrap it in a ProgressReader. It logs a progress bar to console as
    # python-requests cycles through the bytes doing the POST below.
    fp.seek(0)
    reader = ProgressReader(fp.read())
    fp.close()

    # Do the push.
    puts(colored.yellow('Pushing to the bundler...'))
    response = requests.post(bundler_url, data=reader, stream=True, headers={
        'Accept-Encoding': 'gzip;q=0,deflate,sdch' # explicitly disables gzip
    }, timeout=(10, None)) # unlimited read timeout
    reader.close()

    if response.ok:
        msg = None
        for line in response.iter_lines():
            l = line.decode('utf-8')
            if 'ERROR' in l:
                msg = l
                if len(msg) > 200:
                    msg = msg[0:200]
            print(l)

        if msg:
            mixpanel_props = {'error': msg}
            mixpanel_event(MIXPANEL_EVENT_PUSH_ERROR,
                           properties=mixpanel_props)
            return False
    else:
        msg = response.content.decode('utf-8')
        if len(msg) > 200:
            msg = msg[0:200]
        mixpanel_props = {'error': msg}
        mixpanel_event(MIXPANEL_EVENT_PUSH_ERROR,
                       properties=mixpanel_props)
        raise SiphonBundlerException('Problem writing changes: %s' %
                                     response.content)
    return True

def project_hash():
    """ Generates a SHA-256 hash for the whole project directory. """
    hasher = hashlib.sha256()
    ignore_patterns = get_ignored()
    for root, dirs, files in os.walk('.'):
        # Tidy up the root
        if root == '.':
            prefix = ''
        elif root.startswith('./'):
            prefix = root[2:] + '/'
        else:
            raise RuntimeError('Unexpected root "%s"' % root)

        dirs[:] = keep(dirs, ignore_patterns, prefix)

        # Hash each root directory name, so that the creation of new
        # directories also alters the hash
        hasher.update(root.encode('utf-8'))

        for fil in keep(files, ignore_patterns, prefix):
            local_path = root + '/' + fil # relative to current directory
            # Hash the name of the file (because empty files and the
            # renaming of a file should alter the hash).
            hasher.update(fil.encode('utf-8'))
            # Hash the content of the file
            with open(local_path, 'rb') as fp:
                for chunk in iter(lambda: fp.read(4096), b''):
                    hasher.update(chunk)
    return hasher.hexdigest()

@login_required
@config_required
def push(track_event=True, watch=False, app_id=None):
    # Request the correct bundler URL from siphon-web
    puts(colored.green('Preparing to push your local files...'))
    conf = Config()
    auth = Auth()
    siphon = Siphon(auth.auth_token)

    if app_id is None:
        app_id = conf.app_id

    if track_event:
        event_properties = {'app_id': app_id, 'watch': watch}
        mixpanel_event(MIXPANEL_EVENT_PUSH, properties=event_properties)

    bundler_url = siphon.get_bundler_url(app_id, action='push')
    server_hashes = get_hashes(bundler_url)
    return post_archive(bundler_url, server_hashes)

class EventHandler(FileSystemEventHandler):
    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__(*args, **kwargs)
        self.project_hash = project_hash()

    def on_any_event(self, event):
        new_hash = project_hash()
        if self.project_hash != new_hash:
            puts(colored.green('--- Change detected ---'))
            self.project_hash = new_hash
            push(watch=True)
            puts(colored.yellow('Watching for changes... (ctrl-c to stop)'))

@config_required
def watch():
    # Users expect an implicit push
    push(watch=True)

    # Start the observer
    observer = PollingObserver()
    observer.event_queue.max_size = 1
    observer.schedule(EventHandler(), os.getcwd(), recursive=True)
    observer.start()
    puts(colored.yellow('Watching for changes... (ctrl-c to stop)'))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    # Block until the thread terminates
    observer.join()

def run(args=None):
    if args is None:
        args = []
    if '--help' in args:
        print_usage()
    elif len(args) > 0:
        if args[0] != '--watch':
            print_usage()
        else:
            watch()
    else:
        puts(colored.yellow('## This is a one-time push, try live ' \
            'reloading: siphon push --watch'))
        push()
