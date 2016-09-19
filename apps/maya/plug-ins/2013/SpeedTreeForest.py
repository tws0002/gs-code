##############################################################################
## SpeedTree Forest Plug-In For Maya #########################################
#
#        - Loads SpeedTree Forest files into Maya
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
import math, sys, os, shutil, re, datetime, getpass

#plug-in variables
kSpeedTreeForestNodeId = om.MTypeId( 0x44442 )
kSpeedTreeForestNodeName = "SpeedTreeForest"
kSpeedTreeForestNodeClassify = "SpeedTreeForest"
kSpeedTreeForestImporterName = "importSpeedTreeForest"
kSpeedTreeAssignForestEntryName = "assignSpeedTreeForestEntry"
kSpeedTreeForestTranslatorName = "SpeedTree Forest"
MayaVersion = mel.eval( 'getApplicationVersionAsFloat' )


#Assign SpeedTree Shader
class AssignSpeedTreeForestEntry( OpenMayaMPx.MPxCommand ):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__( self )
	
	def doIt( self, argList ):
		"""Creates forest instances from a scene object."""
		
		argsLen = argList.length()
		if argsLen >= 4:
			SpeedTreeForest = argList.asString(0)
			partCloudShape = argList.asString(1)
			tree = argList.asString(2)
			setIndex = argList.asInt(3)
			
			if argsLen == 5:
				instancerPrefix = argList.asString(4)
			else:
				instancerPrefix = partCloudShape[:-5]
			instancerName = instancerPrefix + '_Instancer'
			
			treeShape = ''
			partInstancer = ''
			SpeedTreeAsset = ''
			treePlug = mc.connectionInfo( SpeedTreeForest + '.forestObjects[' + str( setIndex ) + ']', sfd=1 )
			
			if tree != '':
				if mc.nodeType( tree ) != None:
					treeShapes = mc.listRelatives( tree, s=1 )
					if treeShapes != None and len( treeShapes ) > 0:
						treeShape = treeShapes[0]
						
				supportedTreeTypes = [ 'transform', 'mesh', 'nurbsSurface', 'nurbsCurve', 'subdiv' ]
				assignForestObject = False
				
				#remove existing object if there is one
				cons = mc.listConnections( partCloudShape )
				if ( cons != None and len( cons ) > 0 and mc.objExists( cons[0] ) and mc.nodeType( cons[0] ) == 'instancer' and mc.nodeType( treeShape ) != 'particle' ):
					if treePlug != '':
						oldObj = mel.eval( "instancer -index 0 -q -obj " + cons[0] )
						if oldObj != '':
							mc.particleInstancer( partCloudShape, n=cons[0], edit=True, obj=oldObj, rm=True )
						
					partInstancer = mc.particleInstancer( partCloudShape, n=cons[0], edit=True, obj=tree, a=True )
					assignForestObject = True
					
				elif mc.nodeType( tree ) in supportedTreeTypes and mc.nodeType( treeShape ) != 'particle':
					
					partInstancer = mc.particleInstancer( partCloudShape, n=instancerName, obj=tree, a=True, lod='geometry', p='position', r='rotationPP', sc='UserVector1PP' )
					useBBs = mc.getAttr( SpeedTreeForest + ".bb" )
					mc.setAttr( partInstancer + '.lod', useBBs )
						
					assignForestObject = True
				
				if assignForestObject:
					if treePlug != '':
						mc.disconnectAttr( treePlug, SpeedTreeForest + '.forestObjects[' + str( setIndex ) + ']' )
						mc.setAttr( treePlug.split( '.' )[0] + '.visibility', 1 )
					mc.connectAttr( tree + '.message', SpeedTreeForest + '.forestObjects[' + str( setIndex ) + ']' )
					
					#create asset
					if MayaVersion >= 2009:
						SpeedTreeAsset = mc.container( q=True, findContainer=[ partCloudShape ] )
						if partInstancer != '' and SpeedTreeAsset != None and SpeedTreeAsset != '':
							mc.container( SpeedTreeAsset, edit=True, addNode=partInstancer, force=True )


