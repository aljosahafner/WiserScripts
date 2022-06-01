# -*- coding: utf-8 -*-
"""
Created on Thu Apr  8 14:48:42 2021

@author: Mike
"""

import h5py
from LibWiser.EasyGo import * 
from LibWiser.Errors import WiserException


#%%
#--------------------------------------------------------------------------------------------------------
def GetData(Datafile, Group,Name):
	'''
	Shorthand for getting the Data values, 
	the Attributes and the dataset from a Datafile
	
	Return a tern of values
	'''
	Dataset = Datafile[Group][Name]
	Value = Dataset.value
	Attr = Dataset.attrs

#	class _():
#		pass
#	
#	D = _()
#	D.Value  = Value
#	D.Attr = Attr
#	D.Dataset = Dataset
#	
	return Value, Attr, Dataset
#--------------------------------------------------------------------------------------------------------	
def FormatAxisLabel(Dataset : h5py.Dataset,
					ScaleLetter = ''):
	try:
		Label = Dataset.attrs['Label']
		Unit = Dataset.attrs['Unit']
		return '%s [%s%s]' % (Label, ScaleLetter, Unit)
	except:
		_FileName = Dataset.file
		WiserException("Error while fortmatting the plot. I could not find 'Label' Or 'Unit' in the h5 file",
				 Args = [('_FileName', _FileName)]
				 )
		
		return None

FileName = 'D:\Topics\Simulazioni WISER\LDM\LDM Spot Size vs Lambda\Output1 (WISEr)\LambdaScan_LAYOUT_LDM_VH_01__IntensityVsDetectorVsParameter_OrientationLetter=H,XParameter=Lambda_byPurosangue2.h5'
FileName = 'D:\Topics\Simulazioni WISER\LDM\LDM Spot Size vs Lambda\Output1 (WISEr)\LambdaScan_LAYOUT_LDM_VH_01__IntensityVsDetectorVsParameter_OrientationLetter=H,XParameter=Lambda_byPurosangue2.h5'
FileName = "D:\Topics\Simulazioni WISER\LDM\LDM Spot Size vs Lambda\Output1 (WISEr)\LambdaScan_LAYOUT_LDM_VH_03__OrientationLetter=H.h5"
DataFile = h5py.File(FileName, mode = 'r')



#%% Example: how to list the keys
if 1==0:
	Group = 'TaskLambdaScan'
	XName = 'Lambda' # name of the X variable
	YName = 'Hew'    # name of the Y variable

	g = DataFile[Group]
	print(list(g.keys()))
	
	
	D = dict()
	for VarName in [XName, YName]:
		d = g[VarName]
		D.update({VarName : d.value })
	
	
	SmartPlot(D[XName], D[YName], 
			  XInfo = {'Units' : 'm', 'Label' : '$\lambda$'}, 
			  YInfo = {'Units' :'m', 'Label' : 'HEW'})
