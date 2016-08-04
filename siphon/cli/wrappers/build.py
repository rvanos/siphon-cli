
import os
import re
import shutil
import tarfile

from siphon.cli.constants import SIPHON_TMP
from siphon.cli.wrappers.cache import Cache

from siphon.cli.utils.system import cleanup_dir, ensure_dir_exists

class Build(object):
    """
    A wrapper for siphon-build-<app_id>-<base_version> temp directory.
    """
    def __init__(self, app_id, base_version, dev_mode=False):
        self.app_id = app_id
        self.base_version = base_version
        self.build_id = 'build-%s-%s' % (self.app_id, self.base_version)
        self.directory = os.path.join(SIPHON_TMP, self.build_id)
        self.dev_mode = dev_mode
        self.archive_dir = os.path.join(self.directory, 'archives')

    def project_dir(self, platform='ios'):
        return os.path.join(self.directory, 'base-project', platform)

    def archive_dir_path(self, device_name, os_version=None, platform='ios'):
        if os_version:
            archive_dir_name = 'archive-%s-%s-%s' % (device_name,
                                                     platform, os_version)
        else:
            archive_dir_name = 'archive-%s-%s' % (device_name, platform)

        if self.dev_mode:
            archive_dir_name = '%s-%s' % (archive_dir_name, 'dev')
        archive_dir_name = '%s-%s' % (archive_dir_name, os.environ['SP_HOST'])
        archive_path = os.path.join(self.archive_dir, archive_dir_name)
        return archive_path

    def archived(self, device_name, os_version=None, platform='ios'):
        """
        Returns True if an archive exists for a given app; False otherwise.
        """
        arch_dir = self.archive_dir_path(device_name, os_version, platform)
        arch_path = os.path.join(
            arch_dir,
            'archive.xcarchive'
        )

        if os.path.exists(arch_path):
            return True
        else:
            return False

    def ensure_build_dir(self):
        ensure_dir_exists(self.directory)
        build_contents = os.listdir(self.directory)
        if not build_contents:
            tf = tarfile.open(Cache.base_package_path(self.base_version),
                              'r:gz')
            tf.extractall(self.directory)

    def clean_archive(self, sim_name, os_version=None, platform='ios'):
        """ Remove a specific archive directory if it exists """
        arch_dir = self.archive_dir_path(sim_name, os_version, platform)
        cleanup_dir(arch_dir)

    def clean_archives(self):
        """ Remove the archives directory if it exists """
        cleanup_dir(self.archive_dir)

    def clean_builds(self):
        """ Remove all build directories for a given app """
        tmp = SIPHON_TMP
        ensure_dir_exists(tmp)
        regex = 'build-%s-[0-9]+.[0-9]+' % self.app_id
        build_dirs = [os.path.join(tmp, f) for f in os.listdir(tmp)
                      if re.search(regex, f)]
        for b in build_dirs:
            shutil.rmtree(b)
