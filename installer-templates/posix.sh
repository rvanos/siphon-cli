#!/bin/bash
set -e

export INSTALL_BASE="/usr/local"
export INSTALL_PATH="$INSTALL_BASE/siphon-cli"
export BIN_BASE="/usr/local/bin"
export BIN_PATH="$BIN_BASE/siphon"

export VERSION="{{version}}"
export REMOTE_SOURCE_PATH="{{remote_source_path}}"
export REMOTE_BINARIES_PATH="{{remote_binaries_path}}"
export SP_HOST="{{host}}"
export SP_PORT="{{port}}"
export SP_STATIC_HOST="{{static_host}}"
export SP_STATIC_PORT="{{static_port}}"

print_error() {
    RED='\033[0;31m'
    NC='\033[0m' # normal
    printf "${RED}$1${NC}\n" >&2
}

print_info() {
    YELLOW='\e[0;33m'
    NC='\033[0m' # normal
    printf "${YELLOW}$1${NC}\n"
}

check_permissions() {
    if ! [ -w "$INSTALL_BASE" ] || ! [ -w "$BIN_BASE" ]; then
        export SUDO_PREFIX="sudo"
        if ! sudo -n whoami; then
            print_info "\nThe installer needs to copy files to $INSTALL_BASE, please enter your administrator password to continue:"
            sudo whoami > /dev/null
        fi
    else
        export SUDO_PREFIX=""
    fi

    if ! [ -w "$BIN_BASE" ]; then
        echo "   Directory $BIN_BASE does not exist, creating it..."
        ${SUDO_PREFIX} mkdir -p $BIN_BASE
    fi
}

which_pyrun_archive() {
    IS_X86_64=0
    if uname -a | grep x86_64 > /dev/null; then
        IS_X86_64=1
    fi

    IS_DARWIN=0
    if uname | grep Darwin > /dev/null; then
        IS_DARWIN=1
    fi

    if [ $IS_DARWIN = 1 ] && [ $IS_X86_64 = 1 ]; then
        echo "pyrun3.4-mac-64.gz"
    elif [ $IS_DARWIN = 1 ] && [ $IS_X86_64 = 0 ]; then
        echo "pyrun3.4-mac-32.gz"
    elif [ $IS_DARWIN = 0 ] && [ $IS_X86_64 = 1 ]; then
        echo "pyrun3.4-linux-64.gz"
    else
        echo "pyrun3.4-linux-32.gz"
    fi
}

install_siphon() {
    echo "-> Loading the Siphon CLI installer..."
    echo "   Version: $VERSION"
    echo "   Installation path: $INSTALL_PATH"
    echo "   Executable: $BIN_PATH"
    echo "   Host: $SP_HOST:$SP_PORT"

    # We need a temporary directory in which to download our gubbins
    if [ "$(uname)" = "Darwin" ]; then
        export TMP_DEST=`mktemp -d -t siphon-cli.XXXXXX`
    else
        export TMP_DEST=`mktemp -d`
    fi

    # Fetch the source files
    echo "-> Fetching sources..."
    echo "   Remote sources: $REMOTE_SOURCE_PATH"
    echo "   Downloading into $TMP_DEST"
    curl -L "$REMOTE_SOURCE_PATH" | tar xz -C $TMP_DEST

    # Fetch the binary
    local PYRUN_ARCHIVE_NAME=$(which_pyrun_archive)
    local PYRUN_BINARY="$TMP_DEST/pyrun"
    local PYRUN_REMOTE_PATH="$REMOTE_BINARIES_PATH/$PYRUN_ARCHIVE_NAME"
    echo "-> Fetching binary..."
    echo "   Remote binary: $PYRUN_REMOTE_PATH"
    echo "   Downloading into $TMP_DEST"
    curl -L $PYRUN_REMOTE_PATH | gunzip > $PYRUN_BINARY

    echo "-> Checking permissions..."
    check_permissions

    # Remove the current installation and swap in our new one
    echo "-> Installing..."
    ${SUDO_PREFIX} rm -f $BIN_PATH
    if [ "$INSTALL_PATH" != "/" ]; then # just in case!
        ${SUDO_PREFIX} rm -rf $INSTALL_PATH
        ${SUDO_PREFIX} mv $TMP_DEST $INSTALL_PATH
        echo "   Installed into $INSTALL_PATH"
        echo "   Symlink installed at $BIN_PATH"

        # Make the install directory writable
        ${SUDO_PREFIX} chmod -R +w $INSTALL_PATH
    else
        print_error "   Problem with the installer. Please contact support."
        exit 1
    fi

    # Keep track of which version is installed
    ${SUDO_PREFIX} echo "$VERSION" > $INSTALL_PATH/version

    # Make sure PyRun is executable
    ${SUDO_PREFIX} chmod +x "$INSTALL_PATH/pyrun"

    # Add a script to make sure CLI is run with PyRun, not stock Python (we
    # will link to this script)
    ${SUDO_PREFIX} echo "#!/bin/bash" > $INSTALL_PATH/siphon-cli.sh
    ${SUDO_PREFIX} echo "$INSTALL_PATH/pyrun $INSTALL_PATH/siphon-cli.py \$@" >> $INSTALL_PATH/siphon-cli.sh
    ${SUDO_PREFIX} chmod +x $INSTALL_PATH/siphon-cli.sh

    # Special config module so that environment vars can be set
    ${SUDO_PREFIX} echo "HOST='$SP_HOST'" > $INSTALL_PATH/siphon_config.py
    ${SUDO_PREFIX} echo "PORT='$SP_PORT'" >> $INSTALL_PATH/siphon_config.py
    ${SUDO_PREFIX} echo "STATIC_HOST='$SP_STATIC_HOST'" >> $INSTALL_PATH/siphon_config.py
    ${SUDO_PREFIX} echo "STATIC_PORT='$SP_STATIC_PORT'" >> $INSTALL_PATH/siphon_config.py
    ${SUDO_PREFIX} echo "VERSION='$VERSION'" >> $INSTALL_PATH/siphon_config.py
    ${SUDO_PREFIX} echo "REMOTE_SOURCE='http://$REMOTE_SOURCE_PATH'" >> $INSTALL_PATH/siphon_config.py

    # Puts the siphon command in $PATH
    ${SUDO_PREFIX} chmod +x "$INSTALL_PATH/siphon-cli.py"
    ${SUDO_PREFIX} ln -s "$INSTALL_PATH/siphon-cli.sh" $BIN_PATH

    # Test that the siphon executable works
    echo "-> Checking the installation..."
    if siphon --init-installation > /dev/null; then
        echo "   OK."
        printf "\nSiphon CLI was successfully installed. To create an app:\n\n   $ siphon create <my-new-app>\n\n"
        exit 0
    else
        print_error "   ERROR: Failed to locate the Siphon CLI executable. Please contact support."
        exit 1
    fi
}

install_siphon
