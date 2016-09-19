# convertTex2EXR v0.1 by Henry Foster, henry@toadstorm.com
# this script currently is for PC only
# usage: run in maya to convert all textures above size fileSizeThresh to tiled EXRs and repath file nodes.
# requires installation of nuke and the compiled openEXR library, or at least exrmaketiled.exe
# also requires img2exr.py in your nuke's install directory (wherever nuke.exe is)
# change the nukePath, nukeExe, openExrPath and fileSizeThresh for your own system configuration
# to run in maya's python window:
#    import convertTex2EXR
#    convertTex2EXR.convertTex2EXR()

def convertTex2EXR(fileSizeThresh=9.0):
	import pymel.core as pm
	import os
	import sys
	import subprocess

	nukePath = "//SCHOLAR/assets/SCHOLARPREFS/NUKE/5.1v4_64bit/"
	nukeExe = "Nuke5.1.exe"
	openExrPath = "//SCHOLAR/assets/SCHOLARPREFS/UTILS/openexr-1.4.0-vs2005/bin/"
	texList = pm.ls(type='file')
	print('\nBeginning conversion of all file textures above '+str(fileSizeThresh)+' megabytes.')
	# pm.mel.eval('print("eat my shit")') # this evaluates mel statements

	for tex in texList:
		texPath = tex.fileTextureName.get() 
		# should return full UNC path
		fileSize = os.path.getsize(texPath) / (1024*1024.0)
		fileExt = texPath[-4:]
		# print fileExt 
		if ((fileSize > fileSizeThresh) and (fileExt != ".exr")):
			# this file is huge and should be converted.
			# subprocess.PIPE: Special value that can be used as the stdin, stdout or stderr argument to Popen and indicates that a pipe to the standard stream should be opened.
			vomit = subprocess.Popen('"'+nukePath+nukeExe+'" -t "'+nukePath+'img2exr.py" "'+texPath+'"', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			# The value returned from a call to communicate() is a tuple with two values, the first is the data from stdout and the second is the data from stderr.
			stdout, stderr = vomit.communicate() 
			# this should force a pause until the process is finished, since it's waiting for stdout to say something.
			logFile = open(r"C:\img2exr.log","r")
			exrPath = logFile.readline()
			# now we have to tile this guy using exrMakeTiled.
			puke = subprocess.Popen('"'+openExrPath+'exrmaketiled.exe" -m "'+exrPath+'" "'+exrPath+'"', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			stdout, stderr = puke.communicate()
			# the in and out file is the same, so now we replace the texture node's file with the new fancy EXR.
			tex.fileTextureName.set(exrPath)
			# also need to set the filter type to mipmap for vray to utilize this shit
			tex.filterType.set(1)
			print('\nset file node '+tex+' to tiled EXR: '+exrPath)
	print('\nEXR conversion complete!')