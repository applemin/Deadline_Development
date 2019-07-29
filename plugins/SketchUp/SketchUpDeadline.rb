require 'sketchup.rb'

# exports job to different format (.3ds, etc.)
def render_model
	puts "SU_PROGRESS 0%"
	$output_path = File.join( $output_directory, $output_name + "#{$format}" )
	Sketchup.set_status_text( "Exporting 3d model to #{$output_path}" )
	begin
		$model.export( $output_path )
	rescue
		puts "Error: #{$!}"
		close_sketchup
	end
	puts "SU_PROGRESS 100%"
	puts "Finished exporting 3d model to #{$output_path}"
	close_sketchup
end


#render with vray 
def render_vray
	if is_win?
		$output_directory+="\\"
	else
		$output_directory+="\/"
	end

	$output_path = "" + $output_directory + $output_name + "#{$format}" + ""
	puts "Path: " + $output_path
	if vray_version >= 3
		scene = VRay::LiveScene.active
		scene["/SettingsOutput"][:img_file] = $output_path
		scene["/SettingsOutput"][:do_animation] = false
		scene["/SettingsOutput"][:img_width] = $width
		scene["/SettingsOutput"][:img_height] = $height
		scene.render
	else
		# V-Ray 2
		VRayForSketchUp.setOutputPath($output_path)
		VRayForSketchUp.setOutputSize($width, $height)
		VRayForSketchUp.launch_vray_render
	end
end

#render sequence with vray batch render
def render_vray_sequence
	if is_win?
		$output_directory+="\\"
	else
		$output_directory+="\/"
	end

	$output_path = "" + $output_directory + $output_name + "#{$format}" + ""
	puts "Path: " + $output_path
	if vray_version >= 3
		scene = VRay::LiveScene.active
		scene["/SettingsOutput"][:img_file] = $output_path
		scene["/SettingsOutput"][:do_animation] = true
		scene["/SettingsOutput"][:animation_time_segment] = 1 # Switches from "Entire Animation" to "Frame Range"
		scene["/SettingsOutput"][:frame_range_start] = $vray_start_frame
		scene["/SettingsOutput"][:frame_range_end] = $vray_end_frame
		scene["/SettingsOutput"][:img_width] = $width
		scene["/SettingsOutput"][:img_height] = $height
		scene.render
	else
		# V-Ray 2
		VRayForSketchUp.setOutputPath($output_path)
		VRayForSketchUp.setOutputSize($width, $height)
		VRayForSketchUp.launch_vray_batch_render
		close_sketchup
	end
end

# renders current view as image
def render_image
	puts "SU_PROGRESS 0%"
	$output_path = File.join( $output_directory, $output_name + "#{$format}" )
	Sketchup.set_status_text( "Exporting current view to #{$output_path}" )
	
	begin
		if not $scene_name == ""
			$page = $model.pages[ $scene_name ]
			$page.transition_time = 0
			$model.pages.selected_page = $page
		end
	rescue
		puts "Error: #{$!}"
		close_sketchup
	end
	
	begin
		if $use_vray == "True"
			render_vray
		else
			$view.write_image( $output_path, $width, $height, $anti_alias, $compression, $transparent )
		end
	rescue
		puts "Error: #{$!}"
		close_sketchup
	end
	
	puts "SU_PROGRESS 100%"
	puts "Finished exporting 2d image to #{$output_path}"
end

class AnimationExport
	def initialize
		@pages = $model.pages
		@default_transition_time = $model.options["PageOptions"]["TransitionTime"]
		@curr_page_index = 0
		@curr_page = @pages[@curr_page_index]
		@curr_page_start = 0.0
		@curr_page_transition = @curr_page.transition_time
		@curr_page_transition = @default_transition_time if @curr_page_transition == -1.0
		@curr_page_end = @curr_page_start + @curr_page_transition

		@curr_time = 0.0
		@delay = 1.0 / $frame_rate
		@frame = 1
		@total_frames = get_total_frames

		#start animation
		puts "Starting animation export..."
		Sketchup.active_model.active_view.animation = self
	end

	def get_total_frames
		puts "Getting total frames..."
		@total_time = 0.0
		for page in @pages
			if page.transition_time == -1.0
				@total_time += @default_transition_time
			else
				@total_time += page.transition_time
			end
		end

		return ( ( @total_time * $frame_rate ) + 1 ).to_i
	end

	def nextFrame(view) #stupid SketchUp method has to be overridden (ruby methods/vars should be snake_case)
		$output_path = File.join( $output_directory, $output_name + "#{@frame}" + "#{$format}" )
		Sketchup.set_status_text( "Exporting frame #{@frame} of #{@total_frames} to #{$output_path}" )
		puts "Exporting frame #{@frame} of #{@total_frames} to #{$output_path}"

		begin
			$view.write_image( $output_path, $width, $height, $anti_alias, $compression, $transparent )
			puts "SU_PROGRESS #{ ( 100.0 * (@frame) ) / @total_frames }%"
		rescue
			puts "Error: #{$!}"
			close_sketchup
		end

		#move to next page (if at the end of transition time)
		if @curr_time.to_f >= @curr_page_end
			@curr_page_index += 1
			if @curr_page_index == @pages.count #done
				Sketchup.set_status_text( "Finished exporting 2d image sequence to #{File.dirname($output_path)}" )
				puts "Finished exporting 2d image sequence to #{File.dirname($output_path)}"
				close_sketchup
			else
				@curr_page = @pages[@curr_page_index]
				@curr_page_start = @curr_time.to_f
				@curr_page_transition = @curr_page.transition_time
				@curr_page_transition = @default_transition_time if @curr_page_transition == -1.0
				@curr_page_end = @curr_page_start + @curr_page_transition
			end
		end

		@curr_time = @curr_time + @delay
		@frame += 1
		view.show_frame()
	end
