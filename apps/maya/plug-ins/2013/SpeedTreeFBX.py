##############################################################################
## SpeedTree FBX Plug-In For Maya ############################################
#
#        - Loads SpeedTree FBX files and optimizes them for Maya
#
#    *** INTERACTIVE DATA VISUALIZATION (IDV) PROPRIETARY INFORMATION ***
#
#    This software is supplied under the terms of a license agreement or non-
#    disclosure agreement with Interactive Data Visualization and may not be
#    copied or disclosed except in accordance with the terms of that agreement.
#
#    Copyright (c) 2012 IDV, Inc.
#    All Rights Reserved.
#
##############################################################################

#includes
import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as om
import maya.OpenMayaMPx as OpenMayaMPx
import math, sys, os
import __main__


#session variables
__main__.SpeedTreeShaderNetworkResults = []
__main__.SpeedTreeReplacedMaterials = []
__main__.SpeedTreeMatShapeArray = []
try:
	tmpvar = __main__.SpeedTreeScriptJobRendererChanged
except:
	__main__.SpeedTreeScriptJobRendererChanged = 0


#plug-in variables
kSpeedTreeFbxNodeId = om.MTypeId( 0x44441 )
kSpeedTreeFbxNodeName = "SpeedTreeFbx"
kSpeedTreeFbxNodeClassify = "SpeedTreeFbx"
kSpeedTreeFbxImporterName = "importSpeedTreeFbx"
kSpeedTreeFbxTranslatorName = "SpeedTree FBX"
kSpeedTreeDagChangedName = "SpeedTreeDagMembersChanged"
kSpeedTreeUpdateShaderName = "updateSpeedTreeShader"
kSpeedTreeAssignShaderName = "assignSpeedTreeShader"
kSpeedTreeBuildShaderName = "buildSpeedTreeShaderNetwork"
kSpeedTreeBakeShaderName = "bakeSpeedTreeShaderNetwork"

supportedRenderers = [ 'generic', 'mentalRay' ]
hardwareRenderers = [ 'mayaHardware', 'mayaHardware2' ]
MayaVersion = mel.eval( 'getApplicationVersionAsFloat' )
if MayaVersion >= 2012:
	supportedRenderers += hardwareRenderers

#callback function
def SpeedTreeCallbacks():
	"""Allocates unique variable names for all SpeedTree ScriptJobs"""
	
	mc.evalDeferred( 'import maya.cmds as mc' )
	__main__.SpeedTreeShaderNetworkResults = []
	__main__.SpeedTreeReplacedMaterials = []
	__main__.SpeedTreeMatShapeArray = []
	
	#renderer changed
	if __main__.SpeedTreeScriptJobRendererChanged == 0:
		__main__.SpeedTreeScriptJobRendererChanged = mc.scriptJob( ac=[ 'defaultRenderGlobals.currentRenderer', SpeedTreeRendererChanged ] )
	
	#allow blending
	blendValid = 0
	currRenderer = mc.getAttr( 'defaultRenderGlobals.currentRenderer' )
	if ( currRenderer != 'mayaSoftware' and currRenderer != 'mayaHardware' and currRenderer != 'mayaHardware2' ):
		blendValid = 1
	
	try:
		SpeedTreeFbxNodes = mc.ls( type='SpeedTreeFbx' )
	except:
		SpeedTreeFbxNodes = []
		
	stFbxNodesLen = len( SpeedTreeFbxNodes )
	for s in range( 0, stFbxNodesLen ):
		stNode = SpeedTreeFbxNodes[s]
		mc.setAttr( stNode + '.blendValid', blendValid )
		stNodeSg = mc.connectionInfo( stNode + '.shadingEngine', sfd=1 ).split('.')[0]
		
		if stNodeSg != '':
			if mc.getAttr( stNode + '.scriptJob' ) == 0:
				scriptJobNum = mc.scriptJob( ac=[ stNodeSg + '.dagSetMembers', 'mc.SpeedTreeDagMembersChanged("' + stNode + '", 2)' ], alc=True, dri=True, kws=True )
				mc.setAttr( stNode + '.scriptJob', scriptJobNum ) 


#callback triggers
if __main__.SpeedTreeScriptJobRendererChanged == 0:
	mc.scriptJob( e=[ 'NewSceneOpened', SpeedTreeCallbacks ] )
	try:
		#"PostSceneRead" event added in 2012
		mc.scriptJob( e=[ 'PostSceneRead', SpeedTreeCallbacks ] )
	except:
		mc.scriptJob( e=[ 'SceneOpened', SpeedTreeCallbacks ] )


#shared functions
def SpeedTreeRendererChanged():
	"""Sets renderer-specific SpeedTree variables"""
	
	processShader = rendererIndex = blendValid = 0
	currRenderer = mc.getAttr( 'defaultRenderGlobals.currentRenderer' )
	rendererList = mc.renderer( query=True, namesOfAvailableRenderers=True )
	rendererList[0] = 'generic'
	
	if currRenderer == 'mayaSoftware':
		currRenderer = 'generic'
		
	for s in supportedRenderers:
		if s not in rendererList:
			supportedRenderers.remove( s )
			
	if currRenderer in supportedRenderers:	
		rendererIndex = supportedRenderers.index( currRenderer )
		processShader = 1
		
	if ( currRenderer != 'generic' and currRenderer != 'mayaHardware' and currRenderer != 'mayaHardware2' ):
		blendValid = 1
	
	oldSelection = mc.ls( sl=True )
	SpeedTreeFbxNodes = mc.ls( type='SpeedTreeFbx' )
	processLen = len( supportedRenderers ) + 1
	sceneGamma = stSceneGammaPlug()
	
	for stNode in SpeedTreeFbxNodes:
		mc.setAttr( stNode + '.blendValid', blendValid )
		mc.setAttr( stNode + '.rendererIndex', rendererIndex )
		if mc.getAttr( stNode + '.processIndex' ) > processLen:
			mc.setAttr( stNode + '.processIndex', 0 )
		
		useGammaCorrection = mc.getAttr( stNode + '.useGammaCorrection' )
		currSceneGamma = mc.connectionInfo( stNode + '.sceneGamma', sfd=1 )
		if currSceneGamma != '':
			mc.disconnectAttr( currSceneGamma, stNode + '.sceneGamma' )
			mc.connectAttr( sceneGamma[0], stNode + '.sceneGamma' )
		
		#update shader for renderer
		pInd = mc.getAttr( stNode + '.processIndex' )
		autoUpdate = mc.optionVar( q='SpeedTreeAutoUpdate' )
		autoUpdate *= ( 1 - mc.referenceQuery( stNode, inr=True ) )
		
		if processShader and pInd == 0 and autoUpdate:
			matSg = mc.connectionInfo( stNode + '.shadingEngine', sfd=True ).split('.')[0]
			if matSg != '':
				mat = stShaderFromSg( matSg )
				if mat != '':
					matInfoArray = mc.listConnections( matSg, type='materialInfo' )
					if matInfoArray != None and len( matInfoArray ) > 0:
						matInfo = matInfoArray[0]
						
						#replace shader node
						mc.updateSpeedTreeShader( stNode, mat, matInfo )
				
	mc.select( clear=True )
	if len( oldSelection ) > 0:
		mc.select( oldSelection )


def stSceneGammaPlug():
	"""Figures out the best available gamma source from the scene"""
	
	currRenderer = mc.getAttr( 'defaultRenderGlobals.currentRenderer' )
	gammaPlug = 'defaultRenderGlobals.gammaCorrection'
	if currRenderer == 'mentalRay' and mc.objExists( 'miDefaultFramebuffer' ):
		gammaPlug = 'miDefaultFramebuffer.gamma'
	
	#get camera to query exposure control
	panelWithFocus = mc.getPanel( withFocus=True )
	visiblePanels = mc.getPanel( vis=True )
	modelPanels = mc.getPanel( typ='modelPanel' )
	
	camNode = 'persp'
	activePanel = None
	if modelPanels != None and len( modelPanels) > 0:
		for p in modelPanels:
			if p in visiblePanels:
				activePanel = p
	
	if activePanel != None:
		camNode = mc.modelEditor( activePanel, query=True, cam=True )
		camShape = mc.listRelatives( camNode, shapes=True )[0]
		
		if currRenderer == 'mentalRay' and mc.attributeQuery( 'miLensShader', node=camShape, ln=True ):
			gammaNode = mc.connectionInfo( camShape + '.miLensShader', sfd=True ).split('.')[0]
			if gammaNode != '':
				gammaPlug = gammaNode + '.gamma'
				
	gammaValue = mc.getAttr( gammaPlug )
	return ( gammaPlug, gammaValue )


def stTestForAlphaMap( fileNode ):
	"""Tests for extra maps matching an _Alpha naming convention"""
	
	nodeFilename = mc.getAttr( fileNode + '.fileTextureName' )
	nodeHasAlpha = mc.getAttr( fileNode + '.fileHasAlpha' )
	nodeAlphaFilename = nodeFilename.rpartition('.')[0] + '_Alpha.' + nodeFilename.rpartition('.')[2]
	nodeAlphaExists = mc.file( nodeAlphaFilename, q=1, ex=1 )
	
	return ( fileNode, nodeFilename, nodeHasAlpha, nodeAlphaExists, nodeAlphaFilename )


def stShaderFromSg( sg ):
	"""Derive material shader from a shading group node"""
	
	sgOutCon = ''
	if sg != None:
		c = 0
		sgOutCons = mc.listConnections( sg, s=True, d=False )
		skipCons = [ 'groupId', 'transform', 'displacementShader', 'file' ]
		if sgOutCons != None and len( sgOutCons ) > 0:
			while c < len( sgOutCons ) and mc.nodeType( sgOutCons[c] ) in skipCons:
				c += 1
				
			if c < len( sgOutCons ):
				sgOutCon = sgOutCons[c]		
	return sgOutCon

	
def stShaderExists( mat, shaderExists=False ):
	"""Checks if a shader is already in the scene"""
	
	#get increment value
	matIncr = mat[-1:]
	if matIncr.isdigit():
		matPrefix = mat[:-1]
		keepTesting = True
		while keepTesting:
			nextDigit = matPrefix[-1:]
			if nextDigit.isdigit() and nextDigit != '0':
				matIncr = nextDigit + matIncr
				matPrefix = matPrefix[:-1]
			else:
				keepTesting = False
				
		matIncr = int( matIncr )
		
		#get color filename
		colorCon = ''
		colorFilename = ''
		colorPlugNames = [ 'color', 'S01', 'S11' ]
		for plug in colorPlugNames:
			if mc.objExists( mat + '.' + plug ):
				colorCon = mc.connectionInfo( mat + '.' + plug, sfd=True ).split( '.' )[0]
				break
		
		if mc.objExists( colorCon ):
			if mc.nodeType( colorCon ) == 'layeredTexture':
				colorCon = mc.connectionInfo( colorCon + '.inputs[1].color', sfd=1 ).split( '.' )[0]
			if mc.nodeType( colorCon ) == 'file':
				colorFilename = mc.getAttr( colorCon + '.fileTextureName' )
				colorFilename = '/'.join( colorFilename.split('\\') )
		
		prevIncr = 0
		prevMat = matPrefix
		materialFound = False
		preSpeedTreeFbx = mc.ls( typ='SpeedTreeFbx' )
		while prevIncr < matIncr and not materialFound:
			if prevIncr > 0:
				prevMat = matPrefix + str( prevIncr )
			prevIncr += 1
			
			if prevMat + '_SpeedTreeFBX' in preSpeedTreeFbx:
				if colorFilename == '' or mc.getAttr( prevMat + '_SpeedTreeFBX.dm' ) == colorFilename:
					materialFound = ( prevMat not in __main__.SpeedTreeReplacedMaterials )
		
		if materialFound:
			__main__.SpeedTreeReplacedMaterials.append( prevMat )
			shaderExists = True
		
		return ( shaderExists, prevMat )
		
	else:
		return ( False, mat )


def stCheckBackfaceCulling( mat, matTransforms, bAllowBFCulling=True ):
	"""Checks per-object backface culling validity"""
	
	shapeDirty = BackfaceCull = False
	
	for matTransform in matTransforms:
		matTransform = matTransform.split( '.' )[0]
		if mc.nodeType( matTransform ) == 'transform':
			matShapes = mc.listRelatives( matTransform, c=True )
		else:
			matShapes = [ matTransform ]
			
		if matShapes != None and len( matShapes ) > 0:
			matShape = matShapes[0]
			if matShape != "" and matShape != None:
				
				#get shaders on this matShape
				oldSelection = mc.ls( sl=1 )
				mc.select( matShape )
				mc.hyperShade( smn=1 )
				matShaders = mc.ls( sl=1 )
				matShadersCompare = []
				mats = [ mat ]
				shaderExists = stShaderExists( mat )
				mats.append( shaderExists[1] )
				
				for matShader in matShaders:
					if mc.nodeType( matShader ) != 'displacementShader' and matShader not in mats:
						matShadersCompare.append( matShader )
				
				if len( oldSelection ) > 0:
					mc.select( oldSelection )
				else:
					mc.select( clear=True )
					
				for s in matShadersCompare:
					shaderDirty = False
					sHistory = mc.listHistory(s)
					
					for h in sHistory:
						if mc.nodeType( h ) == 'SpeedTreeFbx':
							shaderDirty = 1 - mc.getAttr( h + '.bfc' )
							break
							
					if shaderDirty:
						shapeDirty = True
						break
				
				if not shapeDirty:
					if bAllowBFCulling:
						mc.setAttr( matShape + '.doubleSided', 0 )
						BackfaceCull = True
					else:
						mc.setAttr( matShape + '.doubleSided', 1 )
						BackfaceCull = bAllowBFCulling = False
						shapeDirty = True
					
	return [ BackfaceCull, shapeDirty ]


#SpeedTree DAG Members
class stDagMembersChanged( OpenMayaMPx.MPxCommand ):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__( self )
	
	def stConnectUvChoosers( self, SpeedTreeFbx, mat, matShapes ):
		"""Connects existing UV choosers for new file textures""" 
		
		if SpeedTreeFbx != '' and mat != '':
			matCPVs = []
			matPlace2ds = []
			matUvChoosers = []
			matUvChoosersHistory = mc.listHistory( mat, bf=True )
			
			for h in matUvChoosersHistory:
				if mc.nodeType( h ) == 'place2dTexture':
					matPlace2ds.append( h )
				if mc.nodeType( h ) == 'multiplyDivide' and mc.objExists( h + '.uvcs' ):
					matPlace2ds.append( h )
				if mc.nodeType( h ) == 'uvChooser':
					matUvChoosers.append( h )
				if mc.nodeType( h ) == 'mentalrayVertexColors':
					matCPVs.append( h )
			
			if matUvChoosers != None:
					
				#no UV chooser found, create one
				if len( matUvChoosers) == 0 and len( matPlace2ds ) > 0:
					matUvChooser = ''
					for p in matPlace2ds:
						if mc.objExists( p + '.uvcn' ) and mc.objExists( p + '.uvcs' ):
							uvChooserName = mc.getAttr( p + '.uvcn' )
							uvChooserSet = mc.getAttr( p + '.uvcs' )
							
							if not mc.objExists( uvChooserName ):
								matUvChooser = mc.createNode( 'uvChooser', name=uvChooserName )
								mc.setAttr( matUvChooser + '.ihi', 0 )
								
								#add it to the container if in use
								matHistory = mc.listHistory( mat, lv=1 )
								if SpeedTreeFbx in matHistory:
									matHistory.remove( SpeedTreeFbx )
								if mat in matHistory:
									matHistory.remove( mat )
									
								SpeedTreeAsset = mc.container( q=True, findContainer=matHistory )
								if SpeedTreeAsset != None:
									mc.container( SpeedTreeAsset, edit=True, addNode= [matUvChooser] )
							else:
								matUvChooser = uvChooserName
								
							if mc.nodeType( p ) == 'multiplyDivide':
								mc.connectAttr( matUvChooser + '.outU', p + '.input1X' )
							else:
								mc.connectAttr( matUvChooser + '.outUv', p + '.uvCoord' )
								mc.connectAttr( matUvChooser + '.outVertexCameraOne', p + '.vertexCameraOne' )
								mc.connectAttr( matUvChooser + '.outVertexUvThree', p + '.vertexUvThree' )
								mc.connectAttr( matUvChooser + '.outVertexUvTwo', p + '.vertexUvTwo' )
								mc.connectAttr( matUvChooser + '.outVertexUvOne', p + '.vertexUvOne' )
								
							if uvChooserSet < 5 and matUvChooser != '':
								uvChooserSetsLen = 0
								uvChooserPlugs = mc.getAttr( matUvChooser + '.uvSets', mi=1 )
								if uvChooserPlugs != None:
									uvChooserSetsLen = len( uvChooserPlugs )
								
								if matShapes != None and len( matShapes ) > 0:
									for shapeNode in matShapes:
										shapeNodePlug = shapeNode + '.uvSet[' + str( uvChooserSet ) + '].uvSetName'
										uvChooserPlug = matUvChooser + '.uvSets[' + str( uvChooserSetsLen ) + ']'
										if mc.connectionInfo( uvChooserPlug, sfd=1 ) != shapeNodePlug:
											mc.connectAttr( shapeNodePlug, uvChooserPlug, f=True )
				
				#UV chooser found
				elif len( matUvChoosers) > 0:
					uvStart = 1
					
					#reorder uvChoosers
					matUvChoosers.sort()
					if len( matUvChoosers ) > 2:
						detailUvSet = matUvChoosers.pop()
						matUvChoosers.insert( 0, detailUvSet )
						blendUvSet = matUvChoosers.pop(2)
						matUvChoosers.insert( 1, blendUvSet )
						
					elif len( matUvChoosers ) == 2:
						matUvChoosers.reverse()
						uvStart = 2
					
					#hook up the uvChoosers	
					for uvChooser in matUvChoosers:
						if matShapes != None and len( matShapes ) > 0:
							for shapeNode in matShapes:
								
								uvSets = mc.polyUVSet( shapeNode, q=True, allUVSets=True )
								uvChooserPlugs = mc.getAttr( uvChooser + '.uvSets', mi=1 )
								
								#the shape must have enough UV set to need hooking up
								if len( uvSets ) > uvStart and uvChooserPlugs != None:
									alreadyHookedUp = False
									uvChooserSetLen = len( uvChooserPlugs )
									
									for s in uvChooserPlugs:
										if shapeNode == mc.connectionInfo( uvChooser + '.uvSets[' + str(s) + ']', sfd=1 ).split( '.' )[0]:
											alreadyHookedUp = True
											break
										
									if alreadyHookedUp == False:
										mc.connectAttr( shapeNode + '.uvSet[' + str( uvStart ) + '].uvSetName', uvChooser + '.uvSets[' + str( uvChooserSetLen ) + ']' )
						uvStart += 1
			
			if matCPVs != None and len( matCPVs ) > 0:
				#hook up the CPV nodes
				
				for cpv in matCPVs:
					if matShapes != None and len( matShapes ) > 0:
						for shapeNode in matShapes:
							alreadyHookedUp = False
							cpvSetIndices = mc.getAttr( cpv + '.cpvSets', mi=1 ) 
							if cpvSetIndices != None and len( cpvSetIndices ) > 0:
								cpvSetLen = len( cpvSetIndices )
								for s in range( 0, cpvSetLen ):
									if shapeNode == mc.connectionInfo( cpv + '.cpvSets[' + str(s) + ']', sfd=1 ).split( '.' )[0]:
										alreadyHookedUp = True
										break
										
								if not alreadyHookedUp:
									mc.connectAttr( shapeNode + '.colorSet[' + str( cpvSetLen - 1) + '].colorName', cpv + '.cpvSets[' + str( cpvSetLen ) + ']' )

	def doIt( self, argList ):
		"""Assigns dagSetMembers to SpeedTreeFBX nodes"""
		
		argsLen = argList.length()
		if argsLen == 0:
			SpeedTreeFbxNodes = mc.ls( type="SpeedTreeFbx" )
		else:
			SpeedTreeFbxNodes = [argList.asString(0)]
		
		if argsLen == 2:
			processUVs = argList.asInt(1)
		else:
			processUVs = 1
		
		for s in range( 0, len( SpeedTreeFbxNodes ) ):
			if SpeedTreeFbxNodes[s] != '' and SpeedTreeFbxNodes[s] != None:
				stNode = SpeedTreeFbxNodes[s]
				stNodeSg = mc.connectionInfo( stNode + '.shadingEngine', sfd=1 ).split('.')[0]
				
				dagMembers = []
				if stNodeSg != '':
					mat = stShaderFromSg( stNodeSg )					
					shapeIndices = mc.getAttr( stNode + '.shapeNodes', mi=1 )
					if shapeIndices != None and len( shapeIndices ) > 0:
						for s in shapeIndices:
							mc.removeMultiInstance( stNode + '.shapeNodes[' + str(s) + ']', b=True )
					
					dagMemberIndices = mc.getAttr( stNodeSg + '.dagSetMembers', mi=1 )
					if dagMemberIndices != None and len( dagMemberIndices ) > 0:
						for s in dagMemberIndices:
							dagMember = mc.connectionInfo( stNodeSg + '.dagSetMembers[' + str(s) + ']', sfd=1).split( '.' )[0]
							mc.connectAttr( dagMember + '.message', stNode + '.shapeNodes[' + str(s) + ']' )
							dagMembers.append( dagMember )
						
						if processUVs >= 1:
							self.stConnectUvChoosers( stNode, mat, dagMembers )
							
							#new material added
							if processUVs == 2 and dagMembers != None and len( dagMembers ) > 0:
								stCheckBackfaceCulling( mat, dagMembers, mc.getAttr( stNode + '.bfc' ) )
								
		
		if argsLen != 1:
			__main__.SpeedTreeMatShapeArray = dagMembers
		else:
			__main__.SpeedTreeMatShapeArray = []


