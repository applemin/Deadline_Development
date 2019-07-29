#perl
# The scene is loaded before this script is executed. All this script does is accept
# commands through file communication and executes them.

#use strict
#use warnings

#-----------------------------------------------------------
# HELPER FUNCTIONS
#-----------------------------------------------------------

# Writes to an ack file.
# Usage: write_ack( $filename, $message )
sub write_ack
{
	print STDOUT "Sending ack: @_[1]\n";
	open( ACKFILE, ">@_[0]" ) or exit_with_error( "could not open ACK file for writing" );
	print ACKFILE "@_[1]\n";
	close ACKFILE;
}

# Reads from a job file, waiting until the file exists.
# Usage: read_job( $filename )
# Returns: an array of lines from the file.
sub read_job
{
	my $jobFilename = @_[0];
	while( 1 )
	{
		# Check if file exists, has a size greater than 0, and is readable and writable.
		if( (-s $jobFilename) && (-r $jobFilename) && (-w $jobFilename) )
		{
			open( JOBFILE, "<$jobFilename" ) or exit_with_error( "could not open JOB file for reading" );
			my @data = <JOBFILE>;
			close JOBFILE;
			unlink $jobFilename;
			
			# Remove any end of line characters from the data.
			foreach (@data)
			{
				$_ =~ s/\n//g;
			}
			
			return @data;
		}
		
		# Sleep for 250 milliseconds.
		select( undef, undef, undef, 0.25 );
	}
}

# Exits Modo with exit code of -1.
# Usage: exit_with_error( $errorMessage )
sub exit_with_error
{
	print STDOUT "ERROR: @_[0]\n";
	exit( -1 );
}

#-----------------------------------------------------------
# MAIN SCRIPT
#-----------------------------------------------------------

# Perform flush after each write to STDOUT.
$| = 1;

# Get the job and ack filenames from the arguments.
my $jobFilename = $ARGV[0];
my $ackFilename = $ARGV[1];
print STDOUT "Job filename: $jobFilename\n";
print STDOUT "Ack filename: $ackFilename\n";

# Write the initial ACK to indicate we're ready to go.
write_ack( $ackFilename, "READY" );
while( 1 )
{
	# Wait for a command.
	my @command = read_job( $jobFilename );
        
	print STDOUT "Received command: @command[0]: @command[1]\n";
	
	# Interpret the command.
    if( @command[0] =~ m/EXECUTE/ )
	{
		if( @command[1] eq "QUIT" )
		{
			# Time to quit.
			print STDOUT "Exiting modo\n";
			exit( 0 );
		}
		else
		{
			# Execute the command.
			my $result = lx( @command[1] );
			if( !$result )
			{
				# An error occurred.
				my $errorCode = lxres();
				print STDOUT "Command '@command[1]' failed with $errorCode\n";
				write_ack( $ackFilename, "ERROR" );
			}
			else
			{
				write_ack( $ackFilename, "SUCCESS" );
			}
		}
	}
    elsif( @command[0] =~ m/QUERY/ )
	{
		# Execute the query and return the results.
		my $result = lxq( @command[1] );
		if( !$result )
		{
			# An error occurred.
			my $errorCode = lxres();
			print STDOUT "Command '@command[1]' failed with $errorCode\n";
			write_ack( $ackFilename, "ERROR" );
		}
		else
		{
			write_ack( $ackFilename, "$result" );
		}
	}
    elsif( @command[0] =~ m/PATHMAPPING/ )
    {
        if( @command[1] =~ m/START/ )
        {
            # Get the item count
            my $n = lxq( "query sceneservice item.N ?" );
            
            # Loop through the items in the scene, looking for output items
            for( $i=0; $i < $n; $i++ ) {
                my $type = lxq( "query sceneservice item.type ? $i" );
                if( $type eq "renderOutput" ) {
                    # Get the item ID
                    my $itemID = lxq( "query sceneservice item.id ? $i" );
                    print STDOUT "Render output item ID: $itemID\n";
             
                    # Select the item
                    lx( "select.item $itemID" );
             
                    # Get the original path
                    my $originalPath = lxq( "item.channel renderOutput\$filename ?" );
             
                    # If the path is empty, skip it
                    if( !$originalPath ) {
                        next;
                    }
                    
                    write_ack( $ackFilename, "$originalPath" );
                    my @pathCommand = read_job( $jobFilename );
                    if( @pathCommand[0] =~ m/PATHMAPPING/ )
                    {
                        my $newPath = @pathCommand[1];
                        if( $originalPath ne $newPath )
                        {
                            print STDOUT "Updated render output item path: $newPath\n";
                            lx( "item.channel renderOutput\$filename {$newPath}" );
                        }
                    }
                    else
                    {
                        print STDOUT "Path mapping error: unexpected command during path mapping: @pathCommand[0]\n";
                        write_ack( $ackFilename, "ERROR" );
                        last;
                    }
                }
            }
            
            write_ack( $ackFilename, "FINISHED" );
        }
        else
        {
            print STDOUT "Path mapping error: expected START command for path mapping, but received: @command[1]\n";
            write_ack( $ackFilename, "ERROR" );
        }
    }
	else
	{
		print STDOUT "Unknown command: @command[0]\n";
		write_ack( $ackFilename, "ERROR" );
	}
}
