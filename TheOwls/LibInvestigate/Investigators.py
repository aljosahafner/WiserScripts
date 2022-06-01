# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 17:07:34 2021

@author: Mike - Manfredda
"""
from pathlib import Path as MakePath
from LibWiser.Scrubs import Enum
#PathInvestigators = MakePath("D:\Topics\WISEr\LibInvestigate")
#PathPurosangue4 = "D:\Topics\WISEr\LibInvestigate\InvestigatorPurosangue4.py"
#PathExecuteKernelHelper = "ExecuteKernelHelper.py"
#PathSound = PathInvestigators / "res\horse1.wav"

class Paths():
	LibInvestigate = MakePath("D:\Topics\WISEr\Repository WiserLegacy\LibInvestigate")
	Purosangue4 = LibInvestigate / "InvestigatorPurosangue4.py"
	ExecuteKernelHelper = LibInvestigate / "ExecuteKernelHelper.py"
	Sound = LibInvestigate / "res\\horse1.wav"


class PurosangueTasks (Enum):
	EXTENSIVE_ANGLE_SCAN = 'fast angle scan'
	ANGLE_SCAN = 'ultrafast angle scan'
	SOURCEDELTA_SCAN = 'ultrafast sourcedelta scan'
	LAMBDA_SCAN = 'lambda scan'
	BEST_FOCUS = 'best focus'
	SIMPLE = 'simple'
	CAUSTICS = 'caustics'
	
	
class AutofocusType():
	NONE = 2**0
	ON_START = 2**2
	FOR_EACH_X = 2**3
	FIND_BEST_FOCUS_FOREACH_X = 2*3
	USE_AS_PREINPUT =  2**3


class Enums():

    class AutofocusType():
    	NONE = 2**0
    	ON_START = 2**2
    	FOR_EACH_X = 2**3
    	FIND_BEST_FOCUS_FOREACH_X = 2*3
    	USE_AS_PREINPUT =  2**3
    	
    class PurosangueTasks (Enum):
    	EXTENSIVE_ANGLE_SCAN = 'fast angle scan'
    	ANGLE_SCAN = 'ultrafast angle scan'
    	SOURCEDELTA_SCAN = 'ultrafast sourcedelta scan'
    	LAMBDA_SCAN = 'lambda scan'
    	BEST_FOCUS = 'best focus'
    	SIMPLE = 'simple'


	
