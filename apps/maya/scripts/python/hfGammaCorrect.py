""" hfGammaCorrect v0.1 by henry foster (henry@toadstorm.com)
rev 06/24/2013
"""

import maya.cmds as cmds
import os

dataChannels = ['bumpMap','reflectionGlossiness','refractionGlossiness']
ignoreMats = ['VRayBlendMtl']

def gammaCorrectMaterials(mats,displayGamma=2.2):
    gamma = 1.0 / displayGamma
    for mat in mats:
        if cmds.objectType(mat) not in ignoreMats:
            print 'processing material %s' % (mat)
            # get all attributes that have color swatches.
            attrs = [f for f in cmds.listAttr(mat,u=1,w=1,c=1) if cmds.attributeQuery(f,node=mat,uac=1) and f not in dataChannels]
            # for each channel listed, if the value is not pure black or white, attach a gammaCorrect node.
            for attr in attrs:
                val = cmds.getAttr(mat+'.'+attr)
                # this is a possible contender. is there already a gammaCorrect node feeding into this channel?
                conn = cmds.listConnections(mat+'.'+attr,p=1,s=1,d=0)
                if conn:
                    # something is already connected. is it a gammaCorrect node?
                    node = conn[0].split('.')[0]
                    plug = conn[0].split('.')[-1]
                    if cmds.objectType(node) == 'gammaCorrect':
                        # set the gammaCorrect gamma value to our current gamma, in case it's different.
                        cmds.setAttr(node+'.gammaX',gamma)
                        cmds.setAttr(node+'.gammaY',gamma)
                        cmds.setAttr(node+'.gammaZ',gamma)
                    else:
                        # is it a file? if so, make sure it's not floating-point data.
                        if cmds.objectType(node) == 'file':
                            # does the path end in .HDR or .EXR?
                            file = cmds.getAttr(node+'.fileTextureName')
                            ext = os.path.splitext(file)[-1].lower()
                            if ext != '.hdr' and ext != '.exr':
                                # insert the gammaCorrect node into the dependency graph.
                                newGamma = cmds.shadingNode('gammaCorrect',au=1,n=mat+'_'+attr+'_gamma')
                                cmds.setAttr(newGamma+'.gammaX',gamma)
                                cmds.setAttr(newGamma+'.gammaY',gamma)
                                cmds.setAttr(newGamma+'.gammaZ',gamma)
                                cmds.connectAttr(node+'.'+plug,newGamma+'.value',f=1)
                                cmds.connectAttr(newGamma+'.outValue',mat+'.'+attr,f=1)
                        else:
                            newGamma = cmds.shadingNode('gammaCorrect',au=1,n=mat+'_'+attr+'_gamma')
                            cmds.setAttr(newGamma+'.gammaX',gamma)
                            cmds.setAttr(newGamma+'.gammaY',gamma)
                            cmds.setAttr(newGamma+'.gammaZ',gamma)
                            cmds.connectAttr(node+'.'+plug,newGamma+'.value',f=1)
                            cmds.connectAttr(newGamma+'.outValue',mat+'.'+attr,f=1)
                else:
                    if val != [(0.0,0.0,0.0)] and val != [(1.0,1.0,1.0)]:
                        # create a new gammaCorrect node and set the value to the value of the current swatch.
                        newGamma = cmds.shadingNode('gammaCorrect',au=1,n=mat+'_'+attr+'_gamma')
                        cmds.setAttr(newGamma+'.gammaX',gamma)
                        cmds.setAttr(newGamma+'.gammaY',gamma)
                        cmds.setAttr(newGamma+'.gammaZ',gamma)
                        cmds.setAttr(newGamma+'.value',val[0][0],val[0][1],val[0][2],type='double3')
                        # connect to input.
                        cmds.connectAttr(newGamma+'.outValue',mat+'.'+attr,f=1)
    
def doGammaCorrect(gamma=2.2):
    sel = cmds.ls(sl=1)
    if not sel:
        cmds.error('You need to select at least one material to correct.')
    gammaCorrectMaterials(sel,gamma)