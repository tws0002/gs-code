"""
hfRig Limb construction functions by renry (henry@toadstorm.com)
v0.01
11/26/2012

Functions for constructing Limbs (arms and legs).

"""

class Limb():
    def __init__():
		# create variable dictionaries. these will eventually get values from an existing rig, or be established by functions later on.
		self.ik = [] # ik joints, handles, stretch locators, pole vector, etc
		self.fk = [] # fk joints, pole vector guide for switching
		self.bind = [] # bind joints, parent locators, up vectors, bind curve, clusters
		self.pivots = [] # drivers for bind joints, controlled by control skeletons
		self.controls = [] # interactive controls
		self.info = [] # miscellaneous
		self.infoNode = ''
		self.debugMode = 1
		if self.debugMode: print 'Init Limb object'
		
	def makeInfoNode(self,rigName='hfRig',*args):
		# create info node to store rig info. 
		self.infoNode = cmds.group(n=rigName+'_INFO',w=1,em=1)
		if self.debugMode: print 'Created info node %s.' % (self.infoNode)
		
		
	def readRigInfo(self,master,*args):
		# from master node, read all dynamic attributes from the master and child nodes
		# deleteAttr -q lists all custom attributes
		allAttrs = cmds.deleteAttr(self.infoNode,q=1)
		ikAttrs = [f for f in allAttrs if f.startswith('IK_')]
		fkAttrs = [f for f in allAttrs if f.startswith('FK_')]
		bindAttrs = [f for f in allAttrs if f.startswith('BIND_')]
		pivotsAttrs = [f for f in allAttrs if f.startswith('PIVOTS_')]
		controlsAttrs = [f for f in allAttrs if f.startswith('CONTROLS_')]
		infoAttrs = [f for f in allAttrs if f.startswith('INFO_')]
		# populate dictionaries. for each attr, key is the attr, value is getAttr(attr)
		for key in ikAttrs:
			val = cmds.listConnections(self.infoNode+'.'+key)[0]
			self.ik[key]=val
		for key in fkAttrs:
			val = cmds.listConnections(self.infoNode+'.'+key)[0]
			self.fk[key]=val
		for key in bindAttrs:
			val = cmds.listConnections(self.infoNode+'.'+key)[0]
			self.bind[key]=val
		for key in pivotsAttrs:
			val = cmds.listConnections(self.infoNode+'.'+key)[0]
			self.pivots[key]=val
		for key in controlsAttrs:
			val = cmds.listConnections(self.infoNode+'.'+key)[0]
			self.controls[key]=val
		for key in infoAttrs:
			val = cmds.listConnections(self.infoNode+'.'+key)[0]
			self.info[key]=val
		if self.debugMode: print 'Loaded rig info from %s.' % (master)

	def registerNode(self,key,value,*args):
		# register a node with the Info Node
		if not self.infoNode: cmds.error('Can\'t find info node!')
		cmds.addAttr(self.infoNode,ln=key,at='message')
		cmds.connectAttr(value+'.message',self.infoNode+'.'+key,f=1)
		if key.startswith('IK_'): self.ik[key]=value
		elif key.startswith('FK_'): self.fk[key]=value
		elif key.startswith('BIND_'): self.bind[key]=value
		elif key.startswith('PIVOTS_'): self.pivots[key]=value
		elif key.startswith('CONTROLS_'): self.controls[key]=value
		elif key.startswith('INFO_'): self.info[key]=value
		else:
			err = 'Can\'t register node with %s: unrecognized key prefix %s' % (self.infoNode,key)
		    cmds.error(err)
		if self.debugMode: print 'Registered key %s with value %s.' % (key,value)

	def makeControlSkeletons(self,top,mid,bot,type='arm',orient='xyz',secondaryAxis='zup',*args):
		# create control arms from template joints. orient new joints. attach new nodes to info node.
		# start by creating and parenting template joints.
		topName = 'shoulder'
		midName = 'elbow'
		botName = 'wrist'
		if type=='leg':
		   topName = 'femur'
		   midName = 'knee'
		   botName = 'ankle'
		tempTop = cmds.duplicate(top,po=1,n=top+'_TEMP')[0]
		tempMid = cmds.duplicate(mid,po=1,n=mid+'_TEMP')[0]
		tempBot = cmds.duplicate(bot,po=1,n=bot+'_TEMP')[0]
		tempBot = cmds.parent(tempBot,tempMid)
		tempMid = cmds.parent(tempMid,tempTop)
		# apply orientation
		cmds.joint(tempShoulder,e=1,oj=orient,sao=secondaryAxis,ch=1,zso=1)
		cmds.joint(tempWrist,e=1,oj='none')
		# create and register ik/fk chains
		fkTop,fkMid,fkBot = cmds.duplicate(tempTop)
		fkBot = cmds.rename(fkBot,'FK_'+botName)
		fkMid = cmds.rename(fkMid,'FK_'+midName)
		fkTop = cmds.rename(fkTop,'FK_'+topName)
		ikTop,ikMid,ikBot = cmds.duplicate(tempTop)
		ikBot = cmds.rename(ikBot,'IK_'+botName)
		ikMid = cmds.rename(ikMid,'IK_'+midName)
		ikTop = cmds.rename(ikTop,'IK_'+topName)
		self.registerNode('FK_top',fkTop)
		self.registerNode('FK_mid',fkMid)
		self.registerNode('FK_bot',fkBot)
		self.registerNode('IK_top',ikTop)
		self.registerNode('IK_mid',ikMid)
		self.registerNode('IK_bot',ikBot)
		if self.debugMode: print 'Created IK/FK control skeletons.'
		
		
		