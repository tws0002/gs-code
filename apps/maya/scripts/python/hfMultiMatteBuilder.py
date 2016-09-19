# auto mattes builder v0.02 by henry foster, 06/21/2011
# 
#
# automagically builds and manages VROPs for assets, helps build passes for scenes.
# functions: automatically build VROPS for assigned materials, add/remove materials from a given VROP
# script to build passes automatically will need to analyze object VROPs and matIDs on shaders.

# usage: 
# import hfMultiMatteBuilder as hfMMB
# hfMMB.matteBuilderUI()
# 

# to do list:
# +add button to generate matIDs for selected materials
# +create button to link shaders to matIDs instead of using selectionChanged event
# +create button to build multimatte elements
# +reload materials button
# +reload matIDs button
# -disable generation controls if nothing is selected
# +add control to give selected materials a new matID

import maya.cmds as cmds
import maya.mel as mel
import math
import natSort

def makeMattesForMats(mats=cmds.ls(sl=1),index=0):
	''' make matIDs for selected materials. '''
	# mel command for adding matID: vray addAttributesFromGroup black_glossy_vray vray_material_id 1;
	for m in mats:
		# this first command takes a while to finish, so we'll cheat a bit here and add
		# the vrayMaterialId attribute manually to avoid errors.
		mel.eval("vray addAttributesFromGroup "+m+" vray_material_id 1;")
		mel.eval("vrayAddAttr "+m+" vrayMaterialId")
		cmds.setAttr(m+'.vrayMaterialId',index)
		print 'assigned matID %d to material %s' % (index,m)
		index+=1

def getIndexInfo(getVrops=1):
	''' find the highest index for matID and VROP from the current scene, and return it with a list of all used indices. '''
	vrops = cmds.ls(type='VRayObjectProperties')
	sgs = cmds.ls(type='shadingEngine')
	indices = []
	vropIndices = []
	mats = []
	for sg in sgs:
		try:
			mats.extend(cmds.listConnections(sg+'.surfaceShader'))
		except TypeError:
			# no material attached
			pass
	# now we have populated lists, so let's see who has the highest index.
	hiIndex = 0
	if getVrops==1:
		for vrop in vrops:
			index = cmds.getAttr(vrop+'.objectID')
			vropIndices.append(index)
			if index > hiIndex: hiIndex = index
	for mat in mats:
		index = 0
		try:
			index = cmds.getAttr(mat+'.vrayMaterialId')
			indices.append(index)
		except(TypeError,ValueError):
			# this material has no ID
			pass
		if index > hiIndex: hiIndex = index
	# remove duplicates from indices
	indices = list(set(indices))
	vropIndices = list(set(vropIndices))
	return indices, hiIndex, vropIndices

def makeMultiMattes(preserveOldMultis=0,useVrops=1):
    ''' analyze scene and make multimattes based on VROPs and matIDs in the scene. '''
    indices, hiIndex, vropIndices = getIndexInfo(useVrops)
    currentMatte = ''
    cmds.select(cl=1)
    if preserveOldMultis==1:
    	exclusionList = []
    	vropExclusionList = []
    	# check out all the current multiMatte elements and figure out what numbers are already represented.
    	# then remove these numbers from the indices list.
    	multiMattes = [f for f in cmds.ls(type='VRayRenderElement') if cmds.getAttr(f+'.vrayClassType') == 'MultiMatteElement' and cmds.getAttr(f+'.vray_usematid_multimatte') == 1]
    	for m in multiMattes:
    		r = cmds.getAttr(m+'.vray_redid_multimatte')
    		g = cmds.getAttr(m+'.vray_greenid_multimatte')
    		b = cmds.getAttr(m+'.vray_blueid_multimatte')
    		exclusionList.append(r)
    		exclusionList.append(g)
    		exclusionList.append(b)
    	exclusionList = list(set(exclusionList))
    	vropMultiMattes = [f for f in cmds.ls(type='VRayRenderElement') if cmds.getAttr(f+'.vrayClassType') == 'MultiMatteElement' and cmds.getAttr(f+'.vray_usematid_multimatte') == 0]
    	for m in vropMultiMattes:
    		r = cmds.getAttr(m+'.vray_redid_multimatte')
    		g = cmds.getAttr(m+'.vray_greenid_multimatte')
    		b = cmds.getAttr(m+'.vray_blueid_multimatte')
    		vropExclusionList.append(r)
    		vropExclusionList.append(g)
    		vropExclusionList.append(b)
    	indices = [a for a in indices if a not in exclusionList]
    	vropIndices = [a for a in vropIndices if a not in vropExclusionList]
    		
    count = 0
    mattes = 0
    # first we make multimattes for matIDs. VROPs have to be separate because they are for object-based multimattes.
    print('\n---------MULTIMATTE RESULTS---------')
    for x in range(0,len(indices)):
        if count == 0:
            mel.eval("vrayAddRenderElement MultiMatteElement")
            currentMatte = cmds.ls(sl=1)[0]
            mattes += 1
            cmds.setAttr(currentMatte+'.vray_usematid_multimatte',1)
            cmds.setAttr(currentMatte+'.vray_redid_multimatte',indices[x])
            print '\nassigned matID %d to RED channel of %s' % (indices[x],currentMatte)
        elif count == 1:
            cmds.setAttr(currentMatte+'.vray_greenid_multimatte',indices[x])
            print '\nassigned matID %d to GREEN channel of %s' % (indices[x],currentMatte)
        elif count == 2:
            cmds.setAttr(currentMatte+'.vray_blueid_multimatte',indices[x])
            print '\nassigned matID %d to BLUE channel of %s' % (indices[x],currentMatte)
            count = -1
        count += 1
    if useVrops==1:
    	count = 0
    	cmds.select(cl=1)
    	for x in range(0,len(vropIndices)):
    		if count == 0:
    			mel.eval("vrayAddRenderElement MultiMatteElement")
    			currentMatte = cmds.ls(sl=1)[0]
    			mattes += 1
    			cmds.setAttr(currentMatte+'.vray_redid_multimatte',vropIndices[x])
    			print '\nassigned VROP with objectID %d to RED channel of %s' % (vropIndices[x],currentMatte)
    		elif count == 1:
    			cmds.setAttr(currentMatte+'.vray_greenid_multimatte',vropIndices[x])
    			print '\nassigned VROP with objectID %d to GREEN channel of %s' % (vropIndices[x],currentMatte)
    		elif count == 2:
    			cmds.setAttr(currentMatte+'.vray_blueid_multimatte',vropIndices[x])
    			print '\nassigned VROP with objectID %d to BLUE channel of %s' % (vropIndices[x],currentMatte)
    			count = -1
    		count += 1
    outString = 'created %d MultiMatte elements. see script editor for details.' % (mattes)
    cmds.warning(outString)

