# -*- coding: utf-8 -*-
"""
The description goes here.
Bla bla bla.

As an alternative, we can decide that each one of script files CAN contain a
MyDoc attribute, which is displayed instead of __doc__ (if existing).
Here I show a possible blueprint

"""

import TheOwls.Tools as imp
MyFunction = imp.GetWiserBeamline
MyDoc = MyFunction.__doc__


wb = owt.GetWiserBeamline(in_object_1)
out_object = wb