#Update SpeedTreeShader
class UpdateSpeedTreeShader( OpenMayaMPx.MPxCommand ):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__( self )
		
	def doIt( self, argList ):
		"""Replaces an existing SpeedTree-linked shader"""
		
		argsLen = argList.length()
		if argsLen >= 3:
			SpeedTreeFbx = argList.asString(0)
			mat = argList.asString(1)
			matInfo = argList.asString(2)
			matShapes = __main__.SpeedTreeMatShapeArray
			renameShader = True
				
			if argsLen >= 6:
				stShader = argList.asString(3)
				colorSource = argList.asString(4)
				processType = argList.asString(5)
				renameShader = False
				
			else:
				#remove asset container first
				matHistory = mc.listHistory( mat, lv=1 )
				if SpeedTreeFbx in matHistory:
					matHistory.remove( SpeedTreeFbx )
				if mat in matHistory:
					matHistory.remove( mat )
				SpeedTreeAsset = mc.container( q=True, findContainer=matHistory )
				if SpeedTreeAsset != None:
					mc.container( SpeedTreeAsset, edit=True, removeContainer=True )
					
				#check for color sets
				mc.hyperShade( objects=mat )
				colorSets = mc.polyColorSet( q=True, acs=True )
				doCpv = ( colorSets != None and len( colorSets ) > 0 )
				
				mc.buildSpeedTreeShaderNetwork( SpeedTreeFbx, matInfo, mat, doCpv )
				stShader = __main__.SpeedTreeShaderNetworkResults[0]
				processType = __main__.SpeedTreeShaderNetworkResults[1]
				colorSource = __main__.SpeedTreeShaderNetworkResults[2]
			
			if stShader == '':
				stShaderSg = mc.connectionInfo( SpeedTreeFbx + '.shadingEngine', sfd=True ).split( '.' )[0]
				if stShaderSg != '':
					stShader = stShaderFromSg( stShaderSg )
				
			if stShader != '':
				mc.assignSpeedTreeShader( SpeedTreeFbx, mat, matInfo, stShader, colorSource, processType, renameShader )
				mc.SpeedTreeDagMembersChanged( SpeedTreeFbx, 1 )
				
				if matShapes != None and len( matShapes ) > 0:
					stCheckBackfaceCulling( mat, matShapes, mc.getAttr( SpeedTreeFbx + '.bfc' ) ) 
					
			__main__.SpeedTreeShaderNetworkResults = [ stShader ]
			__main__.SpeedTreeMatShapeArray = []
	

#Assign SpeedTree Shader
class AssignSpeedTreeShader( OpenMayaMPx.MPxCommand ):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__( self )
	
	def stFixTextureDisplay( self, matInfo, colorSource='', stShader='', processType='generic' ):
		"""Switches the texture plug for viewport display"""
		
		matTex = ''
		outChannel = '.outColor'
		if colorSource != '':
			matTex = colorSource
		else:
			matTex = stShader
			if processType == 'mentalRay':
				#matTexCon = mc.connectionInfo( stShader + '.diffuse', sfd=True ).split( '.' )[0]
				outChannel = '.outValue'
		
		if mc.objExists( matTex ) and matTex != '':
			
			if mc.connectionInfo( matInfo + '.material', sfd=True ) == '':
				mc.connectAttr( stShader + '.message', matInfo + '.material' )
				
			texConnections = mc.listConnections( matInfo + '.texture', connections=1, shapes=1 )
			if texConnections != None:
				for i in range( len( texConnections ), 0, -2):
					mc.disconnectAttr( texConnections[i-1] + '.message', texConnections[i-2] )
			
			texChannelCon = mc.connectionInfo( matInfo + '.textureChannel', sfd=True )
			if texChannelCon != '':
				mc.disconnectAttr( texChannelCon, matInfo + '.textureChannel' )
				
			mc.connectAttr( matTex + outChannel, matInfo + '.textureChannel' )
			mc.connectAttr( matTex + '.message', matInfo + '.texture', na=True )
	
	
	def doIt( self, argList ):
		"""Processes SpeedTree shader assignment"""
		
		argsLen = argList.length()
		# do texture fix only
		if argsLen == 4:
			matInfo = argList.asString(0)
			colorSource = argList.asString(1)
			stShader = argList.asString(2)
			processType = argList.asString(3)
			self.stFixTextureDisplay( matInfo, colorSource, stShader, processType )
			
		elif argsLen >= 5:
			SpeedTreeFbx = argList.asString(0)
			mat = argList.asString(1)
			matInfo = argList.asString(2)
			stShader = argList.asString(3)
			colorSource = argList.asString(4)
			
			#determine process type
			validTypes = [ 'generic', 'mentalRay' ]
			processType = 'generic'
			if argsLen >= 6:
				processType = argList.asString(5)
			
			if processType not in validTypes:
				processType = 'generic'
				
			if processType == 'mentalRay':
				shaderOut = '.outValue'
				shaderConnection = '.miMaterialShader'
			else:
				shaderOut = '.outColor'
				shaderConnection = '.surfaceShader'
			
			newMatSg = matSg = ''
			matSgArray = mc.listConnections( mat, s=True, t='shadingEngine' )
			if matSgArray != None and len( matSgArray ) > 0:
				matSg = matSgArray[0]
			else:
				matSgArray = mc.listConnections( stShader, s=True, t='shadingEngine' )
				if matSgArray != None and len( matSgArray ) > 0:
					matSg = matSgArray[0]
			
			#collect old shader and utilities
			matHistory = mc.listHistory( mat, pdo=True )
			existingHistory = mc.listHistory ( stShader, pdo=True )
			
			#don't delete shared nodes
			if SpeedTreeFbx in matHistory:
				matHistory.remove( SpeedTreeFbx )
					
			for e in existingHistory:
				if e in matHistory:
					matHistory.remove( e )
			
			gammaCon = mc.connectionInfo( SpeedTreeFbx + '.sceneGamma', sfd=True ).split( '.' )[0]
			if gammaCon in matHistory:
				matHistory.remove( gammaCon )
			
			#to prevent a warning in older versions of Maya
			for h in matHistory:
				if mc.nodeType( h ) == 'vectorProduct':
					mc.setAttr( h + '.normalizeOutput', 0 )
			
			#to set an existing material
			shadingGroupArray = mc.connectionInfo( stShader + shaderOut, dfs=True )
			if shadingGroupArray != None and len( shadingGroupArray ) > 0:
				newMatSg = shadingGroupArray[0].split( '.' )[0]
				try:
					mc.sets( e=True, forceElement=newMatSg )
				except:
					mc.sets( e=True, forceElement=matSg )
			
			#to change the type of a material
			elif matSg != None and matSg != '':
				matInfoMaterialCon = mc.connectionInfo( matInfo + '.material', sfd=1 )
				if matInfoMaterialCon != "":
					mc.disconnectAttr( matInfoMaterialCon, matInfo + '.material' )
				
				mc.defaultNavigation( connectToExisting=True, source=stShader, destination=matSg )
				
				if mc.connectionInfo( matSg + shaderConnection, sfd=1 ).split( '.' )[0] == "":
					mc.connectAttr( stShader + shaderOut, matSg + shaderConnection )
				
					if processType == 'mentalRay':
						mc.connectAttr( stShader + shaderOut, matSg + '.miShadowShader' )
						mc.connectAttr( stShader + shaderOut, matSg + '.miPhotonShader' )
			
			self.stFixTextureDisplay( matInfo, colorSource, stShader, processType )
			
			#mc.delete(matHistory)
			if matHistory != []:
				#delete old shader and update texture display on idle
				mc.evalDeferred( "mc.delete( " + str( matHistory ) + " )", lp=True )
				mc.evalDeferred( "mc.assignSpeedTreeShader('" + matInfo + "','" + colorSource + "','" + stShader + "','" + processType + "')", lp=True )
				#rename new materials only
				if argsLen == 7 and argList.asBool(6):
					mc.evalDeferred( "mc.rename( '" + stShader + "', '" + mat + "' )", lp=True )
			
			#dirty attributes
			mc.setAttr( SpeedTreeFbx + '.fbxsh', max( 0.02, ( mc.getAttr( SpeedTreeFbx + '.fbxsh' ) ) ) )
			mc.setAttr( SpeedTreeFbx + '.fbxds', mc.getAttr( SpeedTreeFbx + '.fbxds' ) )
	

