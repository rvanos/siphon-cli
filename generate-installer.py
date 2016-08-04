#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import argparse
import tarfile
import shutil

from siphon.cli.utils.system import make_temp_dir, bash, cd

from install_constants import (
    PYRUN_BINARIES_DIR,
    REPOS,
    TEMPLATES_DIR,
    INSTALLER_FILE,
    SOURCE_FILE,
    CLI_DIR,
    INCLUDE_ROOT_FILES,
    INCLUDE_ROOTS
)

def add_repo_to_archive(repo, commit, name, tar_archive, directories=(),
                        files=(), prefix=''):
    with make_temp_dir() as tmp:
        with cd(tmp):
            print('Cloning %s into %s' % (name, tmp))
            bash('git clone %s' % repo)
            bash('cd %s && git checkout %s' % (name, commit))
        for f in files:
            relative_path = os.path.join(name, f)
            src = os.path.join(tmp, relative_path)
            tar_path = os.path.join(prefix, f)
            tar_archive.add(src, tar_path)
        for d in directories:
            relative_path = os.path.join(name, d)
            src = os.path.join(tmp, relative_path)
            tar_path = os.path.join(prefix, d)
            tar_archive.add(src, tar_path, recursive=True)

def make_installer_file(version=None, host=None, port=None,
                        static_host=None, static_port=None,
                        dest=None, remote_path=None):
    assert None not in (version, host, port, static_host, static_port,
                        dest, remote_path)
    src_fil = os.path.join(TEMPLATES_DIR, 'posix.sh')
    dest_fil = os.path.join(dest, INSTALLER_FILE)

    # Where the installer script can download the source/binaries
    remote_binaries_path = '%s:%s%s' % (static_host, static_port, remote_path)
    remote_source_path = '%s:%s%s/%s' % (static_host, static_port, remote_path,
        SOURCE_FILE)

    s = open(src_fil).read()
    s = s.replace('{{host}}', host)
    s = s.replace('{{port}}', str(port))
    s = s.replace('{{static_host}}', static_host)
    s = s.replace('{{static_port}}', str(static_port))
    s = s.replace('{{version}}', version)
    s = s.replace('{{remote_source_path}}', remote_source_path)
    s = s.replace('{{remote_binaries_path}}', remote_binaries_path)
    s = s.strip()

    print('Writing: %s' % dest_fil)
    with open(dest_fil, 'w') as fp:
        fp.write(s)

def make_source_file(dest=None):
    assert None not in (dest,)
    paths = []
    for root, dirs, files in os.walk(CLI_DIR):
        # Tidy up the prefix regardless of where this script is run from
        root = root.replace(CLI_DIR, '')
        if root.startswith('/'):
            root = root[1:]
        # Filter files in the root of the repository
        if root == '':
            paths += [fil for fil in files if fil in INCLUDE_ROOT_FILES]
        # Filter files within subdirectories
        else:
            if any([root.startswith(s) for s in INCLUDE_ROOTS]):
                paths += [os.path.join(root, fil) for fil in files
                          if not fil.endswith('.pyc') \
                          and not fil.endswith('.DS_Store')]

    source_file = os.path.join(dest, SOURCE_FILE)
    print('Writing: %s' % source_file)
    with tarfile.open(source_file, 'w:gz') as tf:
        # Write the siphon-cli files
        for path in paths:
            local_path = os.path.join(CLI_DIR, path)
            tf.add(local_path, path)
        # Write everything in lib/
        lib_dir = os.path.join(CLI_DIR, 'lib')
        for root, dirs, files in os.walk(lib_dir):
            for fil in files:
                local_path = os.path.join(root, fil)
                path = local_path.replace(lib_dir, '')[1:]
                tf.add(local_path, path)

        for r in REPOS:
            repo_info = REPOS[r]
            repo = repo_info['repo']
            repo_name = repo_info['repo_name']
            commit = repo_info['commit']
            directories = repo_info['directories']
            files = repo_info['files']
            root = repo_info['root']
            add_repo_to_archive(repo, commit, repo_name, tf, directories,
                                files, prefix=root)

def copy_pyrun_binaries(dest=None):
    assert None not in (dest,)
    for fil in os.listdir(PYRUN_BINARIES_DIR):
        if fil.endswith('.gz'):
            dest_fil = os.path.join(dest, fil)
            print('Writing: %s' % dest_fil)
            shutil.copy(os.path.join(PYRUN_BINARIES_DIR, fil), dest_fil)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', type=str)
    parser.add_argument('--version', type=str, help='Commit of siphon-cli.')
    parser.add_argument('--host', type=str, help='Django server hostname.')
    parser.add_argument('--port', type=int, help='Django server port.')
    parser.add_argument('--static-host', type=str,
                help='Static resource server hostname (defaults to --host).')
    parser.add_argument('--static-port', type=str,
                help='Static resource server port (defaults to --port).')
    parser.add_argument('--dest', type=str, help='Directory to store output.')
    parser.add_argument('--remote-path', type=str,
        help='Location where the source files can be found on the remote ' \
             'host and port, e.g. /static/installers')
    args = parser.parse_args()

    if not args.platform or not args.version or not args.host \
    or not args.port or not args.dest or not args.remote_path:
        parser.print_usage(file=sys.stderr)
        sys.exit(1)
    elif args.platform != 'posix':
        sys.stderr.write('Only the "posix" platform is current supported.\n')
        sys.exit(1)
    elif os.path.isfile(args.dest):
        sys.stderr.write('Destination is a file: %s\n' % args.dest)
        sys.exit(1)

    if not os.path.isdir(args.dest):
        print('Creating destination directory: %s' % args.dest)
        os.makedirs(args.dest)

    if args.static_host:
        static_host = args.static_host
    else:
        static_host = args.host

    if args.static_port:
        static_port = args.static_port
    else:
        static_port = args.port

    make_installer_file(
        version=args.version,
        host=args.host,
        port=args.port,
        static_host=static_host,
        static_port=static_port,
        dest=args.dest,
        remote_path=args.remote_path
    )

    make_source_file(dest=args.dest)
    copy_pyrun_binaries(dest=args.dest)
    print('Done.')
