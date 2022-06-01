#%% Standard import snippet (2020)
#=======================================================================
import importlib
from LibWiser.EasyGo import *
import LibWiser.WiserImport as lw # this file and the Simulator are 'lw' compliant
from LibWiser.must import *
from LibWiser.WiserImport import * # a big mess but... preserves 'tl' in the layout file
importlib.reload(lw)
import time
import logging
import os
from pathlib import Path as MakePath
from LibWiser.Scrubs import Enum
from LibInvestigate.Investigators import PurosangueTasks as TaskList

SettingsDefaultInvestigator = {'Task' : 'simple',
    'DetectorDefocus': 0,
    'WorkingPath' : "D:\Topics\Simulazioni FERMI\LDM",
	'NamingList' :  ['OrientationLetter'],
	'NamingIndex' : 1,
    'Layout' : None,
    'OutputSubfolder' : 'Output1 (WISEr)',
'DetectorToUseName' : None,
'FocussingElementToUse': None,
'NSamples' : 4000 ,	
'FileNameBase' : 'Purosangue',
'LambdaList' : [],
'Lambda' : 10e-9,
'AngleList' : [],
'SourceDeltaList' : [],
'SourceDelta' : 0 ,
'SourceAngle' : 0,
'DefocusOffset_mm' : 0,
'DefocusRange_mm': 4,
'Defocus_N':21,
'DetectorSize' :100e-6,
'Name' : '',
'SaveData' : True,
'OrientationToPropagate' : None,
'XParameterFormatter' : lambda x : lw.Units.SmartFormatter(x),
'SessionTag' : ''}

#=====================================================================
#%% DIGEST SETTINGS
#=====================================================================
# Expands variables of "Settings" into local variable (aliases)
File = MakePath(Settings.get('Script', ''))
PathWorking = Settings.get('WorkingPath', File.parent)
PathOutput = PathWorking / MakePath(Settings.get('OutputSubFolder', 'Output1 (WISEr)'))
OutFolder = PathOutput




# Merge the default settings of <SettingsDefault> with the current settings of <Settings>, if
# the latter exist in the python namespace. 
S = SettingsDefaultInvestigator
try:
	S.update(Settings)
except:
	pass


	

#=======================================================================================================
#Check that the essential parameters are defined in _S_ DICTIONARY (settings)
#=======================================================================================================
for _ in  ('Layout', 'DetectorToUseName', 'FocussingElementToUse', 'OrientationToPropagate'):
	try:
		if S[_] is None:
			raise WiserException('The following parameter, inside the Settings dictionary, is None', 
								  By = 'Purosangue4',Args = [(_,None)])
	except:
			raise WiserException('The following variable does not exist', 
								  By = 'Purosangue4',Args = [(_,None)])	

#=======================================================================================================
# Handle OrientationToPropagate
#=======================================================================================================
'''
Parameters flow as: investigator script -> layout -> investigator kernel

however, the layout can handle more "OrientationToCompute", whereas investigator can handle only one.
For this reason, if there is a list, we get only the first one.

However, since the PropagationManager is the one who takes care of orientation, and the 
topology is (investigator lopps (propagation manager(...)), it is not clear to me whad would happen
if Beamline.ComputationSettings.OrientationToPropagate is a list....

'''
# Ensure that OrientationToPropagate is a list, even if single element
if type(S['OrientationToPropagate']) is not list:
	 S['OrientationToPropagate']  = [S['OrientationToPropagate']]
	    
# Pick the first orientation in orientation list	 
try:
	_Investigator_OrientationToPropagate = S['OrientationToPropagate'][0]
	S['OrientationLetter'] = _Investigator_OrientationToPropagate.name[0]
	
except KeyError:
	raise WiserException('KeyError: OrientationLetter is not found in the dictionary ', By = "Investigator")
except:
	raise WiserException('<Orientation> is not a valid enum', By = "Investigator")
	 

	
#=======================================================================================================
#Extract the parameters from the Settings dictionary
#Local Variables have the same name as in the dictionary.
#=======================================================================================================
#Process Everything :-)
for Key in S.keys():
	Value = S[Key]
	locals()[Key] = Value

			
def MakeDefocusList(DefocusOffset, DefocusRange, Defocus_N):
	a = -(DefocusRange/2) + DefocusOffset
	b = (DefocusRange/2) + DefocusOffset
	DefocusList = np.linspace( a, b, Defocus_N)
	return DefocusList

LogFile = lw.Paths.Tmp / 'PurosangueLog.txt'
lw.ToolLib.PathCreate(LogFile)

Tic = time.time()
LogPrint = lambda Msg : logging.warning(Msg)
try:
	os.rmdir(LogFile)
except:
	pass


	

class AUTOFOCUS():
	NONE = 2**0
	ON_START = 2**2
	FOR_EACH_X = 2**3
	FIND_BEST_FOCUS_FOREACH_X = 2*3
	USE_AS_PREINPUT =  2**4
	USE_SINGLE_VALUE_OF_X = 2**5
SourceDeltaInfo = DataContainer()
# Possible settings
# Possible Autofocus Configurations:
# AutofocusForEach:
# 	for every value to be scanned, the detector is placed in the best focus (Focust is called)
#  Used in: Intensity-Scan-Mode
# AutofocusOnStart:
#	The Best focus if found just before starting the computation
#  the DefocusOffset_mm property is overwritten by the output of a FindBestFocust procedure.
#	Example: Angular jittering, HEW scan. You find the best focus
if 1==1:
	logging.basicConfig(filename = LogFile, filemode='w', format='%(message)s [%(asctime)s]')
	''' preliminary and almost transparent '''
	# Catch missing variables
	#-----------------------------------------------
	AutofocusMode = AUTOFOCUS.FOR_EACH_X

#%% Read Task
	try:
		Task = Settings['Task']
		Task = Task.lower()
		TaskUsed = True
	except:
		raise WiserException('Investigator Task is not defined', By = 'InvestigatorPurosangueX') 


#%% init buffers
	AngleInfo = ''
	HewInfo = ''

	AsIsHewList = []
	HewCollection = []
	SigmaCollection = []
	ECollection= []
	ZCollection = [] # it's a 2D matrix, appended column by column
	BestFocalShiftList = [] # 1d, used in YType=1, for storing the best defocys
	BestHewList = [] # as before
	OptimizationResultList = [] # used to check if the opt were terminated correctly