#Build new SpeedTree Shader
class BuildSpeedTreeShaderNetwork( OpenMayaMPx.MPxCommand ):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__( self )
	
	def stSetFileNodeDefaults( self, nodeName, alphaToLum=False, mipMap=False ):
		"""Forces default values for file nodes"""
		
		mc.setAttr( nodeName + '.ihi', 0 )
		if mc.nodeType( nodeName ) == 'file':
			if mipMap:
				mc.setAttr( nodeName + '.ft', 1 )
			
			if alphaToLum:
				mc.setAttr( nodeName + '.alphaIsLuminance', 1 )
	
	
	def stAdd2dTexture( self, outNode, matName='SpeedTree', alphaToLum=False, mipMap=False ):
		"""Adds a place2dTexture node to file textures using a UV chooser"""
		
		if mc.nodeType( outNode ) == 'file':
			
			self.stSetFileNodeDefaults( outNode, alphaToLum, mipMap )
			alpha2dTex = mc.connectionInfo( outNode + '.uvCoord', sfd=1 ).split ( '.' )[0]
			
			if alpha2dTex == "":
				alpha2dTex = mc.createNode( 'place2dTexture', name=matName+'_Place2d' )
				mc.connectAttr( alpha2dTex + '.outUV', outNode + '.uvCoord' )
				mc.connectAttr( alpha2dTex + '.outUvFilterSize', outNode + '.uvFilterSize' )
				mc.connectAttr( alpha2dTex + '.vertexCameraOne', outNode + '.vertexCameraOne' )
				mc.connectAttr( alpha2dTex + '.vertexUvThree', outNode + '.vertexUvThree' )
				mc.connectAttr( alpha2dTex + '.vertexUvTwo', outNode + '.vertexUvTwo' )
				mc.connectAttr( alpha2dTex + '.vertexUvOne', outNode + '.vertexUvOne' )
				mc.connectAttr( alpha2dTex + '.repeatV', outNode + '.repeatV' )
				mc.connectAttr( alpha2dTex + '.repeatU', outNode + '.repeatU' )
				mc.connectAttr( alpha2dTex + '.rotateFrame', outNode + '.rotateFrame' )
				mc.connectAttr( alpha2dTex + '.offsetV', outNode + '.offsetV' )
				mc.connectAttr( alpha2dTex + '.offsetU', outNode + '.offsetU' )
				mc.setAttr( alpha2dTex + '.ihi', 0 )
			
			return alpha2dTex
	
	
	def stAddUvChooser( self, SpeedTreeFbx, matName, uvChooser, map=None, uvSet=5, alphaToLum=False ):
		"""Creates a new connection to a UV chooser"""
		
		if map != None:
			mipMap = ( uvChooser == matName + '_DetailUVs' ) or ( uvChooser == matName + '_DetailBlendUVs' )
			place2d = self.stAdd2dTexture( map, matName, alphaToLum, mipMap )
			mc.addAttr( place2d, longName='uvChooserSet', shortName='uvcs', at='short', dv=uvSet, r=1, w=1, h=1, s=1 )
			mc.addAttr( place2d, longName='uvChooserName', shortName='uvcn', dt='string', r=1, w=1, h=1, s=1 )
			mc.setAttr( place2d + '.uvChooserName', uvChooser, type='string' )
				
			#create blend UVs	
			mc.connectAttr( uvChooser + '.outUv', place2d + '.uvCoord' )
			mc.connectAttr( uvChooser + '.outVertexCameraOne', place2d + '.vertexCameraOne' )
			mc.connectAttr( uvChooser + '.outVertexUvThree', place2d + '.vertexUvThree' )
			mc.connectAttr( uvChooser + '.outVertexUvTwo', place2d + '.vertexUvTwo' )
			mc.connectAttr( uvChooser + '.outVertexUvOne', place2d + '.vertexUvOne' )
		
		if uvSet < 5 and mc.getAttr( SpeedTreeFbx + '.shapeNodes', mi=True ) != None:
			numMatShapes = len( mc.getAttr( SpeedTreeFbx + '.shapeNodes', mi=True ) )
			for m in range( 0, numMatShapes ):
				matShape = mc.connectionInfo( SpeedTreeFbx + '.shapeNodes[' + str(m) + ']', sfd=1 ).split( '.' )[0]
				mc.connectAttr( matShape + '.uvSet[' + str( uvSet ) + '].uvSetName', uvChooser + '.uvSets[' + str(m) + ']' )
					
		uvSet += 1
		return uvSet
	
	
	def doIt( self, argList ):
		"""Builds all of the nodes needed for the specified shader type and returns settings """
				
		argsLen = argList.length()
		if argsLen >= 2:
			SpeedTreeFbx = argList.asString(0)
			matInfo = argList.asString(1)
			matSg = mc.connectionInfo( matInfo + '.shadingGroup', sfd=1 ).split( '.' )[0]
			
			doCpv = False
			if argsLen > 2:
				mat = argList.asString(2)
				if argsLen > 3:
					doCpv = argList.asBool(3)
			
			if argsLen <= 2 or mat == '':
				mat = SpeedTreeFbx[:-13]
			
			#disable hypergraph incrementing
			mc.hyperShade( inc=0 )
			
			#process variables
			shaderName = mat + '_Shader'
			displayMap = baseMap = baseNormalMap = colorSource = ''
			colorHasAlpha = specHasAlpha = normalHasAlpha = False
			doColor = mc.getAttr( SpeedTreeFbx + '.dm' ) != ""
			doDetail = mc.getAttr( SpeedTreeFbx + '.ddm' ) != ""
			doOpacity = mc.getAttr( SpeedTreeFbx + '.om' ) != ""
			doBlendMask = mc.getAttr( SpeedTreeFbx + '.bm' ) != ""
			doSpec = mc.getAttr( SpeedTreeFbx + '.sm' ) != ""
			doTrans = mc.getAttr( SpeedTreeFbx + '.tm' ) != ""
			doNormal = mc.getAttr( SpeedTreeFbx + '.nm' ) != ""
			doDetailNormal = doNormal and mc.getAttr( SpeedTreeFbx + '.dnm' ) != ""
			doHeight = mc.getAttr( SpeedTreeFbx + '.hm' )!= ""
			doBlend = mc.getAttr( SpeedTreeFbx + '.bib' ) != 0
			doGamma = mc.getAttr( SpeedTreeFbx + '.ugc' ) != 0
			fbxAmbc = mc.getAttr( SpeedTreeFbx + '.ambc' )[0]
			fbxShininess = max( 2, ( mc.getAttr( SpeedTreeFbx + '.fbxShininess' ) * 100 ) )
			
			#add attribut plugs to array
			SpeedTreeAttributes = []
			SpeedTreeAttributes.append( SpeedTreeFbx + '.ambc' )
			SpeedTreeAttributes.append( SpeedTreeFbx + '.ds' )
			SpeedTreeAttributes.append( SpeedTreeFbx + '.shininess' )
			SpeedTreeAttributes.append( SpeedTreeFbx + '.so' )
			SpeedTreeAttributes.append( SpeedTreeFbx + '.vd' )
			
			#establish shader type for process
			pInd = mc.getAttr( SpeedTreeFbx + '.processIndex' )
			autoUpdate = mc.optionVar( q='SpeedTreeAutoUpdate' )
			currRenderer = mc.getAttr( 'defaultRenderGlobals.currentRenderer' )
			hardwareMode = False
			hardwareType = None
			
			try:
				#mental ray mia_material
				if( pInd == 0 and currRenderer == 'mentalRay' ) or ( pInd > 1 and supportedRenderers[ pInd - 1 ] == 'mentalRay' ):
					stShader = mc.shadingNode( 'mia_material', asShader=True, name=shaderName )
					mc.addAttr( stShader, longName='normalCamera', dt='float3', r=0, w=0, h=1, s=0 )
					processType = 'mentalRay'
					
				#hardware shading only
				elif( pInd == 0 and currRenderer in hardwareRenderers ) or ( pInd > 1 and supportedRenderers[ pInd - 1 ] in hardwareRenderers ):
					stShader = mc.shadingNode( 'phong', asShader=True, name=shaderName )
					doGamma = doBlend = doDetailNormal = doHeight = doBlendMask = 0
					SpeedTreeAttributes[2] = ''
					hardwareMode = True
					if pInd == 0:
						processType = hardwareType = currRenderer
					else:
						processType = hardwareType = rendererList[ pInd - 1 ]
					
				#standard generic shader
				else:
					stShader = mc.shadingNode( 'phong', asShader=True, name=shaderName )
					processType = 'generic'
					
			except:
				stShader = mc.shadingNode( 'phong', asShader=True, name=shaderName )
				processType = 'generic'
			
			mc.setAttr( SpeedTreeFbx + '.processedType', processType, type='string' )
			mc.setAttr( stShader + '.ihi', 1 )
			
			if hardwareMode:
				processType = 'generic'
				
			
			#################################################
			# Diffuse / Detail
			
			colorPlug = SpeedTreeFbx + '.dc'
			
			#gamma correction
			if doGamma:
				sceneGammaPlug = stSceneGammaPlug()
				colorGamma = mc.createNode( 'gammaCorrect', name=mat+'_ColorGamma' )
				mc.connectAttr( SpeedTreeFbx + '.gammaCorrection', colorGamma + '.gamma' )
				mc.setAttr( colorGamma + '.ihi', 0 )
				
				gammaConnection = mc.connectionInfo( SpeedTreeFbx + '.sceneGamma', sfd=True )
				if gammaConnection != '':
					mc.disconnectAttr( gammaConnection, SpeedTreeFbx + '.sceneGamma' )
				
				vGammaValue = mc.optionVar( q='SpeedTreeGammaValue' )
				mc.setAttr( SpeedTreeFbx + '.sceneGamma', vGammaValue )
				#mc.setAttr( SpeedTreeFbx + '.sceneGamma', sceneGammaPlug[1] )
				if mc.getAttr( SpeedTreeFbx + '.syncGamma' ):
					mc.connectAttr( sceneGammaPlug[0], SpeedTreeFbx + '.sceneGamma' )
				
				colorPlug = colorGamma + '.outValue'
			
			#color per vertex
			if doCpv and processType == 'mentalRay':
				
				cpvSwitch = mc.createNode( 'condition', name=mat+'_CpvSwitch' )
				cpvMultiply = mc.createNode( 'multiplyDivide', name=mat+'_CPVMultiply' )
				colorPerVertex = mc.createNode( 'mentalrayVertexColors', name=mat+'_VertexColors' )
				mc.setAttr( cpvSwitch + '.ihi', 0 )
				mc.setAttr( cpvMultiply + '.ihi', 0 )
				mc.setAttr( colorPerVertex + '.ihi', 0 )
				
				#get shape nodes
				shapeNodeIndices = mc.getAttr( SpeedTreeFbx + '.shapeNodes', mi=1 )
				if shapeNodeIndices != None and len( shapeNodeIndices ) > 0:
					shapeNodesLen = len( mc.getAttr( SpeedTreeFbx + '.shapeNodes', mi=1 ) )
					for s in range( 0, shapeNodesLen ):
						shapeNode = mc.connectionInfo( SpeedTreeFbx + '.shapeNodes[' + str(s) + ']', sfd=True ).split( '.' )[0]
						mc.connectAttr( shapeNode + '.colorSet[0].colorName', colorPerVertex + '.cpvSets[' + str(s) + ']' )
				
				mc.connectAttr( colorPerVertex + '.outColor', cpvMultiply + '.input2' )
				mc.connectAttr( SpeedTreeFbx + '.cpv', cpvSwitch + '.firstTerm' )
				mc.connectAttr( cpvMultiply + '.output', cpvSwitch + '.colorIfFalse' )
				if doGamma:
					mc.connectAttr( cpvSwitch + '.outColor', colorGamma + '.value' )
				else:
					colorPlug = cpvSwitch + '.outColor'
		
			if doColor:
				colorSource = baseMap = displayMap = mc.createNode( 'file', name=mat+'_DiffuseMap' )
				mc.connectAttr( SpeedTreeFbx + '.dm', baseMap + '.fileTextureName' )
				if hardwareType != 'mayaHardware2':
					mc.connectAttr( SpeedTreeFbx + '.dc', baseMap + '.colorGain' )
				
				self.stSetFileNodeDefaults( baseMap )
				colorHasAlpha = stTestForAlphaMap( baseMap )[2]
				colorSourcePlug = colorSource + '.outColor'
				
				if doDetail:
					detailMap = detailMask = mc.createNode( 'file', name=mat+'_DetailMap' )
					mc.connectAttr( SpeedTreeFbx + '.ddm', detailMap + '.fileTextureName' )
					if hardwareType != 'mayaHardware2':
						mc.connectAttr( SpeedTreeFbx + '.dc', detailMap + '.colorGain' )
					detailUvs = mc.createNode( 'uvChooser', name=mat+'_DetailUVs' )
					self.stAddUvChooser( SpeedTreeFbx, mat, detailUvs, detailMap, 1 )
					mc.setAttr( detailUvs + '.ihi', 0 )
					
					if doBlendMask:
						detailMask = mc.createNode( 'file', name=mat+'_DetailMask' )
						mc.connectAttr( SpeedTreeFbx + '.bm', detailMask + '.fileTextureName' )
						self.stAddUvChooser( SpeedTreeFbx, mat, detailUvs, detailMask, 5, True )
						
					colorSource = displayMap = mc.createNode( 'layeredTexture', name=mat+'_DiffuseLayers' )
					colorSourcePlug = colorSource + '.outColor'
					mc.setAttr( colorSource + '.ihi', 0 )
					
					mc.connectAttr( baseMap + '.outColor', colorSource + '.inputs[3].color' )
					mc.connectAttr( detailMap + '.outColor', colorSource + '.inputs[1].color' )
					mc.connectAttr( detailMask + '.outAlpha', colorSource + '.inputs[1].alpha' )
				
				if doBlend:
					displayMap = baseMap
					if colorSource == baseMap:
						colorSource = mc.createNode( 'layeredTexture', name=mat+'_DiffuseLayers' )
						mc.connectAttr( baseMap + '.outColor', colorSource + '.inputs[3].color' )
						colorSourcePlug = colorSource + '.outColor'
						mc.setAttr( colorSource + '.ihi', 0 )
						
					baseBlendMap = mc.createNode( 'file', name=mat+'_DiffuseBlend' )
					mc.connectAttr( SpeedTreeFbx + '.dm', baseBlendMap + '.fileTextureName' )
					mc.connectAttr( SpeedTreeFbx + '.dc', baseBlendMap + '.colorGain' )
					blendUvs = mc.createNode( 'uvChooser', name=mat+'_BaseBlendUVs' )
					self.stAddUvChooser( SpeedTreeFbx, mat, blendUvs, baseBlendMap, 3 )
					mc.setAttr( blendUvs + '.ihi', 0 )
					
					mc.connectAttr( baseBlendMap + '.outColor', colorSource + '.inputs[2].color' )
					
					#blend data
					blendData = mc.createNode( 'uvChooser', name=mat+'_BlendData' )
					self.stAddUvChooser( SpeedTreeFbx, mat, blendData, None, 2 )
					blendWeight = mc.createNode( 'multiplyDivide', name=mat+'_BlendWeight' )
					blendClamp = mc.createNode( 'clamp', name=mat+'_BlendClamp' )
					blendInvert = mc.createNode( 'reverse', name=mat+'_ReverseBlend' )
					mc.connectAttr( SpeedTreeFbx + '.blendWeight', blendWeight + '.input2X' )
					mc.connectAttr( blendData + '.outU', blendWeight + '.input1X' )
					mc.connectAttr( blendWeight + '.output', blendClamp + '.input' )
					mc.connectAttr( blendClamp + '.output', blendInvert + '.input' )
					mc.connectAttr( blendInvert + '.outputX', colorSource + '.inputs[2].alpha' )
					mc.addAttr( blendWeight, longName='uvChooserSet', shortName='uvcs', at='short', dv=2, r=1, w=1, h=1, s=1 )
					mc.addAttr( blendWeight, longName='uvChooserName', shortName='uvcn', dt='string', r=1, w=1, h=1, s=1 )
					mc.setAttr( blendWeight + '.uvcn', blendData, type='string' )
					mc.setAttr( blendWeight + '.operation', 3 )
					mc.setAttr( blendWeight + '.ihi', 0 )
					mc.setAttr( blendClamp + '.maxR', 1.0 )
					mc.setAttr( blendClamp + '.ihi', 0 )
					mc.setAttr( blendData + '.ihi', 0 )
					mc.setAttr( blendInvert + '.ihi', 0 )
					
					if doDetail:
						detailBlendMap = detailBlendMask = mc.createNode( 'file', name=mat+'_DetailBlend' )
						mc.connectAttr( SpeedTreeFbx + '.ddm', detailBlendMap + '.fileTextureName' )
						mc.connectAttr( SpeedTreeFbx + '.dc', detailBlendMap + '.colorGain' )
						
						detailBlendUvs = mc.createNode( 'uvChooser', name=mat+'_DetailBlendUVs' )
						self.stAddUvChooser( SpeedTreeFbx, mat, detailBlendUvs, detailBlendMap, 4 )
						mc.connectAttr( detailBlendMap + '.outColor', colorSource + '.inputs[0].color' )
						mc.setAttr( detailBlendUvs + '.ihi', 0 )
						
						if doBlendMask:
							detailBlendMask = mc.createNode( 'file', name=mat+'_DetailBlendMask' )
							mc.connectAttr( SpeedTreeFbx + '.bm', detailBlendMask + '.fileTextureName' )
							self.stAddUvChooser( SpeedTreeFbx, mat, detailBlendUvs, detailBlendMask, 5, True )
							
						#detail blend data
						detailBlendMultiply = mc.createNode( 'multiplyDivide', name=mat+'_DetailBlendMask' )
						mc.connectAttr( blendInvert + '.output', detailBlendMultiply + '.input1' )
						mc.connectAttr( detailBlendMask + '.outAlpha', detailBlendMultiply + '.input2X' )
						mc.connectAttr( detailBlendMask + '.outAlpha', detailBlendMultiply + '.input2Y' )
						mc.connectAttr( detailBlendMask + '.outAlpha', detailBlendMultiply + '.input2Z' )
						mc.connectAttr( detailBlendMultiply + '.outputX', colorSource + '.inputs[0].alpha' )
						mc.setAttr( detailBlendMultiply + '.ihi', 0 )
				
				if doCpv and processType == 'mentalRay':
					mc.connectAttr( colorSourcePlug, cpvMultiply + '.input1' )
					mc.connectAttr( colorSourcePlug, cpvSwitch + '.colorIfTrue' )
					
				elif doGamma:
					mc.connectAttr( colorSourcePlug, colorGamma + '.value' )
				else:
					colorPlug = colorSourcePlug
				
			else:
				colorHasAlpha = 0
				colorSource = baseMap = ''
				if doCpv and processType == 'mentalRay':
					mc.connectAttr( SpeedTreeFbx + '.dc', cpvMultiply + '.input1' )
					mc.connectAttr( SpeedTreeFbx + '.dc', cpvSwitch + '.colorIfTrue' )
					
				elif doGamma and not hardwareMode:
					mc.connectAttr( SpeedTreeFbx + '.dc', colorGamma + '.value' )
				
			SpeedTreeAttributes.append( colorPlug )		
			
			
			#################################################
			# Opacity / Backface culling
			
			opacityPlug = opacSource = opacClamp = ''
			if doOpacity and not hardwareMode:
				opacSource = mc.createNode( 'file', name=mat+'_Opacity' )
				mc.connectAttr( SpeedTreeFbx + '.om', opacSource + '.fileTextureName' )
				self.stSetFileNodeDefaults( opacSource, True )
				
			elif doColor and colorHasAlpha:
				opacSource = baseMap
			
			#opacit layers (currently disabled)
			doOpacityLayers = False
			if doOpacityLayers:
				opacLayeredSource = mc.createNode( 'layeredTexture', name=mat+'_OpacityLayers' )
				mc.connectAttr( opacSource + '.outAlpha', opacLayeredSource + '.inputs[3].colorR' )
				mc.connectAttr( opacSource + '.outAlpha', opacLayeredSource + '.inputs[3].colorG' )
				mc.connectAttr( opacSource + '.outAlpha', opacLayeredSource + '.inputs[3].colorB' )
				mc.connectAttr( detailMask + '.outAlpha', opacLayeredSource + '.inputs[1].colorR' )
				mc.connectAttr( detailMask + '.outAlpha', opacLayeredSource + '.inputs[1].colorG' )
				mc.connectAttr( detailMask + '.outAlpha', opacLayeredSource + '.inputs[1].colorB' )
				mc.setAttr( opacLayeredSource + '.inputs[1].blendMode', 4 )
				mc.setAttr( opacLayeredSource + '.alphaIsLuminance', 1 )
				mc.setAttr( opacLayeredSource + '.ihi', 0 )
				opacSource = opacLayeredSource
			
			#backface culling
			if processType == 'generic' and hardwareMode == False:
				bfcSwitch = mc.createNode( 'condition', name=mat+'_BackfaceCullSwitch' )
				bfcMultiply = mc.createNode( 'multiplyDivide', name=mat+'_BackfaceCull' )
				sampleObj = mc.createNode( 'samplerInfo', name=mat+'_SampleShape' )
				mc.setAttr( bfcSwitch + '.ihi', 0 )
				mc.setAttr( bfcMultiply + '.ihi', 0 )
				mc.setAttr( sampleObj + '.ihi', 0 )
				opacityPlug = bfcSwitch + '.outColor'
				
				mc.connectAttr( sampleObj + '.flippedNormal', bfcMultiply + '.input1X' )
				mc.connectAttr( SpeedTreeFbx + '.backfaceCull', bfcMultiply + '.input2X' )
				mc.connectAttr( bfcMultiply + '.outputX', bfcSwitch + '.firstTerm' )
				
				if opacSource != '' and ( opacSource != baseMap or colorHasAlpha ):
					mc.connectAttr( opacSource + '.outTransparency', bfcSwitch + '.colorIfTrue' )
			
			if opacSource != '':
				if hardwareMode:
					opacityPlug = ''
					if colorHasAlpha:
						opacityPlug = opacSource + '.outTransparency'
						if hardwareType == 'mayaHardware':
							mc.connectAttr( SpeedTreeFbx + '.alphaScalar', opacSource + '.alphaGain' )
							
				elif processType == 'mentalRay' or opacSource != baseMap:
					opacityPlug = opacSource + '.outAlpha'
					
					if mc.nodeType( opacSource ) == 'file':
						mc.connectAttr( SpeedTreeFbx + '.alphaScalar', opacSource + '.alphaGain' )
					#opacit layers (currently disabled)
					elif doOpacity and doOpacityLayers:
						opacityInputPlugs = mc.getAttr( opacSource + '.inputs', mi=1 )
						for p in opacityInputPlugs:
							mc.connectAttr( SpeedTreeFbx + '.alphaScalar', opacSource + '.inputs[' +str(p)+ '].alpha' )
					
					opacClamp = mc.createNode( 'clamp', name=mat+'_OpacClamp' )
					mc.setAttr( opacClamp + '.max', 1, 1, 1, type='float3' )
					mc.setAttr( opacClamp + '.ihi', 0 )
			
					if processType == 'generic':
						mc.connectAttr( bfcSwitch + '.outColor', opacClamp + '.input' )
						
					elif opacClamp != '':
						mc.connectAttr( opacityPlug, opacClamp + '.inputR' )
						mc.connectAttr( opacityPlug, opacClamp + '.inputB' )
						mc.connectAttr( opacityPlug, opacClamp + '.inputG' )
							
					opacityPlug = opacClamp + '.output'
			
			SpeedTreeAttributes.append( opacityPlug )
			
			
			#################################################
			# Normal mapping
			
			normalPlug = layeredNormalPlug = layeredNormals = ''
			if doNormal:
				bumpSource = baseNormalMap = mc.createNode( 'file', name=mat+'_NormalMap' )
				mc.connectAttr( SpeedTreeFbx + '.nm', baseNormalMap + '.fileTextureName' )
				self.stSetFileNodeDefaults( baseNormalMap )
				
				baseBump2d = mc.createNode( 'bump2d', name=mat+'_BaseBump2d' )
				mc.connectAttr( baseNormalMap + '.outAlpha', baseBump2d + '.bumpValue' )
				mc.setAttr( baseBump2d + '.bumpInterp', 1 )
				mc.setAttr( baseBump2d + '.ihi', 0 )
				
				if hardwareMode:
					normalPlug = baseBump2d + '.outNormal'
				else:
					if doDetailNormal:
						detailNormalMap = mc.createNode( 'file', name=mat+'_DetailNormal' )
						mc.connectAttr( SpeedTreeFbx + '.dnm', detailNormalMap + '.fileTextureName' )
						self.stAddUvChooser( SpeedTreeFbx, mat, detailUvs, detailNormalMap )
						
						detailBump2d = mc.createNode( 'bump2d', name=mat+'_DetailBump2d' )
						mc.connectAttr( detailNormalMap + '.outAlpha', detailBump2d + '.bumpValue' )
						mc.setAttr( detailBump2d + '.bumpInterp', 1 )
						mc.setAttr( detailBump2d + '.ihi', 0 )
						
						if processType == 'generic':
							bumpSource = softwareLayeredNmls = mc.createNode( 'layeredTexture', name=mat+'_SoftwareLayeredNormals' )
							mc.connectAttr( baseNormalMap + '.outColor', bumpSource + '.inputs[1].color' )
							mc.connectAttr( detailNormalMap + '.outColor', bumpSource + '.inputs[0].color' )
							mc.connectAttr( detailMask + '.outAlpha', bumpSource + '.inputs[0].alpha' )
							mc.setAttr( bumpSource + '.ihi', 0 )
					
					if processType == 'generic':
						#software normal mapping
						softwareSwitch = mc.createNode( 'condition', name=mat+'_SoftwareSwitch' )
						rgbToXyz = mc.createNode( 'setRange', name=mat+'_RGBtoXYZ' )
						vecProd0 = mc.createNode( 'vectorProduct', name=mat+'_NmlCrossProd' )
						vecProd1 = mc.createNode( 'vectorProduct', name=mat+'_NmlX' )
						vecProd2 = mc.createNode( 'vectorProduct', name=mat+'_NmlY' )
						vecProd3 = mc.createNode( 'vectorProduct', name=mat+'_NmlZ' )
						normalMatrix = mc.createNode( 'vectorProduct', name=mat+'_SoftwareMatrix' )
						mc.setAttr( softwareSwitch + '.ihi', 0 )
						mc.setAttr( rgbToXyz + '.ihi', 0 )
						mc.setAttr( vecProd0 + '.ihi', 0 )
						mc.setAttr( vecProd1 + '.ihi', 0 )
						mc.setAttr( vecProd2 + '.ihi', 0 )
						mc.setAttr( vecProd3 + '.ihi', 0 )
						mc.setAttr( normalMatrix + '.ihi', 0 )
						
						mc.connectAttr( bumpSource + '.outColor', rgbToXyz + '.value' )
						mc.setAttr( rgbToXyz + '.min', -1, 1, -1, type='float3' )	#green inverted
						mc.setAttr( rgbToXyz + '.max', 1, -1, 1, type='float3' )	#green inverted
						mc.setAttr( rgbToXyz + '.oldMax', 1, 1, 1, type='float3' )
						mc.setAttr( vecProd0 + '.operation', 2 )
						mc.setAttr( vecProd0 + '.normalizeOutput', 1 )
						try:
							mc.connectAttr( sampleObj + '.tangentUCamera', vecProd0 + '.input1' )
						except:
							sampleObj = mc.createNode( 'samplerInfo', name=mat+'_SampleShape' )
							mc.connectAttr( sampleObj + '.tangentUCamera', vecProd0 + '.input1' )
							mc.setAttr( sampleObj + '.ihi', 0 )
							
						mc.connectAttr( sampleObj + '.normalCamera', vecProd0 + '.input2' )
						mc.connectAttr( sampleObj + '.tangentUx', vecProd1 + '.input2X' )
						mc.connectAttr( sampleObj + '.normalCameraX', vecProd1 + '.input2Z' )
						mc.connectAttr( sampleObj + '.tangentUy', vecProd2 + '.input2X' )
						mc.connectAttr( sampleObj + '.normalCameraY', vecProd2 + '.input2Z' )
						mc.connectAttr( sampleObj + '.tangentUz', vecProd3 + '.input2X' )
						mc.connectAttr( sampleObj + '.normalCameraZ', vecProd3 + '.input2Z' )
						mc.connectAttr( vecProd0 + '.outputX', vecProd1 + '.input2Y' )
						mc.connectAttr( vecProd0 + '.outputY', vecProd2 + '.input2Y' )
						mc.connectAttr( vecProd0 + '.outputZ', vecProd3 + '.input2Y' )
						mc.connectAttr( rgbToXyz + '.outValue', vecProd1 + '.input1' )
						mc.connectAttr( rgbToXyz + '.outValue', vecProd2 + '.input1' )
						mc.connectAttr( rgbToXyz + '.outValue', vecProd3 + '.input1' )
						
						mc.connectAttr( normalMatrix + '.output', softwareSwitch + '.colorIfTrue' )
						mc.connectAttr( SpeedTreeFbx + '.rendererIndex', softwareSwitch + '.firstTerm' )
						mc.connectAttr( vecProd1 + '.outputX', normalMatrix + '.input1X' )
						mc.connectAttr( vecProd2 + '.outputX', normalMatrix + '.input1Y' )
						mc.connectAttr( vecProd3 + '.outputX', normalMatrix + '.input1Z' )
						mc.setAttr( normalMatrix + '.operation', 3 )
						
						#mental ray generic
						normalPlug = softwareSwitch + '.outColor'
						layeredNormalPlug = softwareSwitch + '.colorIfFalse'
						
					elif processType == 'mentalRay':
						setNormal = mc.createNode( 'misss_set_normal', name=mat+'_SetNormal' )
						normalPlug = layeredNormalPlug = setNormal + '.normal'
						mc.setAttr( setNormal + '.ihi', 0 )
						
					#mental ray normal mapping
					if doBlend or doDetailNormal:
						layeredNormals = baseNormals = mc.createNode( 'blendColors', name=mat+'_LayeredNormals' )
						mc.connectAttr( layeredNormals + '.output', layeredNormalPlug )
						mc.setAttr( layeredNormals + '.ihi', 0 )
						
						if doBlend:
							blendNormalMap = mc.createNode( 'file', name=mat+'_NormalBlend' )
							mc.connectAttr( SpeedTreeFbx + '.nm', blendNormalMap + '.fileTextureName' )
							self.stAddUvChooser( SpeedTreeFbx, mat, blendUvs, blendNormalMap )
							
							blendBump2d = mc.createNode( 'bump2d', name=mat+'_BlendBump2d' )
							mc.connectAttr( blendNormalMap + '.outAlpha', blendBump2d + '.bumpValue' )
							mc.setAttr( blendBump2d + '.bumpInterp', 1 )
							mc.setAttr( blendBump2d + '.ihi', 0 )
							
							if doDetailNormal:
								blendDetailNormalMap = mc.createNode( 'file', name=mat+'_DetailNormal' )
								mc.connectAttr( SpeedTreeFbx + '.dnm', blendDetailNormalMap + '.fileTextureName' )
								self.stAddUvChooser( SpeedTreeFbx, mat, detailBlendUvs, blendDetailNormalMap )
								
								blendDetailBump2d = mc.createNode( 'bump2d', name=mat+'_BlendDetailBump2d' )
								mc.connectAttr( blendDetailNormalMap + '.outAlpha', blendDetailBump2d + '.bumpValue' )
								mc.setAttr( blendDetailBump2d + '.bumpInterp', 1 )
								mc.setAttr( blendDetailBump2d + '.ihi', 0 )
								
								baseNormals = mc.createNode( 'blendColors', name=mat+'_BaseNormals' )
								blendNormals = mc.createNode( 'blendColors', name=mat+'_BlendNormals' )
								mc.setAttr( baseNormals + '.ihi', 0 )
								mc.setAttr( blendNormals + '.ihi', 0 )
								
								mc.connectAttr( baseNormals + '.output', layeredNormals + '.color2' )
								mc.connectAttr( blendNormals + '.output', layeredNormals + '.color1' )
								mc.connectAttr( blendInvert + '.outputX', layeredNormals + '.blender' )
								
								mc.connectAttr( blendBump2d + '.outNormal', blendNormals + '.color2' )
								mc.connectAttr( blendDetailBump2d + '.outNormal', blendNormals + '.color1' )
								mc.connectAttr( detailBlendMask + '.outAlpha', blendNormals + '.blender' )
							
								mc.connectAttr( baseBump2d + '.outNormal', baseNormals + '.color2' )
								mc.connectAttr( detailBump2d + '.outNormal', baseNormals + '.color1' )
								mc.connectAttr( detailMask + '.outAlpha', baseNormals + '.blender' )
							else:
								mc.connectAttr( baseBump2d + '.outNormal', baseNormals + '.color2' )
								mc.connectAttr( blendBump2d + '.outNormal', baseNormals + '.color1' )
								mc.connectAttr( blendInvert + '.outputX', baseNormals + '.blender' )
						else:
							mc.connectAttr( baseBump2d + '.outNormal', baseNormals + '.color2' )
							mc.connectAttr( detailBump2d + '.outNormal', baseNormals + '.color1' )
							mc.connectAttr( detailMask + '.outAlpha', baseNormals + '.blender' )
						
					else:
						mc.connectAttr( baseBump2d + '.outNormal', layeredNormalPlug )
				
			SpeedTreeAttributes.append( normalPlug )	
			
			
			#################################################
			# Specular / Transmission
			
			specSource = transSource = transClamp = ''
			specPlug = SpeedTreeFbx + '.sc'
			transColorPlug = SpeedTreeFbx + '.translucency'
			transScalePlug = SpeedTreeFbx + '.translucencyScalar'
			
			if doSpec or opacSource !='':
				specSource = mc.createNode( 'file', name=mat+'_SpecMap' )
				self.stSetFileNodeDefaults( specSource )
				specPlug = specColorPlug = specSource + '.outColor'
				
				if hardwareType != 'mayaHardware2':
					mc.connectAttr( SpeedTreeFbx + '.sc', specSource + '.colorGain' )
				
				if doSpec:
					mc.connectAttr( SpeedTreeFbx + '.sm', specSource + '.fileTextureName' )
					specHasAlpha = stTestForAlphaMap( specSource )[2]
					
				elif doOpacity or colorHasAlpha:
					if doOpacity:
						mc.connectAttr( SpeedTreeFbx + '.om', specSource + '.fileTextureName' )
					elif colorHasAlpha:
						mc.delete( specSource )
						specSource = mc.createNode( 'multiplyDivide', name=mat+'_SpecMultiply' )
						mc.connectAttr( SpeedTreeFbx + '.sc', specSource + '.input1' )
						mc.connectAttr( baseMap + '.outAlpha', specSource + '.input2X' )
						mc.connectAttr( baseMap + '.outAlpha', specSource + '.input2Y' )
						mc.connectAttr( baseMap + '.outAlpha', specSource + '.input2Z' )
						specPlug = specColorPlug = specSource + '.output'
						
					specHasAlpha = False
					doSpec = True
					
				
				else:
					mc.delete( specSource )
					specPlug = SpeedTreeFbx + '.sc'
			
			if hardwareMode:
				transScalePlug = ''
				
			else:
				specSwitch = mc.createNode( 'condition', name=mat+'_SpecSwitch' )
				mc.setAttr( specSwitch + '.colorIfFalse', 0, 0, 0, type='float3' )
				mc.setAttr( specSwitch + '.ihi', 0 )
				
				specPlug = specSwitch + '.outColor'
				
				try:
					mc.connectAttr( sampleObj + '.flippedNormal', specSwitch + '.firstTerm' )
				except:
					sampleObj = mc.createNode( 'samplerInfo', name=mat+'_SampleShape' )
					mc.connectAttr( sampleObj + '.flippedNormal', specSwitch + '.firstTerm' )
					mc.setAttr( sampleObj + '.ihi', 0 )
					
				if doSpec:
					mc.connectAttr( specColorPlug, specSwitch + '.colorIfTrue' )
					
					if doTrans:
						transSource = mc.createNode( 'file', name=mat+'_TransMap' )
						mc.connectAttr( SpeedTreeFbx + '.tm', transSource + '.fileTextureName' )
						self.stSetFileNodeDefaults( transSource, True )
						
						transScalePlug = transSource + '.outAlpha'
						transColorPlug = transSource + '.outColor'
						
						if processType == 'generic':
							mc.connectAttr( SpeedTreeFbx + '.translucencyScalar', transSource + '.alphaGain' )
						else:
							mc.connectAttr( SpeedTreeFbx + '.translucency', transSource + '.colorGain' )
						
					elif specHasAlpha:
						transSource = specSource
						if processType == 'generic':
							mc.connectAttr( SpeedTreeFbx + '.translucencyScalar', transSource + '.alphaGain' )
							transScalePlug = transSource + '.outAlpha'
						else:
							transMultiply = mc.createNode( 'multiplyDivide', name=mat+'_TransMultiply' )
							mc.connectAttr( SpeedTreeFbx + '.trans', transMultiply + '.input1' )
							mc.connectAttr( transSource + '.outAlpha', transMultiply + '.input2X' )
							mc.connectAttr( transSource + '.outAlpha', transMultiply + '.input2Y' )
							mc.connectAttr( transSource + '.outAlpha', transMultiply + '.input2Z' )
							mc.setAttr( transMultiply + '.ihi', 0 )
							
							transColorPlug = transMultiply + '.output'
							transScalePlug = transMultiply + '.outputX'
								
				else:
					mc.connectAttr( SpeedTreeFbx + '.sc', specSwitch + '.colorIfTrue' )
					if processType == 'generic':
						transMultiply = mc.createNode( 'multiplyDivide', name=mat+'_TransMultiply' )
						mc.connectAttr( SpeedTreeFbx + '.translucencyScalar', transMultiply + '.input1X' )
						mc.connectAttr( SpeedTreeFbx + '.enableTranslucency', transMultiply + '.input2X' )
						mc.setAttr( transMultiply + '.ihi', 0 )
						
						transScalePlug = transMultiply + '.outputX'
				
				#clamp "transparency" to 0.5
				if processType == 'mentalRay':
					transClamp = mc.createNode( 'clamp', name=mat+'_TransClamp' )
					mc.connectAttr( SpeedTreeFbx + '.enableTranslucency', transClamp + '.inputR' )
					mc.setAttr( transClamp + '.max', 0.5, 0.5, 0.5, type='float3' )
					mc.setAttr( transClamp + '.ihi', 0 )
				
			SpeedTreeAttributes.append( specPlug )
			SpeedTreeAttributes.append( transScalePlug )
			SpeedTreeAttributes.append( transColorPlug )
			
			
			#################################################
			# Displacement Mapping
			
			dispHistory = []
			dispPlug = heightSource = ''
			heightMapPlugs = mc.connectionInfo( SpeedTreeFbx + '.hm', dfs=True )
			dispEnabled = mc.getAttr( SpeedTreeFbx + '.bdisp' )
			preDispShader = dispShader = mc.connectionInfo( matSg + '.displacementShader', sfd=1 ).split( '.' )[0]
			if baseNormalMap != '':
				normalHasAlpha = stTestForAlphaMap( baseNormalMap )[2]
			
			#case of existing displacement
			dispShaderPlug = mc.connectionInfo( matSg + '.displacementShader', sfd=True )
			if dispShaderPlug != '' and dispShaderPlug != None and len( dispShaderPlug ) > 0:
					dispShader = dispShaderPlug.split( '.' )[0]
					dispHistory = mc.listHistory( dispShader )
					if SpeedTreeFbx in dispHistory:
						dispHistory.remove( SpeedTreeFbx )
						
			#create displacement nodes
			elif not hardwareMode and ( len( heightMapPlugs ) > 0 and doHeight ) or ( doNormal and normalHasAlpha ):
				if doHeight or ( doNormal and stTestForAlphaMap( baseNormalMap )[2] ):
					heightSource = mc.createNode( 'file', name = mat + '_Disp' )
					if not doHeight and doNormal:
						mc.connectAttr( SpeedTreeFbx + '.nm', heightSource + '.fileTextureName' )
						self.stSetFileNodeDefaults( heightSource )
					else:
						mc.connectAttr( SpeedTreeFbx + '.hm', heightSource + '.fileTextureName' )
						self.stSetFileNodeDefaults( heightSource, True )
						
					mc.connectAttr( SpeedTreeFbx + '.dispf', heightSource + '.filterOffset' )
					mc.setAttr( heightSource + '.preFilter', 1 )
					dispHistory.append( heightSource )
					
				if heightSource != '':
					mc.connectAttr( SpeedTreeFbx + '.dispo', heightSource + '.alphaOffset' )
					mc.connectAttr( SpeedTreeFbx + '.displacement', heightSource + '.alphaGain' )
						
					dispShader = mc.createNode( 'displacementShader', name = mat + '_DispShader' )
					mc.connectAttr( heightSource + '.outAlpha', dispShader + '.displacement' )
					dispHistory.append( dispShader )
			
			dispPlug = dispShader + '.displacement'
			
			#connect displacement
			if preDispShader == '' and dispShader != '' and dispEnabled and not hardwareMode:
				mc.connectAttr( dispPlug, matSg + '.displacementShader' )
				
			#or disconnect displacement
			elif ( preDispShader != '' and not dispEnabled ) or ( hardwareMode and len( heightMapPlugs ) > 0 ):
				
				dispHistory = []
				if preDispShader != '':
					mc.disconnectAttr( dispPlug, matSg + '.displacementShader' )
					dispHistory = mc.listHistory( dispPlug )
					
				elif len( heightMapPlugs ) > 0:
					heightSource = heightMapPlugs[0].split( '.' )[0]
					dispHistory = mc.listHistory( heightSource, f=True )
				
				if SpeedTreeFbx in dispHistory:
					dispHistory.remove( SpeedTreeFbx )
					
				if dispHistory != []:
					mc.delete( dispHistory )
					dispHistory = []
			
			
			#################################################
			# Connect Shader Attributes
			
			#generic (phong) shader
			if processType == 'generic':
				mc.setAttr( stShader + '.cosinePower', fbxShininess )
				mc.setAttr( stShader + '.diffuse', mc.getAttr( SpeedTreeFbx + '.ds' ) )
				
				if SpeedTreeAttributes[0] != '':
					mc.connectAttr( SpeedTreeAttributes[0], stShader + '.ambc' )
				if hardwareType != 'mayaHardware':
					mc.connectAttr( SpeedTreeAttributes[1], stShader + '.diffuse' )
				if SpeedTreeAttributes[2] != '':
					mc.connectAttr( SpeedTreeAttributes[2], stShader + '.cosinePower' )
					
				mc.connectAttr( SpeedTreeAttributes[3], stShader + '.translucenceDepth' )
				mc.connectAttr( SpeedTreeAttributes[4], stShader + '.translucenceFocus' )
				mc.connectAttr( SpeedTreeAttributes[5], stShader + '.color' )
				
				if SpeedTreeAttributes[6] != '':
					mc.connectAttr( SpeedTreeAttributes[6] + 'R', stShader + '.transparencyR' )
					mc.connectAttr( SpeedTreeAttributes[6] + 'G', stShader + '.transparencyG' )
					mc.connectAttr( SpeedTreeAttributes[6] + 'B', stShader + '.transparencyB' )
					#this is for the viewport display
					if doColor and colorHasAlpha and not doGamma and not doDetail:
						mc.connectAttr( baseMap + '.outTransparency', stShader + '.transparency' )
				
				if SpeedTreeAttributes[7] != '':
					mc.connectAttr( SpeedTreeAttributes[7], stShader + '.normalCamera' )
				mc.connectAttr( SpeedTreeAttributes[8], stShader + '.sc' )
				if SpeedTreeAttributes[9] != '':
					mc.connectAttr( SpeedTreeAttributes[9], stShader + '.translucence' )
					
			#mia_material
			elif processType == 'mentalRay':
				mc.setAttr( stShader + '.diffuse_roughness', 0.15 )
				mc.setAttr( stShader + '.thin_walled', 1 )
				mc.setAttr( stShader + '.refr_gloss', 0.1 )
				mc.setAttr( stShader + '.refr_gloss_samples', 2 )
				mc.setAttr( stShader + '.refr_trans_weight', 1.0 )
				mc.setAttr( stShader + '.refl_hl_only', 1 )
				mc.setAttr( stShader + '.brdf_0_degree_refl', 0.1 )
				mc.setAttr( stShader + '.brdf_90_degree_refl', 0.9 )
				mc.setAttr( stShader + '.refr_color', 0.5, 0.5, 0.5, type='float3' )
				mc.connectAttr( SpeedTreeFbx + '.backfaceCull', stShader + '.backface_cull' )
				if transClamp != '':
					mc.connectAttr( transClamp + '.outputR', stShader + '.transparency' )
				
				mc.connectAttr( SpeedTreeAttributes[1], stShader + '.diffuse_weight' )
				mc.connectAttr( SpeedTreeAttributes[2], stShader + '.refl_gloss' )
				mc.connectAttr( SpeedTreeAttributes[5], stShader + '.diffuse' )
				
				if doColor != False:
					mc.connectAttr( SpeedTreeAttributes[5], stShader + '.refr_color' )
				if SpeedTreeAttributes[6] != '':
					mc.connectAttr( SpeedTreeAttributes[6] + 'R', stShader + '.cutout_opacity' )
				if SpeedTreeAttributes[7] != '':
					mc.connectAttr( SpeedTreeAttributes[7], stShader + '.bump' )
					
				mc.connectAttr( SpeedTreeAttributes[8], stShader + '.refl_color' )
				mc.connectAttr( SpeedTreeAttributes[9], stShader + '.refr_translucency' )
				mc.connectAttr( SpeedTreeAttributes[10], stShader + '.refr_trans_color' )
				
				
			#################################################
			# Create asset container
			
			vCreateAssets = mc.optionVar( q='SpeedTreeCreateAssets' )
			if MayaVersion >= 2009 and vCreateAssets:
				
				#get dependency nodes
				stShaderHistory = mc.listHistory( stShader, pdo=True, bf=True )
				stShaderHistoryRemove = mc.listHistory( stShader, pdo=True, bf=True, il=0 )
					
				for n in stShaderHistory:
					if SpeedTreeFbx in mc.listHistory( n, f=True ):
						stShaderHistory.remove( n )
					
				if stShader in stShaderHistory:
					stShaderHistory.remove( stShader )
				
				stShaderHistory.extend( dispHistory )
						
				#create container
				SpeedTreeAsset = mc.container( name=SpeedTreeFbx[:-3] + 'Assets', addNode=stShaderHistory, force=True )
				
				#asset settings
				SpeedTreeFbxPath = mc.pluginInfo( 'SpeedTreeFBX.py', path=True, query=True )
				SpeedTreeFbxPart = SpeedTreeFbxPath.rpartition( '/' )
				SpeedTreeIconPath = SpeedTreeFbxPart[0] + '/icons/SpeedTreeAsset.xpm'
				if os.path.isfile( SpeedTreeIconPath ):
					mc.setAttr( SpeedTreeAsset + '.iconName', SpeedTreeIconPath, type='string' )
                    	
				mc.setAttr( SpeedTreeAsset + '.blackBox', 0 )
				mc.setAttr( SpeedTreeAsset + '.viewMode', 0 )
				if mc.objExists( SpeedTreeAsset + '.uiTreatment' ):
				    mc.setAttr( SpeedTreeAsset + '.uiTreatment', 1 )
				elif mc.objExists( SpeedTreeAsset + '.isAsset' ):
					mc.setAttr( SpeedTreeAsset + '.isAsset', 1 )  
			
			#re-enable hypergraph incrementing
			mc.hyperShade( inc=1 )
		
		else:
			sys.stderr.write( "SpeedTreeFBX: Failed to build shader network" )
			
		__main__.SpeedTreeShaderNetworkResults = ( stShader, processType, displayMap )
		

