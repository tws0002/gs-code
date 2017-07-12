from __future__ import with_statement
import nuke,math,random
import os,re,sys
import nukescripts

linkKnobs=['translate','rotate','scaling','focal','haperture','vaperture']


def setupCameraOffset():
    cam=nuke.thisNode()['camera'].value()
    cam=nuke.toNode(cam)
    thisNode=nuke.thisNode()
    if cam:
        with thisNode:
            fCam=nuke.toNode('offsetCam')
            for lk in linkKnobs:
                fCam[lk].setExpression('parent.parent.'+cam.name()+'.'+lk+"(frame+offset)")
                

