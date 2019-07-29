require 'sketchup.rb'

if( not file_loaded?( "DeadlineSketchUpClient.rb" ) )
    menu = UI.menu( "Plugins" )
    menu.add_separator
    menu.add_item( "Submit To Deadline" ) { SubmitSketchUpToDeadline.new }
end
file_loaded( "DeadlineSketchUpClient.rb" )

class SubmitSketchUpToDeadline

    def initialize
        submit_to_deadline
    end

    def is_mac
        if Sketchup.version.to_i < 14
            (/darwin/ =~ RUBY_PLATFORM) != nil
        else
            Sketchup.platform == :platform_osx
        end
    end

    def is_windows
        if Sketchup.version.to_i < 14
            (/cygwin|mswin|mingw|bccwin|wince|emx/ =~ RUBY_PLATFORM) != nil
        else
            Sketchup.platform == :platform_win
        end
    end

    def get_repository_path
        deadline_bin = ""
        begin
            deadline_bin = ENV['DEADLINE_PATH']
        rescue
            deadline_bin = ""
        end
        
        if deadline_bin == "" || deadline_bin == nil
            # On OSX, if the env variable doesn't exist we look for the DEADLINE_PATH file.
            if is_mac and File.file?( "/Users/Shared/Thinkbox/DEADLINE_PATH" )
                deadline_bin = IO.read( "/Users/Shared/Thinkbox/DEADLINE_PATH" ).chomp
            end
        end
        
        if Sketchup.version.to_i < 14 # as of SU2014 release, the return value from the commandline doesn't seem to be working
            $deadline_command = File.join( deadline_bin, "deadlinecommand" )
        else
            $deadline_command = File.join( deadline_bin, "deadlinecommandbg" )
        end

        if Sketchup.version.to_i < 14 # TODO: CHECK IF SHELL COMMANDS ARE STILL A PROBLEM (test deadlinecommand (not bg) from within SketchUp)
            @path = %x(\"#{$deadline_command}\" -getrepositoryfilepath scripts/Submission/SketchUpSubmission.py) # Executes from the shell NEEDS TO BE TESTED
        else
            temp_dir = Sketchup.temp_dir #2014+ only
            exit_file = File.join( temp_dir, "deadline_exit.txt" )
            output_file = File.join( temp_dir, "deadline_output.txt" )
            %x(\"#{$deadline_command}\" -outputfiles \"#{output_file}\" \"#{exit_file}\" -getrepositoryfilepath scripts/Submission/SketchUpSubmission.py) #sends command from shell
            @path = IO.read( output_file ).chomp
        end

        puts @path
        @path = @path.sub( "\n", "" ).sub( "\r", "" )
        return @path
    end

    def submit_to_deadline
        path = get_repository_path
        if path != ""
            puts "Running script \"#{path}\""
            scene = Sketchup.active_model.path
            version = Sketchup.version.to_i # ignores after decimal. no need to floor
            
            currentPage = Sketchup.active_model.pages.selected_page
            pageName = ""
            if currentPage != nil
                pageName = currentPage.name
            end

            if version > 8
                version = "20#{version}" #Sketchup changed naming conventions for their version released in 2013... bleh
            end

            begin
                # Send command from shell.
                if is_mac
                    %x(\"#{$deadline_command}\" -ExecuteScript \"#{path}\" \"#{scene}\" #{version} \"#{pageName}\")
                else # windows
                    system("start \"\" " + "\"#{$deadline_command}\" -ExecuteScript \"#{path}\" \"#{scene}\" #{version} \"#{pageName}\"")
                end
            rescue
                puts "Error: The SketchUpSubmission.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository."
            end
        else
            puts "Error: The SketchUpSubmission.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository."
        end
    end
end