#SpeedTree Import Command
class BakeSpeedTreeShaderNetwork ( OpenMayaMPx.MPxCommand ):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__( self )
	
	def doIt( self, argList ):
		"""Removes this SpeedTreeFBX node, leaving behind a fixed shading network that does not require the SpeedTreeFBX plug-in."""
		
		argsLen = argList.length()
		if argsLen >= 1:
			SpeedTreeFbx = argList.asString(0)
			fbxCons = mc.listConnections( SpeedTreeFbx, s=0, d=1, c=1, p=1 )
			sj = mc.getAttr( SpeedTreeFbx + '.scriptJob' )
			shadingEngine = mc.getAttr( SpeedTreeFbx + '.shadingEngine' )
			shadingEngine = mc.connectionInfo( SpeedTreeFbx + '.shadingEngine', sfd=True ).split( '.' )[0]
			stShader = stShaderFromSg( shadingEngine )
			
			if stShader != "":
				if sj != 0:
					mc.scriptJob( kill=sj, force=True )
				
				#check for asset container
				matHistory = mc.listHistory( stShader, lv=1 )
				matHistoryRemove = mc.listHistory( stShader, lv=1, il=1 )
				for m in matHistoryRemove:
					if m in matHistory:
						matHistory.remove( m )
				
				SpeedTreeAsset = mc.container( q=True, findContainer=matHistory )
				if SpeedTreeAsset != None and SpeedTreeAsset != '':
					
					#check for ".template" file
					viewMode = 0
					arrScriptPaths = SpeedTreeCheckEnvVarPath( 'MAYA_SCRIPT_PATH', True )
					for scriptPath in arrScriptPaths:
						if os.path.exists( os.path.join( scriptPath, 'SpeedTreeFbxContainer.template' ) ):
							viewMode = 1
							break
					
					mc.setAttr( SpeedTreeAsset + '.templateName', 'SpeedTreeFbxContainer', type='string' )
					mc.setAttr( SpeedTreeAsset + '.viewName', 'BakedSpeedTreeSettings', type='string' )
					mc.setAttr( SpeedTreeAsset + '.viewMode', viewMode )
					
				i = 0
				while i + 1 < len( fbxCons ):
					s = fbxCons[i]
					d = fbxCons[i + 1]
					sType = mc.getAttr( s, type=True )
					sValue = mc.getAttr( s )
					mc.disconnectAttr( s, d )
					
					if sType == 'float3':
						sValue = sValue[0]
						mc.setAttr( d, sValue[0], sValue[1], sValue[2], type='float3' )
					elif sType == 'string':
						mc.setAttr( d, sValue, type='string' )
					else:
						if d.split( '.' )[1] == 'diffuse_weight':
							mc.setAttr( d, min( 1, sValue ) )
						else:
							mc.setAttr( d, sValue )
					
					#publish to asset
					dSplit = d.split( '.' )
					nodeContainer = mc.container( q=True, findContainer= [d.split( '.' )[0]] )
					if SpeedTreeAsset != None and SpeedTreeAsset != '' and nodeContainer == SpeedTreeAsset:
						mc.container( SpeedTreeAsset, edit=True, pb=[ d, s.split( '.' )[1] ] )
						
					i += 2
					
				selection = mc.ls( sl=True )
				if SpeedTreeAsset != None and SpeedTreeAsset != '':
					mc.select( SpeedTreeAsset )
				elif ( len( selection ) == 0 or ( len( selection ) == 1 and selection[0] == SpeedTreeFbx ) ) and stShader != '':
					mc.select( stShader )
				
				mc.delete( SpeedTreeFbx )
			
			else:
				print "SpeedTree FBX: Error locating shader"


