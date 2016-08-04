#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONF_DIR="/local-conf"
LIB="/lib"
CLI="/siphon-cli.py"
INSTALL_LOCAL_TOOLS="/install_local_tools.py"
IOS_DEPLOY="/lib/ios-deploy"
CONF_PATH=$DIR$CONF_DIR/$1
WATCHMAN_DIR="TRUE"

# Extract our environment variables from the config
if [ -z $1 ] || [ ! -e $CONF_PATH ]
  then
    echo "Config '$1' not found in $DIR$CONF_DIR"
    exit 1
fi

source $CONF_PATH

# Remove any old versions of pyrun that we've put in temp
find $TMPDIR -type f -name 'siphon_pyrun3.4*' -delete

# We extract the PyRun executable to temp file each time
TEMP_PYRUN=`mktemp -t siphon_pyrun3.4`
gunzip -c $DIR/pyrun-binaries/pyrun3.4-mac-64.gz > $TEMP_PYRUN
chmod +x $TEMP_PYRUN

# Ensure that the version of xctool that the client will use is installed
(cd $DIR && $TEMP_PYRUN $DIR$INSTALL_LOCAL_TOOLS)

IOS_DEPLOY_PATH=$DIR$IOS_DEPLOY

# Get the location of the xctool install
XCTOOL_PATH=$(
cd $DIR && PYTHONPATH=$DIR$LIB $TEMP_PYRUN - <<EOF
import os
from install_constants import LOCAL_ROOTS
from siphon.cli.constants import SIPHON_TMP

print(os.path.join(SIPHON_TMP, LOCAL_ROOTS['xctool'], 'xctool.sh'))
EOF
)

FASTLANE_DIR=$(
cd $DIR && PYTHONPATH=$DIR$LIB $TEMP_PYRUN - <<EOF
import os
from install_constants import LOCAL_FASTLANE
from siphon.cli.constants import SIPHON_TMP

print(os.path.join(SIPHON_TMP, LOCAL_FASTLANE))
EOF
)

run_cli() {
    PYTHONPATH=$DIR$LIB \
    SP_LOCAL_CLI=1 \
    SP_HOST=$SP_HOST \
    SP_PORT=$SP_PORT \
    SP_SCHEME=$SP_SCHEME \
    SP_STATIC_HOST=$SP_STATIC_HOST \
    SP_STATIC_PORT=$SP_STATIC_PORT \
    SP_STATIC_SCHEME=$SP_STATIC_SCHEME \
    SP_REMOTE_SOURCE=$SP_REMOTE_SOURCE \
    IOS_DEPLOY_PATH=$IOS_DEPLOY_PATH \
    XCTOOL_PATH=$XCTOOL_PATH \
    FASTLANE_DIR=$FASTLANE_DIR \
    WATCHMAN_DIR=$WATCHMAN_DIR \
    $TEMP_PYRUN $DIR$CLI ${@:2}
}

run_cli $@
rm $TEMP_PYRUN
