from __future__ import print_function
import rhinoscriptsyntax as rs
import os
import time

name = "Deadline V-Ray DBR"

if name not in rs.ToolbarCollectionNames():
	file = "DEADLINEFILELOCATION"
	print(rs.OpenToolbarCollection( file ))
	rs.Command('-Toolbar T "%s" S "%s" Y Enter Enter' % ( name, name ) )
else:
	print("Deadline V-Ray DBR toolbar already installed!")

rs.Exit()