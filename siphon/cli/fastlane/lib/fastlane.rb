#!/usr/bin/env ruby

# Add siphon's fastlane tools so they can be exported
require 'fileutils'
require 'fastlane_core'
require 'spaceship'
require_relative 'fastlane/constants'
require_relative 'fastlane/certificate'
require_relative 'fastlane/utils'
require_relative 'fastlane/device'
require_relative 'fastlane/profile'

module Fastlane
  Helper = FastlaneCore::Helper
end
