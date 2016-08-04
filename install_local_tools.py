#!/usr/bin/env python
# -*- coding: utf-8 -*-

# For local testing/development:
# Install xctool locally in the tmp dir (if it doesn't exist already).
# We do this in python and not in bash so that we can use the same Configuration
# as the end user will without duplicating any vars (commit, file list etc).

import shutil
import os
import re
import tempfile
from distutils.dir_util import copy_tree
from siphon.cli.constants import SIPHON_TMP
from siphon.cli.utils.system import (
    bash,
    cd,
    ensure_dir_exists,
    copyfile,
    make_temp_dir,
)

from install_constants import (
    REPOS,
    LOCAL_ROOTS,
    FASTLANE_COMMIT_SUM,
)

def add_repo_to_directory(repo, commit, name, destination, directories=(),
                          files=()):
    with make_temp_dir() as tmp:
        with cd(tmp):
            print('Clone destination: %s' % tmp)
            bash('git clone %s' % repo)
            bash('cd %s && git checkout %s' % (name, commit))

            print('Copying required files & directories...')
            repo_base = os.path.join(tmp, name)
            for f in files:
                src_path = os.path.join(repo_base, f)
                dest_path = os.path.join(destination, f)
                # copyfile does not make intermediate directories if they do
                # not exist
                target_dir = os.path.dirname(dest_path)
                ensure_dir_exists(target_dir)
                copyfile(src_path, dest_path)

            for d in directories:
                src_path = os.path.join(repo_base, d)
                dest_path = os.path.join(destination, d)
                copy_tree(src_path, dest_path, preserve_symlinks=True)

def clean_old():
    # Looks for old installations in the temp directory and removes them
    tmp = tempfile.gettempdir()
    regex = 'siphon-(xctool|fastlane)-\w+'
    dirs = [os.path.join(tmp, f) for f in os.listdir(tmp)
            if re.search(regex, f)]
    for d in dirs:
        dir_name = d.split('/')[-1]
        current_xctool = LOCAL_ROOTS['xctool']
        current_fastlane = 'siphon-fastlane-%x' % FASTLANE_COMMIT_SUM
        if dir_name != current_xctool and dir_name != current_fastlane:
            shutil.rmtree(d)

def repo_installed(repo):
    tmp = SIPHON_TMP
    root = os.path.join(tmp, LOCAL_ROOTS[repo])
    for d in REPOS[repo]['directories']:
        dir_path = os.path.join(root, d)
        if not os.path.isdir(dir_path):
            return False
    for f in REPOS[repo]['files']:
        file_path = os.path.join(root, f)
        if not os.path.exists(file_path):
            return False
    return True

def main():
    """
    Ensures the that the correct version of xctool & fastlane
    are installed the tmp directory.
    """
    tmp = SIPHON_TMP

    for r in REPOS:
        dest = os.path.join(tmp, LOCAL_ROOTS[r])
        if not repo_installed(r):
            print('Installing %s...' % r)
            repo_info = REPOS[r]
            repo = repo_info['repo']
            repo_name = repo_info['repo_name']
            commit = repo_info['commit']
            directories = repo_info['directories']
            files = repo_info['files']
            add_repo_to_directory(repo, commit, repo_name, dest, directories,
                                  files)
    clean_old()

if __name__ == '__main__':
    main()
