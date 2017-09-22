#load Dynamic master and bring in correct abc cache to currently opened lighting file
#example execution: #hairDynImport('miaYoungest')

import maya.cmds as cmds
import os
import glob
import xgenm as xg #can be outside of maya accessing xgen
import xgenm.xgGlobal as xgg #inside maya accessing xgen with check if xgg.Maya:

def hairDynImport(charStr):

    ##############################################################
    #remove .xgen files that correspond to opened lighting file.
    curPath = cmds.file(q = True, location = True)
    fileStr = cmds.file(q=True, exn=True).replace('.mb','*.xgen')
    fileLs = glob.glob(fileStr)

    for curFile in fileLs:
      print ('Removing '+curFile)
      os.remove(curFile)
    ##############################################################

    ##############################################################
    # variable def
    ##############################################################    
    #charStr = 'miaAdult'
    
    if charStr == 'morton':
        charHead = 'mortonYoung'
        char = 'morton'
        headGeo=charHead+'_head_geo'
    
    if charStr == 'mortonOld':
        charHead = 'mortonYoung'
        char = 'morton'
        headGeo=charHead+'_head_geo'
    
    if charStr == 'miaYoungest':
        charHead = charStr
        char = charStr
        headGeo = charStr+'_body_head'
    
    #miaMid static only
    #miaTeen dynamic button unchanged
    
    if charStr == 'miaAdult':
        charHead = charStr
        char = charStr
        headGeo=charStr+'_head'
    
    # move time to first frame
    cmds.currentTime(str(int(cmds.playbackOptions(q=True, minTime=True))))
    
    prjDir = cmds.workspace( q=True, rootDirectory = True)
    fileStrLs = (cmds.file(q=True, exn=True)).split('/')
    curShot = fileStrLs[len(fileStrLs)-3]
    
    # import hair dynamic master
    cmds.file(prjDir+'scenes/01_cg_elements/01_models/groom_'+charStr+'/groom_'+charStr+'_dynamic_master.mb',i=True,)
    
    #blendshape hair to shot space
    cmds.select('char_'+char+':'+headGeo,r=True)
    cmds.select(charStr+'_head_blend', add=True)
    cmds.blendShape(origin='world',n=charStr+'_head_blend')
    cmds.setAttr(charStr+'_head_blend1.'+headGeo, 1)
    
    cmds.select(cl=True)
    
    # import hair cache files for shot
    cacheFileLs = glob.glob(prjDir+'/cache/alembic/'+curShot+'/'+charStr+'*sim_curves_groom.abc')
    
    for curCache in cacheFileLs:
        cmds.AbcImport(curCache, mode='import')
        strLs=curCache.split('/')
        strLsB = strLs[len(strLs)-1].split('\\')
        curves = strLsB[len(strLsB)-1].replace('.abc','')
        cmds.select(curves, r = True)
        strLs = curves.split('_')
        curDescr = strLs[len(strLs)-4]
        
        # blendshape output curves to dynamic cache curves
        if charStr != 'miaYoungest':
            cmds.select('groom_'+char+'_GRP|RIGgrp|hairSystem1OutputCurves', add=True)
            cmds.blendShape(origin='world',n=charStr+'_'+curDescr+'_static2dyn')
            cmds.setAttr(charStr+'_'+curDescr+'_static2dyn.'+curves, 1)
    
        if charStr == 'miaYoungest':
            if curDescr == 'scalp':
                cmds.select('groom_'+char+'_GRP|RIGgrp|hairSystem1OutputCurves', add=True)
                cmds.blendShape(origin='world',n=charStr+'_'+curDescr+'_static2dyn')
                cmds.setAttr(charStr+'_'+curDescr+'_static2dyn.'+curves, 1)
    
            if curDescr == 'bun':
                cmds.select('groom_'+char+'_GRP|RIGgrp|hairSystem2OutputCurves', add=True)
                cmds.blendShape(origin='world',n=charStr+'_'+curDescr+'_static2dyn')
                cmds.setAttr(charStr+'_'+curDescr+'_static2dyn.'+curves, 1)
            
            cmds.select(curves, add=True)
    
    #Xgen editor
    cmds.loadPlugin('xgenToolkit.mll')
    cmds.XgCreateDescriptionEditor()
    
    #remove preview
    #xgui.createDescriptionEditor(False).preview(True)
    
    #figuring out xgen code below
    '''
    curDescr = 'lashes'
    if xgg.Maya:
        #run command in maya for xgen
        xgg.setActive( charStr+'hair_collection', charStr+'_'+curDescr+'_hair'+, bool previewer=False )()
        string getAttr( string attrName,string palette, string description="", string object="" )()
        cmds.getAttr('width', charStr+'hair_collection',charStr+'_'+curDescr, 'morton_beard_emitter_mortonOld_beard_hair')
    '''
    