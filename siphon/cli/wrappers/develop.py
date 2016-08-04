
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

from siphon.cli.utils.node import node_cmd, npm_cmd
from siphon.cli.utils.system import cd, background_process, ensure_dir_exists
from siphon.cli.utils.watchman import local_watchman_dir
from siphon.cli.utils.input import yn
from siphon.cli.constants import PACKAGER_RESOURCES
from siphon.cli.constants import SIPHON_TMP


def packager_dependencies(version):
    """
    Returns a dictionary of module_name: version pairs.
    """
    pkg_path = os.path.join(PACKAGER_RESOURCES, version, 'package.json')

    with open(pkg_path, 'r') as f:
        deps = json.loads(f.read())['dependencies']

    return deps

class DevelopDir(object):
    """
    A wrapper for the 'develop' directory. This contains the relevant
    version of React Native for a given base version and the corresponding
    bundled dependencies. Project files are symlinked here to be used with
    the packager.
    """
    def __init__(self, base_version):
        self.base_version = base_version
        self.directory = os.path.join(SIPHON_TMP, self._dir_name())

    def _dir_name(self):
        # Of the form develop-<base_version>-<node_modules_version_hash>
        dep_id = self._dependencies_id()
        dir_name = 'develop-%s-%s' % (self.base_version, dep_id)
        return dir_name

    def _dependencies_id(self):
        # Concatenates the version of each node module required for
        # the given base version and returns a hash of the string
        dependencies = packager_dependencies(self.base_version)
        dep_names = sorted(list(dependencies.keys()))
        dep_versions = ''
        for d in dep_names:
            dep_versions += dependencies[d]
        hashed = hashlib.md5(dep_versions.encode()).hexdigest()
        return hashed

    def ensure_develop_dir(self):
        ensure_dir_exists(self.directory)
        # Make sure that the entry script is copied over
        scripts_dir = os.path.join(PACKAGER_RESOURCES, self.base_version,
                                   'scripts')
        scripts = os.listdir(scripts_dir)
        for s in scripts:
            src = os.path.join(scripts_dir, s)
            dest = os.path.join(self.directory, s)
            shutil.copyfile(src, dest)

        # We make sure that the required node modules are installed
        modules_installed = True
        dependencies = packager_dependencies(self.base_version)
        required_modules = list(dependencies.keys())
        try:
            modules_dir = os.path.join(self.directory, 'node_modules')
            node_modules = os.listdir(modules_dir)

            if not set(node_modules) >= set(required_modules):
                modules_installed = False
        except OSError:
            modules_installed = False

        if not modules_installed:
            proceed = yn('We need to download some dependencies. ' \
                         'This may take a few minutes. Proceed? [Y/n] ')
            if not proceed:
                sys.exit(1)
            with cd(self.directory):
                try:
                    npm = npm_cmd(self.base_version)
                    # We want to install react-native first so peer
                    # dependencies are met
                    required_modules.insert(0, required_modules.pop( \
                        required_modules.index('react-native')))
                    for m in required_modules:
                        version = dependencies[m]
                        is_repo = 'http' in version
                        print('Downloading %s...' % m)
                        if is_repo:
                            p = background_process('%s install %s' % \
                                               (npm, version),
                                               spinner=True)
                        else:
                            p = background_process('%s install ' \
                                               '%s@%s' % (npm, m, version),
                                               spinner=True)
                        out, err = p.communicate()
                        if p.returncode != 0:
                            print(err.decode())
                            sys.exit(1)
                    # Run the associated post-install script if it exists
                    if os.path.isfile('post-install.sh'):
                        print('Running postinstall script...')
                        background_process('sh post-install.sh',
                                           spinner=True)
                except KeyboardInterrupt:
                    sys.exit(1)

    def clean_old(self):
        """ Remove old develop directories for this version if they exist """
        try:
            tmp = SIPHON_TMP
            regex = 'develop-%s-\w+' % self.base_version
            dev_dirs = [os.path.join(tmp, f) for f in os.listdir(tmp)
                       if re.search(regex, f)]

            for d in dev_dirs:
                if d != self.directory:
                    print('Dependencies updated. Removing old ones...')
                    shutil.rmtree(d)
        except FileNotFoundError:
            pass

    def start_packager(self, project_path, global_watchman=False):
        """ Start the packager and return the process """
        cmd = [node_cmd(self.base_version)]
        cmd.append(os.path.join(self.directory))
        cmd.append('--project-path')
        cmd.append(project_path)
        env = os.environ.copy()
        local_watchman = local_watchman_dir()
        if local_watchman and not global_watchman:
            # We add the path of the local watchman directory to front of PATH
            env['PATH'] = '%s:%s' % (local_watchman, env['PATH'])
        else:
            print('Using a global installation of watchman if one exists.')
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
        return p
