from __future__ import with_statement
import nuke,math
import os,re,sys
import nukescripts

linkKnobs=['translate','rotate','scaling','focal','haperture','vaperture']

def setup():
    cam=nuke.thisNode()['camera'].value()
    cam=nuke.toNode(cam)
    thisNode=nuke.thisNode()
    if cam:
        with thisNode:
            pCam=nuke.toNode('particleCam')
            for lk in linkKnobs:
                pCam[lk].setExpression('parent.parent.'+cam.name()+'.'+lk)
            offset=nuke.toNode('particleOffset')
            offset['translate'].setValue(cam['translate'].value())

    else:
        nuke.message("must enter a valid camera")
