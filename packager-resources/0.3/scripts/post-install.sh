#!/bin/bash

# Deduplicate fbjs modules (https://gist.github.com/jrichardlai/a6a36352e1b98eb2946a)
# There is a problem with this module causing naming collisions in the
# packager (RN 0.18)
find node_modules/react-native -name 'fbjs' -print | grep "\./node_modules/fbjs" -v | xargs rm -rf
find node_modules/react -name 'fbjs' -print | grep "\./node_modules/fbjs" -v | xargs rm -rf