#%% Configure Task, assign XParameterList, etc...
	# Task presets control variables
	# ----------------------------------------------
	TaskTag = TaskList(Task)
	if Task == 'fast angle scan':
		'''
		It is the historical angle scan, extensive version.
		It is called "fast" because with respect the very first version it is faster
		(thanks to numba), but actually it is the "slow one" :-)
		'''
		XParameter = 'Angle'
		AutofocusMode = AUTOFOCUS.FOR_EACH_X | AUTOFOCUS.ON_START
		YTypeScan = 0
		HewInfo = DataContainer(Name = 'HEW',
							Unit = 'm',
							Label = 'Spot Size (HEW)',
							VisualizationFactor = 1e6,
							VisualizationPrefix = 'u')

		AngleInfo = DataContainer(Name = 'Source Angle',
							Unit = 'rad',
							Label = '$\\vartheta$',
							VisualizationFactor = 1e6,
							VisualizationPrefix = 'u')
#		XParameterList XParameterList
	elif Task == 'ultrafast angle scan':
		'''
		Does not compute the focal shift.
		Computes only the HEW at SourceAngle = 0 (best focus), then performs the scan
		Used to compute HEW(theta)/HEW(0)
		'''
		XParameter = 'Angle'
		AutofocusMode = AUTOFOCUS.ON_START
		YTypeScan = 1
		HewInfo = DataContainer(Name = 'HEW',
							Unit = 'm',
							Label = 'Spot Size (HEW)',
							VisualizationFactor = 1e6,
							VisualizationPrefix = 'u')

		AngleInfo = DataContainer(Name = 'Source Angle',
							Unit = 'rad',
							Label = '$\\vartheta$',
							VisualizationFactor = 1e6,
							VisualizationPrefix = 'u')

	elif Task == 'fast sourcedelta scan':
		'''
		The same as ultrafast angle scan, but with source delta.
		Provides HEW(SourceDelta)/HEW(SourceDelta=0)

		'''
		XParameter = 'SourceDelta'
		AutofocusMode = AUTOFOCUS.FOR_EACH_X | AUTOFOCUS.ON_START
		YTypeScan = 1
		HewInfo = DataContainer(Name = 'HEW',
							Unit = 'm',
							Label = 'Spot Size (HEW)',
							VisualizationFactor = 1e6,
							VisualizationPrefix = 'u')

		SourceDeltaInfo = DataContainer(Name = 'Source Delta',
							Unit = 'm',
							Label = '$\\Delta s$',
							VisualizationFactor = 1,
							VisualizationPrefix = '')

	elif Task == 'ultrafast sourcedelta scan':
		'''
		The same as ultrafast angle scan, but with source delta.
		Provides HEW(SourceDelta)/HEW(SourceDelta=0)

		'''
		XParameter = 'SourceDelta'
		AutofocusMode = AUTOFOCUS.ON_START
		YTypeScan = 1
		HewInfo = DataContainer(Name = 'HEW',
							Unit = 'm',
							Label = 'Spot Size (HEW)',
							VisualizationFactor = 1e6,
							VisualizationPrefix = 'u')

		SourceDeltaInfo = DataContainer(Name = 'Source Delta',
							Unit = 'm',
							Label = '$\\Delta s$',
							VisualizationFactor = 1,
							VisualizationPrefix = '')

#		XParameterList XParameterList
	elif Task == 'lambda scan':
		'''
		Returns a plot: HEW vs Wavelength
		
		'''
		XParameter = 'Lambda'
		AutofocusMode = AUTOFOCUS.FOR_EACH_X
		YTypeScan = 1
		TaskTag = "LambdaScan"



	elif Task == 'hew scan': #??
		AutofocusMode = AUTOFOCUS.NONE
		YTypeScan = 0

	elif Task == 'best focus':
		'''
		Returns a plot: HEW vs Defocus
		Each value of HEW is obtained via quick optimization.
		'''
		YTypeScan = 0        # scan the HEW along z
		XParameter = 'Lambda'
		LambdaList = [Lambda]   #forzatura, there is no LambdaList to scan
		AutofocusMode =  AUTOFOCUS.USE_SINGLE_VALUE_OF_X | AUTOFOCUS.USE_AS_PREINPUT | AUTOFOCUS.FOR_EACH_X

	elif (Task == 'best focus manual'):
		'''
		Returns a plot: HEW vs Defocus
		Each value of HEW is obtained via extensive optimization.		
		'''
		YTypeScan = 0
		XParameter = 'Lambda'
		LambdaList = [Lambda]   #forzatura, there is no LambdaList to scan
		AutofocusMode =  AUTOFOCUS.USE_SINGLE_VALUE_OF_X |  AUTOFOCUS.FOR_EACH_X

	elif Task == 'simple':
		'''
		Run a single simulation, just as is
		'''
		YTypeScan = 1
		AutofocusMode = AUTOFOCUS.NONE
		XParameter = 'Lambda' # forzatura, in realtà non c'è nessun XParameter è una simulazione che non fa scansione
		LambdaList = [Lambda]   #forzatura, there is no LambdaList to scan
	elif Task == 'caustics':
		'''
		Return a plot of HEW vs DEFOCUS (like )
		Return a list of the INTENISTY PROFILES vs DEFOCUS
		'''
		XParameter = 'Lambda'
		YTypeScan = 0
		TaskTag = "Caustics"
		AutofocusMode =  0

		
		
	else:
		TaskUsed = False

	try:
		if ForceAutofocusMode is not None:
			AutofocusMode = ForceAutofocusMode
	except:
		pass		
		 
