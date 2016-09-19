import maya.OpenMaya

def Cas_printInfo(s):
	maya.OpenMaya.MGlobal.displayInfo(s)

def Cas_printWarning(s):
	maya.OpenMaya.MGlobal.displayWarning(s)
