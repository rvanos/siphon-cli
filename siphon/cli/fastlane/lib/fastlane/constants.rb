
module Fastlane
  HOME_PATH = ENV['HOME']
  CACHE_PATH = File.join(HOME_PATH, '.siphon/cache')
  IOS_CACHE_PATH = File.join(CACHE_PATH, 'ios')
  PROVISIONING_PROFILE_NAME = 'Siphon Dev'
end
