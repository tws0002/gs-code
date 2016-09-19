import maya.OpenMaya
import maya.cmds as cmds
import Cas_IO

def Cas_CRTS_getJointSet(jCluster):
    set = cmds.listSets(o =jCluster)
    return set
    
def Cas_CRTS_swapObjectNames(obj1 , obj2):
    result=[]
    for o in obj1:
        temp1 = o.split(".")
        temp2 = obj2+"."+temp1[1]
        result.append(temp2)
        
    return result
    
def Cas_CRTS_getJointDeformer(cluster):
    listOfDeformers = cmds.cluster(cluster,q=1,dt=1)
    if listOfDeformers == None :
        return None
    
    for deformer in listOfDeformers:
        if cmds.nodeType(deformer) == "joint":
            return deformer
    return None
    

def Cas_convertRigidToSmooth_cmd(object):
	
	def getObjectVertices(ob,verts):
		
		ov = cmds.polyListComponentConversion(ob,tv=1)
		ov = cmds.filterExpand(ov,ex=1,fp=1,sm=31)
		
		verts = cmds.filterExpand(verts,ex=1,fp=1,sm=31)
		
		#print ov
		#print verts
		
		com = []
		for v in verts:
			if v in ov:
				com.append(v)
		return com
		
	
	"""
	"""
	warningCount = 0;
	num = 0
	
	objects = object[:]
	#objects.append(object)
		
	allClusters=[]
	#get all the joint cluster names
	jCluster = cmds.ls(typ="jointCluster")
	#print cmds.cluster(jCluster,q=1,g=1)
	#print jCluster
	#return
	if jCluster == None:
		return [num,warningCount]
		
	for objT in objects:
		obj=cmds.listRelatives(objT,s=1,pa=1)#full path!!!
		if obj == None:
			continue
		#print obj
		#objShape = obj[0]
		#iterate through to see if any clusters are connected to the object
		joint=[]
		cluster=[]
		jointSet=[]
		#find related clusters jointsets and joints     
		for c in jCluster:
			jc = []
			jc = cmds.cluster(c,q=1,g=1)
			#print obj[0]
			
			if obj[0] in jc:
				#print "deformer found"
				#print jc
				deformer = Cas_CRTS_getJointDeformer(c)
				if deformer != None:
					joint.append(deformer)
					jointSet.append(Cas_CRTS_getJointSet(c))
					cluster.append(c)
					if c not in allClusters:
						allClusters.append(c)
		#check if any jointcluster exists for this object
		if cluster == []:
			#print "No jointCluster found for node : %s" %objT
			continue
		
		
		#now joint should contain all the joints names which i need to bind my new object to
		#bind skin
		
		#print joint
		#print objT
		#return
		
		newClusterName=[]
		try:
			newClusterName = cmds.skinCluster(joint,objT,tst=True)[0]
		except Exception , msg:
			Cas_IO.Cas_printWarning("Failed to assign skinCluster. skinCluster may exist already for node : %s" %objT)
			warningCount = warningCount +1
			continue
		else:
			print "jointCluster found for node : %s" %objT
		
		#setAttr "skinCluster4.normalizeWeights" 1;
		#cmds.setAttr(newClusterName+".normalizeWeights",0)

		#now needs to copy weights over.
		index = 0
		for c in cluster:
			
			jSet = jointSet[index]
			jsetName = jSet[0].split(".")
			#print jsetName
			vertices = cmds.sets(jsetName[0],q=1)
			
			vertices = getObjectVertices(objT,vertices)
						
			#print vertices
			if (vertices == None) or (vertices == []):
				#print "skip"
				index = index +1
				continue
			
			deformer = joint[index]
			parentDeformer = cmds.listRelatives(deformer,p=1)
			#print parentDeformer
			#vertices = cmds.filterExpand(vertices,ex=1,fp=1,sm=31)
			cmds.select(vertices)
			
			value = cmds.percent(c,q=1,v=1)
			
			#print len(value)
			#print len(vertices)
			
			if not parentDeformer == None:
				cmds.skinPercent(newClusterName,vertices,tv=([parentDeformer[0],1]))
					
			#for j in joint:
			#	cmds.skinPercent(newClusterName,vertices,tv=([j,0]))
			
			i = 0
			for v in value:
				cmds.skinPercent(newClusterName,vertices[i],tv=([deformer,v]))
				
				#if not parentDeformer == None:
				#	cmds.skinPercent(newClusterName,vertices[i],tv=([parentDeformer[0],(1-v)]))
				#print i
				i += 1
			
			cmds.percent(c,vertices,v=0)
			index = index +1
		num=num+1
		#print num
	#print "done"
	return [num,warningCount]
	

def Cas_CRTS_deleteJointCluster(object):

	"""
	"""
	num = 0
	allClusters=[]
	#get all the joint cluster names
	jCluster = cmds.ls(typ="jointCluster")
	#print cmds.cluster(jCluster,q=1,g=1)
	
	objects = object[:]
	objects.append(object)
	
	if jCluster == None:
		return num
	
	for objT in objects:
		obj=cmds.listRelatives(objT,s=1,pa=1)#full path!!!
		#iterate through to see if any clusters are connected to the object
		cluster=[]
		#find related clusters jointsets and joints     
		for c in jCluster:
			jc = cmds.cluster(c,q=1,g=1)
			#print obj[0]
			if obj[0] in jc:
				#print "deformer found"
				deformer = Cas_CRTS_getJointDeformer(c)
				if deformer != None:
					if c not in allClusters:
						num=num+1
						allClusters.append(c)
		#check if any jointcluster exists for this object
		if cluster == []:
			#print "No jointCluster found for node : %s" %objT
			continue
		
		print "jointCluster found for node : %s" %objT
		
	#delete jointcluster.    Not sure if I need to delete jointset but it appears to be deleted when i delete 
	if allClusters != []:
		print "joint clusters deleted : %s" %allClusters
		cmds.delete(allClusters)
	
	return num
