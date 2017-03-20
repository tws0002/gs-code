'''
name : drawAnim

author : Guillaume FERRACHAT

LAUNCH :
import maya.cmds as cmds

import gf_drawAnim as daCtx
reload(daCtx)
daCtx.UI().create()
'''
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import math as math
from functools import partial
import maya.mel as mel

class UI():
	'''
	UI class
	'''
	
	def __init__(self):
		self.version = '2.1.1'
		self.winTitle = 'GF Draw Animation ' + self.version
		self.winName = 'DRAWANIM_WIN'
	
		# check main window existence
		if cmds.window(self.winName,query=True,exists=True):
			cmds.deleteUI(self.winName)
	
	def create(self):
		cmds.window(self.winName, title = self.winTitle)
		cmds.columnLayout(rs = 3, cat=("left",5))
		self.timeFacField = cmds.floatFieldGrp(label = "Time Factor : ", value1 = 1.0, cw2 = (70,75),h=25)
		self.simpCbx = cmds.checkBox(label = "Simplify curve", v=True)
		self.channelbCbx = cmds.checkBox(label = "From channel box", v=False)
		
		cmds.separator(style = "single", h = 25, w = 200)
		cmds.button(label = "Draw Anim (Translate)", w = 150, c=partial(self.run,"translate"))
		
		cmds.separator(style = "single", h = 25, w = 200)
		self.aimCbx = cmds.checkBox(label = "Best Guess", v = False)
		self.aimVecField = cmds.floatFieldGrp(label = "Aim Vector : ", nf = 3,value1 = 0.0, value2 = 1.0, value3 = 0.0, cw4 = (70,60,60,60),h=25)
		
		cmds.button(label = "Draw Anim (Rotate)", w = 150, c=partial(self.run,"rotate"))
		
		cmds.separator(style = "single", h = 25, w = 200)
		cmds.button(label = "Draw Anim (Both)", w = 150, c=partial(self.run,"translaterotate"))
		cmds.showWindow(self.winName)
		cmds.window(self.winName, edit = True, wh=(300,290))
		
	def run(self,mode,*args):
		simplify = cmds.checkBox(self.simpCbx,q=True,v=True)
		timeFactor = cmds.floatFieldGrp(self.timeFacField,q=True,value1=True)
		channelBox = cmds.checkBox(self.channelbCbx,q=True,v=True)
		autoAim = cmds.checkBox(self.aimCbx,q=True,v=True)
		idLocalVec = [cmds.floatFieldGrp(self.aimVecField,q=True,value1=True),cmds.floatFieldGrp(self.aimVecField,q=True,value2=True),cmds.floatFieldGrp(self.aimVecField,q=True,value3=True)]
		
		drawAnim(cmds.ls(sl=True,fl=True),simplify=simplify,timeFactor = timeFactor, mode = mode, channelBox = channelBox, autoAim = autoAim, idLocalVec = idLocalVec).run()
		
