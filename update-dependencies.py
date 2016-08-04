#!/usr/bin/env python3

import os
from termcolor import colored

from siphon.cli.constants import PACKAGER_RESOURCES
from siphon_dependencies import Dependencies

def main():
    versions = os.listdir(PACKAGER_RESOURCES)
    latest_version = sorted(versions)[-1]
    print(colored('Fetching latest dependencies...', 'yellow'))
    dependencies = Dependencies(latest_version)
    pkg_path = os.path.join(PACKAGER_RESOURCES,
                            dependencies.version, 'package.json')
    dependencies.update_package_file(pkg_path)

if __name__ == '__main__':
    main()
