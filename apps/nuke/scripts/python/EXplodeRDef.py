import nuke
import string

#Takes a selected EXR read node and explodes out the channel layers into RGBA nodes with thumbnails
#Each is a group consisting of a Shuffle and a Remove
#Shuffles the layer into rgba, and removes anything else
#If the layer contains unusual channels, or more than 4 channels, they will be separated out. 

def MNE_EXplodeR():
	
	readNode = nuke.selectedNode()
	if readNode.Class()=='Read':
		#get resolution
		resX = str(readNode.width())
		resY = str(readNode.height())
		
		#get Read path
		readPath = readNode['file'].value()
		pathArray = string.split(readPath, "/")
		i = 0
		for pathBit in pathArray:
			if (i == len(pathArray)-1):
				fileName=pathBit
				break
			i = i+1
		
		#get extension and filename
		nameBits = string.split(fileName, ".")
		i = 0
		for nameBit in nameBits:
			if (i == len(nameBits)-1):
				fileType = nameBit
			i = i+1
		
		if fileType=='exr':
			cStore = ""
			nx = readNode['xpos'].value()
			ny = readNode['ypos'].value()
			
			i = 0
			groupNodes = []
			textNodes = []
			theNames = []
			normalChannels = ['r','g','b','a','red','green','blue','alpha','x','y','z','MX','MY','MZ','NX','NY','NZ','Z']
			
			#check if this actually contains other layers
			otherChannelsExist = False
			for rnc in readNode.channels():
				layerBits = string.split(rnc, ".")
				if not (layerBits[0] == 'rgba'):
					otherChannelsExist = True
					break
			
			if otherChannelsExist:
				#make a dot node
				d = nuke.createNode('Dot', inpanel = False)
			
				for c in readNode.channels():
					layerBits = string.split(c, ".")
					layerName = layerBits[0]
					channelName = layerBits[1]
					
					if not(layerName==cStore) or (channelName not in normalChannels):
						#this is a new layer
						g = nuke.createNode('Group', inpanel = False)
						if channelName in normalChannels:
							groupName = checkNodeName(layerName)
						else:
							groupName = checkNodeName(layerName+'.'+channelName)
						g['name'].setValue(groupName)
						
						g.begin()        
						inp = nuke.createNode('Input', inpanel = False)
						inp['selected'].setValue('False')
						
						if channelName in normalChannels:
							s = nuke.createNode('Shuffle', inpanel = False)
							s.setInput(0,inp)
							s['in'].setValue(layerName)
							#check if this is just a 3 channel layer (ie r,g,b) and set alpha to black
							count = 0
							for c2 in readNode.channels():
								layerBits2 = string.split(c2, ".")
								if layerBits2[0]==layerName:
									count = count+1
							if count==3:
								#there are three channels with this layer's name
								s['alpha'].setValue('black')
								
							s['selected'].setValue('True')
							
						else:
							cp = nuke.createNode('Copy', inpanel = False)
							cp.setInput(0,inp)
							cp.setInput(1,inp)
							for f in ['from0','from1','from2','from3']:
								cp[f].setValue(c)
							cp['to0'].setValue('rgba.red')
							cp['to1'].setValue('rgba.green')
							cp['to2'].setValue('rgba.blue')
							cp['to3'].setValue('rgba.alpha')
							cp['selected'].setValue('True')
							
							
						r = nuke.createNode('Remove', inpanel = False)
						r['operation'].setValue('keep')
						r['channels'].setValue('rgba')
						nuke.createNode('Output', inpanel = False)
						g.end()
						
						g.setInput(0,d)
						g['postage_stamp'].setValue(True)
						newXpos = nx - (100*i)
						g['xpos'].setValue(newXpos)
						g['ypos'].setValue(ny+250)
						if layerName=='rgba':
							g.knob('tile_color').setValue(int(0xaaff55ff))
						else:
							g.knob('tile_color').setValue(int(0xe955ffff))
						
						groupNodes.append(g)
						if channelName in normalChannels:
							theNames.append(layerName)
						else:
							theNames.append(layerName+'.'+channelName)
						i = i + 1
					cStore = layerName
				
				#create a new group for the contact sheet and text nodes
				csGroup = nuke.createNode('Group', inpanel = False)
				groupName = checkNodeName('EXR_sheet')
				
				csGroup['name'].setValue(groupName)
				csGroup['xpos'].setValue(newXpos)
				csGroup['ypos'].setValue(ny+100)
				csGroup['postage_stamp'].setValue(True)
				
				csGroup.begin()
				
				#create a contact sheet node
				cs = nuke.createNode('ContactSheet', inpanel = False)
				cs.knob('width').setValue(float(resX))
				cs.knob('height').setValue(float(resY))
				cs['center'].setValue(True)
				cs['roworder'].setValue('TopBottom')
				cs['gap'].setValue(5)
				cs['selected'].setValue(False)
				
				#create another contact sheet node to get outline alpha (so the sheet background will appear grey)
				csMatte = nuke.createNode('ContactSheet', inpanel = False)
				csMatte.knob('width').setValue(float(resX))
				csMatte.knob('height').setValue(float(resY))
				csMatte['center'].setValue(True)
				csMatte['roworder'].setValue('TopBottom')
				csMatte['gap'].setValue(5)
				csMatte['selected'].setValue(False)
				
				numGroups = len(groupNodes)
				
				for i in range(0,numGroups):
					#create input
					inp = nuke.createNode('Input', inpanel = False)
					
					#create text for contact sheet
					t = nuke.createNode('Text', inpanel = False)
					t['message'].setValue(theNames[i])
					t['Transform'].setValue(True)
					t['box'].setValue([float(resX)*0.01,float(resY)*0.9,float(resX)*0.99,float(resY)*0.98])
					t['yjustify'].setValue('top')
					t['size'].setValue(int(resX)/20) #adjust the size based on the EXR resolution
					
					#create reformat node
					ref = nuke.createNode('Reformat', inpanel = False)
					ref['type'].setValue('scale')
					theScale = 1.0 / numGroups
					ref['scale'].setValue(theScale)
					
					#create shuffle node
					sh = nuke.createNode('Shuffle', inpanel = False)
					sh['red'].setValue('black')
					sh['green'].setValue('black')
					sh['blue'].setValue('black')
					sh['alpha'].setValue('white')
					sh['black'].setValue('white')
					
					cs.setInput(i,ref)
					sh.setInput(0,ref)
					csMatte.setInput(i,sh)
					
					ref['selected'].setValue(False)
					sh['selected'].setValue(False)
					
					
				#choose the best layout depending on the number of layers
				if numGroups==1:
					cs['rows'].setValue(1)
					cs['columns'].setValue(1)
					csMatte['rows'].setValue(1)
					csMatte['columns'].setValue(1)
				elif numGroups==2:
					cs['rows'].setValue(1)
					cs['columns'].setValue(2)
					csMatte['rows'].setValue(1)
					csMatte['columns'].setValue(2)	
				elif numGroups==3 or numGroups==4:
					cs['rows'].setValue(2)
					cs['columns'].setValue(2)
					csMatte['rows'].setValue(2)
					csMatte['columns'].setValue(2)	
				elif numGroups==5 or numGroups==6:
					cs['rows'].setValue(2)
					cs['columns'].setValue(3)
					csMatte['rows'].setValue(2)
					csMatte['columns'].setValue(3)	
				elif numGroups==7:
					cs['rows'].setValue(2)
					cs['columns'].setValue(4)
					csMatte['rows'].setValue(2)
					csMatte['columns'].setValue(4)	
				elif numGroups==8 or numGroups==9:
					cs['rows'].setValue(3)
					cs['columns'].setValue(3)
					csMatte['rows'].setValue(3)
					csMatte['columns'].setValue(3)
				elif numGroups==10 or numGroups==11 or numGroups==12:
					cs['rows'].setValue(3)
					cs['columns'].setValue(4)
					csMatte['rows'].setValue(3)
					csMatte['columns'].setValue(4)
				else:
					#do nothing
					cs['center'].setValue(True)	
					csMatte['center'].setValue(True)
				
				#create grade node to produce background colour
				csMatte['selected'].setValue(True)
				gr = nuke.createNode('Grade', inpanel = False)
				gr['add'].setValue(0.1)
				gr['maskChannelInput'].setValue('rgba.alpha')
				gr['invert_mask'].setValue('true')
				
				#create invert node
				inv = nuke.createNode('Invert', inpanel = False)
				inv['channels'].setValue('alpha')
				
				#create premult node
				pre = nuke.createNode('Premult', inpanel = False)
				
				#create merge and output node
				cs['selected'].setValue(True)
				mer = nuke.createNode('Merge', inpanel = False)
				nuke.createNode('Output', inpanel = False)
				mer.setInput(0,pre)
				
				csGroup.end()
				
				#connect the groups to the contact sheet group inputs
				for i in range(0,numGroups):
					csGroup.setInput(i,groupNodes[i])
				
				#select everything except the read node
				for g in groupNodes:
					g['selected'].setValue(True)
				#for t in textNodes:
					#t['selected'].setValue(True)
				d['selected'].setValue(True)
				csGroup['selected'].setValue(True)
				readNode['selected'].setValue(False)
				
			else:
				nuke.message('This EXR only contains RGBA channels.')
			
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