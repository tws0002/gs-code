import nuke

#Takes a stereo image and formats it into a single 'Side By Side' image, for viewing on a 3D TV. The left and right sides are squashed horizontally and placed next to each other in the same format as the input. If this is a non-stereo comp, it will detect that and give LEFT and RIGHT inputs for you to plug in your two left and right images.

def MNE_sideBySide3D():
	#store this for later
	selectedNode = nuke.selectedNode()

	#make a group
	g = nuke.createNode('Group', inpanel=False)
	g['name'].setValue(checkNodeName('SideBySide3D'))
	g.begin()
	
	#create a test node to check if this is a stereo comp
	test = nuke.createNode('JoinViews', inpanel=False)
	
	#create first/left input
	il = nuke.createNode('Input', inpanel=False)
	il['selected'].setValue(False)
	
	if test.maxInputs() == 2:
		#set up for stereo views
		
		#create left and right OneView nodes
		ovL = nuke.createNode('OneView',inpanel=False)
		ovL['view'].setValue('left')
		ovL.setInput(0,il)
		ovL['selected'].setValue(False)
		
		ovR = nuke.createNode('OneView',inpanel=False)
		ovR['view'].setValue('right')
		ovR.setInput(0,il)
		ovR['selected'].setValue(False)
		
		#create dot
		d1 = nuke.createNode('Dot', inpanel=False)
		d1.setInput(0,ovL)
		d1['selected'].setValue(False)
		
		#create dot
		d2 = nuke.createNode('Dot', inpanel=False)
		d2.setInput(0,ovR)
		d2['selected'].setValue(False)
	else:
		#set up for normal mono view
		
		#create right input, rename 1st input
		il['name'].setValue('left')
		il['selected'].setValue(False)
		
		ir = nuke.createNode('Input', inpanel=False)
		ir['name'].setValue('right')
		ir['selected'].setValue(False)
		
		#create dot
		d1 = nuke.createNode('Dot', inpanel=False)
		d1.setInput(0,il)
		d1['selected'].setValue(False)
		
		#create dot
		d2 = nuke.createNode('Dot', inpanel=False)
		d2.setInput(0,ir)
		d2['selected'].setValue(False)
		
		
	#left side------------------
	
	ref1 = nuke.createNode('Reformat', inpanel=False)
	ref1['type'].setValue('scale')
	ref1['scale'].setValue([0.5,1])
	ref1['resize'].setValue('distort')
	ref1['black_outside'].setValue(True)
	ref1['pbb'].setValue(True)
	ref1.setInput(0,d1)
	ref1['selected'].setValue(False)
	
	r = nuke.createNode('Remove', inpanel=False)
	r['operation'].setValue('keep')
	r['channels'].setValue('rgb')
	r.setInput(0,d1)
	r['selected'].setValue(False)
	
	sh = nuke.createNode('Shuffle', inpanel=False)
	sh['red'].setValue('black')
	sh['green'].setValue('black')
	sh['blue'].setValue('black')
	sh['alpha'].setValue('black')
	sh.setInput(0,r)
	sh['selected'].setValue(False)

	m1 = nuke.createNode('Merge', inpanel=False)
	#m1['inputs'].setValue(2)
	m1['operation'].setValue('plus')
	m1['bbox'].setValue('B')
	m1.setInput(0,sh)
	m1.setInput(1,ref1)
	m1['selected'].setValue(False)

	m2 = nuke.createNode('Merge', inpanel=False)
	#m2['inputs'].setValue(2)
	m2['operation'].setValue('plus')
	m2['bbox'].setValue('B')
	#set A input later
	m2.setInput(0,sh)
	m2['selected'].setValue(False)

	m3 = nuke.createNode('Merge', inpanel=False)
	#m3['inputs'].setValue(2)
	m3['operation'].setValue('plus')
	m3.setInput(0,m1)
	m3.setInput(1,m2)
	m3['selected'].setValue(False)


	#right side------------------

	cr1 = nuke.createNode('Crop',inpanel=False)
	cr1['box'].setValue(0,0)
	cr1['box'].setValue(0,1)
	cr1['box'].setExpression('input.width',2)
	cr1['box'].setExpression('input.height',3)
	cr1.setInput(0,d2)
	cr1['selected'].setValue(False)

	ref2 = nuke.createNode('Reformat', inpanel=False)
	ref2['type'].setValue('scale')
	ref2['scale'].setValue([0.5,1])
	ref2['resize'].setValue('distort')
	ref2['black_outside'].setValue(True)
	ref2.setInput(0,cr1)
	ref2['selected'].setValue(False)

	t1 = nuke.createNode('Transform', inpanel=False)
	t1['translate'].setExpression('input.width',0)
	t1['translate'].setValue(0,1)
	t1['center'].setExpression('input.width/2',0)
	t1['center'].setExpression('input.height/2',1)
	t1.setInput(0,ref2)
	t1['selected'].setValue(False)

	#join left side
	m2.setInput(1,t1)
	m2['selected'].setValue(False)

	cr2 = nuke.createNode('Crop',inpanel=False)
	cr2['box'].setValue(0,0)
	cr2['box'].setValue(0,1)
	cr2['box'].setExpression('input.width',2)
	cr2['box'].setExpression('input.height',3)
	cr2['crop'].setValue(False)
	cr2.setInput(0,m3)
	cr2['selected'].setValue(False)
	
	
	o = nuke.createNode('Output', inpanel=False)
	o.setInput(0,cr2)
	
	g.end()
	
	#connect the input (or the left input) to the last selected node in the comp
	g.setInput(0,selectedNode)
	
def checkNodeName(theName):
	#adds a number in brackets to the string if another node
	#exists with that name, otherwise just returns the string
	i = 1
	stillChecking = True
	origName = theName
	while stillChecking:
		alreadyUsed = False
		for a in nuke.allNodes():
			if (a['name'].value()==(theName)):
				alreadyUsed = True	
				break
		if alreadyUsed:
			theName = origName + ' (' + str(i) + ')'
			i = i+1	
		else:
			stillChecking=False
	
	return theName