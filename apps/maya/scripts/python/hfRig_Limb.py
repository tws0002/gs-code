# rig some things: the script v0.03
# class: Limb, for arms and legs
# henry foster (henry@toadstorm.com) 2012/03/20

# TO DO LIST
#
# -rigging a foot and connecting it correctly requires some restructuring of the main rig; specifically, the ankle_IK needs to be moved outside the group and into its own pivot group
#  entirely in order to allow the ankle to raise.
#  the ik group is then constrained to the controller, and the foot skeleton group is constrained to both ankle joints from the control skeletons.
#  the ik group also needs to be constrained to the FK controller, with a blend attribute.
# -still doesn't solve being able to individually rotate the ball and toe joints when in FK mode...?
# -in order to allow global scaling, a hip controller for a torso needs to parent constrain the IK hips, and the FK leg controllers.
#  same idea for shoulders.
# -the script should probably define an attachment point for a limb, such as a hip or clavicle joint to attach to. this can set up all this constraint bullshit for us.
#
# -arms would be attached to the clavicles. constrain the FK shoulder controls and the IK shoulder bones.
# -legs would be attached to the COG or hip joint. constrain the FK hip controls and the IK hip bones.
#
# -rotate orders...? probably should connect rotate order of control joints to those of their corresponding controllers

import maya.cmds as cmds
import maya.mel as mel
import hfRig_Support as support
import os
import math

iconsPath = '//scholar/assets/SCHOLARPREFS/MAYA2011/PC/icons/hfQuickCtrl2'