end

def vray_version
	begin
		VRay.get_version_details.split(" ")[0].to_f
	rescue
		VRayForSketchUp.getVRayForSketchUpVersion().split(" ")[0].to_f
	end
end

def is_osx?
	if Sketchup.version.to_i < 14
		( /darwin/ =~ RUBY_PLATFORM ) != nil
	else
		Sketchup.platform == :platform_osx
	end
end

def is_win?
	if Sketchup.version.to_i < 14
		( /cygwin|mswin|mingw|bccwin|wince|emx/ =~ RUBY_PLATFORM ) != nil
	else
		Sketchup.platform == :platform_win
	end
end

def close_sketchup # SketchUp 2014 has Sketchup.quit
	if Sketchup.version.to_i >= 14
		# Model.close was added in 2015. This avoids relying on Deadline popup handling to dismiss the unsaved changes
		# dialog which doesn't work if SketchUp isn't in focus. V-Ray steals focus for its frame buffer.
		if Sketchup.version.to_i >= 15
			Sketchup.active_model.close(ignore_changes: true)
		end
		Sketchup.quit
	else
		if is_osx?
			Sketchup.send_action('terminate:') # Mac Cocoa automation command
		elsif is_win?
			Sketchup.send_action(57665) # todo: always check this works on SU/ruby version updates (must be v7 or higher )
		else # unsupported platform
			puts "Error: Platform \"#{RUBY_PLATFORM}\" is not supported by SketchUp"
			return false
		end
	end
end

def main
	#Reverts Sketchup's IO (their console) to the ACTUAL standard IO
	$stdout = STDOUT
	$stderr = STDERR
	$stdout.sync = true

	$model = Sketchup.active_model
	$view = $model.active_view

	# render_type, directory, filename, format, width, height, antialias, compression, transparent, framerate
	begin
		puts "Reading input from environment variable..."
		@settings_file = IO.readlines( ENV['DEADLINE_SKETCHUP_INFO'] )
		#@settings_file = readlines # file passed from stdin. Deadline cannot handle "< or |"
	rescue
		puts "Error: Failed to read lines from environment variable file"
		close_sketchup
	end

	$render_type = @settings_file[0].chomp
	$output_directory = @settings_file[1].chomp		
	$output_name = @settings_file[2].chomp
	$format = @settings_file[3].chomp

	if $output_name.chomp == ""
		$output_name = File.basename( $model.path, ".skp" ) # gets basename name from .skp file
	end

	if $render_type == "3D model"
		render_model
	else
		$width = @settings_file[4].to_i
		$height = @settings_file[5].to_i
		$anti_alias = ( @settings_file[6].chomp == "true" )
		$compression = @settings_file[7].to_f
		$transparent = ( @settings_file[8].chomp == "true" )
		
		# if user set width/height to 0
		if $width == 0
			$width = $view.vpwidth
		end

		if $height == 0
			$height = $view.vpheight
		end

		$use_vray = @settings_file[9].chomp.to_str 
		#make sketchup wait for vray to finish render before close
		if $use_vray == "True"
			if @settings_file[12] != nil
				$vray_submission_version = @settings_file[12].chomp.to_i
				$vray_start_frame = @settings_file[13].chomp.to_i
				$vray_end_frame = @settings_file[14].chomp.to_i

				# Fail early if there's a major version mismatch, could cause loads of miscommuncation
				if $vray_submission_version != vray_version.to_i
					puts "Error: V-Ray submission version \"#{$vray_submission_version}\" does not match the V-Ray for Sketchup version \"#{vray_version.to_i}\" installed on this slave"
					close_sketchup
				end
			end

			if vray_version >= 3
				$image_counter = 0
				VRay.on(:imageReady){ 
					$image_counter += 1
					if !VRay.is_rendering_image and ( $vray_end_frame - $vray_start_frame + 1 ) == $image_counter
						close_sketchup
					end
				}
			else
				VRayForSketchUp.registerCb( "Nill", "renderFinished", "close_sketchup" )
			end
		end
		
		if $render_type == "2D image"
			$scene_name = @settings_file[11].chomp
			render_image
			if $use_vray == "False"
				close_sketchup
			end
		elsif $render_type == "2D image sequence"
			pages = $model.pages
			if pages[1] == nil
				puts "Error: No pages were found, ensure that you have at least 2 pages before exporting an image sequence"
				close_sketchup
			end

			$frame_rate = @settings_file[10].to_f
			#render with vray or sketchup
			if $use_vray == "True"
				render_vray_sequence
			else
				AnimationExport.new
			end
		else
			puts "Error: $render_type: \"#{$render_type}\" does not match \"3D model\", \"2d image\", or \"2D image sequence\""
			close_sketchup
		end
	end
end

main

#########################################################################################
### UNUSED CODE - but potentially useful later
#########################################################################################
# 
# UI.start_timer(2.0,false) {Sketchup.send_action(21386)} #brings up export dialog
# @total_time = @pages.slideshow_time
# @start_time = Time.new
# @num_pages = @pages.count
#
# menu = UI.menu("Plugins")
# menu.add_separator
# menu.add_item("Submit To Deadline") { main }
#
# Sketchup.send_action("showRubyPanel:")
# UI.start_timer( 1.0, false ) { puts main } 
#
#########################################################################################
### Command-line
#########################################################################################
#
# #change directory to where sketchup.exe is located
# cd "C:\Program Files (x86)\SketchUp\SketchUp 2013"
# sketchup.exe -RubyStartup "C:\Users\Co-op\Desktop\SketchUpDeadline.rb" < "C:\Users\Co-op\Desktop\pipe.txt" "C:\Users\Co-op\Desktop\sketchtest.skp" 
#
#########################################################################################