#add importer to "File->Import" menu
class SpeedTreeFbxFileTranslator( OpenMayaMPx.MPxFileTranslator ):
	def __init__(self):
		OpenMayaMPx.MPxFileTranslator.__init__( self )
	def haveWriteMethod(self):
		return False
	def haveReadMethod(self):
		return True
	def filter(self):
		return "*.fbx"
	def defaultExtension(self):
		return "fbx"
	def canBeOpened(self):
		return False
	def writer( self, fileObject, optionString, accessMode ):
		pass
	def reader( self, fileObject, optionString, accessMode ):
		try:
			stFile = fileObject.fullName()
			mc.evalDeferred( """import maya.cmds as mc
mc.importSpeedTreeFbx( 0, '""" + stFile + """' )""" )
		
		except:
			sys.stderr.write( "Failed to read SpeedTree FBX file.\n" )
			raise


#SpeedTree Import Command
class SpeedTreeFbxImporter( OpenMayaMPx.MPxCommand ):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__( self )
	
	def stCatchTextures( self, mat, plug, SpeedTreeFbx, matShapes ):
		"""Collects data on each texture plug"""
		
		source = baseMap = baseFilename = alphaFilename = detailFilename = detailAlphaFilename = ''
		hasAlpha = hasDetailAlpha = isLayered = False
		
		if mc.objExists( mat + '.' + plug ):
			source = baseMap = mc.connectionInfo( mat + '.' + plug, sfd=1 ).split ( '.' )[0]
			
			if source != "":
				#has detail layer
				if mc.nodeType( source ) == 'layeredTexture':
					baseMap = mc.connectionInfo( source + '.inputs[1].color', sfd=1 ).split ( '.' )[0]
					detailMap = mc.connectionInfo( source + '.inputs[0].color', sfd=1 ).split ( '.' )[0]
					isLayered = True
					
					if detailMap != '':
						arrDetailAlphaTest = stTestForAlphaMap( detailMap )
						detailFilename = arrDetailAlphaTest[1]
						
						if arrDetailAlphaTest[3]:
							detailAlphaFilename = arrDetailAlphaTest[4]
							hasDetailAlpha = True
					
				#bitmap texture
				if baseMap != '':
					arrBaseAlphaTest = stTestForAlphaMap( baseMap )
					baseFilename = arrBaseAlphaTest[1]
						
					if arrBaseAlphaTest[2] and arrBaseAlphaTest[3]:
						alphaFilename = arrBaseAlphaTest[4]
						hasAlpha = True
			
		return ( source, baseFilename, alphaFilename, detailFilename, detailAlphaFilename, hasAlpha, hasDetailAlpha, isLayered )
	
	
	def stPrevFilename( mat ):
		"""finds the decremented filename"""
		
		#get increment value
		matIncr = mat[-1:]
		if matIncr.isdigit():
			matPrefix = mat[:-1]
			keepTesting = True
			while keepTesting:
				nextDigit = matPrefix[-1:]
				if nextDigit.isdigit() and nextDigit != '0':
					matIncr = nextDigit + matIncr
					matPrefix = matPrefix[:-1]
				else:
					keepTesting = False
					
			matIncr = int( matIncr )
			
			#get color filename
			colorFilename = ''
			colorCon = mc.connectionInfo( mat + '.color', sfd=True ).split( '.' )[0]
			if mc.objExists( colorCon ):
				if mc.nodeType( colorCon ) == 'layeredTexture':
					colorCon = mc.connectionInfo( colorCon + '.inputs[1].color', sfd=1 ).split( '.' )[0]
				if mc.nodeType( colorCon ) == 'file':
					colorFilename = mc.getAttr( colorCon + '.fileTextureName' )
					colorFilename = '/'.join( colorFilename.split('\\') )
			
			prevIncr = 0
			prevMat = matPrefix
			materialFound = False
			preSpeedTreeFbx = mc.ls( typ='SpeedTreeFbx' )
			while prevIncr < matIncr and not materialFound:
				if prevIncr > 0:
					prevMat = matPrefix + str( prevIncr )
				prevIncr += 1
	
	
	def doIt( self, argList ):
		"""Processes imported SpeedTree FBX textures, materials, and mesh assets"""
		
		stFile = None
		baseName = ''
		stPostNodes = []
		stPostMaterials = []
		stPostTextures = []
		stPostMeshes = []
		stSpeedTreeMaterials = []
		stAuxiliaryNodes = []
		stPreNodes = mc.ls( tr=True )
		stPreMaterials = mc.ls( mat=True )
		stPreTextures = mc.ls( tex=True )
		stPreShadingGroups = mc.ls( type='shadingEngine' )
		
		processMode = 0
		argsLen = argList.length()
		
		#process mode
		if argsLen > 1:
			processMode = argList.asBool(0)
			if processMode == 1:
				for a in range( 1, argsLen ):
					stPostNodes.append( argList.asString(a) )
			else:
				stFile = argList.asString(1)
				
		#get FBX filename if blank
		if processMode == 0 and stFile == None:
			if MayaVersion >= 2012:
				try:
					stFile = mc.fileDialog2( fileMode=1, caption="Select a SpeedTree FBX file", okc="Load", fileFilter="*.fbx", dialogStyle=2 )[0]
				except:
					stFile = None
			else:
				stFile = mc.fileDialog( mode=0, title='Select a SpeedTree FBX file', directoryMask='*.fbx' )
		
		#import file if it exists
		if stFile != '' and stFile != None:
			
			#disable hypergraph incrementing
			mc.hyperShade( inc=0 )
			
			#import FBX file
			mel.eval( 'global string $SpeedTreeFbxFile = "' + stFile + '"' )
			mel.eval( 'FBXImport -f $SpeedTreeFbxFile;' )
			
			stPostNodes = mc.ls( tr=True )
			stPostMaterials = mc.ls( mat=True )
			stPostTextures = mc.ls( tex=True )
			
			#parse out the new objects
			for obj in stPreNodes:
				stPostNodes.remove( obj )
				
			for tex in stPreTextures:
				stPostTextures.remove( tex )
				
			for mat in stPreMaterials:
				stPostMaterials.remove( mat )
			
		#start processing data
		if len( stPostNodes ) > 0:	
			skinClusterNode = cacheFileNode = cacheSwitchNode = None
			baseName = os.path.basename( stFile ).rpartition( '.' )[0]
			
			#process objs (left handed tangent space)
			for obj in stPostNodes:
				objShapeArray = mc.listRelatives( obj, c=True )
				
				if mc.nodeType( obj ) == 'joint':
					if mc.objExists( obj + '.radius' ):
						mc.setAttr( obj + '.radius', 1.0 )
						
				elif objShapeArray != None and len( objShapeArray ) > 0:
					objShape = origObjShape = objShapeArray[0]
					
					if mc.nodeType( objShape ) == 'mesh' and mc.objExists( objShape + '.tangentSpace' ):
						mc.setAttr( objShape + '.tangentSpace', 1 )
						mc.setAttr( objShape + '.normalThreshold', 180 )
						mc.setAttr( objShape + '.boundingBoxScale', 1.1, 1.1, 1.1, type='float3' )
						
						#add to lists for following steps
						stPostMeshes.append( obj )
						objSG = mc.listConnections( objShape, s=False, d=True, type='shadingEngine' )
						for sg in objSG:
							mc.listConnections( sg, s=True, d=False )
							sgShader = stShaderFromSg( sg )
							if sgShader != None and sgShader != '':
								stSpeedTreeMaterials.append( sgShader )
								if sgShader in stPostMaterials:
									stPostMaterials.remove( sgShader )
						
						if stFile != '' and stFile != None:
							try:
								#'useAsFilename' not supported before 2012
								mc.addAttr( objShape, longName='fbxFile', shortName='fbx', niceName='SpeedTreeFBX File', dt='string', uaf=1, r=1, w=1, h=0, s=1 )
							except:
								mc.addAttr( objShape, longName='fbxFile', shortName='fbx', niceName='SpeedTreeFBX File', dt='string', r=1, w=1, h=0, s=1 )
							mc.setAttr( objShape + '.fbxFile', stFile, type='string' )
						
						#ping pong point cache animation
						objHistory = mc.listHistory( obj )
						for h in range( 0, len( objHistory ) ):
							if mc.nodeType( objHistory[h] ) == 'cacheFile':
								mc.setAttr( objHistory[h] + '.oscillate', True )
								cacheFileNode = objHistory[h]
								stAuxiliaryNodes.append( cacheFileNode )
								
							if mc.nodeType( objHistory[h] ) == 'historySwitch':
								cacheSwitchNode = objHistory[h]
								
							if mc.nodeType( objHistory[h] ) == 'skinCluster':
								skinClusterNode = mc.rename( objHistory[h], obj + '_SkinCluster' )
								stAuxiliaryNodes.append( skinClusterNode )
								
								skinHistory = mc.listHistory( skinClusterNode )
								for sh in skinHistory:
									if mc.nodeType( sh ) == 'mesh':
										origObjShape = sh
									if mc.nodeType( sh ) == 'dagPose' and baseName not in sh:
										bindNode = mc.rename( sh, baseName + '_BindPose' )
										stAuxiliaryNodes.append( bindNode )
						
						#get bones + wind working
						if skinClusterNode != None and cacheFileNode != None and cacheSwitchNode != None:
							
							#create tweak node to get point cache working over bones
							tweakNode = mc.createNode( 'tweak', name= obj + '_Tweak' )
							mc.setAttr( tweakNode +'.vlist[0].vt[0]', 0, 0, 0 )
							mc.setAttr( tweakNode + '.ihi', 0 )
							stAuxiliaryNodes.append( tweakNode )
							
							mc.connectAttr( cacheSwitchNode + '.outputGeometry[0]', tweakNode + '.input[0].inputGeometry' )
							mc.connectAttr( tweakNode + '.vlist[0].vt[0]', objShape + '.tweakLocation' )
							
							cacheGroupParts = mc.connectionInfo( cacheSwitchNode + '.input[0].inputGeometry', sfd=True )
							cacheGroupPlug = cacheGroupParts.split( '.' )[0]
							skinGroupParts = mc.connectionInfo( skinClusterNode + '.input[0].inputGeometry', sfd=True ).split( '.' )[0]
							lastGroupPart = mc.connectionInfo( skinGroupParts + '.inputGeometry', sfd=True )
							cacheSwitchNodeName = mc.rename( cacheSwitchNode, obj + '_HistorySwitch' )
							stAuxiliaryNodes.append( cacheSwitchNodeName )
							
							mc.disconnectAttr( mc.connectionInfo( cacheGroupPlug + '.inputGeometry', sfd=True ), cacheGroupPlug + '.inputGeometry' )
							mc.connectAttr( lastGroupPart, cacheGroupPlug + '.inputGeometry' )
							
							mc.disconnectAttr( mc.connectionInfo( skinGroupParts + '.inputGeometry', sfd=True ), skinGroupParts + '.inputGeometry' )
							mc.connectAttr( tweakNode + '.outputGeometry[0]', skinGroupParts + '.inputGeometry' )
							
							mc.disconnectAttr( mc.connectionInfo( objShape + '.inMesh', sfd=True ), objShape + '.inMesh' )
							mc.connectAttr( skinClusterNode + '.outputGeometry[0]', objShape + '.inMesh' )
							
						#rename object sets
						objFuture = mc.listHistory( obj, f=True )
						for f in objFuture:
							if mc.nodeType( f ) == 'objectSet':
								if skinClusterNode != None and skinClusterNode in mc.listHistory( f ):
									oSet = mc.rename( f, obj + '_SkinClusterSet' )
								else:
									oSet = mc.rename( f, obj + '_HistorySwitchSet' )
									
								stAuxiliaryNodes.append( oSet )
						
						#rename groupId and groupPart nodes
						objGroupIds = mc.listConnections( objShape, type='groupId' )
						for id in objGroupIds:
							groupIdNode = mc.rename( id, obj + '_' + id[:1].capitalize() + id[1:] )
							stAuxiliaryNodes.append( groupIdNode )
							
							for h in mc.listHistory( groupIdNode, f=True ):
								if mc.nodeType( h ) == 'groupParts' and obj not in h:
									groupPartNode = mc.rename( h, obj + '_' + h[:1].capitalize() + h[1:] )
									stAuxiliaryNodes.append( groupPartNode )
			
			#add auxiliary nodes to asset
			if MayaVersion >= 2009 and len( stAuxiliaryNodes ) > 1:
				try:
					SpeedTreeAsset = mc.container( name=baseName + '_MeshAssets', addNode=stAuxiliaryNodes, force=True )
					
					SpeedTreeFbxPath = mc.pluginInfo( 'SpeedTreeFBX.py', path=True, query=True )
					SpeedTreeFbxPart = SpeedTreeFbxPath.rpartition( '/' )
					SpeedTreeIconPath = SpeedTreeFbxPart[0] + '/icons/SpeedTreeAsset.xpm'
					if os.path.isfile( SpeedTreeIconPath ):
						mc.setAttr( SpeedTreeAsset + '.iconName', SpeedTreeIconPath, type='string' )
				except:
					print "Failed to create SpeedTree mesh assets container node."
			
			
			#delete false nurbs materials
			for mat in stPostMaterials:
				matCons = mc.listConnections( mat )
				for c in matCons:
					if mc.nodeType( c ) == 'materialInfo' or mc.nodeType( c ) == 'shadingEngine':
						mc.delete( c )
				mc.delete( mat )
			
			
			#process materials
			for mat in stSpeedTreeMaterials:
				stShader = matInfo = ''
				preShaderName = mat + '_SpeedTreeFBX'
				matSg = mc.listConnections( mat, s=0, d=1, type='shadingEngine' )[0]
				matSg = mc.rename( matSg, mat + '_SG' )
				matInfoArray = mc.listConnections( matSg, type='materialInfo' )
				if matInfoArray != None and len( matInfoArray ) > 0:
					matInfo = matInfoArray[0]
					matInfo = mc.rename( matInfo, mat + '_MatInfo' )
					mc.setAttr( matInfo + '.ihi', 0 )
				
				#get objects using this mat
				mc.hyperShade( objects=mat )
				matShapes = mc.ls( sl=True )
				
				#check for color sets
				colorSets = mc.polyColorSet( q=True, acs=True )
				doCpv = ( colorSets != None and len( colorSets ) > 0 )
				
				# replace material
				shaderExists = stShaderExists( mat )
				if ( shaderExists[0] ):
					mc.delete( matInfo )
					mc.delete( matSg )
					stShader = shaderExists[1]
					preShaderName = shaderExists[1] + '_SpeedTreeFBX'
					stShaderSg = mc.connectionInfo( preShaderName + '.shadingEngine', sfd=1 ).split( '.' )[0]
					matInfo = mc.listConnections( stShaderSg, type='materialInfo' )[0]
					colorSource = mc.connectionInfo( matInfo + '.texture[0]', sfd=1 ).split( '.' )[0]
					processType = mc.getAttr( preShaderName + '.processedType' )
					
					mc.updateSpeedTreeShader( preShaderName, mat, matInfo, stShader, colorSource, processType )
					stCheckBackfaceCulling( stShader, matShapes, mc.getAttr( preShaderName + '.bfc' ) ) 
					
				#new material
				else:
					numUvSets = 3
					doBlend = bHasBlendSets = False
					
					#SpeedTree FBX variables
					processIndex = blendValid = 0
					vProcessFor = mc.optionVar( q='SpeedTreeProcessFor' )
					
					if vProcessFor in supportedRenderers:
						processIndex = supportedRenderers.index( vProcessFor ) + 1
						
					currRenderer = mc.getAttr( 'defaultRenderGlobals.currentRenderer' )
					if ( currRenderer != 'mayaSoftware' and currRenderer != 'mayaHardware' and currRenderer != 'mayaHardware2' ):
						blendValid = 1
					
					#SpeedTreeFbx node
					SpeedTreeFbx = mc.createNode( 'SpeedTreeFbx', name=preShaderName )
					mc.connectAttr( matSg + '.message', SpeedTreeFbx + '.shadingEngine' )
					mc.setAttr( SpeedTreeFbx + '.processIndex', processIndex )
					mc.setAttr( SpeedTreeFbx + '.blendValid', blendValid )
					mc.setAttr( SpeedTreeFbx + '.ihi', 2 )
					
					#connect shape nodes
					mc.SpeedTreeDagMembersChanged( SpeedTreeFbx, 0 )
					
					#walk mesh faces
					s = 0
					while s < len( matShapes ):
						matShapeFaces = matShapes[s]
						matShape = matShapes[s] = str( matShapes[s] ).partition( '.' )[0]
						uvSets = mc.polyUVSet( matShape, q=True, allUVSets=True )
						
						#check for blending
						if len( uvSets ) >= 4 and not doBlend:
							numUvSets = len( uvSets )
							bHasBlendSets = True
							
							arrMatUvComponent = mc.polyListComponentConversion( matShapeFaces, ff=True, tuv=True )
							for m in arrMatUvComponent:			
								mc.polyUVSet( m, uvSet=uvSets[3], currentUVSet=True )
								mUvs = mc.polyEditUV( m, query=True )
								
								#check detail blend data
								if len( uvSets ) > 4:
									mc.polyUVSet( m, uvSet=uvSets[4], currentUVSet=True )
									mUvsDetail = mc.polyEditUV( m, query=True )
									mUvs += mUvsDetail
									
								mUvs = list( set( mUvs ) )
								if len( mUvs ) != 1 or ( len( mUvs ) == 1 and mUvs[0] != 0.0 ):
									doBlend = True		
						s += 1
					
					#initialize variables
					baseMap = colorSource = ''
					specHasAlpha = colorHasAlpha = False
					vUseFileAmbient = mc.optionVar( q='SpeedTreeUseAmbient' )
					vBackfaceCull = mc.optionVar( q='SpeedTreeUseBfc' )
					vUseTrans = mc.optionVar( q='SpeedTreeUseTrans' )
					vUseDisplacement = mc.optionVar( q='SpeedTreeDisplacement' )
					vVertexColors = mc.optionVar( q='SpeedTreeVertexColors' )
					vGammaCorrect = mc.optionVar( q='SpeedTreeGammaCorrection' )
					vSyncGamma = mc.optionVar( q='SpeedTreeSyncGamma' )
					vGammaValue = mc.optionVar( q='SpeedTreeGammaValue' )
					vBakeShaders = mc.optionVar( q='SpeedTreeBakeShaders' )
					
					#catch textures
					arrOpac = self.stCatchTextures( mat, 'transparency', SpeedTreeFbx, matShapes )
					arrColor = self.stCatchTextures( mat, 'color', SpeedTreeFbx, matShapes )
					arrTrans = self.stCatchTextures( mat, 'incandescence', SpeedTreeFbx, matShapes )
					arrSpec = self.stCatchTextures( mat, 'specularColor', SpeedTreeFbx, matShapes )
					
					matBump2d = mc.connectionInfo( mat + '.normalCamera', sfd=1 ).split ( '.' )[0]
					if matBump2d != '' and mc.nodeType( matBump2d ) == 'bump2d':
						arrBump = self.stCatchTextures( matBump2d, 'bumpValue', SpeedTreeFbx, matShapes )
					else:
						arrBump = self.stCatchTextures( mat, 'normalCamera', SpeedTreeFbx, matShapes )
						
					#catch filename attributes
					mc.setAttr( SpeedTreeFbx + '.om', arrOpac[1], type='string' )
					mc.setAttr( SpeedTreeFbx + '.dm', arrColor[1], type='string' )
					mc.setAttr( SpeedTreeFbx + '.ddm', arrColor[3], type='string' )
					mc.setAttr( SpeedTreeFbx + '.bm', arrColor[4], type='string' )
					mc.setAttr( SpeedTreeFbx + '.tm', arrTrans[1], type='string' )
					mc.setAttr( SpeedTreeFbx + '.sm', arrSpec[1], type='string' )
					mc.setAttr( SpeedTreeFbx + '.nm', arrBump[1], type='string' )
					mc.setAttr( SpeedTreeFbx + '.dnm', arrBump[3], type='string' )
					mc.setAttr( SpeedTreeFbx + '.hm', arrBump[2], type='string' )
					
					if arrColor[5] and ( arrOpac[1] == arrColor[1] ):
						mc.setAttr( SpeedTreeFbx + '.om', arrColor[2], type='string' )
					if arrSpec[5] or ( arrTrans[1] == arrSpec[1] ):
						mc.setAttr( SpeedTreeFbx + '.tm', arrSpec[2], type='string' )
					if arrBump[5]:
						mc.setAttr( SpeedTreeFbx + '.hm', arrBump[2], type='string' )
					
					if arrColor[0] != '':
						colorSource = baseMap = arrColor[0]
						if mc.nodeType( colorSource ) == 'layeredTexture':
							baseMap = mc.connectionInfo( colorSource + '.inputs[1].color', sfd=1 ).split( '.' )[0]
						colorHasAlpha = mc.getAttr( baseMap + '.fileHasAlpha' )
						
					if arrSpec[0] != '':
						specHasAlpha = mc.getAttr( arrSpec[0] + '.fileHasAlpha' )
					
					#surface attributes
					if doBlend:
						mc.setAttr( SpeedTreeFbx + '.bib', 1 )
					else:
						mc.setAttr( SpeedTreeFbx + '.bib', lock=True )
						
					ambColor = mc.getAttr( mat + '.ambc' )
					mc.setAttr( SpeedTreeFbx + '.fbxambc', ambColor[0][0], ambColor[0][1], ambColor[0][2], type="double3" )
					mc.setAttr( SpeedTreeFbx + '.uamb', vUseFileAmbient )
					
					if arrColor[0] == '':
						dColor = mc.getAttr( mat + '.color' )
						mc.setAttr( SpeedTreeFbx + '.dc', dColor[0][0], dColor[0][1], dColor[0][2], type="double3" )
						
					if mc.objExists( mat + '.sc' ):
						if arrSpec[0] == '':
							sColor = mc.getAttr(  mat + '.sc' )
							mc.setAttr( SpeedTreeFbx + '.sc',  sColor[0][0], sColor[0][1], sColor[0][2], type="double3" )
						
						shineAmount = min( 1, max( 0.02, ( mc.getAttr( mat + '.cosinePower' ) / 100 ) ) )
						mc.setAttr( SpeedTreeFbx + '.fbxsh', shineAmount )
					
					#translucency attributes
					transColor = mc.getAttr( mat + '.incandescence' )[0]
					bColorTrans = False
					if transColor != ( 0, 0, 0 ):
						mc.setAttr( SpeedTreeFbx + '.tc',  transColor[0], transColor[1], transColor[2], type="double3" )
						bColorTrans = True
					
					if vUseTrans and ( arrTrans[1] or specHasAlpha or bColorTrans ):
						mc.setAttr( SpeedTreeFbx + '.enableTranslucency', 1 )
					
					#advanced surface attributes
					mc.setAttr( SpeedTreeFbx + '.bdisp', vUseDisplacement )
					mc.setAttr( SpeedTreeFbx + '.cpv', ( vVertexColors * doCpv ) )
					mc.setAttr( SpeedTreeFbx + '.ugc', vGammaCorrect )
					mc.setAttr( SpeedTreeFbx + '.syncg', vSyncGamma )
					if not vSyncGamma:
						mc.setAttr( SpeedTreeFbx + '.sceneg', vGammaValue )
					
					#build shader network
					mc.buildSpeedTreeShaderNetwork( SpeedTreeFbx, matInfo, mat, doCpv )
					if len( __main__.SpeedTreeShaderNetworkResults ) >= 3:
						stShader = __main__.SpeedTreeShaderNetworkResults[0]
						processType = __main__.SpeedTreeShaderNetworkResults[1]
						colorSource = __main__.SpeedTreeShaderNetworkResults[2]
					
					#actually replace shader node
					mc.assignSpeedTreeShader( SpeedTreeFbx, mat, matInfo, stShader, colorSource, processType, True )
					
					#check backface culling
					bHasAlpha = ( 1 - ( colorHasAlpha or arrOpac[1] != "" ) ) * vBackfaceCull
					bfcCheck = stCheckBackfaceCulling( stShader, matShapes, bHasAlpha )
					allowBackfaceCulling = bfcCheck[0]
					if bfcCheck[1]:
						allowBackfaceCulling = bHasAlpha
					mc.setAttr( SpeedTreeFbx + '.bfc', allowBackfaceCulling )
					
					#bake shader (optional)
					if vBakeShaders:
						mc.bakeSpeedTreeShaderNetwork( SpeedTreeFbx )
			
			#clean up
			SpeedTreeCallbacks()
			mc.hyperShade( inc=1 )
			if len( stPostNodes ) > 0:
				mc.select( clear=True )
				mc.select( stPostMeshes )