#SpeedTree Import Command
class SpeedTreeForestImporter( OpenMayaMPx.MPxCommand ):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__( self )
	
	def stCross( self, a, b ):
		"""Computes a cross product"""
		c = [a[1]*b[2] - a[2]*b[1],
			a[2]*b[0] - a[0]*b[2],
			a[0]*b[1] - a[1]*b[0]]
			
		return c
	
	def stStripIllegalChars( self, str ):
		"""Removes problem characters from object names"""
		str = str.replace( " ", "_" )
		str = str.replace( "/", "_" )
		str = str.replace( "\\", "_" )
		str = str.replace( ":", "_" )
		str = str.replace( ";", "_" )
		str = str.replace( "'", "_" )
		str = str.replace( "\"", "_" )
		str = str.replace( ",", "_" )
		str = str.replace( ".", "_" )
		str = str.replace( "<", "_" )
		str = str.replace( ">", "_" )
		str = str.replace( "?", "_" )
		str = str.replace( "{", "_" )
		str = str.replace( "[", "_" )
		str = str.replace( "}", "_" )
		str = str.replace( "]", "_" )
		str = str.replace( "|", "_")
		str = str.replace( "~", "_")
		str = str.replace( "\`", "_")
		str = str.replace( "!", "_" )
		str = str.replace( "@", "_" )
		str = str.replace( "#", "_" )
		str = str.replace( "$", "_" )
		str = str.replace( "%", "_" )
		str = str.replace( "^", "_" )
		str = str.replace( "&", "_" )
		str = str.replace( "*", "_" )
		str = str.replace( "(", "_" )
		str = str.replace( ")", "_" )
		str = str.replace( "+", "_" )
		str = str.replace( "=", "_" )
		
		return str
	
	
	def doIt( self, argList ):
		"""Processes a SpeedTree SWA file for forest instance locations"""
		
		mc.select( clear=True )
		
		#define variables
		swaFile = swaName = ''
		SpeedTreeForest = SpeedTreeAsset = ''
		SpeedTreeForestAssets = []
		arrObjects = []
		arrObjNames = []
		arrObjCount = []
		arrTranslate = []
		upRot = []
		rightRot = []
		outRot = []
		arrScale = []
		arrInstances = []
		partCloud = []
		treeArray = []
		oCount = tCount = 0
		objTotalCount = 0
		swaCount = 0
		treeCount = 0
		objLen = 0
		
		processMode = 2
		argsLen = argList.length()
		startInd = 2
		
		#process mode
		if argsLen > 1:
			processMode = argList.asInt(0)
			swaFile = argList.asString(1)
			if processMode == 1:
				SpeedTreeForest = argList.asString(2)
				startInd = 3
			if argsLen > startInd:
				for a in range( startInd, argsLen ):
					treeArray.append( argList.asString(a) )
				treeCount = len( treeArray )
		
		#get SWA file
		if processMode == 2 and swaFile == '':
			if MayaVersion >= 2012:
				try:
					swaFile = mc.fileDialog2( fileMode=1, caption="Select a SpeedTree SWA file", okc="Load", fileFilter="*.swa", dialogStyle=2 )[0]
				except:
					swaFile = ''
			else:
				swaFile = mc.fileDialog( mode=0, title='Select a SpeedTree SWA file', directoryMask='*.swa' )
		
		swaExists = ( os.path.exists( swaFile ) and not os.path.isdir( swaFile ) )
		if swaExists:
			swaName = swaFile.rpartition("/")[2]
			swaName = swaName[:-4]
			
			#reloading forest node
			if processMode == 1:
				if MayaVersion >= 2012:
					SpeedTreeForest = mc.rename( SpeedTreeForest, swaName + '_Forest' )
					
				oldParticleSets = []
				particleSetInds = mc.getAttr( SpeedTreeForest + '.particleSets', mi=1 )
				if particleSetInds != None:
					for p in particleSetInds:
						particleSet = mc.connectionInfo( SpeedTreeForest + '.particleSets[' + str(p) + ']', sfd=1 ).split( '.' )[0]
						forestObject = mc.connectionInfo( SpeedTreeForest + '.forestObjects[' + str(p) + ']', sfd=1 ).split( '.' )[0]
						
						if particleSet != '':
							mc.removeMultiInstance( SpeedTreeForest + '.particleSets[' + str(p) + ']', b=True )
							mc.removeMultiInstance( SpeedTreeForest + '.forestObjects[' + str(p) + ']', b=True )
							if mc.objExists( forestObject ):
								mc.setAttr( forestObject + '.visibility', 1 )
							
						oldParticleSets.append( particleSet )
						
						particleSetShapes = mc.listRelatives( particleSet, s=1 )
						if particleSetShapes != None and len( particleSetShapes ) > 0:
							particleSetShape = particleSetShapes[0]
							cons = mc.listConnections( particleSetShape, d=1 )
							if cons != None and len( cons ) > 0:
								for c in cons:
									if ( mc.nodeType( c ) == 'instancer' ):
										oldParticleSets.append( c )
					
					for s in oldParticleSets:
						if mc.objExists( s ):
							mc.delete( s )
			
			else:
				SpeedTreeForest = mc.createNode( 'SpeedTreeForest', name=swaName + '_Forest' )
				mc.setAttr( SpeedTreeForest + '.swaFile', swaFile, type='string' )
			
			SpeedTreeForestAssets.append( SpeedTreeForest )
			
			#create asset
			if MayaVersion >= 2009:
				
				if processMode == 1:
					SpeedTreeAsset = mc.container( q=True, findContainer=[ SpeedTreeForest ] )
					
				if SpeedTreeAsset != '':
					if MayaVersion >= 2012:
						SpeedTreeAsset = mc.rename( SpeedTreeAsset, swaName )
					mc.container( SpeedTreeAsset, edit=True, addNode=SpeedTreeForest, force=True )
				else: 	#create container
					SpeedTreeAsset = mc.container( name=swaName, addNode=SpeedTreeForest, force=True )
					
				#asset settings
				SpeedTreeFbxPath = mc.pluginInfo( 'SpeedTreeForest.py', path=True, query=True )
				SpeedTreeFbxPart = SpeedTreeFbxPath.rpartition( '/' )
				
				if MayaVersion >= 2011:
					SpeedTreeIconPath = SpeedTreeFbxPart[0] + '/icons/SpeedTreeForest.png'
				else:
					SpeedTreeIconPath = SpeedTreeFbxPart[0] + 'icons/out_SpeedTreeForest.xpm'
				
				if os.path.isfile( SpeedTreeIconPath ):
					mc.setAttr( SpeedTreeAsset + '.iconName', SpeedTreeIconPath, type='string' )
					
				elif mc.objExists( SpeedTreeAsset + '.isAsset' ):
					mc.setAttr( SpeedTreeAsset + '.isAsset', 1 )
					
				mc.setAttr( SpeedTreeAsset + '.viewMode', 0 )
			
			#open SWA file
			swaData = open(swaFile, 'r')
			while True:
				line = swaData.readline()
				if len(line) == 0:
					break #EOF
				
				while len(line) == 1 or line == "\r\n":
					line = swaData.readline()
			    
				if line != "" and line != "\t" and line != "\n" and line!= "\r\n":
					if line[(len(line) - 2):] == "\r\n":
						line = line[:(len(line) - 2)]
					elif line[(len(line) - 1):] == "\n":
						line = line[:(len(line) - 1)]
					
					arrObjNames.append( self.stStripIllegalChars( line ) )
					line = swaData.readline()
					swaCount = int( line )
					arrObjCount.append( swaCount )
					
					for t in range(0, swaCount):
						line = swaData.readline()
						swa_instance = line.split(' ')
						
						#flip Y and Z and negate Z (Y-up conversion)
						arrTranslate.append( [float( swa_instance[0]), float( swa_instance[2] ), float( swa_instance[1] ) * -1] )
						upRot.append( [float( swa_instance[3] ), float( swa_instance[4] ), float( swa_instance[5] )] )
						rightRot.append( [float( swa_instance[6] ), float( swa_instance[7] ), float( swa_instance[8] )] )
						outRot.append( self.stCross ( upRot[tCount], rightRot[tCount] ) )
						arrScale.append( float( swa_instance[9][:-1] ) )
						tCount = tCount + 1
		
			j = 0
			objLen = len( arrObjNames )
			#handle tree entries
			for t in range( 0, objLen ):
				objName = arrObjNames[t][1:-1]
				arrInstances = []
				
				#particle object
				partCloud = mc.particle( p=arrTranslate[objTotalCount:( objTotalCount + arrObjCount[t] )] )
				partCloud[0] = mc.rename( partCloud[0], objName )
				partCloud[1] = mc.listRelatives( partCloud[0], s=1 )[0]
				particleCons = mc.listConnections( partCloud[1], p=1, c=1 )
				if len( particleCons ) == 4:
					mc.disconnectAttr( particleCons[0], particleCons[1] )
					mc.disconnectAttr( particleCons[3], particleCons[2] )
				
				mc.addAttr( partCloud[1], ln = 'rotationPP', dt='vectorArray', h=1 )
				mc.addAttr( partCloud[1], ln = 'UserVector1PP', dt='vectorArray', h=1 )
				
				if MayaVersion >= 2009 and SpeedTreeAsset != '':
					mc.container( SpeedTreeAsset, edit=True, addNode=partCloud, force=True )
				
				connectedSets = mc.getAttr( SpeedTreeForest + '.particleSets', mi=1 )
				setIndex = 0
				if connectedSets != None:
					setIndex = len( connectedSets )
				mc.connectAttr( partCloud[0] + '.message', SpeedTreeForest + '.particleSets[' + str( setIndex ) + ']' )
				
				#handle instances
				objTotalCount = objTotalCount + arrObjCount[t]
				for i in range(0, arrObjCount[t]):
					
					#transpose the Z-up matrix
					mMatrix = om.MMatrix()
					toYupMatrix = om.MMatrix()
					instRotation = [ rightRot[j][0], rightRot[j][1], rightRot[j][2], 0, outRot[j][0], outRot[j][1], outRot[j][2], 0, upRot[j][0], upRot[j][1], upRot[j][2], 0, 0, 0, 0, 1 ]
					toYup = [ 1, 0, 0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1 ]
					om.MScriptUtil.createMatrixFromList( instRotation, mMatrix )
					om.MScriptUtil.createMatrixFromList( toYup, toYupMatrix )
					yUpMatrix = mMatrix * toYupMatrix
					
					mTransformMtx = om.MTransformationMatrix( yUpMatrix )
					eulerRot = mTransformMtx.eulerRotation()
					angles = [ math.degrees( angle ) for angle in ( eulerRot.x, eulerRot.y, eulerRot.z ) ]
					angles[0] += 90
					mc.particle( e=True, attribute='rotationPP', order=i, vectorValue=angles )
					mc.particle( e=True, attribute='UserVector1PP', order=i, vectorValue=( arrScale[j],  arrScale[j],  arrScale[j] ) )
				
					j += 1
				
				#create cache
				cacheDir = sceneCacheDir = swaDir = ''
				sceneFullPath = mc.file( q=True, sn=True )
				projectDir = mc.workspace( q=True, rd=True )
				if sceneFullPath != '':
					sceneName = sceneFullPath.rpartition( '/' )[2].rpartition( '.' )[0]
				else:
					strDateTime = 'tmp'
					dateTime = str( datetime.datetime.now() )
					dateTime = dateTime.rpartition( ':' )[0]
					dateTime = re.split( '-| |:', dateTime )
					
					if len( dateTime ) >= 5:
						strDateTime = dateTime[0] + dateTime[1] + dateTime[2] + '.' + dateTime[3] + dateTime[4]
					sceneName = getpass.getuser() + '.' + strDateTime
				
				particleDir = projectDir + 'particles'
				if not os.path.exists( particleDir ):
					os.mkdir( particleDir )
				
				swaSceneDir = sceneName
				dynGlobalsNode = mc.dynGlobals( q=True, a=True )
				curCacheDir = mc.getAttr( dynGlobalsNode + '.cacheDirectory' )
				
				#copy cache from previous file save
				if curCacheDir != '' and curCacheDir != None and not os.path.exists( particleDir + '/' + swaSceneDir ):
					shutil.copytree( particleDir + '/' + curCacheDir, particleDir + '/' + swaSceneDir )
				
				#or make a new folder for current scene cache
				elif not os.path.exists( particleDir + '/' + swaSceneDir ):
					os.mkdir( particleDir + '/' + swaSceneDir )
				
				#saving over an old file, so keep cache folder
				else:
					swaSceneDir = curCacheDir
				
				if swaSceneDir != None and swaSceneDir != '':
					mc.dynExport( partCloud[0], atr=( 'position', 'rotationPP', 'UserVector1PP' ), f='cache', p=swaSceneDir )
					mc.saveInitialState( partCloud[1] )
				
				#add trees
				if treeCount > t:
					mc.assignSpeedTreeForestEntry( SpeedTreeForest, partCloud[1], treeArray[t], setIndex, objName )
					if mc.getAttr( SpeedTreeForest + '.hs' ) == 1 and mc.objExists( treeArray[t] + '.visibility' ):
						#hide skeleton if there is one
						rootBone = ''
						treeHistory = mc.listHistory( treeArray[t] )
						for h in treeHistory:
							if mc.nodeType( h ) == 'skinCluster':
								bindPose = mc.connectionInfo( h + '.bindPose', sfd=True ).split( '.' )[0]
								if bindPose != None and bindPose != '' and mc.objExists( bindPose ):
									rootBone = mc.connectionInfo( bindPose + '.members[0]', sfd=True ).split( '.' )[0]
						
						if rootBone != '' and mc.objExists( rootBone ):
							mc.setAttr( rootBone + '.visibility', 0 )
							
						#hide source object
						mc.setAttr( treeArray[t] + '.visibility', 0 )
						
			#if processMode == 0:
			mc.select( SpeedTreeForest )
			
			if mel.eval( 'exists refreshEditorTemplates' ) and processMode == 0:
				mc.refreshEditorTemplates()
			

