import maya.cmds as cmds
import maya.mel as mel

def generateIDs(item,attr,dict,renderLayer):
	hsh= abs(hash(item)) % (10 ** 7)
	while hsh in dict.keys():
		hsh+=1
	if hsh in dict.keys():
		print 'FOUND:',hsh,item
	if not attr in cmds.listAttr(item):
		mel.eval("vrayAddAttr "+item+" "+attr)
	if attr in cmds.listAttr(item):
		#cmds.editRenderLayerAdjustment(item+'.'+attr, layer=renderLayer)#add layer overide
		cmds.setAttr(item+'.'+attr,int(hsh))
	if not hsh in dict.keys():
		dict[hsh]=item
	return dict

def setupIDs():
	currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
	#add ids to objects
	objIDs={}
	for sh in cmds.ls(g=1):
		if cmds.listConnections(sh):
			for x in cmds.listConnections(sh):
				if "shadingEngine" in cmds.nodeType(x):
					objIDs=generateIDs(sh,'vrayObjectID',objIDs,currentRenderLayer)
	#add ids to materials
	matIDs={}
	for mat in cmds.ls(type='shadingEngine'):
		matIDs=generateIDs(mat,'vrayMaterialId',matIDs,currentRenderLayer)
	#add ids to metadata
	metadataString=[]
	for id in objIDs.keys():
		metadataString.append("obj"+str(id).zfill(7)+"="+objIDs[id].replace("Shape",""))
	for id in matIDs.keys():
		metadataString.append("mat"+str(id).zfill(7)+"="+matIDs[id])
	metadataString.sort()
	cmds.setAttr("vraySettings.imgOpt_exr_attributes",";\n".join(metadataString),type="string")

def setupOverides():
	import maya.cmds as cmds
	import maya.mel as mel
	#### Select renderLayer with geo, will create lighting passes and utility layer.

	#get selected renderLayer
	currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
	
	#get settings from any existing vrayObjectProperties, to copy to utility settings
	existingVis=[]
	layerAdj=cmds.editRenderLayerAdjustment(currentRenderLayer, query=True, layer=True )
	if layerAdj:
		for adj in layerAdj:
			if "vrayobjectproperties" in adj:
				existingVis.append([adj,cmds.getAttr(adj)])
	
	matteLayer=currentRenderLayer+"_DeepMatte"
	#create Matte layer
	if not cmds.objExists(matteLayer):
		cmds.createRenderLayer(n=matteLayer,nr=1)
	#add geo
	print "adding geo to",matteLayer
	contents= cmds.editRenderLayerMembers(currentRenderLayer,q=1,fn=1)  
	for obj in contents:
		if cmds.objExists(obj):
			cmds.editRenderLayerMembers(matteLayer,obj,nr=1) 
	cmds.editRenderLayerGlobals(currentRenderLayer=matteLayer)
	currentRenderLayer=matteLayer

	#turn off all existing render Elements in matteLayer
	for elem in mel.eval('vrayRenderElementsExisting'):
		cmds.editRenderLayerAdjustment(elem+".enabled", layer=currentRenderLayer)
		cmds.setAttr(elem+".enabled",0) 
		
	#add render elements for Ids
	if not "vrayRE_Object_ID" in mel.eval('vrayRenderElementsExisting'):
		extraTex=mel.eval("vrayAddRenderElement nodeIDChannel")
	if not "vrayRE_Multi_Matte_ID" in mel.eval('vrayRenderElementsExisting'):
		extraTex=mel.eval("vrayAddRenderElement multimatteIDChannel")
	if not "vrayRE_Render_ID" in mel.eval('vrayRenderElementsExisting'):
		extraTex=mel.eval("vrayAddRenderElement renderIDChannel")

	print 'here'
	#set layer overide renderSettings, turn off GI, resolution, filtering, lights
	cmds.editRenderLayerAdjustment("vraySettings.imageFormatStr", layer=currentRenderLayer)
	cmds.editRenderLayerAdjustment("vraySettings.giOn", layer=currentRenderLayer)
	cmds.editRenderLayerAdjustment("vraySettings.globopt_light_doLights", layer=currentRenderLayer)
	cmds.editRenderLayerAdjustment("vraySettings.globopt_light_doDefaultLights", layer=currentRenderLayer)
	cmds.editRenderLayerAdjustment("vraySettings.globopt_mtl_reflectionRefraction", layer=currentRenderLayer)
	cmds.editRenderLayerAdjustment("vraySettings.globopt_mtl_glossy", layer=currentRenderLayer)
	cmds.editRenderLayerAdjustment("vraySettings.globopt_mtl_SSSEnabled", layer=currentRenderLayer)
	cmds.editRenderLayerAdjustment("vraySettings.globopt_light_disableSelfIllumination", layer=currentRenderLayer)
	print 'testing'
	#vrayObjectProperties
	for vis in existingVis:
		attr,val=vis
		cmds.editRenderLayerAdjustment(attr, layer=currentRenderLayer)

    #set rendersettings layer overides
	cmds.setAttr("vraySettings.imageFormatStr","exr (deep)",type="string")#set deep exr format
	cmds.setAttr("vraySettings.giOn",0)#turn off GI
	cmds.setAttr("vraySettings.globopt_light_doLights",0)#turn off all lights
	cmds.setAttr("vraySettings.globopt_light_doDefaultLights", 1)#turn on headlight
	cmds.setAttr("vraySettings.globopt_mtl_reflectionRefraction", 0)#turn off refraction
	cmds.setAttr("vraySettings.globopt_mtl_glossy", 0)#turn off glossy
	cmds.setAttr("vraySettings.globopt_mtl_SSSEnabled", 0)#turn off sss
	cmds.setAttr("vraySettings.globopt_light_disableSelfIllumination", 1)#turn off self illum
	cmds.setAttr("vraySettings.imgOpt_exr_compression", 3)#set zip1 compression

	matteAovs=[
		"vrayRE_Object_ID",
		"vrayRE_Multi_Matte_ID",
		"vrayRE_Render_ID"]

	#turn on matte aovs
	for aov in matteAovs:
		if aov in mel.eval('vrayRenderElementsExisting'):
			cmds.setAttr(aov+".enabled",1)  
  
	#copy settings from VrayObjectProperties
	for vis in existingVis:
		attr,val=vis
		cmds.setAttr(attr,val)

	#disable imagePlanes
	imagePlanes =  cmds.ls(type="imagePlane")
	for ip in imagePlanes:
		cmds.editRenderLayerAdjustment(ip+".displayMode", layer=currentRenderLayer)
		cmds.setAttr(ip+".displayMode",0)

	print 'final'