class drawAnim():
	'''
	Tool Class
	'''
	def __init__(self,object=[], simplify=True, timeFactor = 1.0, mode = "translate", channelBox = False, autoAim = False, idLocalVec = [0,1,0]):
		'''
		initialization
		'''
		self.object = object[0]
		self.simplify = simplify
		self.lastT = 0
		self.fps = utils().getFps()
		self.worldUp = om.MVector(0,1,0)
		self.timeFactor = timeFactor
		self.mode = mode
		self.channelBox = channelBox
		self.autoAim = autoAim
		self.idLocalVec = idLocalVec
		
		if cmds.objectType(self.object,i='mesh'):
			self.shape = True
		elif cmds.objectType(self.object,i='nurbsSurface'):
			self.shape = True
		elif cmds.objectType(self.object,i='nurbsCurve'):
			self.shape = True
		else:
			self.shape = False
				
		self.currentUnit = cmds.currentUnit(q=True,linear=True)
		if self.currentUnit == 'mm' or self.currentUnit == 'millimeter':
			self.unit = 10
		elif self.currentUnit == 'cm' or self.currentUnit == 'centimeter':
			self.unit = 1
		elif self.currentUnit == 'm' or self.currentUnit == 'meter':
			self.unit = .01
		elif self.currentUnit == 'km' or self.currentUnit == 'kilometer':
			self.unit = 0.00001
		elif self.currentUnit == 'in' or self.currentUnit == 'inch':
			self.unit = 0.393701
		elif self.currentUnit == 'ft' or self.currentUnit == 'foot':
			self.unit = 0.0328084
		elif self.currentUnit == 'yd' or self.currentUnit == 'yard':
			self.unit = 0.0109361
		elif self.currentUnit == 'mi' or self.currentUnit == 'miles':
			self.unit = 0.0000062137
			
	# create dragger context
		self.dragCtx = "gf_meshPlace_draggerCtx"
		if (cmds.draggerContext(self.dragCtx, exists=True)):
			cmds.deleteUI(self.dragCtx)
		cmds.draggerContext( self.dragCtx, pressCommand=self.onPress, dragCommand=self.onDrag, releaseCommand=self.onRelease, holdCommand=self.onHold, cursor='hand', pr = "objectViewPlane", space="world", undoMode = "step" );
		
	def run(self):
		"""
		set current tool
		"""
		if (cmds.draggerContext(self.dragCtx, exists=True)):
			cmds.setToolTo(self.dragCtx)
			
	def onHold(self):
		print "Holding..."
	def onPress(self):
		self.attributes = cmds.channelBox( "mainChannelBox", query=True, sma=True)
		if self.attributes is None:
			self.attributes = []
		self.lastT = 0
		cmds.timer(s=True)
		self.startTime = cmds.currentTime(q=True)
		self.lastHit = cmds.draggerContext(self.dragCtx, q=True, anchorPoint = True)
		
		# get cam vectors
		camObject = utils().getCam()
		viewDir = camObject.viewDirection(om.MSpace.kWorld)
		self.upDir = camObject.upDirection(om.MSpace.kWorld)
		rightDir = camObject.rightDirection(om.MSpace.kWorld)
		self.lastVec = None
		self.lastRot = [0.0,0.0,0.0]
		self.idQuat = utils().quatFromObj(self.object)
		self.idVec = utils().localToWorld(self.idLocalVec,self.object)
		mel.eval('timeControl -e -beginScrub $gPlayBackSlider;')
		
	def onDrag(self):
		# timer
		lap = cmds.timer(lap=True)
		curTime = cmds.currentTime(q=True)
		sub = lap - self.lastT
		
		#get position
		dragPosition = cmds.draggerContext(self.dragCtx, q=True, dragPoint = True)
		
		# start operations
		if sub > self.timeFactor/self.fps:
			self.objPos = cmds.xform(self.object,q=True, ws=True, t=True)
			
			# translate
			if "translate" in self.mode:
				# key attributes
				if self.channelBox is True:
					if 'tx' in self.attributes:
						cmds.move(dragPosition[0] * self.unit,self.object,ws=True,absolute=True,wd=True,x=True)
						cmds.setKeyframe(self.object, at='tx')
					if 'ty' in self.attributes:
						cmds.move(dragPosition[1] * self.unit,self.object,ws=True,absolute=True,wd=True,y=True)
						cmds.setKeyframe(self.object, at='ty')
					if 'tz' in self.attributes:
						cmds.move(dragPosition[2] * self.unit,self.object,ws=True,absolute=True,wd=True,z=True)
						cmds.setKeyframe(self.object, at='tz')
				else:
					cmds.move(dragPosition[0] * self.unit,dragPosition[1] * self.unit,dragPosition[2] * self.unit,self.object,ws=True,absolute=True, wd=True)
					if self.shape:
						cmds.setKeyframe(self.object)
					else:
						cmds.setKeyframe(self.object, at='translate')
			
			# rotate
			if "rotate" in self.mode and self.shape is False:
				self.vector = om.MVector(dragPosition[0] - self.objPos[0],dragPosition[1] - self.objPos[1],dragPosition[2] - self.objPos[2])
				
				if self.autoAim is True:
					if self.lastVec is None:
						self.idVec = self.vector
				
				rotator = om.MQuaternion(self.idVec,self.vector)
				result = self.idQuat * rotator
				euler = result.asEulerRotation()
				dragRotation = [math.degrees(euler.x),math.degrees(euler.y),math.degrees(euler.z)]
				relRotation = [new - old for new,old in zip(dragRotation,self.lastRot)]
				
				# key attributes
				if self.channelBox is True:
					if 'rx' in self.attributes:
						cmds.rotate(dragRotation[0],ws=True,absolute=True,x=True)
						cmds.setKeyframe(self.object, at='rx')
					if 'ry' in self.attributes:
						cmds.rotate(dragRotation[1],ws=True,absolute=True,y=True)
						cmds.setKeyframe(self.object, at='ry')
					if 'rz' in self.attributes:
						cmds.rotate(dragRotation[2],ws=True,absolute=True,z=True)
						cmds.setKeyframe(self.object, at='rz')
				else:
					cmds.rotate(dragRotation[0],dragRotation[1],dragRotation[2],ws=True,absolute=True)
					# cmds.rotate(relRotation[0],relRotation[1],relRotation[2],ws=True,relative=True,eu=True)
					self.lastRot = dragRotation
					cmds.setKeyframe(self.object, at='rotate')
				
				# looping variables
				self.lastVec = self.vector
				
		# change time
			cmds.currentTime(curTime + 1)
			cmds.currentTime(curTime + 1)
			self.lastT = lap
	
	def onRelease(self):
		cmds.timer(e=True)
		self.endTime = cmds.currentTime(q=True)
		if "translate" in self.mode:
			if self.channelBox is True:
				if self.simplify is True:
					utils().simplify(self.object, (self.startTime,self.endTime),at=self.attributes)
			else:
				if self.simplify is True:
					if self.shape is True:
						simpAt = ['xValue','yValue','zValue']
					else:
						simpAt = ['tx','ty','tz']
					utils().simplify(self.object, (self.startTime,self.endTime),at=simpAt)
				
		if "rotate" in self.mode and self.shape is False:
			if self.channelBox is True:
				# euler filter
				for at in self.attributes:
					cmds.filterCurve(self.object + '.' + at, f='euler', s=self.startTime, e=self.endTime)
				if self.simplify is True:
					utils().simplify(self.object, (self.startTime,self.endTime),at=self.attributes)
			else:
				for at in ['rx','ry','rz']:
					cmds.filterCurve(self.object + '.' + at, f='euler', s=self.startTime, e=self.endTime)
				if self.simplify is True:
					utils().simplify(self.object, (self.startTime,self.endTime),at=['rx','ry','rz'])
		mel.eval('timeControl -e -endScrub $gPlayBackSlider;')
		
