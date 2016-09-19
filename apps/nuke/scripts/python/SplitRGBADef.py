import nuke

#Splits selected node off into RGBA shuffle nodes
#Only splits off the alpha if there is an alpha channel

def MNE_SplitRGBA():
	
	n = nuke.selectedNode()
	
	numChannels = len(n.channels())

	posX = n['xpos'].value()
	posY = n['ypos'].value()
	yOffset = 150
	dyOffset = 88
	
	#create dot
	n['selected'].setValue(False)
	d = nuke.createNode('Dot', inpanel = False)
	d['xpos'].setValue(posX+34)
	d['ypos'].setValue(posY+dyOffset)
	d.setInput(0,n)
	
	#create RED
	r = nuke.createNode('Shuffle', inpanel=False)
	r['name'].setValue(checkNodeName('Red'))
	r['xpos'].setValue(posX)
	r['ypos'].setValue(posY + yOffset)
	r['green'].setValue('red')
	r['blue'].setValue('red')
	r['alpha'].setValue('red')
	r['tile_color'].setValue(int(0xff0000ff))
	r['selected'].setValue(False)
	
	#create dot above green
	#d['selected'].setValue(False)
	dg = nuke.createNode('Dot', inpanel = False)
	dg['xpos'].setValue(posX+134)
	dg['ypos'].setValue(posY+dyOffset)
	dg.setInput(0,d)
	dg['selected'].setValue(False)
	
	#create GREEN
	g = nuke.createNode('Shuffle', inpanel=False)
	g['name'].setValue(checkNodeName('Green'))
	g['xpos'].setValue(posX+100)
	g['ypos'].setValue(posY + yOffset)
	g['red'].setValue('green')
	g['blue'].setValue('green')
	g['alpha'].setValue('green')
	g['tile_color'].setValue(int(0xff00ff))
	g['selected'].setValue(False)
	g.setInput(0,dg)
	
	#create dot above blue
	db = nuke.createNode('Dot', inpanel = False)
	db['xpos'].setValue(posX+234)
	db['ypos'].setValue(posY+dyOffset)
	db.setInput(0,dg)
	db['selected'].setValue(False)
	
	#create BLUE
	b = nuke.createNode('Shuffle', inpanel=False)
	b['name'].setValue(checkNodeName('Blue'))
	b['xpos'].setValue(posX+200)
	b['ypos'].setValue(posY +yOffset)
	b['red'].setValue('blue')
	b['green'].setValue('blue')
	b['alpha'].setValue('blue')
	b['tile_color'].setValue(int(0x222dffff))
	b['selected'].setValue(False)
	b.setInput(0,db)
	
	#create ALPHA (if needed)
	if 'rgba.alpha' in n.channels():
		#create dot above alpha
		da = nuke.createNode('Dot', inpanel = False)
		da['xpos'].setValue(posX+334)
		da['ypos'].setValue(posY+dyOffset)
		da.setInput(0,db)
		
		#create ALPHA
		a = nuke.createNode('Shuffle', inpanel=False)
		a['name'].setValue(checkNodeName('Alpha'))
		a['xpos'].setValue(posX+300)
		a['ypos'].setValue(posY +yOffset)
		a['red'].setValue('alpha')
		a['green'].setValue('alpha')
		a['blue'].setValue('alpha')
		a['tile_color'].setValue(int(0xffffffff))
		a['selected'].setValue(False)
		a.setInput(0,da)


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