import maya.cmds as cmds
import Cas_IO
import Cas_convertRigidToSmooth
    
def Cas_massCopyWeight_cmd(pruneValue,autoConvertRigid):
	"""
	Author	: Saehoon Lee
	Date 	: 06/02/2013
	Email	: Saehoon@gmail.com
	http://www.castorlee.com
	Tested for Maya v8.5 v2008 v2009
	
	Description : Python version of Cas_massCopyWeight. More stable and less code than mel.
					GUI added more functions related to rigid skin
	
	DO NOT DISTRIBUTE WITHOUT PERMISSION FROM AUTHOR
	
	How to use : ( v 4.1 )
		run command in python script editor:
	
		import maya.cmds as cmds
		import Cas_massCopyWeight_python
		Cas_massCopyWeight_python.Cas_massCopyWeight_UI()
		
		Select source and Target objects/groups to transfer binding/weights
		the press buttons on GUI that you want to perform
	"""
#		Date: 06/02/2013
#		V 4.1 :
#		minor bug fix , issue with Maya 8.5 (Thanks Alexander from CD4 team)
#
#		Date: 17/07/2009
#		V 4.0 :
#		minor bug fix , issue with Maya 2009
#		
#		Date: 16/02/2009
#		V 3.9 :
#		just realized that if rigid body's weight is less than 1 , resulted smooth skin weight of less than 1 (combined)
#		is going to move the vertices. With bit of help from Tom, managed to come up with workable version of the converter
#		
#		Date: 07/01/2009
#		V 3.8 : 
#		Fixed bug when root of joint is not joint node. (group node) Thanks Andrew
#
#		Date: 27/11/2008
#		V 3.7 : 
#		Fixed iteration bug with Maya 8.5 implementation.
#
#		Date: 05/11/2008
#		V 3.6 : First GUI version with Rigid skin converter
#		Added GUI for normal weight copying function
#		Added function to convert rigid skin to smooth skin and copy the weights from rigid to smooth skin
#		Added option to toggle auto delete rigid joint cluster and auto convert rigid skin to smooth skin
#		Added additional function to delete rigid skin jointcluster if wanted
#		Converting from rigid skin to smooth skin does not delete rigid skin jointcluster by default.
#		But the weights of rigid skin jointCluster is set to 0 after copying the weight to new smooth skinCluster
#
#		More error checking. Better progress bar. Implemented own function for deleteunusedinfluence
#	
#		Date: 03/11/2008
#		V 3.5 : Non Pymel version
#		Pymel was used last version of this sctipt to simplify the process and shorten the code.
#		But this led to some complication of distributing to the other studios. 
#		Therefore removed Pymel commands and used native
#		Maya commands only. Implemented few of own functions that does not exist in Python commands in Maya.
#
#		Date: 15/10/2008
#		V 3.4 : First Python version of the script
#		Python version seems to be more stable and works better.
#		Added more rigrious error checking prune small weight function. Modified the way it works by changing the command
#
#		Date: 09/10/2008
#		V 3.3 : Changed prune small weight method.
#		there was heavy memory leak bug with Maya when UV editor is open and run default
#		prune small weight function. Modified the way it works by changing the command to
#		skinPercent -prw 0.01 ClusterName. Faster and with no memory leak. Also minimised doing
#		lots of selections. Apprently there is another bug or stupid feature in Maya where Texture UV
#		editor keeps the cache of displayed images, so if you do lots of selection it will eat memory 
#		and significantly slow down the process. Known Maya behaviour.
#
#		Date: 14/09/2008
#		V 3.2 : Changed bonding option. Removed cloest joint option which was not 
#		working well with the joints with the same position.
#
#		Date: 15/02/2008
#		V 3.1 : Changed how removing unused influence work. This fixes weird
#		flashing mouse icon issue with Evaldeferred command. But less intuative.
#
#		Date: 18/01/2008
#		V 3.0 : Uses Maya's copyweight function more wisely and now it 
#		is possible to map the objects without the same names. but slower.
#		It is possible to make this bit faster, but don't want to start
#		modifying the user's skin binding, copy weight settings.
#
#		Date: 15/01/2008
#		V 2.0 : Version 2 works with groups of objects too. Meshes needs 
#		to have the same names to work.
#
#		Date: 1/10/2007
#		V 1.0 : First version
#		Select source and destination mesh and it will bind the relevent
#		joints and copy weights across.
#		
	time = cmds.timerX()
	time2 = 0
	timeTook2 = 0
	progressCount = 0
	
	sel = cmds.ls(sl=True , tr= 1)
	
	if (sel == None) or (sel == []):
		Cas_IO.Cas_printWarning ("Please select one object for source and at least one object/groups for target...")
		return
	
	if len(sel) < 2:
		Cas_IO.Cas_printWarning ("Please select one objects for source and at least one object/groups for target...")
		return
	
	warningCount = 0
	undoState = cmds.undoInfo(q = 1 , st = 1)
	texWin = cmds.getPanel(sty ="polyTexturePlacementPanel")
	#texState = cmds.textureWindow(texWin[0],q=1,id=1)
	texState = False
	
	cmds.progressWindow(min=0 , max=100 , t = "Cas_massCopyWeight_Python 3.6")
	
	#cmds.textureWindow(texWin[0],q=1,id=0)
	
	#disable undo for memory issue
	cmds.undoInfo(swf=0)
	
	#print rootjoint
	#print "done"
	#return
	# compile both source and target node lists
	
	
	org = []
	rel = cmds.listRelatives(sel[0],ad = 1,pa =1 , typ="transform")
	if rel != None:
		org = rel
	org.append(sel[0])
	#print org
	#org.append(sel[0])
	source = org[:] # make a copy
	
	#find mesh only
	for node in org :
		shape = cmds.listRelatives(node , s=1 , type = "mesh",pa=1)
		if shape == None:
			#print "opps no mesh shape node has been found for node : %s" % node
			#print node
			source.remove(node)
	
	#convert to soft skin if necessary
	if autoConvertRigid == True:
		#need some sort of warning system .. here ?
		result = Cas_convertRigidToSmooth.Cas_convertRigidToSmooth_cmd(source)
		if result[1] == 0:
			Cas_IO.Cas_printInfo("%s rigid skin converted to smooth skin" %result[0])
		else:
			Cas_IO.Cas_printWarning("%s rigid skin converted to smooth skin with %s warnings. please check your script editor" %(result[0],result[1]))
			
	autoDelete = cmds.checkBox(Cas_MCW_autoDeleteJointClusterCheckCT,q=True,v=True)
	if autoDelete == True:
		time2 = cmds.timerX()
		confirm = cmds.confirmDialog( title="Delete rigid joint clusters" , message="It will disconnect the other objects bind to the deleted clusters as well"+"\n"\
																				+"                                             Are you sure?", button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
		timeTook2 = cmds.timerX(st=time2)
		if confirm == "Yes":
			Cas_convertRigidToSmooth.Cas_CRTS_deleteJointCluster(source)
			
	print "copying smooth skin weights now..."
	progressCount = 10
	cmds.progressWindow(e=1,pr=progressCount)
	
	
	#now finally check to see if objects actually has skinCluster
	org = source[:]
	for node in org:
		if Cas_MCW_findRelatedSkinSluster(node) == None:
			print "No skincluster found for node. Removed from list : %s" %node
			warningCount = warningCount +1
			source.remove(node)
	
	# find the root joint to bind to.
	joints =[]
	try:
		joints = cmds.skinCluster(sel[0], q=1 , inf = 1)
	except Exception, msg:
		Cas_IO.Cas_printWarning("None of the source objects seems to have skin cluster! (or it is rigid skin and not converted to smooth skin) %s" % msg)
		Cas_MCW_restoreMisc(undoState,texState)
		return
	#What is Python version of Rootof command?    
	
	rootjoint = Cas_MCW_getJointDeformer(sel[0])
	if rootjoint == "":
		Cas_IO.Cas_printWarning("Can't find joint deformer!")
		Cas_MCW_restoreMisc(undoState,texState)
		return
	else:
		print "Root joint found : %s" %rootjoint
	
	tar = []
	rel = cmds.listRelatives(sel[1:],ad = 1,pa =1 , typ="transform")
	if rel != None:
		tar = rel
		tar.extend(sel[1:])
	else:
		tar=sel[1:]
	target = tar[:] # make a copy
	cmds.progressWindow(e=1,pr=10)
	#print "target = %s" % target 
	for node in tar :
		shape = cmds.listRelatives(node , s=1 , type = "mesh",pa=1)
		if shape == None:
			#print "opps no mesh shape node has been found for node : %s" % node
			#print node
			target.remove(node)
		if node in source:
			print "The object selected as a target is within the source object list! (skipped) : %s" % node
			warningCount += 1
			target.remove(node)
	
	progressCount = 20
	cmds.progressWindow(e=1,pr=progressCount)
	
	if len(target) == 0: #check if there is nothing to do
		Cas_IO.Cas_printWarning("No targets are valid for skin binding")
		Cas_MCW_restoreMisc(undoState,texState)
		return
		
	#print "original = %s" % source
	
	#cmds.select (source)
	#cmds.select (target)
	
	# Bind joints to the target objects
	#delete history on target objects
	#print source
	#print target
	
	#return
	cmds.delete(target,ch=1)
	# now go through each target objects and do bind and copy weight
	progressRatio = 20.0 / len(target)
	
	for node in target:
		try:
			cmds.skinCluster(rootjoint,node,mi = 4,omi = 0,)
		except Exception , msg:
			warningCount += 1
			print "Failed to bind object %s. %s " % (node,msg)
		
		cmds.select(source)
		cmds.select(node,add=1)
		
		try:
			cmds.copySkinWeights(sm=1,noMirror=1,sa = "closestPoint" , ia = ("name", "oneToOne"))
		except Exception , msg:
			warningCount += 1
			print "Failed to copy weight object %s. %s " % (node,msg)
			
		progressCount = progressCount + progressRatio
		cmds.progressWindow(e=1,pr=progressCount)
	
	
	progressCount = 40
	cmds.progressWindow(e=1,pr=progressCount)
	
	#cmds.select(target)   
	#maya.mel.eval("removeUnusedInfluences();") # remove unused influence to optimise skincluster
	
	# prune small weight to optimise skincluster even more
	progressRatio = 60.0 / len(target)
	for node in target:
		sCluster = Cas_MCW_findRelatedSkinSluster(node)
		if sCluster == None:
			warningCount += 1
			print "Could not find skinCluster related to node : %s" % node
		else:
			removed = Cas_MCW_removeUnusedForSkin(sCluster)
			cmds.skinPercent(sCluster,node,prw=(pruneValue))
		
		progressCount = progressCount + progressRatio
		cmds.progressWindow(e=1,pr=progressCount)
		
	cmds.progressWindow(e=1,pr=100)        
	
	timeTook = cmds.timerX(st=time) - timeTook2
	#print timeTook	
	
	if warningCount > 0:
		Cas_IO.Cas_printWarning("Finished. Time taken : %ssec with %s warnings" % (timeTook,warningCount))
	else:
		Cas_IO.Cas_printInfo("Finished. Time taken : %ssec with %s warnings" % (timeTook,warningCount))
	
	cmds.select(cl=1)
	Cas_MCW_restoreMisc(undoState,texState)
	
	
def Cas_MCW_getJointDeformer(cluster):
	listOfDeformers = cmds.skinCluster(cluster, q=1 , inf = 1)
	if listOfDeformers == None :
		return None
	
	for deformer in listOfDeformers:
		if cmds.nodeType(deformer) == "joint":
			return deformer
	return None
# UI function

# function specific name spaced variables. So it can be accessed from other local functions. But still hidden to the Maya globals
Cas_MCW_pruneValueCT=""
Cas_MCW_convertRidgidToSoftCheckCT=""
Cas_MCW_autoDeleteJointClusterCheckCT=""

def Cas_massCopyWeight_UI():
    Cas_massCopyWeightWin = "Cas_massCopyWeightWindow"
    if cmds.window(Cas_massCopyWeightWin, ex = True):
        cmds.deleteUI(Cas_massCopyWeightWin)
        
    cmds.window(Cas_massCopyWeightWin, title = "Cas_CopyWeight v4.0",wh=[176,180],s=False)
    cmds.columnLayout()
    cmds.rowColumnLayout( numberOfColumns=2 , columnWidth=[(1, 117), (2, 50)])
    cmds.text(l="Weight prune value",al="center")
    globals()["Cas_MCW_pruneValueCT"]=cmds.floatField(v=0.01,max = 1,min=0)
    cmds.setParent( ".." )
    globals()["Cas_MCW_convertRidgidToSoftCheckCT"]=cmds.checkBox(v=False,l="Auto convert rigid to soft skin")
    globals()["Cas_MCW_autoDeleteJointClusterCheckCT"]=cmds.checkBox(v=False,l="Auto delete rigid joint clusters")
    Cas_MCW_convertRidgidToSoftCT=cmds.button(l="Convert rigid skin to soft skin",h=30,al="center",w=170)
    Cas_MCW_deleteRidgidJointClusterCT=cmds.button(l="Delete rigid skin joint clusters",h=30,al="center",w=170)
    Cas_MCW_massWeightCopyCT=cmds.button(l="Perform Copy Weight",w=170,h=40)
    
    #commands
    cmds.button(Cas_MCW_massWeightCopyCT,e=True,c="Cas_massCopyWeight_python.Cas_MCW_massCopyWeight_cmd()")
    cmds.button(Cas_MCW_convertRidgidToSoftCT,e=True,c="Cas_massCopyWeight_python.Cas_MCW_convertRidgidToSoftButton_cmd()")
    cmds.button(Cas_MCW_deleteRidgidJointClusterCT,e=True,c="Cas_massCopyWeight_python.Cas_MCW_deleteRidgidJointCluster_cmd()")
    
    #print cmds.ls(sl=True , tr= 1)
    cmds.window(Cas_massCopyWeightWin,edit=True,wh=[176,180])
    cmds.showWindow(Cas_massCopyWeightWin)

# UI functions Wrapper

def Cas_MCW_massCopyWeight_cmd():
    
    #cmds.floatField(Cas_massCopyWeight_python.Cas_massCopyWeight_UI.Cas_pruneValueCT,q=True,v=True) , \
    #cmds.checkBox(Cas_massCopyWeight_UI.Cas_MCW_convertRidgidToSoftCheckCT,q=True,v=True))")
    var1 = cmds.floatField(Cas_MCW_pruneValueCT,q=True,v=True)
    var2 = cmds.checkBox(Cas_MCW_convertRidgidToSoftCheckCT,q=True,v=True)
    #var2 = False
    Cas_massCopyWeight_cmd(var1,var2)
    

def Cas_MCW_convertRidgidToSoftButton_cmd():
	sel = cmds.ls(sl=True , tr= 1)
	if (sel == None) or (sel==[]):
		Cas_IO.Cas_printWarning ("Please select at lease one objects or group to convert...")
		return
	
	org = []
	rel = cmds.listRelatives(sel[:],ad = 1,pa =1 , typ="transform")
	if rel != None:
		org = rel
	org.extend(sel[:])
	source = org[:] # make a copy
	
	for node in org :
		shape = cmds.listRelatives(node , s=1 , type = "mesh")
		if shape == None:
			source.remove(node)
	
	#print source
	
	result = Cas_convertRigidToSmooth.Cas_convertRigidToSmooth_cmd(source)
	if result[1] == 0:
		Cas_IO.Cas_printInfo("%s rigid skin converted to smooth skin" %result[0])
	else:
		Cas_IO.Cas_printWarning("%s rigid skin converted to smooth skin with %s warnings. please check your script editor" %(result[0],result[1]))
	
	autoDelete = cmds.checkBox(Cas_MCW_autoDeleteJointClusterCheckCT,q=True,v=True)
	if autoDelete == True:
		time2 = cmds.timerX()
		confirm = cmds.confirmDialog( title="Delete rigid joint clusters" , message="It will disconnect the other objects bind to the deleted clusters as well"+"\n"\
																				+"                                             Are you sure?", button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
		timeTook2 = cmds.timerX(st=time2)
		if confirm == "Yes":
			Cas_convertRigidToSmooth.Cas_CRTS_deleteJointCluster(source)

def Cas_MCW_deleteRidgidJointCluster_cmd():
	#need some sort of warning system .. here ?
	
	sel = cmds.ls(sl=True , tr= 1,l=True)
	if (sel == None) or (sel==[]):
		Cas_IO.Cas_printWarning ("Please select at lease one objects or group to delete related rigid joint clusters...")
		return
	
	confirm = cmds.confirmDialog( title="Delete rigid joint clusters" , message="It will disconnect the other objects bind to the deleted clusters as well"+"\n"\
																		+"                                             Are you sure?", button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
	if confirm != "Yes":
		return
	
	
	org = []
	rel = cmds.listRelatives(sel[:],ad = 1,pa =1 , typ="transform")
	if rel != None:
		org = rel
	org.extend(sel[:])
	source = org[:] # make a copy
	
	for node in org :
		shape = cmds.listRelatives(node , s=1 , type = "mesh")
		if shape == None:
			source.remove(node)
	
	result = Cas_convertRigidToSmooth.Cas_CRTS_deleteJointCluster(source)
	Cas_IO.Cas_printInfo("%s rigid joint clusters deleted" %result)


# other misc functions

def Cas_rootOf(s):
    hasParent = True
    object = s
    while hasParent:
        parent = cmds.listRelatives(object,parent=True)
        #print parent
        if parent == None:
            hasParent = False
        else:
            object = parent
    return object

def Cas_MCW_restoreMisc(undoState , texWindowState):
    if undoState == 1:
        cmds.undoInfo(swf=1)
    if texWindowState == 1:
        texWin = cmds.getPanel(sty ="polyTexturePlacementPanel")
        
		#cmds.textureWindow(texWin[0],e=1,id=1)
    cmds.progressWindow(ep=1)
    
def Cas_MCW_findRelatedSkinSluster(object):
    
    obj=cmds.listRelatives(object,s=1,pa=True)
    obj.append(object)
    #Need to find all the rigid joint cluster related with object
    #get all the joint cluster names
    jCluster = cmds.ls(typ="skinCluster")
    if jCluster == None:
        return None
    #iterate through to see if any clusters are connected to the object
    #print "processing node : %s" %object
    for c in jCluster:
        jc = cmds.skinCluster(c,q=1,g=1)
        #print jc		

	if jc != None:
		for o in obj:
			if o in jc:
				#print "found cluster for node : %s" %object
				return c
    
    #print "Not found cluster for node : %s" %object
    return None
    
def Cas_MCW_removeUnusedForSkin(cluster):
    removeCount = 0
    infls = cmds.skinCluster(cluster,q=True, inf = True)
    wtinfls = cmds.skinCluster(cluster,q=True, wi = True)

    nodeState = cmds.getAttr(cluster+".nodeState")
    cmds.setAttr(cluster+".nodeState",1)
    
    for infl in infls:
        found = 0
        for wtinf in wtinfls:
            if wtinf == infl:
                found = 1
                break
            
        if found == 0:
            removeCount = removeCount + 1
            cmds.skinCluster(cluster, e= True, ri = infl)
    
    cmds.setAttr(cluster+".nodeState",nodeState)
    return removeCount
    
if __name__ == "__main__":                 
    print Cas_massCopyWeight_cmd.__doc__