class SpeedTreeFbx( OpenMayaMPx.MPxNode ):
	aShapeNodes = om.MObjectArray()
	aFbxShadowOffset = om.MObject()
	aEnableTranslucency = om.MObject()
	aTransScalar = om.MObject()
	aTransColor = om.MObject()
	aEnableIntBlending = om.MObject()
	aIntBlendWeight = om.MObject()
	aBlendValid = om.MObject()
	aUseFileAmbient = om.MObject()
	aFbxAmbientColor = om.MObject()
	aFbxDiffuseScalar = om.MObject()
	aFbxShininess = om.MObject()
	aUseDisplacement = om.MObject()
	aDisplacementScalar = om.MObject()
	aFbxDispOffset = om.MObject()
	aSceneGamma = om.MObject()
	aRendererIndex = om.MObject()
	aProcessIndex = om.MObject()
	aMarkDirty = om.MObject()
	
	def __init__( self ):
		OpenMayaMPx.MPxNode.__init__(self)
		
	def rendererChanged( self ):
		currRenderer = mc.getAttr( 'defaultRenderGlobals.currentRenderer' )
		
		rendererIndex = 0
		if currRenderer in supportedRenderers:	
			rendererIndex = supportedRenderers.index( currRenderer )
		
		blendValid = 0
		if ( currRenderer != "mayaSoftware" and currRenderer != "mayaHardware" and currRenderer != "mayaHardware2" ):
			blendValid = 1
			
		return ( rendererIndex, blendValid )
						
		
	def compute( self, plug, dataBlock ):
		
		if plug == SpeedTreeFbx.aAmbientColor:
			#inputs
			useAmbientDataHandle = dataBlock.inputValue( SpeedTreeFbx.aUseFileAmbient )
			ambientColorDataHandle = dataBlock.inputValue( SpeedTreeFbx.aFbxAmbientColor )
			useAmbient = useAmbientDataHandle.asBool()
			ambientColor = ambientColorDataHandle.asFloat3()
			outAmbient = ( ( useAmbient * ambientColor[0] ), ( useAmbient * ambientColor[1] ), ( useAmbient * ambientColor[2] ) )
			
			#output
			outAmbientHandle = dataBlock.outputValue( SpeedTreeFbx.aAmbientColor )
			outAmbientHandle.set3Float( outAmbient[0], outAmbient[1], outAmbient[2] )
			outAmbientHandle.setClean()
			
		if plug == SpeedTreeFbx.aDiffuseScalar:
			#inputs
			diffuseScalarDataHandle = dataBlock.inputValue( SpeedTreeFbx.aFbxDiffuseScalar )
			fbxDiffuse = diffuseScalarDataHandle.asFloat()
			transStateDataHandle = dataBlock.inputValue( SpeedTreeFbx.aEnableTranslucency )
			transState = transStateDataHandle.asBool()
			
			thisNode = self.thisMObject()
			depNode = om.MFnDependencyNode( thisNode )
			stShader = depNode.name()
			diffuseMapPlug = depNode.findPlug( 'diffuseMap' )
			scalarPlug = depNode.findPlug( 'diffuseScalar' )
			scalarMPlugArray = om.MPlugArray()
			diffuseMPlugArray = om.MPlugArray()
			
			#mental ray with (non-textured) translucency
			if transState == True and not diffuseMapPlug.isConnected() and scalarPlug.isConnected():
				scalarPlug.connectedTo( scalarMPlugArray, False, True )
				if scalarMPlugArray.length() > 0:
					matNode = om.MFnDependencyNode( scalarMPlugArray[0].node() )
					if matNode.typeName() == 'mia_material':
						shaderName = matNode.name()
						refrColor = mc.getAttr( shaderName + '.refr_color' )[0]
						diffuseRecipricol = ( refrColor[0] + refrColor[1] + refrColor[2] ) / 3
						if diffuseRecipricol > 0:
							fbxDiffuse = fbxDiffuse / diffuseRecipricol
			
			#mental ray with textured translucency	
			elif transState == True and scalarPlug.isConnected() == True:
				scalarPlug.connectedTo( scalarMPlugArray, False, True )
				if scalarMPlugArray.length() > 0:
					matNode = om.MFnDependencyNode( scalarMPlugArray[0].node() )
					if matNode.typeName() == 'mia_material':
						fbxDiffuse = fbxDiffuse * 1.5
						
			#output
			diffuseHandle = dataBlock.outputValue( SpeedTreeFbx.aDiffuseScalar )
			diffuseHandle.setFloat( fbxDiffuse )
			diffuseHandle.setClean()
			
		if plug == SpeedTreeFbx.aShininess:
			#inputs
			shininessDataHandle = dataBlock.inputValue( SpeedTreeFbx.aFbxShininess )
			fbxShininess = shininessDataHandle.asFloat()
			
			thisNode = self.thisMObject()
			depNode = om.MFnDependencyNode( thisNode )
			shininessPlug = depNode.findPlug( 'shininess' )
			shininessMPlugArray = om.MPlugArray()
			
			if shininessPlug.isConnected():
				shininessPlug.connectedTo( shininessMPlugArray, False, True )
				if shininessMPlugArray.length() >= 1:
					matNode = om.MFnDependencyNode( shininessMPlugArray[0].node() )
					if matNode.typeName() == 'phong' or matNode.typeName() == 'kPhong':
						fbxShininess *= 100
						
			#output
			shininessHandle = dataBlock.outputValue( SpeedTreeFbx.aShininess )
			shininessHandle.setFloat( fbxShininess )
			shininessHandle.setClean()
			
		if plug == SpeedTreeFbx.aTranslucency:
			#inputs
			enableTransDataHandle = dataBlock.inputValue( SpeedTreeFbx.aEnableTranslucency )
			transScalarDataHandle = dataBlock.inputValue( SpeedTreeFbx.aTransScalar )
			transColorDataHandle = dataBlock.inputValue( SpeedTreeFbx.aTransColor )
			enableTrans = enableTransDataHandle.asBool()
			transScalar = transScalarDataHandle.asFloat()
			transColor = transColorDataHandle.asFloat3()
			transMax = enableTrans * transScalar
			
			outTrans = ( ( transMax * transColor[0] ), ( transMax * transColor[1] ), ( transMax * transColor[2] ) )
			
			thisNode = self.thisMObject()
			depNode = om.MFnDependencyNode( thisNode )
			transPlug = depNode.findPlug( 'diffuseScalar' )
			transMPlugArray = om.MPlugArray()
			
			if transPlug.isConnected():
				transPlug.connectedTo( transMPlugArray, False, True )
				
				if transMPlugArray.length() >= 1:
					matNode = om.MFnDependencyNode( transMPlugArray[0].node() )
					if matNode.typeName() == 'phong' or matNode.typeName() == 'kPhong':
						rgbToLum = [0.299, 0.587, 0.11]
						transLum = 0
						for i in range (0, 2):
							transLum += outTrans[i] * rgbToLum[i]
							
						outTrans = ( transLum, transLum, transLum )
			
			#output
			outTransHandle = dataBlock.outputValue( SpeedTreeFbx.aTranslucency )
			outTransHandle.set3Float( outTrans[0], outTrans[1], outTrans[2] )
			outTransHandle.setClean()
			
		if plug == SpeedTreeFbx.aShadowOffset:
			#input
			shadowOffsetDataHandle = dataBlock.inputValue( SpeedTreeFbx.aFbxShadowOffset )
			maxShadow = 0.18
			shadowOffset = shadowOffsetDataHandle.asFloat()
			shadowOffset = shadowOffset * maxShadow
			
			#output
			outShadowOffsetHandle = dataBlock.outputValue( SpeedTreeFbx.aShadowOffset )
			outShadowOffsetHandle.setFloat( shadowOffset )
			outShadowOffsetHandle.setClean()
			
		if plug == SpeedTreeFbx.aBlendWeight:
			#input
			intBlendHandle = dataBlock.inputValue( SpeedTreeFbx.aEnableIntBlending )
			intBlendWeightHandle = dataBlock.inputValue( SpeedTreeFbx.aIntBlendWeight )	
			blendValidHandle = dataBlock.inputValue( SpeedTreeFbx.aBlendValid )
			enableIntBlending = intBlendHandle.asBool()
			intBlendWeight = intBlendWeightHandle.asFloat()
			blendValid = blendValidHandle.asInt()
			
			blendValue = (blendValid * enableIntBlending * intBlendWeight )
			
			#output
			blendWeightHandle = dataBlock.outputValue( SpeedTreeFbx.aBlendWeight )
			blendWeightHandle.setFloat( blendValue )
			blendWeightHandle.setClean()
			
		if plug == SpeedTreeFbx.aOutDisplacement:
			#input
			useDispDataHandle = dataBlock.inputValue( SpeedTreeFbx.aUseDisplacement )
			dispScalarDataHandle = dataBlock.inputValue( SpeedTreeFbx.aDisplacementScalar )
			useDisp = useDispDataHandle.asBool()
			dispScalar = dispScalarDataHandle.asFloat()
			
			finalDisplacement = useDisp * dispScalar
			
			#output
			outDispHandle = dataBlock.outputValue( SpeedTreeFbx.aOutDisplacement )
			outDispHandle.setFloat( finalDisplacement )
			outDispHandle.setClean()
			
		if plug == SpeedTreeFbx.aDisplacementOffset:
			#input
			useDispDataHandle = dataBlock.inputValue( SpeedTreeFbx.aUseDisplacement )
			dispScalarDataHandle = dataBlock.inputValue( SpeedTreeFbx.aDisplacementScalar )
			dispOffsetDataHandle = dataBlock.inputValue( SpeedTreeFbx.aFbxDispOffset )
			useDisp = useDispDataHandle.asBool()
			dispScalar = dispScalarDataHandle.asFloat()
			dispOffset = dispOffsetDataHandle.asFloat()
			
			if dispOffset != 0:
				finalDispOffset = useDisp * -( dispScalar / ( 1.0 / -dispOffset ) )
			else:
				finalDispOffset = 0
			
			#output
			outDispOffsetHandle = dataBlock.outputValue( SpeedTreeFbx.aDisplacementOffset )
			outDispOffsetHandle.setFloat( finalDispOffset )
			outDispOffsetHandle.setClean()
			
		if plug == SpeedTreeFbx.aGammaCorrection:
			#inputs
			sceneGammaDataHandle = dataBlock.inputValue( SpeedTreeFbx.aSceneGamma )
			sceneGamma = sceneGammaDataHandle.asFloat()
			outGamma = 1.0
			
			thisNode = self.thisMObject()
			depNode = om.MFnDependencyNode( thisNode )
			sceneGammaPlug = depNode.findPlug( 'sceneGamma' )
			sceneGammaMPlugArray = om.MPlugArray()
			
			if sceneGammaPlug.isConnected():
				sceneGammaPlug.connectedTo( sceneGammaMPlugArray, True, False )
				if sceneGammaMPlugArray.length() == 1:
					if sceneGammaMPlugArray[0].name() != 'miDefaultFramebuffer.gamma' and sceneGamma > 0.0:
						#skip if mental ray framebuffer is in use
						outGamma = 1 / sceneGamma
				
			elif sceneGamma > 0.0:
				outGamma = 1 / sceneGamma
				
			#output
			outGammaHandle = dataBlock.outputValue( SpeedTreeFbx.aGammaCorrection )
			outGammaHandle.set3Float( outGamma, outGamma, outGamma )
			outGammaHandle.setClean()
			
		if plug == SpeedTreeFbx.aRendererIndex:
			#input
			dirtyDataHandle = dataBlock.inputValue( SpeedTreeFbx.aMarkDirty )
			rendererIndex = self.rendererChanged()
			
			#outputs
			rendererIndexHandle = dataBlock.outputValue( SpeedTreeFbx.aRendererIndex )
			rendererIndexHandle.setInt( rendererIndex[0] )
			rendererIndexHandle.setClean()


