#perl
# Submits a Modo scene to Deadline.

#-----------------------------------------------------------
# HELPER FUNCTIONS
#-----------------------------------------------------------

# Removes end of line characters and converts slashes.
# Usage: fix_path( $path )
# Returns: the fixed path.
sub fix_path
{
	$path = @_[0];
	$path =~ s/\n//g; # Remove end of line character.
	$path =~ s/\\/\//g; # Convert slashes.
	return $path;
}

# Displays an eror dialog.
# Usage: error_dialog( $errMsg )
sub error_dialog
{
	lx("dialog.setup error");
	lx("dialog.title {ERROR}");
	lx("dialog.msg {@_[0]}");
	lx("dialog.open");
}

#-----------------------------------------------------------
# MAIN SCRIPT
#-----------------------------------------------------------

# Get scene filename.
my $sceneFile = lxq( "query sceneservice scene.file ? current" );
lxout( "scene: $sceneFile" );
if( $sceneFile eq "" )
{
	# If scene filename is empty, tell user that they must save the scene file.
	my $errmsg = "Scene must be saved once before it can be submitted to Deadline";
	error_dialog( $errmsg );
	return;
}
else
{
	# Save scene if necessary.
	my $sceneChanged = lxq( "query sceneservice scene.changed ? current" );
	if( $sceneChanged )
	{
		lx( "scene.save" );
	}
}

# From the Modo documentation:
# As of modo 302, there is only one render item in the scene, with an item type of polyRender.
# The select.itemType command selects all items of a particular type, so we can use it to select
# the single render item, and then use item.channel to get the first and last frame.
lx( "select.itemType polyRender" );
my $startFrame = lxq( "item.channel first ?" );
my $endFrame = lxq( "item.channel last ?" );
my $stepFrame = int( lxq( "item.channel step ?" ) );

my $frameRange = "$startFrame-$endFrame";
if( $stepFrame > 1 )
{
	$frameRange = $frameRange . "x$stepFrame";
}
lxout( "frames: $frameRange" );

# Get the output paths and formats.
my $outputArguments = "";

# Get the number of items in the scene, and look for output items.
my $itemCount = lxq( "query sceneservice item.N ?" );
for( $i = 0; $i < $itemCount; $i++ ) {
    my $itemType = lxq( "query sceneservice item.type ? $i" );
    if( $itemType eq "renderOutput" ) {
        # Get the item and select it.
        $itemID = lxq( "query sceneservice item.id ? $i" );
        lx( "select.item $itemID" );
 
        # Get the output path and format.
        my $outputPath = lxq( "item.channel renderOutput\$filename ?" );
        if( !$outputPath ) {
            next;
        }
        
        my $outputFormat = lxq( "item.channel renderOutput\$format ?" );
        
        lxout( "render output item: $itemID" );
        lxout( "  output file name: $outputPath" );
        lxout( "  output format: $outputFormat" );
        
        $outputArguments = $outputArguments . "\"$outputPath\" \"$outputFormat\" ";
    }
}


my $deadlinebin = "";
my $deadlinecommand = "deadlinecommand";
my $deadlinecommandbg = "deadlinecommandbg";

$deadlinebin = $ENV{"DEADLINE_PATH"};

if( $deadlinebin eq "" &&  -e "/Users/Shared/Thinkbox/DEADLINE_PATH" )
{
	open my $file, '<', "/Users/Shared/Thinkbox/DEADLINE_PATH"; 
	$deadlinebin = <$file>; 
	close $file;
	
	$deadlinebin =~ s/^\s*(.*)\s*$/$1/;	
}

$deadlinecommand = "$deadlinebin/deadlinecommand";
$deadlinecommandbg = "$deadlinebin/deadlinecommandbg";

# Change directory to avoid dependency issues.
chdir "$deadlinebin";

# Call DeadlineCommand to launch the monitor script file.
my $script = fix_path( `\"$deadlinecommand\" -getrepositoryfilepath scripts/Submission/ModoSubmission.py` );
lxout( "script: $script" );
if( -e $script )
{
	`\"$deadlinecommandbg\" -executescript "$script" "$sceneFile" "$frameRange" $outputArguments`;
}
else
{
	my $scripterrmsg = "The ModoSubmission.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine,\nthat the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository.";
	error_dialog( $scripterrmsg );
	return;
}
