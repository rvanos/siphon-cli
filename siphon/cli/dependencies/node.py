import os
import shutil
import sys
import tarfile
from siphon.cli.utils.download import download_file, format_size
from siphon.cli.utils.download import get_download_size
from siphon.cli.utils.input import yn
from siphon.cli.utils.node import node_cmd
from siphon.cli.utils.platform import get_platform_name, PLATFORM_DARWIN
from siphon.cli.utils.system import ensure_dir_exists
from siphon.cli.constants import NODE_DESTINATION, NODE_BINARIES
from siphon.cli import SiphonClientException

from clint.textui import colored, puts

def move_contents_to_parent(dir):
    # Move the contents of a directory up one level
    contents = os.listdir(dir)
    parent = os.path.dirname(dir)
    for f in contents:
        file_path = os.path.join(dir, f)
        dest_path = os.path.join(parent, f)
        shutil.move(file_path, dest_path)

def ensure_node(version):
    if not node_cmd(version):
        # Neither a valid global or siphon installation was found, so we
        # must download the correct binary.
        version_exists = NODE_BINARIES.get(version)
        if not version_exists:
            puts(colored.red('Base version not supported. Please set ' \
                 'the "base_version" value in your app\'s Siphonfile to one ' \
                 'of the following: '))

            for k in reversed(sorted(list(NODE_BINARIES.keys()))):
                print(k)
            sys.exit(1)

        if get_platform_name() != PLATFORM_DARWIN:
            raise SiphonClientException('Node not supported on platform.')

        url = NODE_BINARIES[version]['darwin-64']['url']
        node_size = format_size(get_download_size(url))
        proceed = yn('We need to download Node.js & npm (we won\'t override ' \
                    'any current installations you may have). ' \
                    'These are required to run the packager and download ' \
                    'any dependencies we need. Download? (%s) ' \
                    '[Y/n] ' % node_size)

        if not proceed:
            sys.exit(1)
        version_dest = os.path.join(NODE_DESTINATION, version)
        ensure_dir_exists(version_dest)
        dest = os.path.join(version_dest, os.path.basename(url))
        download_file(url, dest, 'Downloading Node.js & npm...')
        print('Installing node...')
        tf = tarfile.open(dest, 'r:gz')
        content_dir = os.path.join(version_dest,
                  NODE_BINARIES[version]['darwin-64']['content'])
        tf.extractall(version_dest)
        move_contents_to_parent(content_dir)
        print('Installation successful.')