#%% MANAGE X,Y,Z,Info


	VariableToReplace = XParameter
	XAxisLabel = VariableToReplace
	YScanDescription = {	 0:'HewVsDefocusVsParameter' ,
												 1:'IntensityVsDetectorVsParameter' ,
												 2: 'plot HEW' ,
												 -1:'IntensityVsDetectorVsParameter_NominalFocus',
												 -3: 'no scan'}

	YAxisLabels = { 0: 'Defocus' ,  1 : 'detector' ,
				4:'Detector', -1 :'detector', -2 : 'alambra', -3: 'detector' }
	YAxisLabel = YAxisLabels[YTypeScan]

	if VariableToReplace == 'Lambda':
		XInfo = DataContainer(Name = 'Lambda',
									Unit = 'm',
									Label = '$\\lambda$',
									VisualizationFactor = 1e9,
									VisualizationPrefix = 'n')

	elif VariableToReplace == 'Angle':
		XInfo = DataContainer(Name = 'Angle',
									Unit = 'rad',
									Label = '$\\vartheta$',
									VisualizationFactor  = 1e6,
									VisualizationPrefix = 'u')

	elif VariableToReplace == 'DeltaSource' or VariableToReplace == 'SourceDelta':
		XInfo = DataContainer(Name = 'Source Shift',
									Unit = 'm',
									Label = '$\\Delta S$',
									VisualizationFactor  = 1,
									VisualizationPrefix = '')

	YAxisInfo = DataContainer()
	if YTypeScan == 0: #returns defocus + HEW
		YInfo = DataContainer(Name = 'Defocus',
									Unit = 'm',
									Label = '$\\Delta f$',
									VisualizationFactor = 1e3,
									VisualizationPrefix = 'm')

		ZInfo = DataContainer(Name = 'HEW',
									Unit = 'm',
									Label = 'Spot Size (HEW)',
									VisualizationFactor = 1e6,
									VisualizationPrefix = 'u')
		ZAxisLabel = 'HEW'
		# Compute the Defocus Range for Defocus Scan
		a = -(DefocusRange_mm/2) + DefocusOffset_mm
		b = (DefocusRange_mm/2) + DefocusOffset_mm
		DefocusList = np.linspace( a*1e-3, b* 1e-3, Defocus_N)

	elif YTypeScan == 1 or YTypeScan == -1: #returns detector position +  intensity
		YInfo = DataContainer(Name = 'Detector',
									Unit = 'm',
									Label = '$s$',
									VisualizationFactor = 1e3,
									VisualizationPrefix = 'm')

		ZInfo = DataContainer(Name = 'Intensity',
									Unit = 'a.u.',
									Label = 'I',
									VisualizationFactor = 1,
									VisualizationPrefix = '')

		ZAxisLabel = 'Intensity'
		DefocusOffset_mm = np.NAN
		DefocusRange_mm = np.NAN

	else: # dummy. Introduced only to not perform any scan (debug purposes)
		YInfo = DataContainer(Name = 'dummy',
									Unit = '',
									Label = '',
									VisualizationFactor = 1,
									VisualizationPrefix = '')

		ZInfo = DataContainer(Name = 'dummy',
									Unit = '',
									Label = '',
									VisualizationFactor = 1,
									VisualizationPrefix = '')

		ZAxisLabel = ''
		DefocusOffset_mm = np.NAN
		DefocusRange_mm = np.NAN

	# to set in any case
	HewInfo = DataContainer(Name = 'HEW',
								Unit = 'm',
								Label = 'Spot Size (HEW)',
								VisualizationFactor = 1e6,
								VisualizationPrefix = 'u')

	FocalShiftInfo = DataContainer(Name = 'Focal shift',
								Unit = 'm',
								Label = '$\\Delta f$',
								VisualizationFactor = 1e3,
								VisualizationPrefix = 'm')
	#---- Associating the ScanList to the right variable,
	# and setting to NaN the "non-sweeping" variable with the same name
	if VariableToReplace == 'Angle':
#		SourceAngle = np.NAN
		XParameterList =  AngleList
		XParameterSingleValue = Lambda

	elif VariableToReplace == 'Lambda':
		XParameterList = LambdaList
		XParameterSingleValue = SourceAngle

	elif VariableToReplace == 'DeltaSource' or VariableToReplace == 'SourceDelta':
		SourceDelta = np.NAN
#		XParameterList = SourceDeltaList
		XParameterList = SourceDeltaList
		XParameterSingleValue = SourceDelta

	if (AutofocusMode &  AUTOFOCUS.USE_SINGLE_VALUE_OF_X):
		XParameterList = [XParameterList[0]]
	else:
		pass

	#=======================================================================================================
	# Makes the labels associated to the X parameter
	#=======================================================================================================
	XParameterLabelList = [lw.Units.SmartFormatter(x) for x in XParameterList]


#%% SET FileAttributes
	FileAttributes = dict()
	#--- general (possibly overwritten by ParameterScan)
	FileAttributes['Task'] = Task
	FileAttributes['Waist0'] = Waist0
	FileAttributes['SourceAngle'] = SourceAngle
	FileAttributes['Lambda'] = Lambda
	FileAttributes['SourceDelta'] = SourceDelta
	FileAttributes['NSamples'] = NSamples 
	FileAttributes['DetectorSize'] = DetectorSize
	FileAttributes['YTypeScan'] = YTypeScan
	FileAttributes['YScanDescription'] = YScanDescription [YTypeScan]
	FileAttributes['UseFigureErrorOnFocusing'] = UseFigureErrorOnFocusing
	FileAttributes['OrientationLetter'] = S['OrientationLetter']
	
	#--- Defocus scan 
	FileAttributes['DefocusRange_mm'] = DefocusRange_mm
	FileAttributes['DefocusOffset_mm'] = DefocusOffset_mm
	FileAttributes['AutofocusMode'] = AutofocusMode
	
	#--- ParameterScan
	FileAttributes['XParameter'] = XAxisLabel
	FileAttributes['whos_X'] = XAxisLabel
	FileAttributes['whos_Y'] = YAxisLabel
	FileAttributes['whos_Z'] = ZAxisLabel


	#----- Default naming list, if not existing in the namespace
#%% make file name
	for _ in NamingList:
		try:
			globals()[_]
		except:
			raise WiserException('Parameter in NamingList not defined', 'InvestigatorPurosangueX', [(_,None)])
	#----- change the working folder if needed
	FileBeamlineLayout = MakePath(Layout)
	__ = FileBeamlineLayout.parts
	FileBeamlineLayoutName = __[-1]
# 	WorkingFolder = FileBeamlineLayout.parents[0]
# 	WorkingFolder = WorkingPath.parents[0]
	os.chdir(PathWorking)

	#----- Define the name of the output file
	KernelTag = ''
	__ = os.path.splitext(FileBeamlineLayoutName)[0] # get the file name without extension
	__ = __.replace('beamline_layout_','').upper() # remove 'beamline_layout' in the file name

	__ = '%s_%02d_' % (__,S['NamingIndex'])
	if (FileNameBase =='auto' ) :
		FileNameBase = __
	else :
			FileNameBase = FileNameBase + '_' + __

	NamingValues = ','.join([ Key + '=' + str(FileAttributes[Key]) for Key in NamingList])
#	NamingValues = ','.join([ Key + '=' + lw.Units.SmartFormatter(FileAttributes[Key]) for Key in NamingList])
	if TaskUsed  == True :
		FileName = FileNameBase + '_' + YScanDescription [YTypeScan] + '_' + NamingValues + '_' + KernelTag + '.h5'
		FileName = FileNameBase + '_' + NamingValues + '.h5'
	else:
		FileName = FileNameBase + '_' + Task + '_' + NamingValues + '_' + KernelTag + '.h5'




	FileOut = PathJoin(OutFolder,FileName)