class Limb:
    def __init__(self,name,limbType,*args):
        # initialize variables for Limb.
        self.name = name
        self.ik_top = ''
        self.ik_mid = ''
        self.ik_bot = ''
        self.ik_poleVector = ''
        self.fk_top = ''
        self.fk_mid = ''
        self.fk_bot = ''
        self.fk_poleVectorGuide = ''
        self.topTemplate = ''
        self.midTemplate = ''
        self.upperJoints = []
        self.lowerJoints = []
        self.topName = 'top'
        self.midName = 'mid'
        self.botName = 'bot'
        self.gutsGrp = ''
        self.pivot = ''
        self.ik_botHandle = ''
        self.limbType = limbType
        if limbType == 'arm':
            self.topName = 'shoulder'
            self.midName = 'elbow'
            self.botName = 'wrist'
        elif limbType == 'leg':
            self.topName = 'hip'
            self.midName = 'knee'
            self.botName = 'ankle'
        self.makeBindResults = []
        self.fkTopCtrl = ''
        self.fkMidCtrl = ''
        self.fkBotCtrl = ''
        self.ik_ctrl = ''
        self.ik_pvCtrl = ''
        self.curveCtrl = ''
        self.upperUp = ''
        self.lowerUp = ''
        # create associated display layer for hiding guts.
        self.gutsLayer = cmds.createDisplayLayer(n=self.name+'_guts')
        # the attachPoint is an optional definition for what the limb will be attached to.
        self.attachPoint = ''
        print 'generated new Limb object: %s' % (name)

    def makeControlSkeletons(self,top=False,mid=False,bot=False,orient='xyz',secondaryAxis='zup',*args):
        # given a top, mid, bot: orient joints, create duplicates for fk and ik, create template joints for top and mid
        # first, name the joints and start orienting.
        if top==False or mid==False or bot==False:
            # use selection instead.
            if not cmds.ls(sl=1):
                cmds.error('No joints defined for base skeleton, and no joints selected. Aborting')
            top=cmds.ls(sl=1)[0]
            mid=cmds.ls(sl=1)[1]
            bot=cmds.ls(sl=1)[2]
        self.gutsGrp = cmds.group(em=1,n=self.name+'_guts')
        cmds.setAttr(self.gutsGrp+'.inheritsTransform',0)
        chans = ['tx','ty','tz','rx','ry','rz','sx','sy','sz']
        for i in chans:
            cmds.setAttr(self.gutsGrp+'.'+i,l=1)
        self.pivot = cmds.group(em=1,n=self.name+'_group')
        cmds.addAttr(self.pivot,ln='hfRig',at='message')
        cmds.connectAttr(self.gutsGrp+'.message',self.pivot+'.hfRig')
        cmds.addAttr(self.pivot,ln='rigType',dt='string')
        cmds.setAttr(self.pivot+'.rigType','limb',type='string')
        pc = cmds.parentConstraint(top,self.pivot)
        cmds.delete(pc)
        cmds.makeIdentity(self.pivot,a=1,t=1,r=1)
        cmds.delete(self.pivot,ch=1)
        skelGrp = cmds.group(em=1,n=self.name+'_controlSkeletons')
        cmds.editDisplayLayerMembers(self.gutsLayer,skelGrp)
        cmds.parent(skelGrp,self.pivot)
        self.fk_top = cmds.rename(top,self.name+'_FK_'+self.topName)
        self.fk_mid = cmds.rename(mid,self.name+'_FK_'+self.midName)
        self.fk_bot = cmds.rename(bot,self.name+'_FK_'+self.botName)
        cmds.joint(self.fk_top,e=1,oj=orient,sao=secondaryAxis,ch=1,zso=1)
        cmds.joint(self.fk_bot,e=1,oj='none')
        ik_top = cmds.duplicate(self.fk_top,po=1)
        ik_mid = cmds.duplicate(self.fk_mid,po=1)
        ik_bot = cmds.duplicate(self.fk_bot,po=1)
        cmds.parent(ik_bot,ik_mid)
        cmds.parent(ik_mid,ik_top)
        self.ik_top = cmds.rename(ik_top,self.name+'_IK_'+self.topName)
        self.ik_mid = cmds.rename(ik_mid,self.name+'_IK_'+self.midName)
        self.ik_bot = cmds.rename(ik_bot,self.name+'_IK_'+self.botName)
        topTemp = cmds.duplicate(self.fk_top,po=1)
        midTemp = cmds.duplicate(self.fk_mid,po=1)
        cmds.parent(midTemp,topTemp)
        self.midTemplate = cmds.parent(midTemp,w=1)[0]
        self.topTemplate = topTemp
        # tell fk_mid not to nullify scale from parent
        cmds.setAttr(self.fk_mid+'.segmentScaleCompensate',0)
        cmds.setAttr(self.ik_mid+'.segmentScaleCompensate',1)
        # reconnect each parent joint's scale to the child's inverseScale to prevent weird stretching issues
        cmds.connectAttr(self.ik_top+'.scale',self.ik_mid+'.inverseScale',f=1)
        cmds.connectAttr(self.ik_mid+'.scale',self.ik_bot+'.inverseScale',f=1)
        cmds.connectAttr(self.fk_top+'.scale',self.ik_mid+'.inverseScale',f=1)
        cmds.connectAttr(self.fk_mid+'.scale',self.ik_bot+'.inverseScale',f=1)
        # parent skeletons to group for organizing
        cmds.parent(self.fk_top,skelGrp)
        cmds.parent(self.ik_top,skelGrp)
        # now build the IK setup on the IK joints.
        self.ik_botHandle = cmds.ikHandle(sj=self.ik_top,ee=self.ik_bot,sol='ikRPsolver',s='sticky')[0]
        cmds.parent(self.ik_botHandle,self.pivot)
        # build a locator to act as the pole vector and position it according to the joint chain.
        self.ik_poleVector = cmds.spaceLocator(name=self.name+'_pvLoc')[0]
        pc = cmds.pointConstraint(self.ik_top,self.ik_bot,self.ik_poleVector)
        ac = cmds.aimConstraint(self.ik_mid,self.ik_poleVector,aimVector=(1,0,0),upVector=(0,1,0),worldUpType='scene')
        cmds.delete(pc)
        cmds.delete(ac)
        # temporarily parent the locator to the middle and zero out rotations, then move along negative Y axis (assuming a joint second axis orient of +Y)
        cmds.parent(self.ik_poleVector,self.fk_mid)
        cmds.setAttr(self.ik_poleVector+'.rx',0)
        cmds.setAttr(self.ik_poleVector+'.ry',0)
        cmds.setAttr(self.ik_poleVector+'.rz',0)
        limbLen = cmds.getAttr(self.fk_mid+'.tx') + cmds.getAttr(self.fk_bot+'.tx')
        cmds.move(limbLen*-1.0,self.ik_poleVector,y=1,wd=1,os=1,r=1)
        # create pole vector constraint.
        cmds.parent(self.ik_poleVector,self.pivot)
        cmds.poleVectorConstraint(self.ik_poleVector,self.ik_botHandle)
        # hide things.
        cmds.editDisplayLayerMembers(self.gutsLayer,self.ik_botHandle,self.ik_poleVector,self.gutsGrp)
        cmds.addAttr(self.pivot,ln='fkTopJnt',at='message')
        cmds.connectAttr(self.fk_top+'.message',self.pivot+'.fkTopJnt')
        # make message attributes on self.pivot for the ik/fk switch
        cmds.addAttr(self.pivot,ln='ik_top',at='message')
        cmds.addAttr(self.pivot,ln='ik_mid',at='message')
        cmds.addAttr(self.pivot,ln='ik_bot',at='message')
        cmds.addAttr(self.pivot,ln='fk_bot',at='message')
        cmds.addAttr(self.pivot,ln='gutsLayer',at='message')
        cmds.connectAttr(self.ik_top+'.message',self.pivot+'.ik_top')
        cmds.connectAttr(self.ik_mid+'.message',self.pivot+'.ik_mid')
        cmds.connectAttr(self.ik_bot+'.message',self.pivot+'.ik_bot')
        cmds.connectAttr(self.fk_bot+'.message',self.pivot+'.fk_bot')
        cmds.connectAttr(self.gutsLayer+'.message',self.pivot+'.gutsLayer')
        print 'generated control skeletons for Limb %s' % (self.name)
        return self.fk_top,self.fk_mid,self.fk_bot

    def makeBindSkeleton(self,numJoints,bindSet=False,*args):
        # create the NURBS curve that drives the bind skeleton, create clusters and pivots for the clusters,
        # create locators along the curve using motionPaths, place joints parented under the locators.
        # create a selection set from the bind joints for easy skinning.
        # start by setting up locators to get the worldPosition of the joints.
        # this command tends to break undo, so we'll have to pass all created nodes to a return value so that we can potentially undo later.
        self.makeBindResults = []
        s = support.getWorldSpace(self.fk_top)
        e = support.getWorldSpace(self.fk_mid)
        w = support.getWorldSpace(self.fk_bot)
        # now we have the translate vectors, but we need to find the halfway and quarter-way points between top and mid, and mid and bot.
        midUpper = support.getVectorMult(s,e,0.5)
        midLower = support.getVectorMult(e,w,0.5)
        quarterUpper = support.getVectorMult(s,e,0.25)
        quarterLower = support.getVectorMult(e,w,0.75)
        # midUpper and midLower are in the correct positions, but the actual curve won't draw through the middle joint unless they are parallel to the "e" control point. is there a way to fix this...?
        limbCurve = cmds.curve(d=3,ws=1,p=[(s[0],s[1],s[2]),(quarterUpper[0],quarterUpper[1],quarterUpper[2]),(midUpper[0],midUpper[1],midUpper[2]),(e[0],e[1],e[2]),
                                           (midLower[0],midLower[1],midLower[2]),(quarterLower[0],quarterLower[1],quarterLower[2]),(w[0],w[1],w[2])])
        # the points around the center CV (2 and 4) need to be in line with the middle CV [3] to form a straight line, otherwise the limb will not be able to straighten properly.
        # to do this, cluster points 2 and 4, snap the cluster to CV 3, then delete the cluster.
        cmds.select(limbCurve+'.cv[2]')
        cmds.select(limbCurve+'.cv[4]',add=1)
        tempCluster = cmds.cluster()[1]
        cmds.pointConstraint(self.midTemplate,tempCluster)
        self.makeBindResults.append(limbCurve)
        # rebuild the curve to ensure 0-1 parameterization.
        # -rebuildCurve -ch 1 -rpo 1 -rt 4 -end 1 -kr 0 -kcp 1 -kep 1 -kt 0 -s 3 -d 3 -tol 0.01
        cmds.rebuildCurve(limbCurve,ch=1,rpo=1,rt=4,end=1,kr=0,kcp=1,kep=1,kt=0,s=3,d=3,tol=0.01)
        cmds.delete(limbCurve,ch=1)
        cmds.delete(tempCluster)
        cmds.parent(limbCurve,self.gutsGrp)
        # for each joint in numJoints, attach it to the curve via a motionPath. divide 1/(numJoints-1) to find the necessary U increment for the motionPaths (-1 because of the joint at U=0).
        # as we create joints, if they are above the midjoint (near the shoulder), add them to self.upperJoints. otherwise add to self.lowerJoints.
        # find the midpoint using nearestPointOnCurve node.
        np = cmds.createNode('nearestPointOnCurve')
        self.makeBindResults.append(np)
        limbCurveShape = cmds.listRelatives(limbCurve,s=1)[0]
        cmds.connectAttr(limbCurveShape+'.worldSpace[0]',np+'.inputCurve',f=1)
        cmds.connectAttr(self.midTemplate+'.translate',np+'.inPosition')
        midpoint = cmds.getAttr(np+'.result.parameter')
        cmds.delete(np)
        print 'generated limb curve for Limb %s' % (self.name)
        print 'limb curve midpoint is %f' % (midpoint)
        # if bindSet is true, create an object set that contains the joints for easy pickings later.
        setName = self.name+'_bindJoints'
        if bindSet:
            cmds.select(cl=1)
            cmds.sets(n=setName,em=1)
        # now we make the locators that will sit on the motion path and hold the joints. there need to be two up vector locators, one for each half of the limb,
        # that are constrained to the upper and mid joints respectively.
        # since the joints are by default oriented along X and are using +Z as the secondary axis, we can move locators "forward" along the correct plane by moving in -Y in local space.
        self.upperUp = cmds.spaceLocator(n=self.name+'_upper_up')[0]
        self.lowerUp = cmds.spaceLocator(n=self.name+'_lower_up')[0]
        cmds.parent(self.upperUp,self.fk_top)
        cmds.parent(self.lowerUp,self.fk_mid)
        cmds.setAttr(self.upperUp+'.tx',0)
        cmds.setAttr(self.upperUp+'.ty',0)
        cmds.setAttr(self.upperUp+'.tz',0)
        cmds.setAttr(self.upperUp+'.rx',0)
        cmds.setAttr(self.upperUp+'.ry',0)
        cmds.setAttr(self.upperUp+'.rz',0)
        cmds.setAttr(self.lowerUp+'.tx',0)
        cmds.setAttr(self.lowerUp+'.ty',0)
        cmds.setAttr(self.lowerUp+'.tz',0)
        cmds.setAttr(self.lowerUp+'.rx',0)
        cmds.setAttr(self.lowerUp+'.ry',0)
        cmds.setAttr(self.lowerUp+'.rz',0)
        upperDist = cmds.getAttr(self.fk_mid+'.tx')
        cmds.move(upperDist*-1,self.upperUp,y=1,wd=1,os=1,r=1)
        lowerDist = cmds.getAttr(self.fk_bot+'.tx')
        cmds.move(lowerDist*-1,self.lowerUp,y=1,wd=1,os=1,r=1)
        cmds.parent(self.upperUp,self.gutsGrp)
        cmds.parent(self.lowerUp,self.gutsGrp)
        # we'll constrain these later when we link the skeletons.
        for i in range(0,numJoints):
            loc = cmds.spaceLocator(n=self.name+'_bind_pivot_'+str(i))[0]
            self.makeBindResults.append(loc)
            # attach to the motion path, then delete any keys on the "U value" parameter.
            # using a worldUp vector will not work if the overall arm is pivoted (which is going to happen all the time). instead we will need an up vector object
            # for each locator that is positioned directly above the locator and parented to self.pivot (i think...)
            uVal = (float(i)/float(numJoints-1))
            # in order for the forward aim axis to know what it's aiming at, we need a little bit of extra curve at the beginning and end. so don't attach
            # anything to U=0 or U=1.
            if uVal == 0.0: uVal = 0.001
            if uVal == 1.0: uVal = 0.999
            upObject = ''
            if uVal < 0.5:
                upObject = self.upperUp
            else:
                upObject = self.lowerUp
            mpath = cmds.pathAnimation(loc,c=limbCurve,fm=1,f=1,fa='x',ua='y',wut='object',wuo=upObject,wu=(0,1,0))
            self.makeBindResults.append(mpath)
            # get the anim curve so we can delete it later.
            animCurves = cmds.listConnections(mpath+'.uValue')
            for x in animCurves:
                cmds.delete(x)
            cmds.setAttr(mpath+'.uValue',uVal)
            # locator is in place. now create a joint and add it to the appropriate array. use the existing templates to align the joints correctly.
            bindJnt = []
            if uVal <= 0.5:
                # use upper template.
                bindJnt = cmds.duplicate(self.topTemplate,po=1,n=self.name+'_bind_upper_'+str(i))
                self.upperJoints.append(bindJnt[0])
            else:
                bindJnt = cmds.duplicate(self.topTemplate,po=1,n=self.name+'_bind_lower_'+str(i))
                self.lowerJoints.append(bindJnt[0])
            cmds.parent(bindJnt[0],loc)
            cmds.setAttr(bindJnt[0]+'.tx',0)
            cmds.setAttr(bindJnt[0]+'.ty',0)
            cmds.setAttr(bindJnt[0]+'.tz',0)
            cmds.setAttr(bindJnt[0]+'.rx',0)
            cmds.setAttr(bindJnt[0]+'.ry',0)
            cmds.setAttr(bindJnt[0]+'.rz',0)
            if bindSet:
                cmds.sets(bindJnt[0],add=setName)
            cmds.parent(loc,self.gutsGrp)
            # connect the scale of self.pivot to the scale of each locator to allow for global scaling.
            # cmds.connectAttr(self.pivot+'.scale',loc+'.scale')
            cmds.scaleConstraint(self.pivot,loc)
        # now, to cluster the curve. points 0-1 are the shoulder. 2-4 are the elbow. 5-6 are the wrist. each cluster should be grouped, with the pivot placed on the respective joint.
        # the elbow needs two identical groups nested inside each other: the outer group will be parent constrained to both shoulder joints, while the inner group will be constrained to both shoulders as well
        # but also receive 50% of Y rotation from the active elbow.
        cmds.select(limbCurve+'.cv[0:1]')
        topCluster = cmds.cluster(n=self.name+'_topCluster')[1]
        cmds.select(limbCurve+'.cv[2:4]')
        midCluster = cmds.cluster(n=self.name+'_midCluster')[1]
        cmds.select(limbCurve+'.cv[5:6]')
        botCluster = cmds.cluster(n=self.name+'_botCluster')[1]
        # cluster groups
        self.topClusterGrp = cmds.group(em=1,n=self.name+'_'+self.topName+'_clusterGrp')
        self.midClusterGrp = cmds.group(em=1,n=self.name+'_'+self.midName+'_clusterOffsetGrp')
        self.midClusterInnerGrp = cmds.group(em=1,n=self.name+'_'+self.midName+'_clusterGrp')
        self.midClusterTrackerGrp = cmds.group(em=1,n=self.name+'_'+self.midName+'_clusterTrackerGrp')
        self.botClusterGrp = cmds.group(em=1,n=self.name+'_'+self.botName+'_clusterGrp')
        pc = cmds.parentConstraint(self.ik_top,self.topClusterGrp)
        cmds.delete(pc)
        cmds.parent(topCluster,self.topClusterGrp)
        cmds.parent(self.midClusterInnerGrp,self.midClusterTrackerGrp)
        cmds.parent(self.midClusterTrackerGrp,self.midClusterGrp)
        pc = cmds.parentConstraint(self.ik_mid,self.midClusterGrp)
        cmds.delete(pc)
        cmds.parent(midCluster,self.midClusterInnerGrp)
        pc = cmds.parentConstraint(self.ik_bot,self.botClusterGrp)
        cmds.delete(pc)
        cmds.parent(botCluster,self.botClusterGrp)
        # now parent groups to the global limb pivot
        cmds.parent(self.topClusterGrp,self.pivot)
        cmds.parent(self.midClusterGrp,self.pivot)
        cmds.parent(self.botClusterGrp,self.pivot)
        # add attribute to self.pivot to control the scale of the midClusterGrp
        cmds.addAttr(self.pivot,ln='midCurveScale',at='float',min=0.0,max=2.0,k=1)
        cmds.addAttr(self.pivot,ln='topCurveScale',at='float',min=0.0,max=2.0,k=1)
        cmds.addAttr(self.pivot,ln='botCurveScale',at='float',min=0.0,max=2.0,k=1)
        cmds.addAttr(self.pivot,ln='showFKControls',at='bool',dv=1)
        cmds.addAttr(self.pivot,ln='showIKControls',at='bool',dv=1)
        cmds.setAttr(self.pivot+'.midCurveScale',cb=1)
        cmds.setAttr(self.pivot+'.topCurveScale',cb=1)
        cmds.setAttr(self.pivot+'.botCurveScale',cb=1)
        cmds.setAttr(self.pivot+'.midCurveScale',k=1,l=0)
        cmds.setAttr(self.pivot+'.topCurveScale',k=1,l=0)
        cmds.setAttr(self.pivot+'.botCurveScale',k=1,l=0)
        cmds.connectAttr(self.pivot+'.midCurveScale',self.midClusterInnerGrp+'.scaleX')
        cmds.connectAttr(self.pivot+'.midCurveScale',self.midClusterInnerGrp+'.scaleY')
        cmds.connectAttr(self.pivot+'.midCurveScale',self.midClusterInnerGrp+'.scaleZ')
        cmds.connectAttr(self.pivot+'.topCurveScale',self.topClusterGrp+'.scaleX')
        cmds.connectAttr(self.pivot+'.topCurveScale',self.topClusterGrp+'.scaleY')
        cmds.connectAttr(self.pivot+'.topCurveScale',self.topClusterGrp+'.scaleZ')
        cmds.connectAttr(self.pivot+'.botCurveScale',self.botClusterGrp+'.scaleX')
        cmds.connectAttr(self.pivot+'.botCurveScale',self.botClusterGrp+'.scaleY')
        cmds.connectAttr(self.pivot+'.botCurveScale',self.botClusterGrp+'.scaleZ')

        # hide cluster groups.
        cmds.editDisplayLayerMembers(self.gutsLayer,self.topClusterGrp,self.midClusterInnerGrp,self.botClusterGrp,limbCurve)
        print 'created bind skeleton and cluster groups for limb %s' % (self.name)


    def undoMakeBindSkeleton(self,*args):
        # since maya is fucking retarded and can't undo motion paths, we have to do it manually.
        for i in self.makeBindResults:
            try:
                print 'attempting to delete: %s' % (i)
                cmds.delete(i)
            except TypeError,RuntimeError:
                pass
        self.makeBindResults = []

    def linkControlToBind(self,*args):
        # link the control arms to the bind skeleton via the clusters. use condition nodes to manage binary connections.
        # also set up the connections from the elbow and shoulder to the midClusterTrackerGrp.
        # self.pivot will contain the message attributes that link controls and nodes together for ik/fk switching.
        topPC = cmds.parentConstraint(self.fk_top,self.topClusterGrp,mo=1)[0]
        topPC = cmds.parentConstraint(self.ik_top,self.topClusterGrp,mo=1)[0]
        midPC = cmds.parentConstraint(self.fk_top,self.midClusterGrp,mo=1)[0]
        midPC = cmds.parentConstraint(self.ik_top,self.midClusterGrp,mo=1)[0]
        botPC = cmds.parentConstraint(self.fk_bot,self.botClusterGrp,mo=1)[0]
        botPC = cmds.parentConstraint(self.ik_bot,self.botClusterGrp,mo=1)[0]
        # create condition nodes to control constraints. first term is 0 for FK, 1 for IK. second term is 1. color if true is r=0,g=1, which outputs to the weight channels of the constraint (fk=0,ik=1).
        # color if false is r=1,g=0.'
        # top switch.
        top_IKFK = cmds.createNode('condition',n=self.name+'_'+self.topName+'_cluster_IKFK_switch')
        cmds.setAttr(top_IKFK+'.colorIfTrueR',0.0)
        cmds.setAttr(top_IKFK+'.colorIfTrueG',1.0)
        cmds.setAttr(top_IKFK+'.colorIfFalseR',1.0)
        cmds.setAttr(top_IKFK+'.colorIfFalseG',0.0)
        cmds.setAttr(top_IKFK+'.secondTerm',1)
        # middle switch.
        mid_IKFK = cmds.duplicate(top_IKFK,n=self.name+'_'+self.midName+'_cluster_IKFK_switch')[0]
        # bottom switch.
        bot_IKFK = cmds.duplicate(top_IKFK,n=self.name+'_'+self.botName+'_cluster_IKFK_switch')[0]
        # connect condition output to constraint weights.
        cmds.connectAttr(top_IKFK+'.outColorR',topPC+'.'+self.fk_top+'W0')
        cmds.connectAttr(top_IKFK+'.outColorG',topPC+'.'+self.ik_top+'W1')
        cmds.connectAttr(mid_IKFK+'.outColorR',midPC+'.'+self.fk_top+'W0')
        cmds.connectAttr(mid_IKFK+'.outColorG',midPC+'.'+self.ik_top+'W1')
        cmds.connectAttr(bot_IKFK+'.outColorR',botPC+'.'+self.fk_bot+'W0')
        cmds.connectAttr(bot_IKFK+'.outColorG',botPC+'.'+self.ik_bot+'W1')
        # add the ikfk switch attribute to self.pivot and connect it to firstTerm of all conditions
        cmds.addAttr(self.pivot,ln='IK_FK_switch',at='byte')
        cmds.setAttr(self.pivot+'.IK_FK_switch',cb=1,l=0)
        cmds.setAttr(self.pivot+'.IK_FK_switch',k=1)
        cmds.connectAttr(self.pivot+'.IK_FK_switch',top_IKFK+'.firstTerm')
        cmds.connectAttr(self.pivot+'.IK_FK_switch',mid_IKFK+'.firstTerm')
        cmds.connectAttr(self.pivot+'.IK_FK_switch',bot_IKFK+'.firstTerm')
        # the elbowClusterTracker gets half the rotate value of the active elbow. elbow.rotate -> condition.colorIfTrue/False, secondTerm=1, etc
        mid_rotateCondition = cmds.createNode('condition',n=self.name+'_'+self.midName+'_midTracker_IKFK_switch')
        mid_rotateMult = cmds.createNode('multiplyDivide',n=self.name+'_'+self.midName+'_midTracker_rotate_divide')
        cmds.connectAttr(self.fk_mid+'.rotate',mid_rotateCondition+'.colorIfFalse')
        cmds.connectAttr(self.ik_mid+'.rotate',mid_rotateCondition+'.colorIfTrue')
        cmds.setAttr(mid_rotateCondition+'.secondTerm',1)
        cmds.connectAttr(mid_rotateCondition+'.outColor',mid_rotateMult+'.input2')
        cmds.setAttr(mid_rotateMult+'.input1X',0.5)
        cmds.setAttr(mid_rotateMult+'.input1Y',0.5)
        cmds.setAttr(mid_rotateMult+'.input1Z',0.5)
        # now output from rotateMult to the elbowClusterTracker
        cmds.connectAttr(mid_rotateMult+'.output',self.midClusterTrackerGrp+'.rotate')
        # connect the mid_rotateCondition to the ikfk switch
        cmds.connectAttr(self.pivot+'.IK_FK_switch',mid_rotateCondition+'.firstTerm')
        # constrain the lowerUp and upperUp locators to both skeletons, make conditions and connect them to the IK FK switch.
        upperPC = cmds.parentConstraint(self.fk_top,self.ik_top,self.upperUp,mo=1)[0]
        lowerPC = cmds.parentConstraint(self.fk_mid,self.ik_mid,self.lowerUp,mo=1)[0]
        upperUpCond = cmds.createNode('condition',n=self.name+'_upperUp_switch')
        lowerUpCond = cmds.createNode('condition',n=self.name+'_lowerUp_switch')
        cmds.setAttr(upperUpCond+'.secondTerm',1)
        cmds.setAttr(upperUpCond+'.colorIfTrueR',0.0)
        cmds.setAttr(upperUpCond+'.colorIfFalseR',1.0)
        cmds.setAttr(upperUpCond+'.colorIfTrueG',1.0)
        cmds.setAttr(upperUpCond+'.colorIfFalseG',0.0)
        cmds.setAttr(lowerUpCond+'.secondTerm',1)
        cmds.setAttr(lowerUpCond+'.colorIfTrueR',0.0)
        cmds.setAttr(lowerUpCond+'.colorIfFalseR',1.0)
        cmds.setAttr(lowerUpCond+'.colorIfTrueG',1.0)
        cmds.setAttr(lowerUpCond+'.colorIfFalseG',0.0)
        cmds.connectAttr(self.pivot+'.IK_FK_switch',upperUpCond+'.firstTerm')
        cmds.connectAttr(self.pivot+'.IK_FK_switch',lowerUpCond+'.firstTerm')
        cmds.connectAttr(upperUpCond+'.outColorR',upperPC+'.'+self.fk_top+'W0')
        cmds.connectAttr(upperUpCond+'.outColorG',upperPC+'.'+self.ik_top+'W1')
        cmds.connectAttr(lowerUpCond+'.outColorR',lowerPC+'.'+self.fk_mid+'W0')
        cmds.connectAttr(lowerUpCond+'.outColorG',lowerPC+'.'+self.ik_mid+'W1')
        print 'bind skeleton is now constrained to control skeletons for limb %s' % (self.name)

    def twistSetup(self,twistType='normal',*args):
        # setup twist on the bind joints. if twistType is normal, the upper bind joints absorb twist backwards from the elbow (start with last index and move back), while the lower joints absorb upwards from the wrist.
        # if twistType is total, all joints absorb twist upwards from the wrist.
        # the percentage of twist is driverJointRotate*(1/numJointsTotal)*bindJointNum = bindJointNum*driverJointRotate / numJointsTotal
        # numJoints = len(self.upperJoints)+len(self.lowerJoints)
        if twistType=='normal':
            for index,jnt in enumerate(self.upperJoints):
                # both top joints output to a condition node, connected to self.pivot like the others. the condition node outputs rotateX to a mult/div node that multiplies the rotation by index/numJoints.
                numJoints = len(self.upperJoints)
                twistCond = cmds.createNode('condition',n=self.name+'_twistSwitchUpper_'+str(index))
                cmds.connectAttr(self.fk_top+'.rx',twistCond+'.colorIfFalseR')
                cmds.connectAttr(self.ik_top+'.rx',twistCond+'.colorIfTrueR')
                cmds.setAttr(twistCond+'.secondTerm',1)
                cmds.connectAttr(self.pivot+'.IK_FK_switch',twistCond+'.firstTerm')
                md1 = cmds.createNode('multiplyDivide',n=self.name+'_twistMultUpper_'+str(index))
                cmds.connectAttr(twistCond+'.outColorR',md1+'.input1X')
                cmds.setAttr(md1+'.input2X',index+1)
                md2 = cmds.createNode('multiplyDivide',n=self.name+'_twistDivUpper_'+str(index))
                cmds.setAttr(md2+'.operation',2)
                cmds.setAttr(md2+'.input2X',numJoints)
                cmds.connectAttr(md1+'.outputX',md2+'.input1X')
                cmds.connectAttr(md2+'.outputX',jnt+'.rotateX')
            for index,jnt in enumerate(self.lowerJoints):
                numJoints = len(self.lowerJoints)
                twistCond = cmds.createNode('condition',n=self.name+'_twistSwitchLower_'+str(index))
                cmds.connectAttr(self.fk_bot+'.rx',twistCond+'.colorIfFalseR')
                cmds.connectAttr(self.ik_bot+'.rx',twistCond+'.colorIfTrueR')
                cmds.setAttr(twistCond+'.secondTerm',1)
                cmds.connectAttr(self.pivot+'.IK_FK_switch',twistCond+'.firstTerm')
                md1 = cmds.createNode('multiplyDivide',n=self.name+'_twistMultLower_'+str(index))
                cmds.connectAttr(twistCond+'.outColorR',md1+'.input1X')
                cmds.setAttr(md1+'.input2X',index+1)
                md2 = cmds.createNode('multiplyDivide',n=self.name+'_twistDivLower_'+str(index))
                cmds.setAttr(md2+'.operation',2)
                cmds.setAttr(md2+'.input2X',numJoints)
                cmds.connectAttr(md1+'.outputX',md2+'.input1X')
                cmds.connectAttr(md2+'.outputX',jnt+'.rotateX')
        else:
            allJoints = []
            allJoints.extend(self.upperJoints)
            allJoints.extend(self.lowerJoints)
            for index,jnt in enumerate(allJoints):
                numJoints = len(allJoints)
                twistCond = cmds.createNode('condition',n=self.name+'_twistSwitch_'+str(index))
                cmds.connectAttr(self.fk_bot+'.rx',twistCond+'.colorIfFalseR')
                cmds.connectAttr(self.ik_bot+'.rx',twistCond+'.colorIfTrueR')
                cmds.setAttr(twistCond+'.secondTerm',1)
                cmds.connectAttr(self.pivot+'.IK_FK_switch',twistCond+'.firstTerm')
                md1 = cmds.createNode('multiplyDivide',n=self.name+'_twistMult_'+str(index))
                cmds.connectAttr(twistCond+'.outColorR',md1+'.input1X')
                cmds.setAttr(md1+'.input2X',index+1)
                md2 = cmds.createNode('multiplyDivide',n=self.name+'_twistDiv_'+str(index))
                cmds.setAttr(md2+'.operation',2)
                cmds.setAttr(md2+'.input2X',numJoints)
                cmds.connectAttr(md1+'.outputX',md2+'.input1X')
                cmds.connectAttr(md2+'.outputX',jnt+'.rotateX')
        print '%s twist setup completed for limb %s' % (twistType,self.name)

    # next up is to fit controls. this will probably take several different functions to figure out, some of which may not belong to this class.
    # FK controls: shoulder, elbow, wrist.
    # IK controls: ikHandle, pole vector.
    # the best way to handle this is to probably make an initial state for each controller at once, switch to a viewing mode that allows
    # them to be seen easily, let the user scale/rotate/whatever each controller, then wait for user input to apply the controllers.

    def setupControls(self,fkColor=13,ikColor=6,curveColor=14,*args):
        # automatically build initial controls and tie them to the overall Limb object.
        self.fkTopCtrl = support.makeCurve('flatCube',self.name+'_'+self.topName+'Ctrl',self.fk_top,True,fkColor)
        self.fkMidCtrl = support.makeCurve('flatCube',self.name+'_'+self.midName+'Ctrl',self.fk_mid,True,fkColor)
        self.fkBotCtrl = support.makeCurve('flatCube',self.name+'_'+self.botName+'Ctrl',self.fk_bot,True,fkColor)
        self.ik_ctrl = support.makeCurve('cube',self.name+'_'+self.botName+'IK_Ctrl',self.ik_bot,True,ikColor)
        self.ik_pvCtrl = support.makeCurve('spike',self.name+'_'+self.midName+'_poleVectorCtrl',self.ik_poleVector,True,ikColor)
        # curveCtrl will be placed halfway between the elbow and polevector for starters.
        n0,n1,n2 = support.getWorldSpace(self.fkMidCtrl)
        n = (n0,n1,n2)
        m0,m1,m2 = support.getWorldSpace(self.ik_pvCtrl)
        m = (m0,m1,m2)
        tx,ty,tz = support.getVectorMult(m,n,0.75)
        self.curveCtrl = support.makeCurve('roundCube',self.name+'_curveCtrl',self.midClusterTrackerGrp,True,curveColor)
        loc = cmds.spaceLocator()[0]
        cmds.setAttr(loc+'.tx',tx)
        cmds.setAttr(loc+'.ty',ty)
        cmds.setAttr(loc+'.tz',tz)
        pc = cmds.pointConstraint(loc,self.curveCtrl)
        cmds.delete(pc)
        cmds.delete(loc)
        cmds.setAttr(self.curveCtrl+'.rz',-90)
        cmds.setAttr(self.ik_pvCtrl+'.rz',-90)
        print 'prebuilt controls for limb %s' % (self.name)

    # now a function to apply the controls.

    def applyControls(self,*args):
        # constrains control skeletons to control objects. adds message attributes to self.pivot to store controller names for ik/fk switch.
        # parents fk controls in correct hierarchy. also duplicates pole vector as self.fk_poleVectorGuide and parents to fk_top.
        support.applyCtrl(self.fkTopCtrl,self.fk_top,1,1,1)
        support.applyCtrl(self.fkMidCtrl,self.fk_mid,1,1,1)
        support.applyCtrl(self.fkBotCtrl,self.fk_bot,1,1,1)
        support.applyCtrl(self.ik_ctrl,self.ik_botHandle,1,0,0)
        support.applyCtrl(self.ik_ctrl,self.ik_bot,0,1,1)
        support.applyCtrl(self.ik_pvCtrl,self.ik_poleVector,1,0,0)
        # get parent of curveCtrl and nuke it
        curveCtrlParent = cmds.pickWalk(self.curveCtrl,d='up')
        cmds.parent(self.curveCtrl,w=1)
        cmds.delete(curveCtrlParent)
        cmds.parent(self.curveCtrl,self.midClusterTrackerGrp)
        cmds.makeIdentity(self.curveCtrl,a=1,t=1,r=1,s=1)
        cmds.delete(self.curveCtrl,ch=1)
        cmds.parent(self.midClusterInnerGrp,self.curveCtrl)
        # reset the pivot of curveCtrl to match the elbow exactly.
        v0,v1,v2 = support.getWorldSpace(self.fk_mid)
        cmds.xform(self.curveCtrl,ws=1,rp=[v0,v1,v2])
        cmds.xform(self.curveCtrl,ws=1,sp=[v0,v1,v2])
        cmds.addAttr(self.pivot,ln='fkTopCtrl',at='message')
        cmds.addAttr(self.pivot,ln='fkMidCtrl',at='message')
        cmds.addAttr(self.pivot,ln='fkBotCtrl',at='message')
        cmds.addAttr(self.pivot,ln='ik_ctrl',at='message')
        cmds.addAttr(self.pivot,ln='ik_pvCtrl',at='message')
        cmds.addAttr(self.pivot,ln='curveCtrl',at='message')
        cmds.connectAttr(self.fkTopCtrl+'.message',self.pivot+'.fkTopCtrl')
        cmds.connectAttr(self.fkMidCtrl+'.message',self.pivot+'.fkMidCtrl')
        cmds.connectAttr(self.fkBotCtrl+'.message',self.pivot+'.fkBotCtrl')
        cmds.connectAttr(self.ik_ctrl+'.message',self.pivot+'.ik_ctrl')
        cmds.connectAttr(self.ik_pvCtrl+'.message',self.pivot+'.ik_pvCtrl')
        cmds.connectAttr(self.curveCtrl+'.message',self.pivot+'.curveCtrl')
        # now you have to handle parenting of the FK hierarchy.
        fk_topGrp = cmds.listRelatives(self.fkTopCtrl,p=1)[0]
        fk_midGrp = cmds.listRelatives(self.fkMidCtrl,p=1)[0]
        fk_botGrp = cmds.listRelatives(self.fkBotCtrl,p=1)[0]
        ik_ctrlGrp = cmds.listRelatives(self.ik_ctrl,p=1)[0]
        ik_pvCtrlGrp = cmds.listRelatives(self.ik_pvCtrl,p=1)[0]
        cmds.parent(fk_botGrp,self.pivot)
        cmds.parent(fk_midGrp,self.pivot)
        cmds.parent(fk_topGrp,self.pivot)
        cmds.parentConstraint(self.fkTopCtrl,fk_midGrp,mo=1)
        cmds.parentConstraint(self.fkMidCtrl,fk_botGrp,mo=1)
        self.fk_poleVectorGuide = cmds.duplicate(self.ik_poleVector,n=self.name+'_fk_poleVectorGuide')[0]
        cmds.addAttr(self.pivot,ln='fk_poleVectorGuide',at='message')
        cmds.connectAttr(self.fk_poleVectorGuide+'.message',self.pivot+'.fk_poleVectorGuide')
        cmds.parent(self.fk_poleVectorGuide,self.fk_top)
        cmds.parent(ik_ctrlGrp,self.pivot)
        cmds.parent(ik_pvCtrlGrp,self.pivot)
        cmds.scaleConstraint(self.fkTopCtrl,self.fkMidCtrl)
        # the curveCtrl will control all the curve and ik/fk switchy stuff, instead of self.pivot. so make those connections.
        cmds.connectAttr(self.pivot+'.showFKControls',self.fkTopCtrl+'.visibility')
        cmds.connectAttr(self.pivot+'.showFKControls',self.fkMidCtrl+'.visibility')
        cmds.connectAttr(self.pivot+'.showFKControls',self.fkBotCtrl+'.visibility')
        cmds.connectAttr(self.pivot+'.showIKControls',self.ik_ctrl+'.visibility')
        cmds.connectAttr(self.pivot+'.showIKControls',self.ik_pvCtrl+'.visibility')
        cmds.addAttr(self.curveCtrl,ln='IK_FK_switch',at='bool')
        cmds.addAttr(self.curveCtrl,ln='showFKControls',at='bool',dv=1)
        cmds.addAttr(self.curveCtrl,ln='showIKControls',at='bool',dv=1)
        cmds.addAttr(self.curveCtrl,ln='midCurveScale',at='float',min=0,max=2)
        cmds.addAttr(self.curveCtrl,ln='topCurveScale',at='float',min=0,max=2)
        cmds.addAttr(self.curveCtrl,ln='botCurveScale',at='float',min=0,max=2)
        cmds.addAttr(self.curveCtrl,ln='minStretch',at='float',min=0.01,max=1,dv=1)
        cmds.addAttr(self.curveCtrl,ln='maxStretch',at='float',min=1,dv=1)
        cmds.addAttr(self.curveCtrl,ln='preserveVolume',at='float',min=0,max=1,dv=1)
        cmds.addAttr(self.curveCtrl,ln='volumeCoefficient',at='float',min=0.01,max=1,dv=0.5)
        cmds.addAttr(self.curveCtrl,ln='stretchThresholdLength',at='float',dv=self.getStretchDistance())
        chans = ['IK_FK_switch','midCurveScale','topCurveScale','botCurveScale','showFKControls','showIKControls']
        for i in chans:
            cmds.setAttr(self.curveCtrl+'.'+i,cb=1)
            cmds.setAttr(self.curveCtrl+'.'+i,k=1)
            cmds.connectAttr(self.curveCtrl+'.'+i,self.pivot+'.'+i)
        # now that controls are set up, if there is a self.attachPoint, we can start constraining everything.
        if self.attachPoint != '':
            # the top IK joint and FK controller should be parent constrained to this attachment.
            cmds.parentConstraint(self.attachPoint,fk_topGrp)
            cmds.parentConstraint(self.attachPoint,self.ik_top)
        print 'controls applied for limb %s!' % (self.name)

    # once controls are applied we can activate squash/stretch.

    def getStretchDistance(self,*args):
        sel = cmds.ls(sl=1)
        # calculate the distance between the shoulder and ik hand control.
        d1 = cmds.getAttr(self.fk_mid+'.tx')
        d2 = cmds.getAttr(self.fk_bot+'.tx')
        return float(d1+d2)
        cmds.select(sel)

    def makeStretchy(self,min=1,max=3,stretchDist=False,*args):
        # set up squash and stretch for IK. global scale is determined by self.pivot.
        # the user should pull the IK control outwards so that the arm is fully stretched before running this function.
        # in order for global scale to calculate properly, self.pivot must be in a consistent hierarchy, meaning it can't be reparented to another scaling transform
        # unless it is scale constrained to something.
        topLoc = cmds.spaceLocator(n=self.name+'_stretchy_topLoc')[0]
        botLoc = cmds.spaceLocator(n=self.name+'_stretchy_botLoc')[0]
        cmds.pointConstraint(self.ik_top,topLoc)
        cmds.pointConstraint(self.ik_ctrl,botLoc)
        dist = cmds.createNode('distanceBetween',n=self.name+'_ikStretchDist')
        topLoc = cmds.parent(topLoc,self.gutsGrp)[0]
        botLoc = cmds.parent(botLoc,self.gutsGrp)[0]
        cmds.connectAttr(topLoc+'.translate',dist+'.point1')
        cmds.connectAttr(botLoc+'.translate',dist+'.point2')
        maxDist = float(cmds.getAttr(dist+'.distance'))
        if stretchDist:
            maxDist = self.getStretchDistance()
            print 'maxDist calculated as %f' % (maxDist)
        # this distance is multiplied by global scale in order to figure out the overall stretch amount.
        # globalScale is just the scale of self.pivot. this requires that self.pivot never be parented under a scaling node; it can only
        # be constrained.
        scaleMult = cmds.shadingNode('multiplyDivide',n=self.name+'_globalScaleMult',asUtility=1)
        cmds.connectAttr(self.pivot+'.sx',scaleMult+'.input1X')
        cmds.setAttr(scaleMult+'.input2X',maxDist)
        outputScale = cmds.createNode('multiplyDivide',n=self.name+'_stretchScaleOutput')
        cmds.connectAttr(scaleMult+'.outputX',outputScale+'.input2X')
        cmds.connectAttr(dist+'.distance',outputScale+'.input1X')
        cmds.setAttr(outputScale+'.operation',2)
        # outputScale needs to be clamped by min and max attributes, from self.pivot.
        cmds.addAttr(self.pivot,ln='minStretch',at='float',dv=1.0)
        cmds.addAttr(self.pivot,ln='maxStretch',at='float',dv=3.0)
        cmds.setAttr(self.pivot+'.minStretch',cb=1)
        cmds.setAttr(self.pivot+'.minStretch',k=1)
        cmds.setAttr(self.pivot+'.maxStretch',cb=1)
        cmds.setAttr(self.pivot+'.maxStretch',k=1)
        outputClamp = cmds.createNode('clamp',n=self.name+'_stretchScaleClamp')
        cmds.connectAttr(self.pivot+'.minStretch',outputClamp+'.minR')
        cmds.connectAttr(self.pivot+'.maxStretch',outputClamp+'.maxR')
        cmds.connectAttr(outputScale+'.outputX',outputClamp+'.inputR')
        cmds.connectAttr(outputClamp+'.outputR',self.ik_top+'.sx')
        cmds.connectAttr(outputClamp+'.outputR',self.ik_mid+'.sx')
        # volume preservation. scaleYZ = 1/scaleX^n, where n is 0.5 by default. higher values exaggerate deformation. n minimum is 0.01.
        # use a blendColors node to blend between the calculated scale and normal scale (easier to calculate!!!)
        cmds.addAttr(self.pivot,ln='preserveVolume',at='float',dv=1.0)
        cmds.addAttr(self.pivot,ln='volumeCoefficient',at='float',dv=0.5)
        cmds.addAttr(self.pivot,ln='stretchThresholdLength',at='float',dv=maxDist)
        cmds.connectAttr(self.pivot+'.stretchThresholdLength',scaleMult+'.input2X')
        cmds.setAttr(self.pivot+'.stretchThresholdLength',cb=1)
        cmds.setAttr(self.pivot+'.stretchThresholdLength',k=1)
        cmds.setAttr(self.pivot+'.preserveVolume',cb=1)
        cmds.setAttr(self.pivot+'.preserveVolume',k=1)
        cmds.setAttr(self.pivot+'.volumeCoefficient',cb=1)
        cmds.setAttr(self.pivot+'.volumeCoefficient',k=1)
        scalePower = cmds.createNode('multiplyDivide',n=self.name+'_preserveVolumePower')
        cmds.setAttr(scalePower+'.operation',3)
        cmds.connectAttr(self.pivot+'.volumeCoefficient',scalePower+'.input2X')
        cmds.connectAttr(outputClamp+'.outputR',scalePower+'.input1X')
        powerInvert = cmds.createNode('multiplyDivide',n=self.name+'_preserveVolumeInvert')
        cmds.setAttr(powerInvert+'.operation',2)
        cmds.connectAttr(scalePower+'.outputX',powerInvert+'.input2X')
        cmds.setAttr(powerInvert+'.input1X',1.0)
        # powerInvert outputs the correct scaleY. feed outputX into a blendColors node, with self.pivot.preserveVolume as the "blender" attribute.
        # color2 is white (1,1,1), where color1 is (outputX,1,1)
        blender = cmds.createNode('blendColors',n=self.name+'_preserveVolumeBlend')
        cmds.setAttr(blender+'.color2',1,1,1,type='double3')
        cmds.connectAttr(powerInvert+'.output',blender+'.color1')
        cmds.connectAttr(self.pivot+'.preserveVolume',blender+'.blender')
        # blender.outputR connects to scaleYZ of bind joints. don't scale the topmost or bottom joint in the chain.
        allJoints = []
        allJoints.extend(self.upperJoints[1:])
        allJoints.extend(self.lowerJoints[:-1])
        for jnt in allJoints:
            cmds.connectAttr(blender+'.outputR',jnt+'.sy')
            cmds.connectAttr(blender+'.outputR',jnt+'.sz')
        chans = ['minStretch','maxStretch','preserveVolume','volumeCoefficient','stretchThresholdLength']
        for i in chans:
            cmds.setAttr(self.curveCtrl+'.'+i,cb=1)
            cmds.setAttr(self.curveCtrl+'.'+i,k=1)
            cmds.connectAttr(self.curveCtrl+'.'+i,self.pivot+'.'+i)
        print 'stretchy setup complete for limb %s' % (self.name)

    def cleanupRig(self,*args):
        # post-rigging operations.
        cmds.delete(self.topTemplate)
        cmds.delete(self.midTemplate)
        cmds.editDisplayLayerMembers(self.gutsLayer,self.gutsGrp)
        if cmds.objExists(self.ik_ctrl):
            cmds.setAttr(self.ik_ctrl+'.tx',0)
            cmds.setAttr(self.ik_ctrl+'.ty',0)
            cmds.setAttr(self.ik_ctrl+'.tz',0)
        cmds.setAttr(self.gutsLayer+'.visibility',0)
        print 'cleanup complete for limb %s' % (self.name)
        # auto-hide the guts layer

    def __del__(self,*args):
        # select the group, then removeRig().
        controls = [self.fkTopCtrl,self.fkMidCtrl,self.fkBotCtrl,self.ik_ctrl,self.ik_pvCtrl,self.curveCtrl]
        for i in controls:
            if cmds.objExists(i):
                parent = cmds.pickWalk(i,d='up')
                if cmds.objectType(parent) == 'transform':
                    cmds.delete(parent)
        cmds.select(self.pivot)
        self.cleanupRig()
        newTop,newMid,newBot = removeRig()
        return newTop,newMid,newBot


