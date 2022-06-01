# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 00:10:55 2022

@author: Mike
Naming Conventions

WiserOE: Native Wiser Optical Element. CLASS: LibWiser.Foundation.OpticalElement
WiserBeamline, WBeamline: Wiser native beamline. CLASS: LibWiser.Foundation.BeamlineElements


"""

'''
Return the native WISER BeamlineElements

Print in the console

Copy to the clipboard

'''
if hasattr(dir(),'in_object_1'):
	pass
else:
	in_object_1 = None
	
from LibWiser.Foundation import BeamlineElements as WBeamline
from LibWiser.Foundation import OpticalElement as WOElement

from LibWiser.Foundation import BeamlineElements as WBeamline
from LibWiser.Foundation import OpticalElement as WOpticalElement

'''
===============================================================================
FUNCTIONS THAT APPLY TO OASYS WIRES
===============================================================================
'''

def IsOasysWiserData(in_object = in_object_1) -> bool:
	'''
	Tell if in_object is of type WiserData or not.
	
	<class 'orangecontrib.wiser.util.wise_objects.WiserData'>
	'''
	return 	hasattr(in_object, 'wise_beamline')

def GetWiserBeamline(in_object = in_object_1, 
				 Index = None)-> WBeamline:
	'''
	Get the wire data of Oasys (as WiserData type) and return the beamline object
	used by (pure) Wiser only.  
	
	Parameters
	---------
	in_object : WiserData (Oasys wire)
	
	Index : None|int
		Optional
		
	Return
	----
	LibWiser.Foundation.BeamlineElements
	
	'''
	if IsOasysWiserData(in_object):
		wb = in_object.wise_beamline
		N = wb.get_propagation_elements_number()

		if Index is None:
			WiserOE =  wb.get_wise_propagation_element(N-1)
		else:
			WiserOE =  wb.get_wise_propagation_element(Index)
	
		WiserBeamline = WiserOE.ParentContainer
		
		return WiserBeamline 
	else:
		raise Exception("Input data is not o valid WiserData type.")

class Wiser:
	def WBeamlineGenerateCode():
		pass
		
#
#B = GetWiserBeamline(in_object_1)
#out_object = B
#print(20 * '\n')
#BeamlineCode = B.GenerateCode()
##print(BeamlineCode)
#B.Print()
#clipboard.copy(BeamlineCode)
#
		