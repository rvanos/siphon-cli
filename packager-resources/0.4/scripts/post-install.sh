#!/bin/bash

# A patch for node-haste that allows our packager to find the Siphon-supplied
# node_modules
cp ResolutionRequest.js node_modules/react-native/node_modules/node-haste/lib/DependencyGraph/ResolutionRequest.js