#%%--Scan section--

	def HewToMinimize(Defocus, d,t):
		# I set the Position the detector at Defocus = Defocus
		# ------------------------------------------------------------
		d.PositioningDirectives.Defocus = Defocus
		t.RefreshPositions()
		# Perform the computation
		t.ComputeFields(Verbose=False)
		I = abs(d.ComputationData.Field) ** 2
		DeltaS = np.mean(np.diff(d.Results.S))  # Sample spacing on the detector
		(Hew, Centre) = rm.HalfEnergyWidth_1d(I, Step=DeltaS, UseCentreOfMass = False) # Compute the HEW

		return Hew

	#===================================================================================================================

	if AutofocusMode & AUTOFOCUS.ON_START: # Tasks: 'fast angle scan',
		'''
		It should compute the best focus at one fixed configuration (of Lambda, Angle, SourceDelta)
		then produce a new reference position for that.

		However biw [23062020] the position is not found correctly.

		I do not know why.

		'''
		# RUN THE BEAMLINE LAYOUT FILE (Waist0, Lambda)
		#----------------------------------------------------------------------------------
		scriptContent = open(FileBeamlineLayout, 'r').read()
		exec(scriptContent)
		exec('DetectorToUse =%s' % DetectorToUseName) #>>> example: DetectorToUse  = dpi_dh
		exec('Detector =%s' % DetectorToUseName) #>>> example: DetectorToUse  = dpi_dh
		try:
			Beamline.ComputationSettings.OrientationToCompute = OrientationToCompute
			raise Exception("I entered this case, but probably it's wrong. Check!!")
		except:
			pass
#		Beamline.Source.CoreOptics.SmallDisplacements.Rotation = SourceAngle
#		Beamline.Source.CoreOptics.SmallDisplacements.Long = SourceDelta
		#----------------------------------------------------------------------------------
		FocussingElement = Beamline[FocussingElementToUse]
		Beamline.ComputeFields()
		AutofocusOnStartResults = Foundation.FocusFind(FocussingElement,
							  DetectorSize = DetectorSize,
											MaxIter = 41)
		AutofocusOnStartBestDefocus = AutofocusOnStartResults.BestDefocus
	#----------------------------------------------------------------------------------

#	XParameterList = XParameterList
	NScans = len(XParameterList)
#%% MAIN LOOP
	if YTypeScan != -2: # (almost) ANY CASE
		
		for iScanValue, ScanValue in enumerate(XParameterList):
			import time
			SubTic = time.time()
			Beep(644,50)
			Beep(744,50)
			Msg= ('Scan %d/%d, %s=%0.1e' %(iScanValue+1, NScans, XParameter, ScanValue))
			LogPrint(Msg)

			# CHANGE THE PARAMETER OF THE SYSTEM
			#---------------------------------------------------------------------------------
			
			
			
			#---------------------------------------------------------------------------------
			# 1) 	External Assignment
			# 	    The scan value is changed in the <Settings> global variable with a key given
			#	    by <VariableToReplace>. The simulation reacts to ScanVsuch a key is 
			#       used within the layout file.
			#         
			
#			CommandStr = '%s=ScanValue' % VariableToReplace
#			exec(CommandStr)     #     example: Angle = ScanValue
			tmp = dict()
			tmp[VariableToReplace] = ScanValue			
			Settings.update(tmp)

#%%--- BUILD THE BEAMLINE
			# RUN THE BEAMLINE LAYOUT FILE (Waist0, Lambda)
			#----------------------------------------------------------------------------------
			scriptContent = open(FileBeamlineLayout, 'r').read()
			exec(scriptContent)
			exec('DetectorToUse =%s' % DetectorToUseName) #>>> example: DetectorToUse  = dpi_dh
			exec('Detector =%s' % DetectorToUseName) #>>> example: DetectorToUse  = dpi_dh
			try:
				Beamline.ComputationSettings.OrientationToCompute = OrientationToCompute
				raise Exception("I entered this case, but probably it's wrong. Check!!")
			except:
				pass
		
			#---------------------------------------------------------------------------------
			#2)      Local Assignments
			#        An 'if' structure catches the most common options
			
			
			# Source Angle and Delta
			#==========================================================================
			if VariableToReplace == 'Angle':
				AngleToUse = ScanValue
			else:
				AngleToUse = SourceAngle

			Beamline.Source.CoreOptics.SmallDisplacements.Rotation = AngleToUse
			Beamline.Source.CoreOptics.SmallDisplacements.Long = ScanValue 


			# Displacement of the detector+
			#==========================================================================
			# Used in Tasks: 'fast angle scan'
			if AutofocusMode & AUTOFOCUS.ON_START:
				Detector.PositioningDirectives.Distance += AutofocusOnStartResults.BestDefocus
				Beamline.RefreshPositions()
#				Detector.CoreOptics.SmallDisplacements.Long = AutofocusOnStartResults.BestDefocus

			# COMPUTE FIELD (up to the nominal position)
			#=========================================================================
			Beamline.ComputeFields()

			#=========================================================================

			try:
				FocussingElement = Beamline[FocussingElementToUse]
			except: 
				raise WiserException("Could not find FocussingElementToUse")
				
			# Additional Check on orientation
			# Special check that the orientation in Beamline.ComputationSettings and
			# that of S['...'] match.
			if iScanValue == 0:
				# Check only on first iteration
				if not (Beamline.ComputationSettings.OrientationToCompute[0] == _Investigator_OrientationToPropagate):
					raise Exception("ERROR: in Investigators, the orientation of _Beamline.ComputationSettins_ do not match with Settings.")
	
				if not (Detector.CoreOptics.Orientation== _Investigator_OrientationToPropagate):
					raise Exception("ERROR: in Investigators, the orientation of _Detector_ and of _Beamline.ComputationSettins_ do not match.")
				
				if not (FocussingElement.CoreOptics.Orientation== _Investigator_OrientationToPropagate):
					raise Exception("ERROR: in Investigators, the orientation of _Detector_ and of _FocussingElement_ do not match.")
					
			#======================================================================================
