import nuke
import os
import string
	
def MNEaverageTrack():
	#ask whether one, two or four point
	#ask how many they want to average on each
	
	p = nuke.Panel("Average Track")
		
	enumerationPulldownp = "1-point 2-point 4-point "
	enumerationPulldowns = "2-tracks 3-tracks 4-tracks "
	
	p.addEnumerationPulldown("What kind of track do you need?", enumerationPulldownp)
	p.addEnumerationPulldown("How many tracks would you like to average for each point?", enumerationPulldowns)
	p.addButton("Cancel") 
	p.addButton("Create Trackers")
	pResult = p.show()
	trackerType = p.value("What kind of track do you need?")
	numTracks = p.value("How many tracks would you like to average for each point?")
	
	#if 'Create Trackers' was pressed, do stuff
	if pResult == 1:
		#deselect nodes and get coordinates of last-selected node
		s = nuke.selectedNodes()
		sCounter = 0
		for ss in s:
			ss.knob("selected").setValue(False)
			if sCounter==0:
				xx = ss['xpos'].value()
				yy = ss['ypos'].value()
				selNode = ss
			sCounter = sCounter+1
			
		#create NoOp node underneath it
		noOp = nuke.createNode("NoOp")
			
		if sCounter > 0:
			noOp.knob('xpos').setValue(xx)
			noOp.knob('ypos').setValue(yy+100)
		xx = noOp['xpos'].value()
		yy = noOp['ypos'].value()
		
		#connect it to the selected node
		if sCounter > 0:
			noOp.setInput(0,selNode)
	
		#call it 'PLATE IN' and increment if that exists
		nCounter = 0
		for a in nuke.allNodes():
			if ((a.knob('name').value()).find("PLATE IN") !=-1):
				nCounter = nCounter + 1
		if nCounter > 0:	
			noOp.knob('name').setValue("PLATE IN" + str(nCounter))
		else:
			noOp.knob('name').setValue("PLATE IN")
	
	
		#create tracker nodes
		t1 = nuke.createNode("Tracker3")
		t1.setInput(0,noOp)
		t1Name = t1.knob('name').value()
		t1.knob('xpos').setValue(xx)
		t1.knob('ypos').setValue(yy+100)
		if (trackerType == "2-point" or trackerType == "4-point"):
			t2 = nuke.createNode("Tracker3")
			t2.setInput(0,noOp)
			t2Name = t2.knob('name').value()
			t2.knob('xpos').setValue(xx+100)
			t2.knob('ypos').setValue(yy+100)
		if (trackerType == "4-point"):
			t3 = nuke.createNode("Tracker3")
			t4 = nuke.createNode("Tracker3")
			t3.setInput(0,noOp)
			t4.setInput(0,noOp)
			t3Name = t3.knob('name').value()
			t4Name = t4.knob('name').value()
			t3.knob('xpos').setValue(xx+200)
			t3.knob('ypos').setValue(yy+100)
			t4.knob('xpos').setValue(xx+300)
			t4.knob('ypos').setValue(yy+100)
		
		#create a fifth
		t5 = nuke.createNode("Tracker3")
		t5.setInput(0,noOp)
		t5.knob('xpos').setValue(xx+200)
		t5.knob('ypos').setValue(yy)
		
		# name it AverageTrack or AverageTrack1, AverageTrack2 etc... if there are multiple
		aCounter = 0
		for a in nuke.allNodes():
			if ((a.knob('name').value()).find("AverageTrack") !=-1):
				aCounter = aCounter + 1
			
		if aCounter > 0:	
			t5.knob('name').setValue("AverageTrack" + str(aCounter))
		else:
			t5.knob('name').setValue("AverageTrack")
		
		#set it to stabilize
		t5.knob('transform').setValue('stabilize')
			
		# set the paramenters of the fifth tracker, depending on the kind of tracker chosen
		if trackerType == "1-point":
			#enable that track, disable other three
			t5.knob('enable1').setValue(1)
			t5.knob('enable2').setValue(0)
			t5.knob('enable3').setValue(0)
			t5.knob('enable4').setValue(0)
			#set to translate only
			t5.knob('use_for1').setValue('T')
		elif trackerType == "2-point":
			#enable those two tracks, disable other two
			t5.knob('enable1').setValue(1)
			t5.knob('enable2').setValue(1)
			t5.knob('enable3').setValue(0)
			t5.knob('enable4').setValue(0)
			#set to translate, rotation and scale
			t5.knob('use_for1').setValue('T R S')
			t5.knob('use_for2').setValue('T R S')
		elif trackerType == "4-point":
			# enable all tracks and set to translate, rotation and scale
			for i in range(1,5):
				t5.knob('enable'+str(i)).setValue(1)
				t5.knob('use_for'+str(i)).setValue('T R S')
		
		#create expressions for each of the tracks of the fifth tracker
		#depending on the options they chose
		
		if (numTracks == "2-tracks" and trackerType == "1-point"):
			t5.knob('track1').setExpression('(' + t1Name + '.track1 + ' + t1Name + '.track2)/2' )
			
			# enable 2 tracks in t1
			t1.knob('enable1').setValue(1)
			t1.knob('enable2').setValue(1)
			
		elif (numTracks == "2-tracks" and trackerType == "2-point"):
			t5.knob('track1').setExpression('(' + t1Name + '.track1 + ' + t1Name + '.track2)/2' )
			t5.knob('track2').setExpression('(' + t2Name + '.track1 + ' + t2Name + '.track2)/2' )
			
			#enable 2 tracks in 2 trackers
			for t in [t1,t2]:
				t.knob('enable1').setValue(1)
				t.knob('enable2').setValue(1)
			
		elif (numTracks == "2-tracks" and trackerType == "4-point"):
			
			#set expression in each track of the master tracker
			i = 1
			for t in [t1Name,t2Name,t3Name,t4Name]:
				t5.knob('track' + str(i)).setExpression('(' + t + '.track1 + ' + t + '.track2)/2' )
				i=i+1
			
			#enable 2 tracks in 4 trackers
			for t in [t1,t2,t3,t4]:
				t.knob('enable1').setValue(1)
				t.knob('enable2').setValue(1)
				
		elif (numTracks == "3-tracks" and trackerType == "1-point"):
			t5.knob('track1').setExpression('(' + t1Name + '.track1 + ' + t1Name + '.track2 + ' + t1Name + '.track3)/3' )
			
			# enable 3 tracks in t1
			for i in range(1,4):
				t1.knob('enable'+str(i)).setValue(1)
			
		elif (numTracks == "3-tracks" and trackerType == "2-point"):
			t5.knob('track1').setExpression('(' + t1Name + '.track1 + ' + t1Name + '.track2 + ' + t1Name + '.track3)/3' )
			t5.knob('track2').setExpression('(' + t2Name + '.track1 + ' + t2Name + '.track2 + ' + t2Name + '.track3)/3' )
			
			#enable 3 tracks in 2 trackers
			for t in [t1,t2]:
				for i in range(1,4):
					t.knob('enable'+str(i)).setValue(1)

		elif (numTracks == "3-tracks" and trackerType == "4-point"):
				
			#set expression in each track of the master tracker
			i = 1
			for t in [t1Name,t2Name,t3Name,t4Name]:
				t5.knob('track' + str(i)).setExpression('(' + t + '.track1 + ' + t + '.track2 + ' + t + '.track3)/3' )
				i=i+1
			
			#enable 3 tracks in 4 trackers
			for t in [t1,t2,t3,t4]:
				for i in range(1,4):
					t.knob('enable'+str(i)).setValue(1)

		elif (numTracks == "4-tracks" and trackerType == "1-point"):
			t5.knob('track1').setExpression('(' + t1Name + '.track1 + ' + t1Name + '.track2 + ' + t1Name + '.track3 + ' + t1Name + '.track4)/4' )
			
			# enable all tracks in t1
			for i in range(1,5):
				t1.knob('enable'+str(i)).setValue(1)
			
		elif (numTracks == "4-tracks" and trackerType == "2-point"):
			t5.knob('track1').setExpression('(' + t1Name + '.track1 + ' + t1Name + '.track2 + ' + t1Name + '.track3 + ' + t1Name + '.track4)/4' )
			t5.knob('track2').setExpression('(' + t2Name + '.track1 + ' + t2Name + '.track2 + ' + t2Name + '.track3 + ' + t2Name + '.track4)/4' )
			
			#enable all tracks in 2 trackers
			for t in [t1,t2]:
				for i in range(1,5):
					t.knob('enable'+str(i)).setValue(1)

		elif (numTracks == "4-tracks" and trackerType == "4-point"):
			
			#set expression in each track of the master tracker
			i = 1
			for t in [t1Name,t2Name,t3Name,t4Name]:
				t5.knob('track'+ str(i)).setExpression('(' + t + '.track1 + ' + t + '.track2 + ' + t + '.track3 + ' + t + '.track4)/4' )
				i=i+1
			
			#enable all tracks in 4 trackers
			for t in [t1,t2,t3,t4]:
				for i in range(1,5):
					t.knob('enable'+str(i)).setValue(1)
			
		
		nuke.message("IMPORTANT!\n\nThe generated tracker node 'AverageTrack' will only work when you bake in the expressions.\n\nTo do this: right-click each track, choose Edit..Generate to generate keyframes in place of the expression. \n\nIf you are not happy with the track, press Undo until all the keyframed curves are turned back to expressions, retrack then generate again.")
