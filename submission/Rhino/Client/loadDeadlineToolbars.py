from __future__ import print_function
import rhinoscriptsyntax as rs
import os

name = "Deadline"

if name not in rs.ToolbarCollectionNames():
	file = "DEADLINEFILELOCATION"
	print(rs.OpenToolbarCollection( file ))
	rs.Command('-Toolbar T "%s" S "%s" Y Enter Enter' % ( name, name ) )
else:
	print("Deadline toolbar already installed!")

rs.Exit()