#%%2D SCAN: (XPARAMETER,DEFOCUS) => HEW
			#======================================================================================
			if YTypeScan == 0:
				'''
				'''
				DefocusList_mm = DefocusList * 1e3
				# used in Tasks: 'fast angle scan', best focus,
				if AutofocusMode & AUTOFOCUS.FOR_EACH_X: # this is used also for auxiliary best HEW computation in 'best focus' task
					AutofocusResults = Foundation.FocusFind(FocussingElement,
									  DetectorSize = DetectorSize,
													MaxIter = 41)
					BestFocalShiftList.append(AutofocusResults.BestDefocus)
					BestHewList.append(AutofocusResults.BestHew)
					OptimizationResultList.append(AutofocusResults)
					# used in Tasks: 'best focus'
					if AutofocusMode & AUTOFOCUS.USE_AS_PREINPUT:
						'''
						best focus => find the best focus, then does the extensive sweep only in the surrounding of
						this value .
						'''

						NewDefocusList = MakeDefocusList(AutofocusResults.BestDefocus,
													  DefocusRange_mm*1e-3,
													  Defocus_N)
					else:
						NewDefocusList = DefocusList

					DefocusList = NewDefocusList # brutto, ma fu fonte di infinito dolori. Nei plot uso sempre DefocusList
					DefocusList_mm  = DefocusList  * 1e3
					ResultList, HewList, SigmaList, More = lw.Foundation.FocusSweep(FocussingElement,
																	NewDefocusList,
																	DetectorSize = DetectorSize)
					#=============================================================
					# Find minimum of HEW over Hew Plot
					#=============================================================
					from scipy.interpolate import UnivariateSpline
					IndexBest = np.argmin(HewList)
					x = ToolLib.GetAround(DefocusList_mm, IndexBest, 2)
					y = ToolLib.GetAround(HewList, IndexBest, 2)
					
					try:
						Interpolant = UnivariateSpline(x, y, s = len(x))
					
						xQuery = np.linspace(x[0], x[-1], 100)
						yQuery =  Interpolant(xQuery)
						_ = np.argmin(yQuery)
						BestHew = yQuery[_]
						BestDefocus = xQuery[_] * 1e-3
					except:
						raise Warning("InvestigatorPurosangue4 failed in fitting the HEW.")
						BestHew = np.nan
						BestDefocus = np.nan
					#------- Replace values found with FocusFind
					BestFocalShiftList[-1] = BestDefocus 
					BestHewList[-1] = BestHew
					
					#=============================================================

					
				else:
					# Used from: CAUSTICS?
					ResultList, HewList, SigmaList, More = lw.Foundation.FocusSweep(FocussingElement,
																	  DefocusList,
																		DetectorSize = DetectorSize)
				# RETURN/APPEND DATA for YTypeScan == 0
				#---------------------------------------------------------------
				HewCollection.append(HewList)
				SigmaCollection.append(SigmaList)
				ZCollection.append(HewList)
				# ResultList: is not appended, but it is "set to last value"
				# Used for: CAUSTICS
			#=====================================================================================
#%% 1D SCAN: (XPARAMETER) => BestHew, BestFocalShift, etc
			#==========================================================================print(Beam)
			elif YTypeScan == 1: 
				'''
				Find the focus by means of a "quick" optimization algorithm.
				
				Returns (always): 
					- AsIsHewList:
						HEWs computed on the current position of the detector
					
				Returns: (if AUTOFOCUS_FOR_EACH_X)	
					- BestHewList
						HEWs computed at the best focus
					- BestFocalShiftList
					- ZCollection of BestI
						BestI is the spot intensity profile at the best focus

				
				Returns: (if not AUTOFOCUS_FOR_EACH_X)	
					- ZCollection of AsIsI
						AsIsI is the spot intensity profile at the current detector position
	
				'''
				AsIsHew = Detector.ComputationData.Hew
				AsIsHewList.append(AsIsHew)
				
				if AutofocusMode & AUTOFOCUS.FOR_EACH_X:
					Results = Foundation.FocusFind(FocussingElement,
													  DetectorSize = DetectorSize,
																	MaxIter = 41)
					OptimizationResultList.append(Results)
					
					BestI = np.abs(Results.BestField)**2
					BestFocalShiftList.append(Results.BestDefocus) # a scalar
					BestHewList.append(Results.BestHew) #tbc
					ZCollection.append(BestI)
				else:
					AsIsI = Detector.ComputationData.Intensity
					ZCollection.append(AsIsI)



			elif YTypeScan == 2 : 
				'''
				 I do an "extensive"  focus sweep scan along z, and for each z-value I return the corresponding HEW
				'''
				HewList = wr.Foundation.FocusSweep2(FocussingElement,
																	   DefocusList,
																		DetectorSize = DetectorSize)

			elif YTypeScan == -1 : 
				''' 
				Simple scan of  the XParameter scan WITHOUT optimizing the focus.
				
				BUT if AutofocusMode = "OnStart", remember that DefocusOffset_mm is overwitten
				
				Return
				--------
				- ZCollection of the Intensity Profile on the current position of the detector
				'''
				
				# The field is already computed
				I = np.abs(Detector.ComputationData.Field)**2
				ZCollection.append(I)
#				BestFocalShiftList.append(0) # do not do nothing
#				BestHewList.append(0)  #@ do not do nothing
				pass

			elif YTypeScan == -2 :
				pass

			import time
			SubToc = time.time()

			Msg= ('\t Delta t %0.1f min' %( (SubToc-SubTic)/60))
			LogPrint(Msg)

	elif YTypeScan == -1:
		Beamline.ComputeFields()

	AsIsHewList = np.array(AsIsHewList)
	BestHewList = np.array(BestHewList)
	BestFocalShiftList = np.array(BestFocalShiftList)
	BestIList = ZCollection # replica
	#%% Computing the ComputationTimeMin
	Toc = time.time()
	_ComputationTimeMin = (Toc-Tic)/60
	FileAttributes['ComputationTimeMin'] = _ComputationTimeMin

	Msg= ('\t Total Elapsed time %f0.1 min' % _ComputationTimeMin)
	LogPrint(Msg)

#%% MANAGE XAxis, YAxis 
	#----- Helper code: Choosing the proper XAxis YAxis
	try:
		if SaveData == True:
			XAxis = XParameterList

			if YTypeScan == 0:
				YAxis = DefocusList
			elif YTypeScan == 1:
				YAxis = DetectorToUse.ComputationData.S
			elif YTypeScan == -1:
				YAxis = DetectorToUse.ComputationData.S
	except:
		pass

	#		print(FileOut)
	#		lw.tl.SaveMatrix(FileOut, ZCollection,  YAxis, XAxis)