#add importer to "File->Import" menu
class SpeedTreeForestFileTranslator( OpenMayaMPx.MPxFileTranslator ):
	def __init__(self):
		OpenMayaMPx.MPxFileTranslator.__init__( self )
	def haveWriteMethod(self):
		return False
	def haveReadMethod(self):
		return True
	def filter(self):
		return "*.swa"
	def defaultExtension(self):
		return "swa"
	def canBeOpened(self):
		return False
	def writer( self, fileObject, optionString, accessMode ):
		pass
	def reader( self, fileObject, optionString, accessMode ):
		try:
			swaFile = fileObject.fullName()
			
			selectedTrees =  mc.ls( sl=1 )
			treeList = "'" +  "', '".join( selectedTrees )
			if len( selectedTrees ) > 0:
				treeList = "', " + treeList + "'"
				
			mc.evalDeferred( """import maya.cmds as mc \nmc.importSpeedTreeForest( 0, '""" + swaFile + treeList + """ )""" )
		
		except:
			sys.stderr.write( "Failed to read SpeedTree SWA file.\n" )
			raise


#SpeedTreeForest node
class SpeedTreeForest( OpenMayaMPx.MPxNode ):
	aShapeNodes = om.MObjectArray()
	
	def __init__( self ):
		OpenMayaMPx.MPxNode.__init__(self)


