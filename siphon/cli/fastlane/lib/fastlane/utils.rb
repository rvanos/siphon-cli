
module Fastlane
  class Utils
    def self.success_msg(msg)
      # Note: Unix only
      puts "\e[32m#{msg}\e[0m"
    end

    def self.error_msg(msg)
      # Note: Unix only
      puts "\e[31m#{msg}\e[0m"
    end

    def self.login(username)
      puts "Starting login with user '%s'" % [username]
      Spaceship.login(username, nil)
      Spaceship.select_team
      success_msg("Successfully logged in")
    end

    def self.get_user_input(prompt)
      u_input = ""
      loop do
        u_input = Readline.readline(prompt).chomp
        if u_input =~ /^\s*$/
          error_msg "Input can not be empty."
        else
          break
        end
      end
      u_input
    end

  end
end
