
# Download/generate wildcard provisioning profiles
module Fastlane
  class Profile
    def ensure_profile
      profiles = fetch_profiles # download the profile if it's there

      if profiles.count > 0
        Utils.success_msg "Found #{profiles.count} matching profile(s)"
        profile = profiles.first

        # Make sure that the profile is up-to-date and includes all devices
        puts "Updating the profile to include all devices"
        profile.devices = Spaceship.device.all_for_profile_type(profile.type)

        profile = profile.update! # assign it, as it's a new profile
      else
        puts "No existing profiles found, that match the certificates you have installed, creating a new one for you"
        ensure_app_exists!
        profile = create_profile!
      end

      Utils.error_msg "Something went wrong fetching the latest profile" unless profile

      ENV.delete("SIGH_PROFILE_ENTERPRISE")
      tmp_path = download_profile(profile)
      install_downloaded(tmp_path)
    end

    def fetch_profiles
      puts "Fetching profiles..."
      results = Spaceship.provisioning_profile.Development.find_by_bundle_id("*").find_all(&:valid?)
      # Take the provisioning profile name into account
      filtered = results.select { |p| p.name.strip == PROVISIONING_PROFILE_NAME.strip }
      results = filtered

      return results.find_all do |a|
        # Also make sure we have the certificate installed on the local machine
        installed = false
        a.certificates.each do |cert|
          file = Tempfile.new('cert')
          file.write(cert.download_raw)
          file.close
          installed = true if FastlaneCore::CertChecker.installed?(file.path)
        end
        installed
      end
    end

    def install_downloaded(path)
      file_name = File.basename(path)
      output = File.join(File.expand_path(IOS_CACHE_PATH), file_name)
      begin
        FileUtils.mv(path, output)
      rescue
        # in case it already exists
      end

      install_profile(output)

      puts output.green

      return File.expand_path(output)
    end

    def install_profile(profile)
      udid = FastlaneCore::ProvisioningProfile.uuid(profile)
      ENV["SIGH_UDID"] = udid if udid

      FastlaneCore::ProvisioningProfile.install(profile)
    end

    # Downloads and stores the provisioning profile
    def download_profile(profile)
      puts "Downloading provisioning profile..."
      profile_name ||= "#{PROVISIONING_PROFILE_NAME.delete(' ')}.mobileprovision" # default name
      profile_name += '.mobileprovision' unless profile_name.include? 'mobileprovision'

      tmp_path = Dir.mktmpdir("profile_download")
      output_path = File.join(tmp_path, profile_name)
      File.open(output_path, "wb") do |f|
        f.write(profile.download)
      end

      Utils.success_msg "Successfully downloaded provisioning profile..."
      return output_path
    end

    def create_profile!
      cert = certificate_to_use
      bundle_id = "*"
      name = PROVISIONING_PROFILE_NAME

      if Spaceship.provisioning_profile.all.find { |p| p.name == name }
        Utils.error_msg "The name '#{name}' is already taken, using another one."
        name += " #{Time.now.to_i}"
      end

      puts "Creating new wildcard development provisioning profile with name '#{name}'"
      profile = Spaceship.provisioning_profile.Development.create!(name: name,
                                bundle_id: bundle_id,
                              certificate: cert)
      profile
    end

    # Certificate to use based on the current distribution mode
    # rubocop:disable Metrics/AbcSize
    def certificate_to_use
      certificates = Spaceship.certificate.development.all

      if certificates.count == 0
        Utils.error_msg "Could not find a matching code signing identity for #{profile_type}. Please contact support (hello@getsiphon.com)"
      end

      return certificates # development profiles support multiple certificates
    end

    def ensure_app_exists!
      return if Spaceship::App.find("*")
      Utils.error_msg "Could not find App with App Identifier '*'"
    end
  end
end