def loadMatIDs(control,*args):
	''' populate list of material IDs for the relationship editor. '''
	indices, hiIndex, vropIndices = getIndexInfo(0)
	cmds.textScrollList(control,e=1,ra=1)
	try:
		indices = natSort.natsorted(indices)
	except TypeError:
		# probably empty, natSort doesn't like this
		pass
	for i in indices:
		cmds.textScrollList(control,e=1,a=i)
		
def loadMaterials(control,selID,*args):
	''' populate and highlight list of materials based on selected material ID. '''
	# control is for THIS control. selID is the currently selected item of the mat ID selector.
	# first, get all materials and populate the control. then highlight materials with the matching matID.
	selID = int(selID)
	sgs = cmds.ls(type='shadingEngine')
	mats = []
	cmds.textScrollList(control,e=1,ra=1)
	for sg in sgs:
		try:
			mat = cmds.listConnections(sg+'.surfaceShader')
			mats.extend(mat)
		except TypeError:
			pass
	try:
		mats = natSort.natsorted(mats)
	except TypeError:
		# probably empty for whatever reason
		pass
	for mat in mats:
		#cmds.textScrollList(control,e=1,a=mat)
		matID = 0
		try:
			matID = cmds.getAttr(mat+'.vrayMaterialId')
			cmds.textScrollList(control,e=1,a=mat)
			if matID == selID:
				cmds.textScrollList(control,e=1,si=mat)
		except(TypeError,ValueError):
			pass
			
def getSelectedMatID(control):
	matID = cmds.textScrollList(control,q=1,si=1)
	try:
		if len(matID) < 1:
			matID = 0
		else:
			matID = matID[0]
	except TypeError:
		# no matID is selected.
		matID = 0
	return matID
	
def linkMatsToIDs(control,selID):
	''' run when user clicks on materials in the right panel based on matID number. sets material matID to this number. '''
	selList = cmds.textScrollList(control,q=1,si=1)
	selID = int(selID)
	for mat in selList:
		try:
			cmds.getAttr(mat+'.vrayMaterialId')
		except TypeError:
			# this guy doesn't have a matId attribute yet
			mel.eval("vray addAttributesFromGroup "+mat+" vray_material_id 1;")
			mel.eval("vrayAddAttr "+mat+" vrayMaterialId")
		cmds.setAttr(mat+'.vrayMaterialId',selID)
		print 'set matID to %d for material %s' % (selID,mat)
	loadMaterials(control,selID)
 
def makeMattesCallback(matsControl,idControl,matsMatchControl,indexControl):
	''' callback function for makeIDsBtn. sends command to refresh the matIDs list after they are added to the materials. '''
	index = int(cmds.textField(indexControl,q=1,tx=1))
	makeMattesForMats(cmds.textScrollList(matsControl,q=1,si=1),index)
	refreshCallback(matsControl,idControl,matsMatchControl,indexControl)
	
