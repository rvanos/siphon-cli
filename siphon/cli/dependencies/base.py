import sys

from siphon.cli.wrappers import Auth, Build, Cache, Config, Siphon

from siphon.cli.utils.download import download_file, format_size
from siphon.cli.utils.input import yn

from clint.textui import colored, puts

def ensure_base(version):
    # Make sure that the correct siphon-base package is installed for this
    # base version; if not, install it. Returns the location of the
    # base project.
    auth = Auth()
    conf = Config()
    siphon = Siphon(auth.auth_token)
    build = Build(conf.app_id, version)
    pkg_url = siphon.base_package_url(version)
    pkg_dest = Cache.base_package_path(version)

    puts(colored.yellow('Checking for required packages...'))
    content_length = siphon.content_length_for_version(version)

    if Cache.base_package_installed(version):
        cached_content_length = Cache.get_length_for_base_version(version)
        if content_length != cached_content_length:
            update_msg = 'Siphon needs to update some files in order to run ' \
                         'your app (%s). Proceed? ' \
                         '[Y/n]: ' % format_size(content_length)
            update = yn(update_msg)

            if not update:
                sys.exit(1)

            msg = 'Updating Siphon files for base version %s...' % version
            try:
                download_file(pkg_url, pkg_dest, msg)
                Cache.set_length_for_base_version(version, content_length)
            except KeyboardInterrupt:
                sys.exit(1)
            # Get rid of the old build dirs (they are now invalid)
            build.clean_builds()

    else:
        download_msg = 'Siphon needs to download some files in order to run ' \
                       'your app (%s). This will not be ' \
                       'required again unless an update is needed, or a ' \
                       'different base version is specified in ' \
                       'the Siphonfile of one of your apps. Proceed? ' \
                       '[Y/n]: ' % format_size(content_length)
        download = yn(download_msg)

        if not download:
            sys.exit(1)

        msg = 'Downloading compatibility files for base version ' \
            '%s...' % version
        try:
            download_file(pkg_url, pkg_dest, msg)
        except KeyboardInterrupt:
            sys.exit(1)
        Cache.set_length_for_base_version(version, content_length)
        build.clean_builds()
    build.ensure_build_dir()