class utils():
	'''
	utilities
	'''
	def __init__(self):
		pass
		
	def getFps(self):
		time = cmds.currentUnit(q=True, time=True)
		
		if time == 'game':
			fps = 15
		if time == 'film':
			fps = 24
		if time == 'pal':
			fps = 25
		if time == 'ntsc':
			fps = 30
		if time == 'show':
			fps = 48
		if time == 'palf':
			fps = 50
		if time == 'ntscf':
			fps = 60
		
		return fps
	
	def simplify(self,obj, time, at=True):
		# cmds.simplify(obj, at='translate',time = time)
		for a in at:
			cmds.filterCurve(obj + '.' + a, f='simplify', s=time[0], e=time[1], timeTolerance = 0.05)
	
	def localToWorld(self,local,obj):
		list = cmds.xform(obj, q=True, matrix=True)
		Vx = om.MVector(list[0],list[1],list[2])
		Vy = om.MVector(list[4],list[5],list[6])
		Vz = om.MVector(list[8],list[9],list[10])
		
		result = (Vx * local[0]) + (Vy * local[1]) + (Vz * local[2])
		result.normalize()
		return result
	
	def worldToView(self,mPt):
		# get current view
		currentView = omui.M3dView().active3dView()
		
		# empty objects
		xPos = om.MScriptUtil().asShortPtr()
		yPos = om.MScriptUtil().asShortPtr()
		
		# conversion
		value = currentView.worldToView(mPt, xPos, yPos)
		
		x = om.MScriptUtil().getShort(xPos)
		y = om.MScriptUtil().getShort(yPos)
		
		# return
		return x,y
		
	def viewToWorld(self,x,y):
		# get current view
		currentView = omui.M3dView().active3dView()
		
		# empty objects
		resultPt = om.MPoint()
		resultVtr = om.MVector()
		
		# conversion
		currentView.viewToWorld(int(x),int(y),resultPt,resultVtr)
		
		# return
		return [resultPt.x,resultPt.y,resultPt.z],om.MVector(resultVtr.x,resultVtr.y,resultVtr.z)
		
	def crossProduct(self,vA,vB):
		vC = om.MVector(((vA.y*vB.z) - (vA.z*vB.y)) , ((vA.z*vB.x) - (vA.x*vB.z)), ((vA.x*vB.y) - (vA.y*vB.x)))
		vC.normalize()
		return vC
		
	def getCam(self):
		# get current view
		currentView = omui.M3dView().active3dView()
		dag = om.MDagPath()
		cam = currentView.getCamera(dag)
		cam = om.MFnCamera(dag)
		
		return cam
		
	def dotProduct(self,vA,vB):
		# vA.normalize()
		# vB.normalize()
		result = (vA.x * vB.x) + (vA.y * vB.y) + (vA.z * vB.z)
		return result
		
	def quatDotProduct(self,vA,vB):
		# vA.normalize()
		# vB.normalize()
		result = (vA.x * vB.x) + (vA.y * vB.y) + (vA.z * vB.z) + (vA.w * vB.w)
		return result
		
	def vectorAngle(self,vA,vB):
		scalar = self.dotProduct(vA,vB)
		mag = self.magnitude(vA) * self.magnitude(vB)
		try:
			angle = math.acos(scalar/mag)
		except:
			angle = 0
		return angle
		
	def magnitude(self,v):
		magnitude = math.sqrt( math.pow(v.x,2) + math.pow(v.y,2) + math.pow(v.z,2) )
		return magnitude
		
	def quatFromObj(self,obj):
		mtx = om.MMatrix()

		list = cmds.xform(obj, q=True, matrix=True)
		om.MScriptUtil().createMatrixFromList(list,mtx)

		transMtx = om.MTransformationMatrix(mtx)

		quat = transMtx.rotation()
		
		return quat
		
	def quatFrom3Vec(self,x,y,z):
		mtx = om.MMatrix()
		list = [x.x,x.y,x.z,0,y.x,y.y,y.z,0,z.x,z.y,z.z,0,0,0,0,1]
		om.MScriptUtil().createMatrixFromList(list,mtx)

		transMtx = om.MTransformationMatrix(mtx)

		quat = transMtx.rotation()
		
		return quat
		
	def vectorSlerp(self,vA,vB,t):
		if vA.isParallel(vB,0.0001):
			vC = vB
		else:
			vAngle = self.vectorAngle(vA,vB)
			vC = (vA * ((math.sin((1-t) * vAngle))/math.sin(vAngle))) + (vB * (math.sin(t * vAngle)/math.sin(vAngle)))
			
		return vC
		
	def quaternionSlerp(a, b, t):
		cos = quaternionDot(a, b)
		if cos < 0.0:
			cos = quatDotProduct(a, b.negateIt())
		theta = math.acos(cos)
		sin = math.sin(theta)
		
		if sin > 0.001:
			w1 = math.sin((1.0 - t) * theta) / sin
			w2 = math.sin(t * theta) / sin
		else:
			w1 = 1.0 - t
			w2 = t
		aa = om.MQuaternion(a)
		bb = om.MQuaternion(b)
		aa.scaleIt(w1)
		bb.scaleIt(w2)
		
		return aa + bb