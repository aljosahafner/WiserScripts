


#%%

class Script():
	'''
	This class implement a script object. 
	'''
	import json
	DefaultSettings = {'default' : 'bad'}
	
	def __init_subclass__(self, Settings = DefaultSettings):
		self._Settings = self.DefaultSettings
		self._MyDoc = str(self.DefaultSettings)	
	
	@property
	def Settings(self):
		return self._Settings
	
	@Settings.setter
	def Settings(self,x : dict):
		self._Settings = x
	
	@property 
	def __doc__(self):
		return self._MyDoc
		
	
	def GetSettingsStr(self, VariableName = 'MySettings'):
		'''
		Return settings as string, where entries are separated
		by line feeds.
		'''
		
		if VariableName == '':
			_ = ''
		else:
			_ = VariableName  + ' = '
			
		Str = _ + Script.json.dumps(self.Settings, indent=4)
		Str = Str.replace('null', 'None')
		return Str
	 
	def GetAutoCodeForScriptFile(self):
		'''
		Return these lines of code
		
		MyDoc = MyScript.__doc__
		MySettings = {
				settings goes here}
		MyScript.Settings = MySettings
		MyScript.Run()
		
		''' 
		StrList = ['MyDoc = MyScript.__doc__', 
			 self.GetSettingsStr('MySettings'),
			'MyScript.Settings = MySettings',
			'MyScript.Run()']
		Str = '\n'.join(StrList)
		return Str
	 
	def Run():
		raise NotImplementedError("The method Run is abstract and is not implemented")
		
	#%%
class TestScript1(Script):
	'''
	This script is doing wonderful things.
	'''
	DefaultSettings = {
				'---main settings---' : None,
				'a':1, # description of parameter A
				'b':2, # description of parameter B,
				'c':'stocatso', # description of parameter c
				'---specific settins---' :None,
				'ColorOfMyShoes' : 'white',
				'SugarInTheCoffee' : 10,
				'RainbowsInTheSky': 0.5}
	
	def Run(self):
		print('\n')
		print("The script is doing stuff here, using these settings")
		print(self.SettingsString)