#initializer
def nodeSpeedTreeForestInit():
	
	nAttr = om.MFnNumericAttribute()
	nMAttr = om.MFnMatrixAttribute()
	nEAttr = om.MFnEnumAttribute()
	nTAttr = om.MFnTypedAttribute()
	nGAttr = om.MFnGenericAttribute()
	cAttr = om.MFnCompoundAttribute()
	stringData = om.MFnStringData().create("")
	
	SpeedTreeForest.aSwaFile = nTAttr.create( "swaFile", "swa", om.MFnData.kString, stringData )
	nTAttr.setUsedAsFilename(1)
	
	SpeedTreeForest.aHideSourceObjects = nAttr.create( "hideSourceObjects", "hs", om.MFnNumericData.kBoolean, True )
	nAttr.setReadable(0)
	
	SpeedTreeForest.aToggleBBs = nAttr.create( "toggleBoundingBoxes", "bb", om.MFnNumericData.kBoolean )
	nAttr.setReadable(0)
	
	SpeedTreeForest.aToggleForest = nAttr.create( "toggleForestVisibility", "tfv", om.MFnNumericData.kBoolean, True )
	nAttr.setReadable(0)
	
	SpeedTreeForest.aForestPlacements = nTAttr.create( "particleSets", "ps", om.MFnData.kString )
	nTAttr.setReadable(0)
	nTAttr.setWritable(1)
	nTAttr.setArray(1)
	
	SpeedTreeForest.aForestObjects = nTAttr.create( "forestObjects", "fo", om.MFnData.kString )
	nTAttr.setReadable(0)
	nTAttr.setWritable(1)
	nTAttr.setArray(1)
	
	SpeedTreeForest.aAssetLink = nTAttr.create( "assetLink", "al", om.MFnData.kString )
	nTAttr.setReadable(1)
	nTAttr.setWritable(1)
	
	SpeedTreeForest.addAttribute( SpeedTreeForest.aSwaFile )
	SpeedTreeForest.addAttribute( SpeedTreeForest.aHideSourceObjects )
	SpeedTreeForest.addAttribute( SpeedTreeForest.aToggleBBs )
	SpeedTreeForest.addAttribute( SpeedTreeForest.aToggleForest )
	SpeedTreeForest.addAttribute( SpeedTreeForest.aForestPlacements )
	SpeedTreeForest.addAttribute( SpeedTreeForest.aForestObjects )
	SpeedTreeForest.addAttribute( SpeedTreeForest.aAssetLink )
	
	
