# -*- coding: utf-8 -*-
"""
Same as OasysWiser 2 Wiser.py. The description goes here OR
we take it from MyDoc
"""

import TheOwls.ScriptLibBase as imp
MyScript = imp.TestScript1()
MyDoc = MyScript.__doc__

MySettings = {
    "---main settings---": None,
    "a": 10,
    "b": 2000,
    "c": "stocatso",
    "---specific settins---": None,
    "ColorOfMyShoes": "white",
    "SugarInTheCoffee": 1e-5,
    "RainbowsInTheSky": 1e10
}

MyScript.Settings = MySettings
MyScript.Run()