def removeRig(*args):
    # completely remove a rig while preserving the original skeleton.
    # select the group group and run this function.
    group = cmds.ls(sl=1)[0]
    # test this object to make sure it's a valid rig.
    if not cmds.attributeQuery('hfRig',node=group,ex=1):
        cmds.error('Please select the pivot group of the rig you want to remove.')
    gutsGrp = cmds.listConnections(group+'.hfRig')[0]
    gutsLayer = cmds.listConnections(group+'.gutsLayer')[0]
    fkTopJnt = cmds.listConnections(group+'.fkTopJnt')[0]
    fkMidJnt = cmds.pickWalk(fkTopJnt,direction='down')[0]
    fkBotJnt = cmds.pickWalk(fkMidJnt,direction='down')[0]
    cmds.delete(fkTopJnt,cn=1)
    cmds.delete(fkMidJnt,cn=1)
    cmds.delete(fkBotJnt,cn=1)
    cmds.delete(gutsLayer)
    newTop = cmds.duplicate(fkTopJnt,po=1)[0]
    newMid = cmds.duplicate(fkMidJnt,po=1)[0]
    newBot = cmds.duplicate(fkBotJnt,po=1)[0]
    cmds.rename(newTop,fkTopJnt)
    cmds.rename(newMid,fkMidJnt)
    cmds.rename(newBot,fkBotJnt)
    cmds.parent(newTop,w=1)
    cmds.parent(newMid,newTop)
    cmds.parent(newBot,newMid)
    # now that the old skeleton is preserved, we'll nuke everything else.
    cmds.delete(group)
    cmds.delete(gutsGrp)
    return newTop,newMid,newBot
    print 'removed selected rig.'