#%%-- PLOT TASK PLOT SECTION--
	XParameterList = np.array(XParameterList)
	try:
		TitleAppend = ' (%s)' % Beamline.Name
	except:
		TitleAppend = ''
	LabelLambda = '$\lambda$ = %0.1f nm' % (Lambda*1e9)
	# ===================================================================================================
	# TASK: FAST ANGLE SCAN
	# ===================================================================================================
	if Task =='fast angle scan':
		# 2D PLOT 2D
		XX, YY = np.meshgrid(XAxis, YAxis, sparse = False)
		h = plt.contourf(YAxis, XAxis, ZCollection)
		
	if Task =='fast angle scan' or Task =='ultrafast angle scan':
		matplotlib.rcParams.update({'font.size': 12})

		try:
			plt.figure(11)
			Title = '$\lambda$ = %0.1f nm - %s' % (Lambda*1e9, FileBeamlineLayout.name)
		#--------------------------------------------------------------------------
		# PLOT Hew (As Is)
			plot(XParameterList * XInfo.VisualizationFactor, AsIsHewList * 1e6, 'o-',
				   label = 'Hew @ the best focus of $\\theta = 0$')
		except:
			pass
		#--------------------------------------------------------------------------
		# PLOT Hew (BEst focus for each Angle)
		if AutofocusMode & AUTOFOCUS.FOR_EACH_X:
			plot(XParameterList * XInfo.VisualizationFactor, BestHewList * 1e6, 'x-',
			   label = 'Hew @ the best focus for each angle ($\\theta$ - misleading)')
		#---
			plt.xlabel(XInfo.Name)
			plt.ylabel('Hew (um)')
			plt.grid('on')
			plt.title(Title + TitleAppend)
			plt.legend()
			plt.grid(which = 'minor')
			
		#--------------------------------------------------------------------------
		# PLOT Focal shift (best focus)
		if AutofocusMode & AUTOFOCUS.FIND_BEST_FOCUS_FOREACH_X:
			if len(BestFocalShiftList) == len(XParameterList):
				plt.figure(2)
				plot(XParameterList * XInfo.VisualizationFactor, BestFocalShiftList * 1e3, 'o',
					   label = 'Focal shift')

				plt.xlabel(XInfo.Name)
				plt.ylabel('Focal shift (mm)')
				plt.grid('on')
				plt.title(Title + TitleAppend)
				plt.legend()

		#--------------------------------------------------------------------------
		# PLOT Intensity on the detector
		try:
			plt.figure(3)
			x = Detector.Results.S * 1e6
			for i, ZList in enumerate(ZCollection):
				plot(x, np.array(ZList).transpose()**2)
				plt.xlabel('detector (um)')
				plt.ylabel('Intensity')
				plt.title(Title)
		except:
			pass
		

		#--------------------------------------------------------------------------
		# PLOT last intensity on the focusing element
		try:
			plt.figure(100)
			x = FocussingElement.Results.S * 1e6
			y = FocussingElement.Results.Intensity
			lw.ToolLib.CommonPlots.IntensityAtOpticalElement(FocussingElement)
		except:
			pass
		
		# 2D PLOT
		if Task =='fast angle scan':
			pass
	# ===================================================================================================
	# TASK: ULTRAFAST SOURCE-DELTA SCAN
	# ===================================================================================================
	if Task  == 'ultrafast sourcedelta scan' or Task  == 'fast sourcedelta scan':
		matplotlib.rcParams.update({'font.size': 12})
		Title = '%s' % (FileBeamlineLayout.name)
		plt.figure(12)

		#--------------------------------------------------------------------------
		# PLOT Hew (As Is)
		plot(XParameterList * XInfo.VisualizationFactor, AsIsHewList * 1e6, 'o-',
			   label = '$\lambda$ = %0.1f nm @ fixed focus' % (Lambda*1e9))
		plt.xlabel(XInfo.Name)
		plt.ylabel('Hew (um)')
		plt.grid_both()
		plt.legend()
		plt.title(Title)

		#--------------------------------------------------------------------------
		# PLOT Hew (BEst focus for each SourceDelta)
		if AutofocusMode & AUTOFOCUS.FOR_EACH_X:
			plot(XParameterList * XInfo.VisualizationFactor, BestHewList * 1e6, 'x-',
			   label = '$\lambda$ = %0.1f nm @ Best Focus' % (Lambda*1e9))
		#---
			plt.xlabel(XInfo.Name)
			plt.ylabel('Hew (um)')
			plt.grid('on')
			plt.title(Title + TitleAppend)
			plt.legend()
		#--------------------------------------------------------------------------
		# PLOT Focal shifr (best focus)
		if AutofocusMode & AUTOFOCUS.FIND_BEST_FOCUS_FOREACH_X:
			if len(BestFocalShiftList) == len(XParameterList):
				plt.figure(2)
				plot(XParameterList * XInfo.VisualizationFactor, BestFocalShiftList * 1e3, 'o',
					   label = 'Focal shift')

				plt.xlabel(XInfo.Name)
				plt.ylabel('Focal shift (mm)')
				plt.grid('on')
				plt.title(Title + TitleAppend)
				plt.legend()

		#--------------------------------------------------------------------------
		# PLOT fields on the detector
		plt.figure(3)
		x = Detector.Results.S * 1e6
		for i, ZList in enumerate(ZCollection):
			plot(x, np.array(ZList).transpose())
			plt.xlabel('detector (um)')
			plt.ylabel('Field')
			plt.title(Title)

	# ===================================================================================================
	# TASK: lambda SCAN
	# ===================================================================================================
	if Task == 'lambda scan':
		#--------------------------------------------------------------------------
		# PLOT FOCAL SHIFT
		plt.figure(64)
		plot(XParameterList *1e9, BestFocalShiftList * 1e3,'o')
		plt.title('Focal Shift' + TitleAppend)
		plt.xlabel('$\lambda$ (nm) ')
		plt.ylabel('Focal shift (mm)')
		plt.grid(True, which = 'both')
		plt.minorticks_on()
		#--------------------------------------------------------------------------
		# (BEST) HEW VS LAMBDA
		plt.figure(65)
		plot(XParameterList *1e9, BestHewList * 1e6,'o')
		plt.title('Focal Shift')
		plt.title('HEW' + TitleAppend)
		plt.ylabel('HEW ($\mu m$)')
		plt.xlabel('$\lambda (nm)$')
		plt.grid(True, which = 'both')
#		#--------------------------------------------------------------------------
#		# Multi-wavelength cumulative plot
#		plt.figure(4)
#		matplotlib.rcParams.update({'font.size': 16})
#		Lambda_nm = Lambda * 1e9
#		iy0= np.where(XParameterList ==0)
#		y0 = AsIsHewList[iy0]
#		y = (y-y0)/y0
#		plot(XParameterList * XInfo.VisualizationFactor, AsIsHewList * 1e6, 'o-',
#
#	   label = '$\\lambda = %0.1fnm$' % Lambda_nm)
#
#		plt.legend()
#		plt.xlabel('$\\vartheta$ ($\mu rad$)')
#		plt.ylabel('Hew')
#		plt.grid('on')
##		plt.title(Title)

	# ===================================================================================================
	if Task == 'hew scan':

		#--------------------------------------------------------------------------
		# PLOT HEW LIST
		plt.figure(321)
		for i, HewList in enumerate(HewCollection):
			StrLabel = '%0.1e' % XAxis[i]
			plot(DefocusList_mm, HewList *1e6,'.-', label = StrLabel)
#				plot(DefocusList_mm, 2*0.68* SigmaList * 1e6 * (1+i*1e-1),'x')
#				plt.legend(['Hew', '0.68 * 2 Sigma'])
			plt.legend()
