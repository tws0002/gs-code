import nuke
import string

#Select a tracked camera and this will create a duplicate projection camera with a freeze frame control.
#Saves you having to remove all animation from a copied camera, plus gives you the advantage of changing the frozen frame later
#Also means any updates to the camera tracker will be reflected in all your projection cameras too.
#You can copy and paste any ProjectorCam node once it has been made.
#It works with cameras tracked in Nuke, as well as imported cameras.

#Made by David Emeny, inspired by a tutorial from FXPHD's Sean Devereaux

def MNE_ProjectorCam():
		
	#check if any nodes are selected
	if len(nuke.selectedNodes()) == 1:
		
		#get selected camera
		cam = nuke.selectedNode()

		#check it's a camera
		if cam.Class() == "Camera" or cam.Class() == "Camera2":
			
			#check it's not a ProjectorCam
			if cam['label'].value() != "[value freezeFrame]":
				
				#store its position
				xx = cam['xpos'].value()
				yy = cam['ypos'].value()
			
				#copy the camera
				nuke.nodeCopy(cam['name'].value())
				#deselect first camera
				cam['selected'].setValue(False)
				#paste it into new reference
				newCam = nuke.nodePaste(cam['name'].value())
				#show the panel in properties
				newCam.showControlPanel()
				#change the name
				newName = checkNodeName('Proj_Cam')
				newCam['name'].setValue(newName)
				
				#Create a custom tab in the new camera node (which will show by default)
				tabKnob = nuke.Tab_Knob('Freeze Frame')
				newCam.addKnob(tabKnob)
					
				#make the knob for the tab
				intKnob = nuke.Int_Knob('freezeFrame','Freeze on frame')
				intKnob.setValue(nuke.frame())
				updateKnob = nuke.PyScript_Knob('Set to this frame')
				updateKnob.setValue("nuke.thisNode()['freezeFrame'].setValue(nuke.frame())")
				
				#add the new knobs
				newCam.addKnob(intKnob)
				newCam.addKnob(updateKnob)
				
				#set the freeze frame to show on the node's label
				newCam['label'].setValue('[value freezeFrame]')
				
				#turn the new camera node an icy blue
				newCam['tile_color'].setValue(int(0x84e0d0ff))
				
				#position it next to the original camera
				newCam['xpos'].setValue(xx+200)
				newCam['ypos'].setValue(yy)
				
				#link all values (and add the expression)
				
				if(cam.Class()=="Camera2"):
					#this is an imported camera, so do things differently
					#there are no expressions only curves. If there's no animation, the value is already there
					#so don't do anything
				
					#translate
					if(newCam['translate'].isAnimated()):
						newCam['translate'].setExpression("curve(freezeFrame)")
					
					#rotate
					if(newCam['rotate'].isAnimated()):
						newCam['rotate'].setExpression("curve(freezeFrame)")
					
					#win_translate
					if(newCam['win_translate'].isAnimated()):
						newCam['win_translate'].setExpression("curve(freezeFrame)")
					
					#win_scale
					if(newCam['win_scale'].isAnimated()):
						newCam['win_scale'].setExpression("curve(freezeFrame)")

					#focal
					if(newCam['focal'].isAnimated()):
						newCam['focal'].setExpression("curve(freezeFrame)")
					
					#haperture
					if(newCam['haperture'].isAnimated()):
						newCam['haperture'].setExpression("curve(freezeFrame)")
					
					#vaperture
					if(newCam['vaperture'].isAnimated()):
						newCam['vaperture'].setExpression("curve(freezeFrame)")
				
				else:
				
					#translate
					tempString =  newCam['translate'].toScript() #get the expression string
					tempArray = string.split(tempString, " ") #split into three for x,y,z
					theExpr = tempArray[0][1:-1] + "(freezeFrame)" #take the x expressions, chop off the {} and add the frame number variable
					newCam['translate'].setExpression(theExpr)
					
					#rotate
					tempString =  newCam['rotate'].toScript() #get the expression string
					tempArray = string.split(tempString, " ") #split into three for x,y,z
					theExpr = tempArray[0][1:-1] + "(freezeFrame)" #take the x expressions, chop off the {} and add the frame number variable
					newCam['rotate'].setExpression(theExpr)
					
					#win_translate
					tempString =  newCam['win_translate'].toScript() #get the expression string
					tempArray = string.split(tempString, " ") #split into two for x,y
					theExpr = tempArray[0][1:-1] + "(freezeFrame)" #take the x expressions, chop off the {} and add the frame number variable
					newCam['win_translate'].setExpression(theExpr)
					
					#win_scale
					tempString =  newCam['win_scale'].toScript() #get the expression string
					tempArray = string.split(tempString, " ") #split into two for x,y
					theExpr = tempArray[0][1:-1] + "(freezeFrame)" #take the x expressions, chop off the {} and add the frame number variable
					newCam['win_scale'].setExpression(theExpr)
				
					#focal
					tempString =  newCam['focal'].toScript() #get the expression string
					theExpr = tempString[1:-1] + "(freezeFrame)" #take the expression, chop off the {} and add the frame number variable
					newCam['focal'].setExpression(theExpr)
					
					#haperture
					tempString =  newCam['haperture'].toScript() #get the expression string
					theExpr = tempString[1:-1] + "(freezeFrame)" #take the expression, chop off the {} and add the frame number variable
					newCam['haperture'].setExpression(theExpr)
					
					#vaperture
					tempString =  newCam['vaperture'].toScript() #get the expression string
					theExpr = tempString[1:-1] + "(freezeFrame)" #take the expression, chop off the {} and add the frame number variable
					newCam['vaperture'].setExpression(theExpr)
					
			else:
				nuke.message("You can't create a ProjectorCam out of another ProjectorCam. Select a tracked camera.")
		
		else:
			nuke.message("The node you selected isn't a camera.")
	else:
		nuke.message("Please select a camera node.")

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