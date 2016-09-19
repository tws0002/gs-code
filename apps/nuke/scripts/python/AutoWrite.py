#
# autowrite.py
#
# Travis Button
# Built upon tutorial by Tim BOWMAN [puffy@netherlogic.com]
#
# Semi-automatic Write node output paths lead to fewer user errors and greater
# consistency in file-naming.
#

import nuke

def dropAutoWrite():
	"""
	Creates an automatic Write node (an "AutoWrite") which uses the name and 
	path of the Nuke script that it's in to create it's own output path.

	Changes made to the script's name (such as versioning up) wil be reflected 
	in the output path auto-magically with no user intervention.
	"""

	# Create the Write node that will become an AutoWrite
	w= nuke.createNode('Write', inpanel=False)
	# Rename it to AutoWrite
	# (Also, deal with the number problem)
	count = 1
	while nuke.exists('AutoWrite' + str(count)):
		count += 1
	w.knob('name').setValue('AutoWrite' + str(count))

	#Get version number
	#snagVersion = nukescripts.version_get( nuke.Root().name(), 'v' ).__getitem__(1)

	# Add the tab to hold the variables containing path fragments so we can have
	# a less messy file path.
	pathFragmentsTab = nuke.Tab_Knob("Path Fragments")
	pathFragmentsTab.setFlag(nuke.INVISIBLE)

	projRootKnob = nuke.EvalString_Knob('proj_root', 'Project Root', '[join [lrange [split [value root.name] / ] 0 3 ] / ]')
	projRootKnob.setFlag(nuke.INVISIBLE)
	shotKnob = nuke.EvalString_Knob('shot', 'Shot Name', '[lrange [split [value root.name] / ] 8 8 ]')
	shotKnob.setFlag(nuke.INVISIBLE)
	projectKnob = nuke.EvalString_Knob('project', 'Project', '[lrange [split [value root.name] / ] 4 4 ]')
	projectKnob.setFlag(nuke.INVISIBLE)
	scriptVersionKnob = nuke.EvalString_Knob('scriptVersion', 'Version', "v[python nukescripts.version_get( nuke.Root().name(), 'v' ).__getitem__(1)]")
	scriptVersionKnob.setFlag(nuke.INVISIBLE)
	scriptKnob = nuke.EvalString_Knob('script', 'Script Name', '[file rootname [file tail [value root.name] ] ]')
	scriptKnob.setFlag(nuke.INVISIBLE)

	w.addKnob(pathFragmentsTab)
	w.addKnob(projRootKnob)
	w.addKnob(shotKnob)
	w.addKnob(projectKnob)
	w.addKnob(scriptVersionKnob)
	w.addKnob(scriptKnob)

	# Display the values of our path fragment knobs on the node in the DAG for
	# error-checking.
	# This can be turned off if it makes too much of a mess for your taste.
	feedback = """
	Output Path: [value file]

	"""
	#w.knob('label').setValue(feedback)

	proj_root = w.knob('proj_root').value()
	shot = w.knob('shot').value()
	project = w.knob('project').value()
	scriptVersion = w.knob('scriptVersion').value()
	script = w.knob('script').value()
	digit = '%04d'

	# Re-assemble the path fragments into a proper output path
	output_path = "%(proj_root)s/%(project)s/04_renders/%(shot)s/03_composite/%(script)s/%(script)s.%(digit)s.png" % locals()
	w.knob('file').fromScript(output_path)

	# Set values for OUTPUT settings
	w.knob('colorspace').setValue("sRGB")
	w.knob('file_type').setValue("png")
	w.knob('datatype').setValue("16 bit")

	#fill the 'before render' box with python code to create the directory if it doesn't exist
	w.knob('beforeRender').setValue("import createWriteDir; createWriteDir.main()")