# well after all that now it's time for UI code.
# UI limb rigging is in three steps, so there will be three self.tabs: creation/definition, control fitting, finalize/cleanup.

class rigLimbUI:
    def __init__(self,*args):
        # the UI object comes with an attached Limb object, called self.rig.
        self.rig = ''
        self.selControl = ''
        self.rigLimbUI()

    def rigLimbUI(self,*args):
        # UI for rigging a limb.
        windowName = 'hfRig_LimbUI'
        if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
        self.window = cmds.window(windowName,t='hfRig: Create Limb')
        mainForm = cmds.formLayout()
        # tab1: rig creation and basic parameters.
        self.tabs = cmds.tabLayout(parent=mainForm)
        tab1Form = cmds.formLayout(parent=self.tabs,ann='Define the top, middle and bottom joints of your joint chain. The "type" only influences joint naming. Press "preview" to see what the chain will look like with the number of joints specified.')
        # col1: labels.
        col1 = cmds.columnLayout(parent=tab1Form,width=80,cat=['left',0],rs=10)
        nameLabel = cmds.text(l='Name:',fn='boldLabelFont',parent=col1)
        topLabel = cmds.text(l='Shoulder:',fn='boldLabelFont',parent=col1)
        midLabel = cmds.text(l='Elbow:',fn='boldLabelFont',parent=col1)
        botLabel = cmds.text(l='Wrist:',fn='boldLabelFont',parent=col1)
        # col2: controls.
        col2 = cmds.columnLayout(parent=tab1Form,width=100,cat=['left',0],rs=5)
        self.nameCtrl = cmds.textField(w=100,parent=col2,tx='newLimb1')
        self.topCtrl = cmds.textField(w=100,parent=col2)
        self.midCtrl = cmds.textField(w=100,parent=col2)
        self.botCtrl = cmds.textField(w=100,parent=col2)

        # col3: more labels.
        col3 = cmds.columnLayout(parent=tab1Form,width=80,cat=['left',0],rs=12)
        typeLabel = cmds.text(l='Type:',fn='boldLabelFont',parent=col3)
        jointsLabel = cmds.text(l='Joints:',fn='boldLabelFont',parent=col3)
        #twistLabel = cmds.text(l='Twist type:',fn='boldLabelFont',parent=col3)
        # col4: more controls.
        col4 = cmds.columnLayout(parent=tab1Form,width=100,cat=['left',0],rs=5)
        typeCtrl = cmds.optionMenu(w=100,parent=col4,cc=lambda *x: self.changeLimbType(cmds.optionMenu(typeCtrl,q=1,v=1),topLabel,midLabel,botLabel))
        cmds.menuItem(l='Arm')
        cmds.menuItem(l='Leg')
        jointsCtrl = cmds.textField(w=100,tx='5',parent=col4,cc=lambda *x: self.changeJointsNum(jointsCtrl))
        #twistCtrl = cmds.optionMenu(w=100,parent=col4)
        #cmds.menuItem(l='Normal')
        #cmds.menuItem(l='Total')
        previewBtn = cmds.button(w=100,h=35,l='Preview',parent=tab1Form,c=lambda *x: self.previewJoints(cmds.textField(self.nameCtrl,q=1,tx=1),cmds.optionMenu(typeCtrl,q=1,v=1),cmds.textField(jointsCtrl,q=1,tx=1)))
        applyBtn = cmds.button(w=100,h=35,l='Apply >>',parent=tab1Form,bgc=[0.6,0.7,1.0],c=lambda *x: self.doRigSettings(cmds.textField(self.nameCtrl,q=1,tx=1),cmds.optionMenu(typeCtrl,q=1,v=1),cmds.textField(jointsCtrl,q=1,tx=1)))
        fillJointsBtn = cmds.button(w=100,h=35,l='get from selection',parent=tab1Form,c=lambda *x: self.getJoints())
        cancelBtn = cmds.button(w=100,h=35,l='cancel rig',parent=tab1Form,bgc=[1.0,0.6,0.7],c=lambda *x: self.cancelRig())
        tm0 = 5
        tm1 = 120
        tm2 = 216
        lm0 = 5
        lm1 = 95
        lm2 = 250
        lm2_3 = 330
        lm3 = 320
        lm4 = 110
        cmds.formLayout(tab1Form,e=1,attachForm=[(col1,'top',tm0),(col1,'left',lm0),(col2,'top',tm0),(col2,'left',lm4),
                                                 (col3,'top',tm0),(col3,'left',lm2),(col4,'top',tm0),(col4,'left',lm3),
                                                 (previewBtn,'top',tm1),(previewBtn,'left',330),(applyBtn,'top',176),(applyBtn,'left',330),
                                                 (fillJointsBtn,'top',tm1),(fillJointsBtn,'left',lm4),(cancelBtn,'top',216),(cancelBtn,'left',330)])

        # tab2: control setup.
        tab2Form = cmds.formLayout(parent=self.tabs,ann='Select a control and press "Get selected" to modify the shape or color, or to rename the control. You can translate, rotate or scale any controller before applying them to the rig.')
        tm0 = 5
        tm1 = 40
        tm2 = 60
        tm3 = 140
        tm4 = 160
        tm5 = 216
        lm0 = 5
        lm1 = 55
        lm2 = 225
        lm3 = 310
        controlLabel = cmds.text(l='Control:',fn='boldLabelFont',parent=tab2Form)
        controlCtrl = cmds.textField(w=140,parent=tab2Form)
        getCtrl = cmds.button(l='Get selected',w=75,h=25,parent=tab2Form,c=lambda *x: self.getControl(controlCtrl))
        renameCtrl = cmds.button(l='Rename',w=75,h=25,parent=tab2Form,c=lambda *x: self.renameControl(controlCtrl))
        styleLabel = cmds.text(l='Control Styles',fn='boldLabelFont',parent=tab2Form)
        colorLabel = cmds.text(l='Control Colors',fn='boldLabelFont',parent=tab2Form)
        styleGrid = cmds.gridLayout(nc=6,cellWidthHeight=(32,32),parent=tab2Form)
        cmds.symbolButton(i=os.path.join(iconsPath,'arrow.xpm'),c=lambda *x: self.doSwapControl('arrow'))
        cmds.symbolButton(i=os.path.join(iconsPath,'bendedDoubleArrow.xpm'),c=lambda *x: self.doSwapControl('bendedDoubleArrow'))
        cmds.symbolButton(i=os.path.join(iconsPath,'circle.xpm'),c=lambda *x: self.doSwapControl('circle'))
        cmds.symbolButton(i=os.path.join(iconsPath,'cross.xpm'),c=lambda *x: self.doSwapControl('cross'))
        cmds.symbolButton(i=os.path.join(iconsPath,'cube.xpm'),c=lambda *x: self.doSwapControl('cube'))
        cmds.symbolButton(i=os.path.join(iconsPath,'flatCube.xpm'),c=lambda *x: self.doSwapControl('flatCube'))
        cmds.symbolButton(i=os.path.join(iconsPath,'locator.xpm'),c=lambda *x: self.doSwapControl('locator'))
        cmds.symbolButton(i=os.path.join(iconsPath,'orient.xpm'),c=lambda *x: self.doSwapControl('orient'))
        cmds.symbolButton(i=os.path.join(iconsPath,'roundCube.xpm'),c=lambda *x: self.doSwapControl('roundCube'))
        cmds.symbolButton(i=os.path.join(iconsPath,'snow.xpm'),c=lambda *x: self.doSwapControl('snow'))
        cmds.symbolButton(i=os.path.join(iconsPath,'spike.xpm'),c=lambda *x: self.doSwapControl('spike'))
        cmds.symbolButton(i=os.path.join(iconsPath,'square.xpm'),c=lambda *x: self.doSwapControl('square'))
        colorGrid = cmds.palettePort(td=1,dim=[11,3],w=190,h=40,parent=tab2Form)
        for x in range(0,30):
            color = cmds.colorIndex(x+1,q=1)
            cmds.palettePort(colorGrid,e=1,rgb=[x,color[0],color[1],color[2]])
        cmds.palettePort(colorGrid,e=1,redraw=1,cc=lambda *x: self.doChangeControlColor(colorGrid))
        applyBtn = cmds.button(l='Apply >>',w=100,h=35,bgc=[0.6,0.7,1.0],parent=tab2Form,c=lambda *x: self.doApplyControls())
        #backBtn = cmds.button(l='<< Settings',w=95,h=35,parent=tab2Form,c=lambda *x: self.undoControls())
        cancelBtn = cmds.button(l='cancel rig',w=100,h=35,bgc=[1.0,0.6,0.7],parent=tab2Form,c=lambda *x: self.cancelRig())
        cmds.formLayout(tab2Form,e=1,attachForm=[(controlLabel,'top',tm0),(controlLabel,'left',lm0),(controlCtrl,'top',tm0),(controlCtrl,'left',lm1),
                                                 (getCtrl,'top',tm0),(getCtrl,'left',lm2),(renameCtrl,'top',tm0),(renameCtrl,'left',lm3),
                                                 (styleLabel,'top',tm1),(styleLabel,'left',lm0),(styleGrid,'top',tm2),(styleGrid,'left',lm0),
                                                 (colorLabel,'top',tm3),(colorLabel,'left',lm0),(colorGrid,'top',tm4),(colorGrid,'left',lm0),
                                                 (applyBtn,'top',176),(applyBtn,'left',330),
                                                 (cancelBtn,'top',216),(cancelBtn,'left',330)])
        # step 3: stretchy setup and finalizing.
        tm0 = 5
        tm1 = 120
        tm2 = 216
        lm0 = 5
        lm1 = 110
        lm2 = 230
        lm2_3 = 330
        tab3Form = cmds.formLayout(parent=self.tabs,ann='The twist type determines whether the twist works like a human arm ("normal"), or like a tentacle ("total"). "Make stretchy" creates stretchy IK (recommended).')
        col1 = cmds.columnLayout(parent=tab3Form,rs=12)
        twistLabel = cmds.text(l='Twist type:',fn='boldLabelFont',parent=col1)
        stretchLabel = cmds.text(l='Make stretchy:',fn='boldLabelFont',parent=col1)
        col2 = cmds.columnLayout(parent=tab3Form,rs=5)
        twistCtrl = cmds.optionMenu(w=150,parent=col2)
        cmds.menuItem(l='Normal')
        cmds.menuItem(l='Total')
        cmds.menuItem(l='None')
        stretchCtrl = cmds.optionMenu(w=150,parent=col2)
        cmds.menuItem('On')
        cmds.menuItem('Off')
        finishBtn = cmds.button('Finish rig',w=100,h=35,bgc=[0.6,1.0,0.7],parent=tab3Form,c=lambda *x: self.doFinishRig(cmds.optionMenu(twistCtrl,q=1,v=1),cmds.optionMenu(stretchCtrl,q=1,v=1),True))
        #backBtn = cmds.button('<< Controls',w=95,h=35,parent=tab3Form)
        cancelBtn = cmds.button('cancel rig',w=100,h=35,bgc=[1.0,0.6,0.7],parent=tab3Form,c=lambda *x: self.cancelRig())
        cmds.formLayout(tab3Form,e=1,attachForm=[(col1,'top',tm0),(col1,'left',lm0),(col2,'top',tm0),(col2,'left',lm1),
                                                 (finishBtn,'top',176),(finishBtn,'left',330),(cancelBtn,'top',216),(cancelBtn,'left',330)])

        # combine self.tabs.
        cmds.tabLayout(self.tabs,e=1,tv=0,tabLabel=[(tab1Form,'Step 1: Settings'),(tab2Form,'Step 2: Controls'),(tab3Form,'Step 3: Finalize')])
        cmds.showWindow(self.window)
        cmds.window(self.window,e=1,w=436,h=256)
        return self.window

    def changeLimbType(self,limbType,topLabel,midLabel,botLabel,*args):
        # switch labels for dialog.
        if limbType=='Arm':
            cmds.text(topLabel,e=1,l='Shoulder:')
            cmds.text(midLabel,e=1,l='Elbow:')
            cmds.text(botLabel,e=1,l='Wrist:')
            #self.rig.limbType = 'arm'
        else:
            cmds.text(topLabel,e=1,l='Hip:')
            cmds.text(midLabel,e=1,l='Knee:')
            cmds.text(botLabel,e=1,l='Ankle:')
            #self.rig.limbType = 'leg'

    def getJoints(self,*args):
        # get joints from selection and fill the text fields.
        # requires selection of top,mid,bot, in that order.
        sel = cmds.ls(sl=1)
        if len(sel) != 3:
            cmds.error('Select exactly three joints: the top, middle, and bottom joint of your chain, in that order.')
        for i in sel:
            if cmds.objectType(i) != 'joint':
                cmds.error('Select exactly three joints: the top, middle, and bottom joint of your chain, in that order.')
        cmds.textField(self.topCtrl,e=1,tx=sel[0])
        cmds.textField(self.midCtrl,e=1,tx=sel[1])
        cmds.textField(self.botCtrl,e=1,tx=sel[2])

    def previewJoints(self,name,limbType,numJoints,*args):
        # build initial control and bind skeleton. destroy any existing skeleton under the given name.
        top = cmds.textField(self.topCtrl,q=1,tx=1)
        mid = cmds.textField(self.midCtrl,q=1,tx=1)
        bot = cmds.textField(self.botCtrl,q=1,tx=1)
        if not cmds.objExists(top) or not cmds.objExists(mid) or not cmds.objExists(bot):
            cmds.error('Joint names are invalid. Select the top, middle and bottom joints in order and press "get from selection."')
        if self.rig != '':
            # a rig has already been generated
            top,mid,bot = self.rig.__del__()
        # now make a new one
        self.rig = Limb(name,limbType.lower())
        top,mid,bot = self.rig.makeControlSkeletons(top,mid,bot)
        self.rig.makeBindSkeleton(int(numJoints),True)
        cmds.textField(self.topCtrl,e=1,tx=top)
        cmds.textField(self.midCtrl,e=1,tx=mid)
        cmds.textField(self.botCtrl,e=1,tx=bot)
        return True


    def changeJointsNum(self,jointsNumCtrl,*args):
        # make sure there are at least five joints in the chain and validate numeric input.
        txt = cmds.textField(jointsNumCtrl,q=1,tx=1)
        if not txt.isdigit():
            cmds.textField(jointsNumCtrl,e=1,tx='5')
            cmds.error('Invalid input.')
        elif int(txt) < 5:
            cmds.textField(jointsNumCtrl,e=1,tx='5')
            cmds.error('Minimum of 5 joints required.')

    def cancelRig(self,*args):
        self.rig.__del__()
        cmds.deleteUI(self.window)
        self.rig = ''

    def doRigSettings(self,name,limbType,numJoints,*args):
        # apply the rig settings and go ahead to the next tab.
        test = self.previewJoints(name,limbType,numJoints)
        if test:
            # link control to bind, then setup controls
            self.rig.linkControlToBind()
            self.rig.setupControls()
            cmds.tabLayout(self.tabs,e=1,sti=2)

    def getControl(self,ctrl,*args):
        # get the name of the selected control and change the text control to match.
        # return an error if the selected object is not a valid control.
        sel = cmds.ls(sl=1)
        if len(sel) != 1:
            cmds.error('Select a single controller.')
        sel = sel[0]
        if sel != self.rig.fkTopCtrl and sel != self.rig.fkMidCtrl and sel != self.rig.fkBotCtrl and sel != self.rig.ik_ctrl and sel != self.rig.ik_pvCtrl and sel != self.rig.curveCtrl:
            # this isn't a controller.
            cmds.error('Select a single controller.')
        cmds.textField(ctrl,e=1,tx=sel)
        self.selControl = sel

    def renameControl(self,ctrl,*args):
        # get the currently loaded control and give it a new name.
        # update the self.rig entry to match the new name.
        newname = cmds.rename(self.selControl,cmds.textField(ctrl,q=1,tx=1))
        cmds.textField(ctrl,e=1,tx=newname)
        # which control was this?
        if self.selControl == self.rig.fkTopCtrl: self.rig.fkTopCtrl = newname
        if self.selControl == self.rig.fkMidCtrl: self.rig.fkMidCtrl = newname
        if self.selControl == self.rig.fkBotCtrl: self.rig.fkBotCtrl = newname
        if self.selControl == self.rig.ik_ctrl: self.rig.ik_ctrl = newname
        if self.selControl == self.rig.ik_pvCtrl: self.rig.ik_pvCtrl = newname
        if self.selControl == self.rig.curveCtrl: self.rig.curveCtrl = newname
        self.selControl = newname

    def doSwapControl(self,controlType,*args):
        # swap self.selControl with a new controller.
        support.swapCurve(self.selControl,controlType)

    def doChangeControlColor(self,palette,*args):
        # get the index of the color palette and change the color of self.selControl.
        colorIndex = cmds.palettePort(palette,q=1,scc=1)
        support.changeCurveColor(self.selControl,colorIndex+1)

    def doApplyControls(self,*args):
        # apply controls and go ahead to the finalize screen.
        self.rig.applyControls()
        cmds.tabLayout(self.tabs,e=1,sti=3)

    def doFinishRig(self,twistType,stretchy,stretchDist,*args):
        # apply extra effects and end this shit.
        if twistType != 'None':
            self.rig.twistSetup(twistType.lower())
        if stretchy.lower() == 'on':
            self.rig.makeStretchy(1,3,stretchDist)
        # now kill this thing.
        self.rig.cleanupRig()
        cmds.deleteUI(self.window)