#			lw.ToolLib.Debug.PutData('hew1',HewList *1e6,'tmp10')



		plt.title('HEW' + TitleAppend)
		plt.xlabel('defocus (mm)')
		plt.ylabel('Hew')
		plt.legend(title = XParameter)
		plt.grid('on')
		
	# ===================================================================================================
	# TASK: BEST FOCUS
	# ===================================================================================================
	if Task == 'best focus' or Task == 'best focus manual' or Task == 'best focus auto' or Task == "caustics":

		#--------------------------------------------------------------------------
		# PLOT HEW LIST
		plt.figure(322)
		for i, HewList in enumerate(HewCollection):
			iBest= np.argmin(HewList)
			if AutofocusMode & AUTOFOCUS.USE_AS_PREINPUT:
				BestFocalShift = BestFocalShiftList[i]
				BestHew = BestHewList[i]
				
				StrLabelBestDefocus = ', $\\Delta f = %0.1f mm$' % (BestFocalShift * 1e3)
				StrTitleBestDefocus = 'defocus (mm)'
			else:
				BestFocalShift  = np.NAN
				BestHew  =  np.NAN
				StrLabelBestDefocus = ''
				StrTitleBestDefocus = ''
				
			StrLabel = '%0.1f nm%s' % (XAxis[i] *1e9, StrLabelBestDefocus)
			p = plot(DefocusList_mm, HewList *1e6,'.-', label = StrLabel)
			
			try:
				if S['ShowSigma']:
					p2 = plot(DefocusList_mm,  2.35 * SigmaList * 1e6 ,'x', label = StrLabel + ' (FWHM)')
					p3 = plot(DefocusList_mm,  SigmaList * 1e6 ,'.', label = StrLabel + ' ($\sigma$)')
				
			except:
				pass
#				plot(DefocusList_mm, 2*0.68* SigmaList * 1e6 * (1+i*1e-1),'x')
#				plt.legend(['Hew', '0.68 * 2 Sigma'])
			Color = p[-1].get_color()

			plot(BestFocalShift * 1e3, BestHew * 1e6, 'o', color = Color)
			plot(DefocusList_mm[iBest], HewList[iBest] * 1e6, 'x', color = Color)
			plt.legend()
#			lw.ToolLib.Debug.PutData('hew1',HewList *1e6,'tmp10')



		plt.title( ('HEW (%s)' + TitleAppend) % FocussingElement.Name)
		plt.xlabel('defocus (mm)')
		plt.ylabel('Hew')
		plt.legend(title = '$\lambda$ ' + StrTitleBestDefocus)
		plt.grid('on')
	
		#--------------------------------------------------------------------------
		# The field at the best focus
		plt.figure(36)
		iBest= np.argmin(HewList)
		
		
# 		for i, Result in enumerate(ResultList):
# 			StrLabel = '%0.1f mm' % DefocusList_mm[i]
# 			plot(Result.S * 1e6, abs(Result.Intensity), label = StrLabel)
# 			
		x = ResultList[iBest].S  * 1e6
		y = ResultList[iBest].Intensity
		y = y/max(y)

		# Set peak at 0
		if 1==1:
			MaxIndex = y.argmax()
			MaxX = x[MaxIndex]
			x -= MaxX


		StrLabel = '%0.1f mm, %s' % (DefocusList_mm[i], FocussingElement.Name)
		p = plot(x, y,'.-', label = StrLabel)
		
		plt.xlabel('um')
		plt.ylabel('I')
		plt.title('Intensity @ best focus'  )
		plt.legend()
		plt.grid(which = 'both')
		plt.minorticks_on()
		
#		#--------------------------------------------------------------------------
#		# PLOT FIGUREERROR USED
#		FocussingElement.PlotFigureError(FigureIndex = 323)
		

	# ===================================================================================================
	# TASK: SIMPLE
	# ===================================================================================================
	if Task == 'simple' :


		#--------------------------------------------------------------------------
		# PLOT HEW LIST


		plt.figure(42)

		#--- plot intensity
		lw.ToolLib.CommonPlots.IntensityAtOpticalElement(Detector, FigureIndex = 42, color = 'g')
		plt.title('Intensity @ detector (simple sim.)' + TitleAppend)
		plt.xlabel('detector (mm)')
		plt.ylabel('I')
		plt.legend(title = '$\lambda (nm) & $ best focus')
		plt.grid('on')

	# ===================================================================================================
	# TASK: CAUSTICS
	# ===================================================================================================
	if Task == 'caustics' :


		#--------------------------------------------------------------------------
		# PLOT HEW LIST


		plt.figure(50)

		#--- plot intensity
		for i, ComputationData in enumerate(ResultList):
			x = ComputationData.S *1e6
			y = ComputationData.Intensity
			LabelStr = "$\Delta f = %0.2e m$" % DefocusList[i]
			plot(x, y, label = LabelStr)
			plt.title('Spot Profiles' + TitleAppend)
			plt.xlabel('detector (mm)')
			plt.ylabel('I')
			plt.legend(title = 'Spot Profiles')
			plt.grid('on')


	#--------------------------------------------------------------------------
	# PLOT FIGUREERROR USED
	FocussingElement.PlotFigureError(FigureIndex = 323)
	# ===================================================================================================

	#% Plot of the Computed Field

#	if YTypeScan == 0 :
#		plt.figure(33)
#		StrLabel = '%0.1f mm' % DefocusList_mm[i]
#		plot(Result.S * 1e6, abs(Result.Field), label = StrLabel)
#
#		plt.title('Computed Fields @ detector')
#		plt.xlabel('detector (um)')
#		plt.ylabel('W (a.u.)')
#		plt.legend(title = 'Defocus (mm)')

	#% Plot of the Computed Field
	if 1 == 1 and YTypeScan == 0 :
		plt.figure(34)
		for i, Result in enumerate(ResultList):
			StrLabel = '%0.1f mm' % DefocusList_mm[i]
			
			# Set the peak value at centre
			I = abs(Result.Intensity)
			MaxIndex = I.argmax()
			x = Result.S
			x -= x[MaxIndex]
			plot( x * 1e6, abs(Result.Intensity), label = StrLabel)

		plt.title('Intensity  @ detector %s (centred at 0)' % DetectorToUseName)
		plt.xlabel('detector (um)')
		plt.ylabel('W (a.u.)')
		plt.legend(title = 'Defocus (mm)')
		plt.grid(True, 'both')
		plt.minorticks_on()
	#% Plot of the Computed Field
#	if 1 == 1:
#		lw.ToolLib.CommonPlots.

#	try:
#		lw.ToolLib.CommonPlots.IntensityAtOpticalElement(, FigureIndex = 1001)
#	except:
#		pass