#initializer
def nodeSpeedTreeFbxInit():
	
	#optionVar defaults
	if not mc.optionVar( exists='SpeedTreeProcessFor' ):
		mc.optionVar( sv=( 'SpeedTreeProcessFor', 'currentRenderer' ) )
	if not mc.optionVar( exists='SpeedTreeAutoUpdate' ):
		mc.optionVar( iv=( 'SpeedTreeAutoUpdate', 1 ) )
	if not mc.optionVar( exists='SpeedTreeCreateAssets' ):
		mc.optionVar( iv=( 'SpeedTreeCreateAssets', 1 ) )
	if not mc.optionVar( exists='SpeedTreeUseBfc' ):
		mc.optionVar( iv=( 'SpeedTreeUseBfc', 1 ) )
	if not mc.optionVar( exists='SpeedTreeUseTrans' ):
		mc.optionVar( iv=( 'SpeedTreeUseTrans', 1 ) )
	if not mc.optionVar( exists='SpeedTreeGammaValue' ):
		mc.optionVar( fv=( 'SpeedTreeGammaValue', 1.0 ) )
	
	#optionVar values
	vProcessFor = mc.optionVar( q='SpeedTreeProcessFor' )
	vUseAmbient = mc.optionVar( q='SpeedTreeUseAmbient' )
	vUseDisplacement = mc.optionVar( q='SpeedTreeDisplacement' )
	vBackfaceCull = mc.optionVar( q='SpeedTreeUseBfc' )
	vVertexColors = mc.optionVar( q='SpeedTreeVertexColors' )
	
	#optionVar dependencies
	processIndex = 1
	if vProcessFor in supportedRenderers:
		processIndex = supportedRenderers.index( vProcessFor ) + 1
	
	#input attributes	
	nAttr = om.MFnNumericAttribute()
	nMAttr = om.MFnMatrixAttribute()
	nEAttr = om.MFnEnumAttribute()
	nTAttr = om.MFnTypedAttribute()
	nGAttr = om.MFnGenericAttribute()
	cAttr = om.MFnCompoundAttribute()
	stringData = om.MFnStringData().create("")
	
	SpeedTreeFbx.aDiffuseMap = nTAttr.create( "diffuseMap", "dm", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aNormalMap = nTAttr.create( "normalMap", "nm", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aSpecMap = nTAttr.create( "specMap", "sm", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aDetailMap = nTAttr.create( "detailMap", "ddm", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aDetailNormalMap = nTAttr.create( "detailNormalMap", "dnm", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aOpacityMap = nTAttr.create( "opacityMap", "om", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aTransMap = nTAttr.create( "translucencyMap", "tm", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aBlendMap = nTAttr.create( "detailBlendMap", "bm", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aHeightMap = nTAttr.create( "heightMap", "hm", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeFbx.aUseFileAmbient = nAttr.create( "useFileAmbient", "uamb", om.MFnNumericData.kBoolean, vUseAmbient )
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aFbxAmbientColor = nAttr.createColor( "fbxAmbientColor", "fbxambc" )
	nAttr.setStorable(1)
	nAttr.setUsedAsColor(1)
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aAmbientColor = nAttr.createColor( "ambientColor", "ambc" )
	nAttr.setKeyable(0)
	nAttr.setStorable(0)
	nAttr.setUsedAsColor(1)
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	
	SpeedTreeFbx.aDiffuseColor = nAttr.createColor( "diffuseColor", "dc" )
	nAttr.setDefault( 1.0, 1.0, 1.0 )
	nAttr.setKeyable(1)
	nAttr.setStorable(1)
	nAttr.setUsedAsColor(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	
	SpeedTreeFbx.aFbxDiffuseScalar = nAttr.create( "fbxDiffuseScalar", "fbxds", om.MFnNumericData.kFloat )
	nAttr.setKeyable(1)
	nAttr.setDefault(1.0)
	nAttr.setMin(0.0)
	nAttr.setSoftMax(2.0)
	nAttr.setMax(5.0)
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	
	SpeedTreeFbx.aDiffuseScalar = nAttr.create( "diffuseScalar", "ds", om.MFnNumericData.kFloat )
	nAttr.setMin(0.0)
	nAttr.setSoftMax(2.0)
	nAttr.setMax(5.0)
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	
	SpeedTreeFbx.aSpecularColor = nAttr.createColor( "specularColor", "sc" )
	nAttr.setDefault( 1.0, 1.0, 1.0 )
	nAttr.setKeyable(1)
	nAttr.setStorable(1)
	nAttr.setUsedAsColor(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	
	SpeedTreeFbx.aFbxShininess = nAttr.create( "fbxShininess", "fbxsh", om.MFnNumericData.kFloat )
	nAttr.setDefault(0.1)
	nAttr.setMin(0.02)
	nAttr.setMax(1.0)
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aShininess = nAttr.create( "shininess", "sh", om.MFnNumericData.kFloat )
	nAttr.setKeyable(0)
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	
	SpeedTreeFbx.aAlphaScalar = nAttr.create( "alphaScalar", "as", om.MFnNumericData.kFloat )
	nAttr.setDefault(1.0)
	nAttr.setMin(0.0)
	nAttr.setSoftMax(2.0)
	nAttr.setMax(5.0)
	nAttr.setChannelBox(1)
	nAttr.setConnectable(1)
	
	SpeedTreeFbx.aBackfaceCull = nAttr.create( "backfaceCull", "bfc", om.MFnNumericData.kBoolean )
	nAttr.setStorable(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	
	SpeedTreeFbx.aEnableTranslucency = nAttr.create( "enableTranslucency", "bt", om.MFnNumericData.kBoolean )
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setChannelBox(1)
	nAttr.setConnectable(0)

	SpeedTreeFbx.aTransScalar = nAttr.create( "translucencyScalar", "ts", om.MFnNumericData.kFloat )
	nAttr.setDefault(1.0)
	nAttr.setMin(0.0)
	nAttr.setSoftMax(1.5)
	nAttr.setMax(5.0)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	nAttr.setChannelBox(1)
	
	SpeedTreeFbx.aTransColor = nAttr.createColor( "translucencyColor", "tc" )
	nAttr.setDefault( 0.55, 0.7, 0.53 )
	nAttr.setStorable(1)
	nAttr.setUsedAsColor(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aTranslucency = nAttr.createColor( "translucency", "trans" )
	nAttr.setDefault( 1.0, 1.0, 1.0 )
	nAttr.setStorable(1)
	nAttr.setUsedAsColor(1)
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	nAttr.setHidden(1)
	
	SpeedTreeFbx.aFbxShadowOffset = nAttr.create( "fbxShadowOffset", "iso", om.MFnNumericData.kFloat )
	nAttr.setDefault(0.5)
	nAttr.setMin(0.0)
	nAttr.setSoftMax(1.0)
	nAttr.setMax(3.0)
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aShadowOffset = nAttr.create( "shadowOffset", "so", om.MFnNumericData.kFloat )
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	nAttr.setHidden(1)
	
	SpeedTreeFbx.aViewDependency = nAttr.create( "viewDependency", "vd", om.MFnNumericData.kFloat )
	nAttr.setDefault(0.5)
	nAttr.setMin(0.0)
	nAttr.setMax(1.0)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setConnectable(1)
	
	
	SpeedTreeFbx.aEnableIntBlending = nAttr.create( "enableIntersectionBlending", "bib", om.MFnNumericData.kBoolean )
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aIntBlendWeight = nAttr.create( "intersectionBlendWeight", "ibw", om.MFnNumericData.kFloat )
	nAttr.setDefault(2.0)
	nAttr.setMin(0.0)
	nAttr.setSoftMax(5.0)
	nAttr.setMax(99.9)
	nAttr.setStorable(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aBlendWeight = nAttr.create( "blendWeight", "bw", om.MFnNumericData.kFloat )
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	nAttr.setConnectable(1)
	
	SpeedTreeFbx.aBlendValid = nAttr.create( "blendValid", "bv", om.MFnNumericData.kInt )
	nAttr.setStorable(1)
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aUseDisplacement = nAttr.create( "useDisplacement", "bdisp", om.MFnNumericData.kBoolean, vUseDisplacement )
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aDisplacementScalar = nAttr.create( "displacementScalar", "disps", om.MFnNumericData.kFloat )
	nAttr.setDefault(0.5)
	nAttr.setSoftMin(0.0)
	nAttr.setMin(-100.0)
	nAttr.setSoftMax(2.0)
	nAttr.setMax(100.0)
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aOutDisplacement = nAttr.create( "displacement", "disp", om.MFnNumericData.kFloat )
	nAttr.setKeyable(0)
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	
	SpeedTreeFbx.aFbxDispOffset = nAttr.create( "fbxDisplacementOffset", "fbxdispo", om.MFnNumericData.kFloat )
	nAttr.setDefault(-0.5)
	nAttr.setMin(-1.0)
	nAttr.setMax(1.0)
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	
	SpeedTreeFbx.aDisplacementOffset = nAttr.create( "displacementOffset", "dispo", om.MFnNumericData.kFloat )
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	
	SpeedTreeFbx.aDisplacementFilter = nAttr.create( "displacementFilter", "dispf", om.MFnNumericData.kFloat )
	nAttr.setDefault(0.1)
	nAttr.setMin(0.0)
	nAttr.setMax(1.0)
	
	SpeedTreeFbx.aVertexColors = nAttr.create( "useVertexColors", "cpv", om.MFnNumericData.kBoolean, vVertexColors )
	nAttr.setStorable(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setConnectable(1)
	
	SpeedTreeFbx.aUseGammaCorrection = nAttr.create( "useGammaCorrection", "ugc", om.MFnNumericData.kBoolean )
	nAttr.setStorable(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setConnectable(1)
	
	SpeedTreeFbx.aSyncGamma = nAttr.create( "syncGamma", "syncg", om.MFnNumericData.kBoolean )
	nAttr.setStorable(1)
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	
	SpeedTreeFbx.aSceneGamma = nAttr.create( "sceneGamma", "sceneg", om.MFnNumericData.kFloat )
	nAttr.setDefault(1.0)
	nAttr.setMin(0.1)
	nAttr.setSoftMax(2.5)
	nAttr.setMax(25.0)
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setConnectable(1)
	
	SpeedTreeFbx.aGammaCorrection = nAttr.createColor( "gammaCorrection", "gc" )
	nAttr.setStorable(1)
	nAttr.setUsedAsColor(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setConnectable(1)
	nAttr.setHidden(1)
	
	SpeedTreeFbx.aShapeNodes = nTAttr.create( "shapeNodes", "sn", om.MFnMeshData.kMesh )
	nTAttr.setReadable(0)
	nTAttr.setWritable(1)
	nTAttr.setHidden(1)
	nTAttr.setArray(1)
	
	SpeedTreeFbx.aShadingEngine = nTAttr.create( "shadingEngine", "se", om.MFnData.kString )
	nTAttr.setStorable(1)
	nTAttr.setReadable(0)
	nTAttr.setWritable(1)
	nTAttr.setHidden(1)
	
	SpeedTreeFbx.aRendererIndex = nAttr.create( "rendererIndex", "ri", om.MFnNumericData.kInt, 0 )
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	nAttr.setHidden(1)

	SpeedTreeFbx.aProcessIndex = nAttr.create( "processIndex", "pri", om.MFnNumericData.kInt, processIndex )
	nAttr.setStorable(1)
	nAttr.setReadable(1)
	nAttr.setWritable(1)
	nAttr.setConnectable(0)
	nAttr.setHidden(1)
	
	stringData = om.MFnStringData().create( "generic" )
	SpeedTreeFbx.aProcessedType = nTAttr.create( "processedType", "pt", om.MFnData.kString, stringData )
	nTAttr.setStorable(1)
	nTAttr.setConnectable(0)
	nTAttr.setHidden(1)
	
	SpeedTreeFbx.aScriptJob = nAttr.create( "scriptJob", "sj", om.MFnNumericData.kInt, 0 )
	nAttr.setReadable(1)
	nAttr.setWritable(0)
	nAttr.setConnectable(0)
	nAttr.setHidden(1)
	
	SpeedTreeFbx.aMarkDirty = nAttr.create( "markDirty", "dirty", om.MFnNumericData.kInt )
	nAttr.setReadable(0)
	nAttr.setWritable(1)
	nAttr.setHidden(1)
	
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aDiffuseMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aNormalMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aSpecMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aDetailMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aDetailNormalMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aOpacityMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aTransMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aBlendMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aHeightMap )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aUseFileAmbient )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aFbxAmbientColor )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aAmbientColor )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aDiffuseColor )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aFbxDiffuseScalar )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aDiffuseScalar )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aSpecularColor )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aFbxShininess )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aShininess )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aAlphaScalar )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aBackfaceCull )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aEnableTranslucency )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aTransScalar )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aTransColor )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aTranslucency )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aFbxShadowOffset )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aShadowOffset )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aViewDependency )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aEnableIntBlending) 
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aIntBlendWeight )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aBlendWeight )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aBlendValid )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aUseDisplacement )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aDisplacementScalar )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aOutDisplacement )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aFbxDispOffset )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aDisplacementOffset )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aDisplacementFilter )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aVertexColors )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aUseGammaCorrection )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aSyncGamma )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aSceneGamma )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aGammaCorrection )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aShapeNodes )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aShadingEngine )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aRendererIndex )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aProcessIndex )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aProcessedType )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aScriptJob )
	SpeedTreeFbx.addAttribute( SpeedTreeFbx.aMarkDirty )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aUseFileAmbient, SpeedTreeFbx.aAmbientColor )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aFbxAmbientColor, SpeedTreeFbx.aAmbientColor )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aFbxShininess, SpeedTreeFbx.aShininess )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aFbxDiffuseScalar, SpeedTreeFbx.aDiffuseScalar )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aEnableTranslucency, SpeedTreeFbx.aDiffuseScalar )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aEnableTranslucency, SpeedTreeFbx.aTranslucency )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aTransScalar, SpeedTreeFbx.aTranslucency )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aTransColor, SpeedTreeFbx.aTranslucency )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aFbxShadowOffset, SpeedTreeFbx.aShadowOffset )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aEnableIntBlending, SpeedTreeFbx.aBlendWeight )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aIntBlendWeight, SpeedTreeFbx.aBlendWeight )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aBlendValid, SpeedTreeFbx.aBlendWeight )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aUseDisplacement, SpeedTreeFbx.aOutDisplacement )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aDisplacementScalar, SpeedTreeFbx.aOutDisplacement )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aUseDisplacement, SpeedTreeFbx.aDisplacementOffset )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aDisplacementScalar, SpeedTreeFbx.aDisplacementOffset )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aFbxDispOffset, SpeedTreeFbx.aDisplacementOffset )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aSyncGamma, SpeedTreeFbx.aSceneGamma )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aSceneGamma, SpeedTreeFbx.aGammaCorrection )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aShadingEngine, SpeedTreeFbx.aShapeNodes )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aMarkDirty, SpeedTreeFbx.aBlendValid )
	SpeedTreeFbx.attributeAffects( SpeedTreeFbx.aMarkDirty, SpeedTreeFbx.aRendererIndex )
	

