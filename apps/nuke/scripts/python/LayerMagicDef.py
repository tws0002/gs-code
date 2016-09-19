#LayerMagic by David Emeny 
#
#Displays a dialog box asking user for up to eight layer names and their respective channel sets.
#Creates those layers and channels in the nuke script
#Creates a node with up to eight inputs, plus a 'Comp' input.
#When they connect up various parts of their script, those elements are shuffled into the new layers
#The 'Comp' is passed through into the normal rgba channels.
#Now they can add a write node, set file_type to 'exr', set channels to 'all', depth to 32bit
#When rendered, the exr will contain the comp, plus all their layers inside it.

import nuke

def MNElayerMagic():
	#ask for layer names
	enumerationPulldown = "rgba rgb a "
	
	p = nuke.Panel("Layer Magic")
		
	p.addSingleLineInput("Layer 1:", "BG")
	p.addEnumerationPulldown("Layer 1 channels:", enumerationPulldown)
	p.addSingleLineInput("Layer 2:", "FG")
	p.addEnumerationPulldown("Layer 2 channels:", enumerationPulldown)
	p.addSingleLineInput("Layer 3:", "")
	p.addEnumerationPulldown("Layer 3 channels:", enumerationPulldown)
	p.addSingleLineInput("Layer 4:", "")
	p.addEnumerationPulldown("Layer 4 channels:", enumerationPulldown)
	p.addSingleLineInput("Layer 5:", "")	
	p.addEnumerationPulldown("Layer 5 channels:", enumerationPulldown)
	p.addSingleLineInput("Layer 6:", "")	
	p.addEnumerationPulldown("Layer 6 channels:", enumerationPulldown)
	p.addSingleLineInput("Layer 7:", "")
	p.addEnumerationPulldown("Layer 7 channels:", enumerationPulldown)
	p.addSingleLineInput("Layer 8:", "")	
	p.addEnumerationPulldown("Layer 8 channels:", enumerationPulldown)
		
	p.addButton("Cancel")
	p.addButton("OK")
	pResult = p.show()
	
	if pResult == 1:
		#if OK was pressed, do stuff
		layerNames = []
		layerChannels = []
		#put all non-blank inputs into a list
		for i in range(1,9):
			theName = p.value('Layer ' + str(i) + ':')
			theChannels = p.value('Layer ' + str(i) + ' channels:')
			if theName.strip() is not "":
				layerNames.append(theName)
				layerChannels.append(theChannels)
		
		numLayers = len(layerNames)
		
		#create the new layers and channels
		for i in range(0,numLayers):
			theName = layerNames[i]
			theChannels = layerChannels[i]
			
			#for nuke versions before 6.2v3, use the tcl versions instead
			if theChannels == "rgba":
				#nuke.Layer(theName, ['red', 'green', 'blue', 'alpha'])
				nuke.tcl('add_layer { ' + theName + ' ' + theName + '.red ' + theName + '.green ' + theName + '.blue ' + theName + '.alpha }')
			elif theChannels == "rgb":
				#nuke.Layer(theName, ['red', 'green', 'blue'])
				nuke.tcl('add_layer { ' + theName + ' ' + theName + '.red ' + theName + '.green ' + theName + '.blue }')
			elif theChannels == "a":
				#nuke.Layer(theName, ['alpha'])
				nuke.tcl('add_layer { ' + theName + ' ' + theName + '.alpha }')
			
		#reverse the order of the layer names so they appear in order on the node
		layerNames.reverse()
		layerChannels.reverse()
		
		#make a group
		LayerMagicGroup = nuke.createNode('Group')
		LayerMagicGroup.knob('name').setValue('LayerMagic')
		LayerMagicGroup.begin()
		
		#create first input node 'Comp'
		input1 = nuke.createNode('Input', inpanel = False)
		input1.knob('name').setValue('Comp')
		
		for i in range(0,numLayers):
			theName = layerNames[i]
			theChannels = layerChannels[i]
			
			#make shufflecopy node
			s = nuke.createNode('ShuffleCopy', inpanel = False)
			#make input node, name it
			inp = nuke.createNode('Input', inpanel = False)
			inp.knob('name').setValue(layerNames[i])
			#set input '1' to the new input
			s.setInput(1,inp)
			
			#shuffle the channels
			
			#rgb already passed through by default, just pass alpha through too
			s['alpha'].setValue('alpha2') 
			
			#set second output to our custom layer
			s['out2'].setValue(theName) 
			
			if theChannels == "rgba":
				#nuke names it's channels all wrong, this is actually right
				s['black'].setValue('red')
				s['white'].setValue('green')
				s['red2'].setValue('blue')
				s['green2'].setValue('alpha')
			elif theChannels == "rgb":
				#nuke names it's channels all wrong, this is actually right
				s['black'].setValue('red')
				s['white'].setValue('green')
				s['red2'].setValue('blue')
			elif theChannels == "a":
				#nuke names it's channels all wrong, this is actually right
				s['black'].setValue('alpha')
		
			inp.knob("selected").setValue(False)
			s.knob("selected").setValue(True)
		
		nuke.createNode('Output', inpanel = False)
		LayerMagicGroup.end()
		tabKnob = nuke.Tab_Knob('Layer Magic v1')
		LayerMagicGroup.addKnob(tabKnob)
		textKnob = nuke.Text_Knob('LayerMagic',' ','Connect your comp and your layer elements,\nthen render out an EXR, with channels set to "all"')
		LayerMagicGroup.addKnob(textKnob)
