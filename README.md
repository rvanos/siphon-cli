
siphon-cli
==========

Command-line interface for Siphon.

**Note:** This codebase is compatible with Python 3.4 for compatibility with
PyRun.

Also note that third-party any dependencies (apart from those only needed to
run tests) should be copied in the `lib/` directory. They must be Python 3
compatible.

Running locally
---------------

The client can be run locally with a variety of configurations. The
configuration is added to in the `local-conf/` directory and supplied as the
first argument to the `run-local.sh` script:

    $ ./run-local.sh [config] [create|ls|push|play] [options]

Generating an installer script
------------------------------

To generate an installer suitable for users to download and run:

    $ ./generate-installer.py --platform posix --version <commit> \
        --host getsiphon.com --port 80 --remote-path /static/cli \
        --dest /some/output/directory

The only supported platform is currently `posix`, i.e. OS X and Linux. The
files are written at `--dest` and should be reachable using the given `--host`,
`--port` and `--remote-path`.

Updating node dependencies
------------------------------

When our siphon-dependencies repo is updated with the latest dependencies
for a given version (modules for sandbox and production environments),
client files need to be updated.

Ensure that Python 3.4 is installed:

    $ brew install python3

Download virtualenvwrapper to set up our Python 3.4 environment:

    $ pip install virtualenvwrapper
    $ export WORKON_HOME=~/.virtualenv # put this in your .bash_profile too
    $ mkdir -p $WORKON_HOME

Create a virtual environment and activate it:

    $ mkvirtualenv --python=`which python3` siphon-cli
    $ workon siphon-packager
    $ python --version # should be Python 3

To update relevant client files, install the developer python dependencies:

    $ pip install -r dev_requirements.txt

Make the update script executable:

    $ chmod +x ./update-dependencies.py

Finally, run the script:

    $ ./update-dependencies.py