def refreshCallback(matsControl,idControl,matsMatchControl,indexControl):
	# deselect everything, reload all textScrollLists
	# first the material list.
	matsList = []
	sgList = cmds.ls(type='shadingEngine')
	for sg in sgList:
		try:
			matsList.extend(cmds.listConnections(sg+'.surfaceShader'))
		except TypeError:
			pass
	matsList = list(set(matsList))
	# make a pruned list of materials with no matID.
	matsNoID = [m for m in matsList if cmds.attributeQuery('vrayMaterialId',node=m,ex=1) == 0]
	matsWithID = [m for m in matsList if cmds.attributeQuery('vrayMaterialId',node=m,ex=1) == 1]
	try:
		matsNoID = natSort.natsorted(matsNoID)
	except TypeError:
		pass
	try:
		matsWithID = natSort.natsorted(matsWithID)
	except TypeError:
		pass
	# populate matsControl and matsMatchControl.
	cmds.textScrollList(matsControl,e=1,ra=1)
	cmds.textScrollList(matsMatchControl,e=1,ra=1)
	for m in matsNoID:
		cmds.textScrollList(matsControl,e=1,a=m)
	for m in matsWithID:
		cmds.textScrollList(matsMatchControl,e=1,a=m)
	# repopulate mat IDs list.
	loadMatIDs(idControl)
	# reload latest index control
	indices, hiIndex, vropIndices = getIndexInfo()
	cmds.textField(indexControl,e=1,tx=(hiIndex+1))

def remakeMattesCallback(matsControl,idControl,matsMatchControl,indexControl):
	''' callback function for remakeIDsBtn. makes new matIDs for selected materials based on the set index. '''
	index = int(cmds.textField(indexControl,q=1,tx=1))
	makeMattesForMats(cmds.textScrollList(matsMatchControl,q=1,si=1),index)
	refreshCallback(matsControl,idControl,matsMatchControl,indexControl)
	
def matteBuilderUI():
    ''' build interface for VROP builder. '''
    windowName = 'hfMatteBuilderUI'
    windowTitle = 'VRay MatID Manager'
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    window = cmds.window(windowName,title=windowTitle)
    form = cmds.formLayout()
    # build materials list for dropdown.
    matsList = []
    sgList = cmds.ls(type='shadingEngine')
    for sg in sgList:
    	try:
    		matsList.extend(cmds.listConnections(sg+'.surfaceShader'))
    	except TypeError:
    		pass
    matsScrollList = cmds.textScrollList(w=220,h=400,ams=1)
    matsScrollLabel = cmds.text(l='select materials to add matID:')
    startingIndexLabel = cmds.text(l='starting index: ')
    startingIndexCtrl = cmds.textField(w=50)
    matIDLabel = cmds.text(l='mat IDs:')
    matIDMatchLabel = cmds.text(l='materials with selected matID:')
    matIDMatchList = cmds.textScrollList(w=220,h=400,ams=1)
    matIDList = cmds.textScrollList(w=100,h=400,ams=0,sc=lambda *x: loadMaterials(matIDMatchList,getSelectedMatID(matIDList)))
    matIDMatchButton = cmds.button(l='assign selected matID to materials',w=220,h=35,c=lambda *x: linkMatsToIDs(matIDMatchList,getSelectedMatID(matIDList)))
    makeIDsBtn = cmds.button(l='generate matIDs',w=200,h=35,c=lambda *x: makeMattesCallback(matsScrollList,matIDList,matIDMatchList,startingIndexCtrl))
    remakeIDsBtn = cmds.button(l='assign new matID to materials',w=220,h=35,c=lambda *x: remakeMattesCallback(matsScrollList,matIDList,matIDMatchList,startingIndexCtrl))
    refreshBtn = cmds.button(l='refresh all',w=220,h=75,bgc=[0.6,0.7,1.0],c=lambda *x: refreshCallback(matsScrollList,matIDList,matIDMatchList,startingIndexCtrl))
    makeVropsCheck = cmds.checkBox(l='include VROPs?',v=1)
    makeMultimattesBtn = cmds.button(l='MAKE MULTIMATTES',w=220,h=75,bgc=[0.6,0.7,1.0],c=lambda *x: makeMultiMattes(1,cmds.checkBox(makeVropsCheck,q=1,v=1)))
    cmds.formLayout(form,e=1,attachForm=[(makeMultimattesBtn,'top',560),(makeMultimattesBtn,'left',400),(makeVropsCheck,'top',540),(makeVropsCheck,'left',400),(refreshBtn,'top',560),(refreshBtn,'left',5),(remakeIDsBtn,'top',475),(remakeIDsBtn,'left',400),(makeIDsBtn,'top',435),(makeIDsBtn,'left',5),(matIDMatchButton,'top',435),(matIDMatchButton,'left',400),(matIDMatchLabel,'top',5),(matIDMatchLabel,'left',400),(matIDLabel,'top',5),(matIDLabel,'left',280),(matsScrollLabel,'top',5),(matsScrollLabel,'left',5),(matsScrollList,'left',5),(matsScrollList,'top',25),(startingIndexLabel,'top',478),(startingIndexLabel,'left',5),(startingIndexCtrl,'top',475),(startingIndexCtrl,'left',80),(matIDList,'top',25),(matIDList,'left',280),(matIDMatchList,'top',25),(matIDMatchList,'left',400)])
    refreshCallback(matsScrollList,matIDList,matIDMatchList,startingIndexCtrl)
    cmds.showWindow(window)
    cmds.window(window,e=1,w=630,h=645)