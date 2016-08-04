
module Fastlane
  class Certificate

    def ensure_certificates
      ENV["CERT_KEYCHAIN_PATH"] = File.expand_path(Dir["#{Dir.home}/Library/Keychains/login.keychain"].last)
      FileUtils.mkdir_p(IOS_CACHE_PATH)
      cert_path = find_existing_cert
      should_create = cert_path.nil?
      return unless should_create

      if create_certificate # no certificate here, creating a new one
          return # success
      else
        Utils.error_msg("Something went wrong when trying to create a new certificate...")
      end
    end

    def find_existing_cert
      certificates.each do |certificate|
        unless certificate.can_download
          next
        end

        path = store_certificate(certificate)
        private_key_path = File.expand_path(File.join(IOS_CACHE_PATH, "#{certificate.id}.p12"))

        if FastlaneCore::CertChecker.installed?(path)
          # This certificate is installed on the local machine
          ENV["CER_CERTIFICATE_ID"] = certificate.id
          ENV["CER_FILE_PATH"] = path

         Utils.success_msg("Found the certificate #{certificate.id} (#{certificate.name}) which is installed on the local machine. Using this one.")

          return path
        elsif File.exist?(private_key_path)
          keychain_import_file(private_key_path)
          keychain_import_file(path)

          ENV["CER_CERTIFICATE_ID"] = certificate.id
          ENV["CER_FILE_PATH"] = path

          Utils.success_msg("Found the cached certificate #{certificate.id} (#{certificate.name}). Using this one.")

          return path
        else
          Utils.error_msg("Certificate #{certificate.id} (#{certificate.name}) can't be found on your local computer")
        end

        File.delete(path) # as apparantly this certificate is pretty useless without a private key
      end

      puts "Couldn't find an existing certificate... creating a new one"
      return nil
    end

    # Development certificates
    def certificates
      cert = Spaceship.certificate.development
      cert.all
    end

    def keychain_import_file(path)
      Utils.error_msg("Could not find file '#{path}'") unless File.exist?(path)
      keychain = File.expand_path(Dir["#{Dir.home}/Library/Keychains/login.keychain"].last)

      command = "security import #{path.shellescape} -k '#{keychain}'"
      command << " -T /usr/bin/codesign" # to not be asked for permission when running a tool like `gym`
      command << " -T /usr/bin/security"

      Helper.backticks(command)
    end

    def create_certificate
      # Create a new certificate signing request
      csr, pkey = Spaceship.certificate.create_certificate_signing_request

      # Use the signing request to create a new distribution certificate
      begin
        certificate = Spaceship.certificate.development.create!(csr: csr)
      rescue => ex
        if ex.to_s.include?("You already have a current")
          Utils.error_msg("Could not create another certificate, reached the maximum number of available certificates.")
        end

        raise ex
      end

      # Store all that onto the filesystem
      request_path = File.expand_path(File.join(IOS_CACHE_PATH, "#{certificate.id}.certSigningRequest"))
      File.write(request_path, csr.to_pem)

      private_key_path = File.expand_path(File.join(IOS_CACHE_PATH, "#{certificate.id}.p12"))
      File.write(private_key_path, pkey)

      cert_path = store_certificate(certificate)

      # Import all the things into the Keychain
      keychain_import_file(private_key_path)
      keychain_import_file(cert_path)

      # Environment variables for the fastlane action
      ENV["CER_CERTIFICATE_ID"] = certificate.id
      ENV["CER_FILE_PATH"] = cert_path

      Utils.success_msg("Successfully generated #{certificate.id} which was imported to the local machine.")

      return cert_path
    end

    def store_certificate(certificate)
      path = File.expand_path(File.join(IOS_CACHE_PATH, "#{certificate.id}.cer"))
      raw_data = certificate.download_raw
      File.write(path, raw_data)
      return path
    end
  end
end