#%% plot caustics
	if 1==0:
		plt.figure(34)
		for I in ZCollection:
			plot(I)
			plt.title('best spot')
			plt.xlabel('detector (um)')
			plt.ylabel('I (a.u.)')

	#%% Best Focus: Plot of the Focal Shift
	if 1==0:
		plt.figure(35)
		plot(XParameterList *1e9, BestFocalShiftList,'o-')
		plt.title('Focal Shift')
		plt.xlabel(XParameter)
		plt.ylabel('Focal shift')

	#%% Best Focus: Plot of the HEW caustics
	if 1==0:
			plt.figure(36)
			plot(XParameterList *1e9, BestHewList,'o-')
			plt.title('HEW')
	#			plt.xlabel('detector (um)')
			plt.ylabel('HEW')
	#%% Plot della HEW caustic
	if YTypeScan == 0 and Task == "HEW":
		plt.figure(32)
		for i, HewList in enumerate(HewCollection):
			StrLabel = '%0.1f' % DefocusList_mm[i]
			plot(DefocusList_mm, HewList *1e6,'b.', label = 'HEW')
#				plot(DefocusList_mm, 2*0.68* SigmaList * 1e6 * (1+i*1e-1),'x')
			plt.title('HEWs')
			plt.xlabel('defocus (mm)')
			plt.ylabel('Hew')
#				plt.legend(['Hew', '0.68 * 2 Sigma'])
			plt.legend()
			lw.ToolLib.Debug.PutData('hew1',HewList *1e6,'tmp10')

	#%% CHECK1 Plot of the First Computed Field on the detector
	if 1==1:
		plt.figure(48)
		lw.ToolLib.CommonPlots.IntensityAtOpticalElement(Detector, 
												   FigureIndex = 48, 
												   color = 'b',
												   AppendToTitle = '(First Computed Field)')
		lw.ToolLib.Debug.PathTemporaryH5File
#		lw.ToolLib.Debug.PutData('s1', Detector.ComputationData.S,'tmp_total')
#		lw.ToolLib.Debug.PutData('i1', Detector.ComputationData.Intensity,'tmp1tmp_total00')

	#%% Plot the Meaningful Spot Profile (either at best focus ofnot) for each Iteration
	# Uses BestIList
	if 1==1:
		
		if AutofocusMode & AUTOFOCUS.FOR_EACH_X:
			Title = 'BEST FOCUS (normalized to max) @ %s\n%s' % (FocussingElement.Name, SessionTag)
		else:
			Title = 'FIXED FOCUS (normalized to max) @ %s\%s' %  (FocussingElement.Name, SessionTag)
		plt.figure(49)
		x = Detector.ComputationData.S
		try:
			for k,y in enumerate(BestIList):
				y = y/np.max(y)
				
				xToPlot = x * 1e6
				
				plt.plot(xToPlot,y, label = XParameterLabelList[k]) 
				plt.legend()
				
				plt.xlabel('um')
				plt.grid(True, which = 'major')
				plt.minorticks_on()
				plt.title(Title)
		except:
			pass
#			lw.ToolLib.CommonPlots.SmartPlot(x,y, 
#									XInfo = {'Units' : 'm', 
#									  'label' : XParameterLabelList[k]})

	#%% CHECK2 figure error
	if 1==0:
		lw.ToolLib.CommonPlots.FigureError(kb, FigureIndex = 49)
#%%   plot field on kb
	if 1==1:
		try:
			tl.Debug.PutData('ks1', kb.ComputationData.S,'tmp100')
			tl.Debug.PutData('ki1', kb.ComputationData.Intensity,'tmp100')
		except:
			pass
#%% plot 2D
	if 1==0:
		try:
			fig = plt.figure(666)
			ax = fig.gca(projection='3d')
			X, Y = np.meshgrid(XAxis*1e6, YAxis*1e3)
			Z = np.array(ZCollection).transpose()
			surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='hot', edgecolor = 'none',antialiased=True)
			plt.xlabel(XInfo.Name)
			plt.ylabel(YInfo.Name)
			plt.title('lambda = %0.1f nm'% (Lambda*1e9))
			plt.show()
		except:
			pass
	try:
		OptimizationSuccessList = [ x.OptResult.success for x in OptimizationResultList]
	except:
			pass
#%%--data save section--
#%% MANAGE Task Output (SAVE)


	# DEFAULT AND COMMON INFO (not all of them will be used)
	HewInfo = DataContainer(Name = 'HEW',
						Unit = 'm',
						Label = 'Spot Size (HEW)',
						VisualizationFactor = 1e6,
						VisualizationPrefix = 'u')

	LambdaInfo = DataContainer(	Name = 'Lambda',
							  Unit = 'm',
							  Label = '$\\lambda$',
							  VisualizationFactor = 1,
							  VisualizationPrefix = '')
	
	FocalShiftInfo = DataContainer(	Name = 'Focal Shift',
							  Unit = 'm',
							  Label = '$\\Delta f$',
							  VisualizationFactor = 1,
							  VisualizationPrefix = '')

	# MANAGE the TaskFolder content	
	if Task == TaskList.LAMBDA_SCAN:
		TaskFolder = 'TaskLambdaScan'
		
		TaskInfo = DataContainer(Plot1 = ('Lambda', 'Hew'),
						      	 Plot2 = ('Lambda', 'DeltaFocus'))
		

		
		OutputTask = [('TaskLambdaScan/Lambda',XAxis, LambdaInfo._GetDict() ),
					('TaskLambdaScan/Hew', BestHewList, HewInfo._GetDict()),
 					  ('TaskLambdaScan/FixedHew', AsIsHewList, HewInfo._GetDict()),
					   ('TaskLambdaScan/FocalShift', BestFocalShiftList, FocalShiftInfo._GetDict() ),
					   ]
	else:
		TaskFolder = 'TaskGeneric'
		OutputDefault  = []
		OutputTask = []	

	
	# ADD the common output
	if YTypeScan != -2:
		OutputDefault =[('ParameterScan/X',XAxis, XInfo._GetDict() ),
 					  ('ParameterScan/Y',YAxis, YInfo._GetDict() ),
 					  ('ParameterScan/Z',ZCollection, ZInfo._GetDict() )
					   ]
		

		
	OutputAttributes = OutputDefault + OutputTask
		
	#Update File Attributes
	FileAttributes.update({'TaskFolder' : TaskFolder})
#%% SAVE to h5
	lw.tl.FileIO.SaveToH5(FileOut,
					OutputAttributes, 
					Attributes = FileAttributes,  Mode = 'w')
#%%
	PathFileOut = FileOut

#%% Play Sound
	Beep(744,50)
	Beep(744,50)
	Beep(744,50)

	print("Current working path:\n " + os.getcwd())

	print("Output file:\n")
	print(20 * '=-.')
	print(FileOut)
	print(20 * '=-.')
	import playsound
	Str = str(Investigators.Paths.Sound)
	for i in range(1,2):
		playsound.playsound(Str)
	#%%
