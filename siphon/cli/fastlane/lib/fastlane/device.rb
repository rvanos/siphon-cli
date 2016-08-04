
require 'readline'

module Fastlane
  class Device
    def ensure_device(udid)
      puts "Checking device..."
      if is_registered(udid)
        Utils.success_msg "Device is registered"
      else
        register_device(udid)
      end
    end

    def is_registered(udid)
      # Get the registered iPhones & iPads and check if a device with the
      # given udid is registered
      registered_iphones =  Spaceship::Device.all_iphones
      registered_ipads = Spaceship::Device.all_ipads
      registered_devices = registered_iphones + registered_ipads

      registered_devices.each do |device|
        if device.udid == udid
          return true
        end
      end

      return false
    end

    def register_device(udid)
      prompt =  "We need to register your device. Please enter a name for the " \
                "device (this may be anything you like). "
      puts prompt

      device_name = Utils.get_user_input("Device name: ")
      Spaceship::Device.create!(name: device_name, udid: udid)
    end
  end
end