#creators
def nodeSpeedTreeFbxCreator():
	return OpenMayaMPx.asMPxPtr( SpeedTreeFbx() )

def cmdSpeedTreeFbxImporter():
	return OpenMayaMPx.asMPxPtr( SpeedTreeFbxImporter() )

def translatorSpeedTreeFbxCreator():
    return OpenMayaMPx.asMPxPtr( SpeedTreeFbxFileTranslator() )
	
def cmdSpeedTreeDagMembersChanged():
	return OpenMayaMPx.asMPxPtr( stDagMembersChanged() )
	
def cmdSpeedTreeUpdateShader():
	return OpenMayaMPx.asMPxPtr( UpdateSpeedTreeShader() )

def cmdSpeedTreeAssignShader():
	return OpenMayaMPx.asMPxPtr( AssignSpeedTreeShader() )

def cmdSpeedTreeBuildShader():
	return OpenMayaMPx.asMPxPtr( BuildSpeedTreeShaderNetwork() )
	
def cmdSpeedTreeBakeShader():
	return OpenMayaMPx.asMPxPtr( BakeSpeedTreeShaderNetwork() )


def SpeedTreeCheckEnvVarPath( envVar, setVar=False, evalMel=None, melPath='' ):
	""""Determines if SpeedTree paths are included for an environment variable"""
	
	try:
		strEnvVarPaths = ''
		arrEnvVarPaths = []
		delimiter = ';'
		if sys.platform == 'darwin' or sys.platform == 'linux2': #Mac OSX, Linux
			delimiter = ':'
			
		SpeedTreeFbxPath = mc.pluginInfo( 'SpeedTreeFBX.py', path=True, query=True )
		SpeedTreeFbxPath = SpeedTreeFbxPath.rpartition( '/' )[0]
		if envVar.upper() == 'XBMLANGPATH':
			SpeedTreeFbxPath += '/icons'
		elif envVar.upper() == 'MAYA_SCRIPT_PATH':
			SpeedTreeFbxPath += '/templates'
		
		#ENV VAR option
		if evalMel == None:
			strEnvVarPaths = os.environ[ envVar.upper() ]
			arrEnvVarPaths = strEnvVarPaths.split( delimiter )
			strEnvVarPaths += delimiter + SpeedTreeFbxPath
			
			if setVar and SpeedTreeFbxPath not in arrEnvVarPaths:
				os.environ[ envVar.upper() ] = strEnvVarPaths
			
			return arrEnvVarPaths
		
		#MEL search path option (for asset templates)
		else:
			arrEnvVarPaths = mel.eval( evalMel )
			for p in arrEnvVarPaths:
				strEnvVarPaths += delimiter + p
			
			strEnvVarPaths = strEnvVarPaths[1:]
			strEnvVarPaths += delimiter + SpeedTreeFbxPath + '/' + melPath + '/'
			
			return [arrEnvVarPaths, strEnvVarPaths]
			
	except:
		raise
		return []


# Initialize the script plug-in
def initializePlugin( mobject ):
	mplugin = OpenMayaMPx.MFnPlugin( mobject )

    # register nodes
	mplugin.registerNode( kSpeedTreeFbxNodeName, kSpeedTreeFbxNodeId, nodeSpeedTreeFbxCreator, nodeSpeedTreeFbxInit, OpenMayaMPx.MPxNode.kDependNode, kSpeedTreeFbxNodeClassify )
        
	#register commands
	mplugin.registerCommand( kSpeedTreeDagChangedName, cmdSpeedTreeDagMembersChanged )
	mplugin.registerCommand( kSpeedTreeUpdateShaderName, cmdSpeedTreeUpdateShader )
	mplugin.registerCommand( kSpeedTreeAssignShaderName, cmdSpeedTreeAssignShader )
	mplugin.registerCommand( kSpeedTreeBuildShaderName, cmdSpeedTreeBuildShader )
	mplugin.registerCommand( kSpeedTreeBakeShaderName, cmdSpeedTreeBakeShader )
	mplugin.registerCommand( kSpeedTreeFbxImporterName, cmdSpeedTreeFbxImporter )
	mel.eval( '''global proc ImportSpeedTreeFbx() { 
	python( "mc.importSpeedTreeFbx()" );
	}''' )
	
	#register plug-in paths
	SpeedTreeFbxPath = mc.pluginInfo( 'SpeedTreeFBX.py', path=True, query=True )
	SpeedTreeFbxPath = SpeedTreeFbxPath.rpartition( '/' )[0]
	arrPluginPaths = SpeedTreeCheckEnvVarPath( 'MAYA_PLUG_IN_PATH' )
	arrScriptPaths = SpeedTreeCheckEnvVarPath( 'MAYA_SCRIPT_PATH', True )
	arrIconPaths = SpeedTreeCheckEnvVarPath( 'XBMLANGPATH', True )
	
	#asset template paths
	assetTemplatePaths = SpeedTreeCheckEnvVarPath( '', True, 'containerTemplate -query -searchPath', 'templates' )
	if ( SpeedTreeFbxPath + '/templates/' ) not in assetTemplatePaths[0]:
		mel.eval( 'workspace -fr "templates" "' + assetTemplatePaths[1] + '"' )
	
	#add SpeedTreeFbx.py to Maya.env
	mayaEnvLoc = ''
	bFoundMayaEnv = False
	bPathLoaded = True
	if SpeedTreeFbxPath not in arrPluginPaths:
		SpeedTreeCheckEnvVarPath( 'MAYA_PLUG_IN_PATH', True )
		mayaEnvLoc = os.path.join( os.environ['MAYA_APP_DIR'], 'Maya.env' )
		bPathLoaded = False
		
		for p in arrPluginPaths:
			if os.environ['MAYA_APP_DIR'] in p:
				mayaEnvLoc = p.rpartition( '/' )[0]
				mayaEnvLoc = os.path.join( mayaEnvLoc, 'Maya.env' )
				if os.path.isfile( mayaEnvLoc ):
					bFoundMayaEnv = True
					break	
		
		if bFoundMayaEnv:
			try :
				if os.path.isfile( mayaEnvLoc ):
					linePrefix = ''
					envSize = os.path.getsize( mayaEnvLoc )
					if str( envSize ).partition('L')[0] != "0":
						linePrefix = '\r'
					envFile = open( mayaEnvLoc, 'a' )
					envFile.write( linePrefix + 'MAYA_PLUG_IN_PATH = ' + SpeedTreeFbxPath )
					envFile.close()
					print( '"SpeedTreeFBX.py" added to Plug-In Manager' )
				else:
					print( 'Error adding SpeedTreeFBX to Plug-In Manager' )
			except :
				print( 'Unable to open Maya.env file %s' % mayaEnvLoc )
	
	#FBX Importer must first be loaded
	mel.eval( 'if ( `exists FBXImport` == 0 ) loadPlugin fbxmaya;' )
	
	#importer doesn't work in 2011
	if MayaVersion < 2011 or MayaVersion >= 2012:
		#check for file translator template
		translatorOptions = 'FBXShowUIOptionsImport'
		arrScriptPaths = SpeedTreeCheckEnvVarPath( 'MAYA_SCRIPT_PATH' )
		
		for scriptPath in arrScriptPaths:
			if os.path.exists( os.path.join( scriptPath, 'SpeedTreeFbxTranslatorOptions.mel' ) ):
				translatorOptions = 'SpeedTreeFbxTranslatorOptions'
		
		#register file translator
		mplugin.registerFileTranslator( kSpeedTreeFbxTranslatorName, None, translatorSpeedTreeFbxCreator, translatorOptions )
				
	print( 'plug-in "SpeedTreeFBX.py" loaded' )
	alreadyLoaded = mc.pluginInfo( SpeedTreeFbxPath + '/SpeedTreeForest.py', query=True, loaded=True)
	if not alreadyLoaded and not bPathLoaded:
		try:
			mc.loadPlugin( 'SpeedTreeForest.py', quiet=True)
		except:
			print( 'SpeedTreeForest plug-in not found.' )
	

# Uninitialize the script plug-in
def uninitializePlugin( mobject ):
	mplugin = OpenMayaMPx.MFnPlugin( mobject )
	
	#deregister nodes
	mplugin.deregisterNode( kSpeedTreeFbxNodeId )
		
	#deregister commands
	mplugin.deregisterCommand( kSpeedTreeFbxImporterName )
	mplugin.deregisterCommand( kSpeedTreeDagChangedName )
	mplugin.deregisterCommand( kSpeedTreeUpdateShaderName )
	mplugin.deregisterCommand( kSpeedTreeAssignShaderName )
	mplugin.deregisterCommand( kSpeedTreeBuildShaderName )
	mplugin.deregisterCommand( kSpeedTreeBakeShaderName )
	
	#deregister file translator
	if MayaVersion < 2011 or MayaVersion >= 2012:
		mplugin.deregisterFileTranslator( kSpeedTreeFbxTranslatorName )


#instantiate callbacks
SpeedTreeCallbacks()