# Creators
def nodeSpeedTreeForestCreator():
	return OpenMayaMPx.asMPxPtr( SpeedTreeForest() )

def cmdSpeedTreeForestImporter():
	return OpenMayaMPx.asMPxPtr( SpeedTreeForestImporter() )

def cmdAssignSpeedTreeForestEntry():
	return OpenMayaMPx.asMPxPtr( AssignSpeedTreeForestEntry() )

def translatorSpeedTreeForestCreator():
	return OpenMayaMPx.asMPxPtr( SpeedTreeForestFileTranslator() )


def SpeedTreeForestCheckEnvVarPath( envVar, setVar=False, evalMel=None, melPath='' ):
	""""Determines if SpeedTree paths are included for an environment variable"""
	
	try:
		strEnvVarPaths = ''
		arrEnvVarPaths = []
		delimiter = ';'
		if sys.platform == 'darwin' or sys.platform == 'linux2': #Mac OSX, Linux
			delimiter = ':'
			
		SpeedTreeForestPath = mc.pluginInfo( 'SpeedTreeForest.py', path=True, query=True )
		SpeedTreeForestPath = SpeedTreeForestPath.rpartition( '/' )[0]
		if envVar.upper() == 'XBMLANGPATH':
			SpeedTreeForestPath += '/icons'
		elif envVar.upper() == 'MAYA_SCRIPT_PATH':
			SpeedTreeForestPath += '/templates'
		
		#ENV VAR option
		if evalMel == None:
			strEnvVarPaths = os.environ[ envVar.upper() ]
			arrEnvVarPaths = strEnvVarPaths.split( delimiter )
			strEnvVarPaths += delimiter + SpeedTreeForestPath
			
			if setVar and SpeedTreeForestPath not in arrEnvVarPaths:
				os.environ[ envVar.upper() ] = strEnvVarPaths
			
			return arrEnvVarPaths
		
		#MEL search path option (for asset templates)
		else:
			arrEnvVarPaths = mel.eval( evalMel )
			for p in arrEnvVarPaths:
				strEnvVarPaths += delimiter + p
			
			strEnvVarPaths = strEnvVarPaths[1:]
			strEnvVarPaths += delimiter + SpeedTreeForestPath + '/' + melPath + '/'
			
			return [arrEnvVarPaths, strEnvVarPaths]
			
	except:
		raise
		return []


