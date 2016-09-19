import os, subprocess, re
import nuke

def exploreMe():

	n = nuke.selectedNodes()
	
	for i in n:
               
		theFile = i.knob('file').value()
		base = os.path.dirname(theFile)
		command = "explorer " + base + "/"
		command = re.sub('/','\\\\', command)
		subprocess.Popen(command)

exploreMe()