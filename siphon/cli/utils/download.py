import os
import sys
import requests
import shutil
import tempfile
from io import BytesIO
from clint.textui import colored, puts, progress

from siphon.cli.utils.system import copyfile, ensure_dir_exists
from siphon.cli import SiphonCommandException


class ProgressReader(BytesIO):
    """ Credit: http://stackoverflow.com/a/14953090/3211027 """
    def __init__(self, buf):
        self._progress = 0
        self._len = len(buf)
        self._bar = None
        if self._len > 4096:
            self._bar = progress.Bar(filled_char='=', every=4096)
        BytesIO.__init__(self, buf)

    def read(self, n=-1):
        chunk = BytesIO.read(self, n)
        self._progress += len(chunk)
        if self._bar:
            self._bar.show(self._progress, count=self._len)
        return chunk

    def close(self):
        if self._bar:
            self._bar.done()
        BytesIO.close(self)


def format_size(size):
    # Takes bytes and returns a string formatted for humans
    units = ['', 'KB', 'MB', 'GB', 'TB']
    for unit in units:
        if abs(size) < 1024:
            if unit == '' or unit == 'KB':
                return '%i%s' % (size, unit)
            else:
                return '%3.1f%s' % (size, unit)
        size /= 1024.0
    return '> 1024 TB'

def get_download_size(url):
    try:
        # We don't want to download the package just yet
        response = requests.head(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print('GET: %s' % url)
        raise SiphonCommandException(str(e))
    size = response.headers.get('content-length')
    if not size:
        size = response.headers.get('Content-Length')
    if not response.ok or not size or not size.isdigit():
        raise SiphonCommandException('Bad response from server. ' \
                'Please try again later.')
    return int(size)

def download_file(url, destination, download_msg=None):
    if not destination[0] == '/':
        destination = os.path.join(os.getcwd(), destination)

    response = requests.get(url, stream=True, timeout=(10, None))
    content_length = response.headers.get('content-length')

    if not response.ok:
        err = 'Could not download file %s (server responded with status ' \
              'code %s)' % (url, response.status_code)
        response.close()
        raise SiphonCommandException(err)

    tmp = tempfile.mkdtemp()
    tmp_dest = os.path.join(tmp, os.path.basename(destination))
    try:
        with open(tmp_dest, 'w+b') as f:
            if download_msg:
                puts(colored.yellow(download_msg))

            if not content_length:
                f.write(response.content)
                return
            else:
                content_length = int(content_length)

            progress = 0
            bar_width= 50 # Length in chars

            for data in response.iter_content(chunk_size=1024):
                progress += len(data)
                f.write(data)
                percentage = round((progress / content_length) * 100, 1)
                bar = int(bar_width * (progress / content_length))
                stats = '%s%% (%s/%s)' % (percentage, format_size(progress),
                                                      format_size(content_length))
                # Include spaces at the end so that if the stat string shortens
                # previously printed text isn't visible
                sys.stdout.write('\r[%s%s] %s ' % ('=' * bar,
                                                    ' ' * (bar_width - bar),
                                                    stats))
                sys.stdout.flush()
        response.close()
        dest_dir = os.path.dirname(destination)
        ensure_dir_exists(dest_dir)
        copyfile(tmp_dest, destination)
        puts(colored.green('\nDownload complete.'))
    except KeyboardInterrupt:
        puts(colored.red('\nDownload interrupted.'))
        raise
    finally:
        shutil.rmtree(tmp)
        response.close()
