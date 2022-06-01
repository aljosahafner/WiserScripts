# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 17:17:30 2021

@author: Mike
Helper file which plugs:
	- from the top, to a configuration file, where SettingsList MUST BE DEFINED
	- to the bottom, do KernelContent (to which Settings is passed)
	
Obviously this pipeline:
	configuration -> helper -> kernel
	
is a terrible workaround, 

"""
import LibInvestigate.Investigators  as Investigators
import logging

#=================================================================================
# Check if the shared (environment) variables exist
#=================================================================================	
try:
	SettingList
except:
	raise Warning("ExecuteKernelHelper did not find SettingList. SettingList must be specified in the workspace.")

#=================================================================================
# CLEAN LOG FILE
#=================================================================================	
try:
	os.remove(LogFile)
except:
	pass

try:
	EntryToUse
except:
	raise Warning("ExecuteKernelHelper did not find EntryToUse. EntryToUse and SettingsList must be specified in the workspace.")

if not type(EntryToUse) is list:
	raise Warning("EntryToUse must be a list, example [0], [0,1], not a scalar.")
	
#logging.basicConfig(filename = LogFile, filemode='w', format='%(message)s || %(asctime)s')

Msg = 100 * '='
#logging.warning(Msg)
	
	

#=================================================================================
# MAIN LOOP - read and execute the kernel
# Remark: the Layout File is read by the kernel
#=================================================================================
FileOutList = [] 
for i in EntryToUse:		
	# Settings is broadcasted in Purosangue
	Settings = SettingList[i]
	KernelContent = open(Investigators.Paths.Purosangue4, 'r').read()
	exec(KernelContent)		
	
	# update the log
	Msg = 'Computation Time = %0.1f min' % _ComputationTimeMin
#	logging.warning(Msg)
	FileOutList.append(FileOut)
	
	
	