# Initialize the script plug-in
def initializePlugin( mobject ):
	mplugin = OpenMayaMPx.MFnPlugin( mobject )
	
	#register plug-in paths
	SpeedTreeForestPath = mc.pluginInfo( 'SpeedTreeForest.py', path=True, query=True )
	SpeedTreeForestPath = SpeedTreeForestPath.rpartition( '/' )[0]
	arrPluginPaths = SpeedTreeForestCheckEnvVarPath( 'MAYA_PLUG_IN_PATH' )
	arrScriptPaths = SpeedTreeForestCheckEnvVarPath( 'MAYA_SCRIPT_PATH', True )
	arrIconPaths = SpeedTreeForestCheckEnvVarPath( 'XBMLANGPATH', True )
	
	#asset template paths
	assetTemplatePaths = SpeedTreeForestCheckEnvVarPath( '', True, 'containerTemplate -query -searchPath', 'templates' )
	if ( SpeedTreeForestPath + '/templates/' ) not in assetTemplatePaths[0]:
		mel.eval( 'workspace -fr "templates" "' + assetTemplatePaths[1] + '"' )
	
	#add SpeedTreeForest.py to Maya.env
	mayaEnvLoc = ''
	bFoundMayaEnv = False
	bPathLoaded = True
	if SpeedTreeForestPath not in arrPluginPaths:
		SpeedTreeForestCheckEnvVarPath( 'MAYA_PLUG_IN_PATH', True )
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
					envFile.write( linePrefix + 'MAYA_PLUG_IN_PATH = ' + SpeedTreeForestPath )
					envFile.close()
					print( '"SpeedTreeForest.py" added to Plug-In Manager' )
				else:
					print( 'Error adding SpeedTreeForest to Plug-In Manager' )
			except :
				print( 'Unable to open Maya.env file %s' % mayaEnvLoc )
	
	#register commands
	mplugin.registerCommand( kSpeedTreeForestImporterName, cmdSpeedTreeForestImporter )
	mplugin.registerCommand( kSpeedTreeAssignForestEntryName, cmdAssignSpeedTreeForestEntry )
	
    # register nodes
	mplugin.registerNode( kSpeedTreeForestNodeName, kSpeedTreeForestNodeId, nodeSpeedTreeForestCreator, nodeSpeedTreeForestInit, OpenMayaMPx.MPxNode.kDependNode, kSpeedTreeForestNodeClassify )
	
	#register file translator
	mplugin.registerFileTranslator( kSpeedTreeForestTranslatorName, None, translatorSpeedTreeForestCreator )
	
	mel.eval( '''global proc ImportSpeedTreeForest() { 
	python( "mc.importSpeedTreeForest()" );
	}''' )
	
	print( 'plug-in "SpeedTreeForest.py" loaded' )
	alreadyLoaded = mc.pluginInfo( SpeedTreeForestPath + '/SpeedTreeFBX.py', query=True, loaded=True)
	if not alreadyLoaded and not bPathLoaded:
		try:
			mc.loadPlugin( 'SpeedTreeFBX.py', quiet=True)
		except:
			print( 'SpeedTreeFBX plug-in not found.' )
	

# Uninitialize the script plug-in
def uninitializePlugin( mobject ):
	mplugin = OpenMayaMPx.MFnPlugin( mobject )
	
	#deregister nodes
	mplugin.deregisterNode( kSpeedTreeForestNodeId )
	
	#deregister commands
	mplugin.deregisterCommand( kSpeedTreeForestImporterName )
	mplugin.deregisterCommand( kSpeedTreeAssignForestEntryName )
	
	#deregister file translator
	mplugin.deregisterFileTranslator( kSpeedTreeForestTranslatorName )
	


