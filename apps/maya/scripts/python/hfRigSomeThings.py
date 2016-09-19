# rig some things: the script v0.01
# henry foster (henry@toadstorm.com) 01/26/2012

# TO DO LIST 
#
# +joint locators need a more consistent up vector (something that follows the pivot)
# +total twist type is pinching at the elbow
# +squash/stretch capability
# +stretching fk controls not working... elbow_fk in particular is not scaling as shoulder scales.
#      +this can be solved by turning off elbow_fk.segmentScaleCompensate, but the animator will no longer be able to scale individual components of the limb
#      +real solution: turn off that channel, unparent the FK control hierarchy, use parent constraints instead to mimic behavior
#      +IK elbow scale compensation must be ON for stretchy IK!!!
# +ikfk auto switch
# -cleanup script should lock appropriate channels
# -fk to ik doesn't properly get wrist controller rotations

import maya.cmds as cmds
import maya.mel as mel

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
        if limbType == 'arm':
            self.topName = 'shoulder'
            self.midName = 'elbow'
            self.botName = 'wrist'
        elif limbType == 'leg':
            self.topName = 'hip'
            self.midName = 'knee'
            self.botName = 'ankle'
        self.makeBindResults = []
        self.fk_topCtrl = ''
        self.fk_midCtrl = ''
        self.fk_botCtrl = ''
        self.ik_ctrl = ''
        self.ik_pvCtrl = ''
        # create associated display layer for hiding guts.
        self.gutsLayer = cmds.createDisplayLayer(n=self.name+'_guts')
        self.worldScaleObject = ''
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
        self.pivot = cmds.group(em=1,n=self.name+'_attachPivot')
        cmds.addAttr(self.pivot,ln='hfRig',at='message')
        cmds.connectAttr(self.gutsGrp+'.message',self.pivot+'.hfRig')
        pc = cmds.parentConstraint(top,self.pivot)
        cmds.delete(pc)
        cmds.makeIdentity(self.pivot,a=1,t=1,r=1)
        cmds.delete(self.pivot,ch=1)
        skelGrp = cmds.group(em=1,n=self.name+'_controlSkeletons')
        cmds.parent(skelGrp,self.pivot)
        self.fk_top = cmds.rename(top,self.name+'_FK_'+self.topName)
        self.fk_mid = cmds.rename(mid,self.name+'_FK_'+self.midName)
        self.fk_bot = cmds.rename(bot,self.name+'_FK_'+self.botName)
        cmds.joint(self.fk_top,e=1,oj=orient,sao=secondaryAxis,ch=1,zso=1)
        cmds.joint(self.fk_bot,e=1,oj='none')
        ik_top,ik_mid,ik_bot = cmds.duplicate(self.fk_top,rc=1)
        self.ik_top = cmds.rename(ik_top,self.name+'_IK_'+self.topName)
        self.ik_mid = cmds.rename(ik_mid,self.name+'_IK_'+self.midName)
        self.ik_bot = cmds.rename(ik_bot,self.name+'_IK_'+self.botName)
        topTemp,midTemp,botTemp = cmds.duplicate(self.fk_top,rc=1)
        cmds.delete(botTemp)
        self.midTemplate = cmds.parent(midTemp,w=1)[0]
        self.topTemplate = topTemp
        # tell fk_mid not to nullify scale from parent
        cmds.setAttr(self.fk_mid+'.segmentScaleCompensate',0)
        cmds.setAttr(self.ik_mid+'.segmentScaleCompensate',1)
        # parent skeletons to group for organizing
        cmds.parent(self.fk_top,skelGrp)
        cmds.parent(self.ik_top,skelGrp)
        # now build the IK setup on the IK joints.
        self.ik_botHandle = cmds.ikHandle(sj=self.ik_top,ee=self.ik_bot,sol='ikRPsolver',s='sticky')[0]
        cmds.parent(self.ik_botHandle,self.pivot)
        ik_pvPivot = cmds.group(em=1)
        # build a locator to act as the pole vector and position it according to the joint chain.
        self.ik_poleVector = cmds.spaceLocator(name=self.name+'_pvLoc')[0]
        cmds.parent(self.ik_poleVector,ik_pvPivot)
        pc = cmds.pointConstraint(self.ik_top,self.ik_bot,ik_pvPivot)
        ac = cmds.aimConstraint(self.ik_mid,ik_pvPivot,aimVector=(1,0,0),upVector=(0,1,0),worldUpType='scene')
        # translate the ik_poleVector locator forward a few units down the pointing axis (x). the distance will be the sum of the length of the upper and lower limb.
        xDist = cmds.getAttr(self.ik_mid+'.tx')+cmds.getAttr(self.ik_bot+'.tx')
        cmds.setAttr(self.ik_poleVector+'.tx',xDist)
        # unparent and delete the group.
        cmds.parent(self.ik_poleVector,w=1)
        cmds.delete(ik_pvPivot)
        # create pole vector constraint.
        cmds.poleVectorConstraint(self.ik_poleVector,self.ik_botHandle)
        cmds.parent(self.ik_poleVector,self.pivot)
        # hide things.
        cmds.editDisplayLayerMembers(self.gutsLayer,self.ik_botHandle,self.ik_poleVector,self.gutsGrp)
        cmds.addAttr(self.pivot,ln='fkTopJnt',at='message')
        cmds.connectAttr(self.fk_top+'.message',self.pivot+'.fkTopJnt')
        # make message attributes on self.pivot for the ik/fk switch
        cmds.addAttr(self.pivot,ln='ik_top',at='message')
        cmds.addAttr(self.pivot,ln='ik_mid',at='message')
        cmds.addAttr(self.pivot,ln='ik_bot',at='message')
        cmds.addAttr(self.pivot,ln='fk_bot',at='message')
        cmds.connectAttr(self.ik_top+'.message',self.pivot+'.ik_top')
        cmds.connectAttr(self.ik_mid+'.message',self.pivot+'.ik_mid')
        cmds.connectAttr(self.ik_bot+'.message',self.pivot+'.ik_bot')
        cmds.connectAttr(self.fk_bot+'.message',self.pivot+'.fk_bot')
        print 'generated control skeletons for Limb %s' % (self.name)
        
    def makeBindSkeleton(self,numJoints,bindSet=False,*args):
        # create the NURBS curve that drives the bind skeleton, create clusters and pivots for the clusters,
        # create locators along the curve using motionPaths, place joints parented under the locators. 
        # create a selection set from the bind joints for easy skinning.
        # start by setting up locators to get the worldPosition of the joints.
        # this command tends to break undo, so we'll have to pass all created nodes to a return value so that we can potentially undo later.
        self.makeBindResults = []
        s = getWorldSpace(self.fk_top)
        e = getWorldSpace(self.fk_mid)
        w = getWorldSpace(self.fk_bot)
        # now we have the translate vectors, but we need to find the halfway and quarter-way points between top and mid, and mid and bot.
        midUpper = getVectorMult(s,e,0.5)
        midLower = getVectorMult(e,w,0.5)
        quarterUpper = getVectorMult(s,e,0.25)
        quarterLower = getVectorMult(e,w,0.75)
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
        for i in range(0,numJoints):
            loc = cmds.spaceLocator(n=self.name+'_bind_pivot_'+str(i))[0]
            self.makeBindResults.append(loc)
            # attach to the motion path, then delete any keys on the "U value" parameter.
            # using a worldUp vector will not work if the overall arm is pivoted (which is going to happen all the time). instead we will need an up vector object
            # for each locator that is positioned directly above the locator and parented to self.pivot (i think...)
            mpath = cmds.pathAnimation(loc,c=limbCurve,fm=1,f=1,fa='x',ua='y',wut='objectrotation',wuo=self.pivot,wu=(0,1,0))
            self.makeBindResults.append(mpath)
            # get the anim curve so we can delete it later.
            animCurves = cmds.listConnections(mpath+'.uValue')
            for x in animCurves:
                cmds.delete(x)
            # cmds.disconnectAttr(mpath+'_uValue.output',mpath+'.uValue')
            uVal = (float(i)/float(numJoints-1))
            # in order for the forward aim axis to know what it's aiming at, we need a little bit of extra curve at the beginning and end. so don't attach
            # anything to U=0 or U=1.
            if uVal == 0.0: uVal = 0.01
            if uVal == 1.0: uVal = 0.99
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
        cmds.editDisplayLayerMembers(self.gutsLayer,self.topClusterGrp,self.midClusterGrp,self.botClusterGrp,limbCurve)
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
        self.fkTopCtrl = makeCurve('flatCube',self.name+'_'+self.topName+'Ctrl',self.fk_top,True,fkColor)
        self.fkMidCtrl = makeCurve('flatCube',self.name+'_'+self.midName+'Ctrl',self.fk_mid,True,fkColor)
        self.fkBotCtrl = makeCurve('flatCube',self.name+'_'+self.botName+'Ctrl',self.fk_bot,True,fkColor)
        self.ik_ctrl = makeCurve('cube',self.name+'_'+self.botName+'IK_Ctrl',self.ik_bot,True,ikColor)
        self.ik_pvCtrl = makeCurve('spike',self.name+'_'+self.midName+'_poleVectorCtrl',self.ik_poleVector,True,ikColor)
        # curveCtrl will be placed halfway between the elbow and polevector for starters.
        n0,n1,n2 = getWorldSpace(self.fkMidCtrl)
        n = (n0,n1,n2)
        m0,m1,m2 = getWorldSpace(self.ik_pvCtrl)
        m = (m0,m1,m2)
        tx,ty,tz = getVectorMult(m,n,0.75)
        self.curveCtrl = makeCurve('roundCube',self.name+'_curveCtrl',self.midClusterTrackerGrp,True,curveColor)
        loc = cmds.spaceLocator()[0]
        cmds.setAttr(loc+'.tx',tx)
        cmds.setAttr(loc+'.ty',ty)
        cmds.setAttr(loc+'.tz',tz)
        pc = cmds.pointConstraint(loc,self.curveCtrl)
        cmds.delete(pc)
        cmds.delete(loc)
        cmds.setAttr(self.curveCtrl+'.rz',-90)
        print 'prebuilt controls for limb %s' % (self.name)
        
    # now a function to apply the controls.
    
    def applyControls(self,*args):
        # constrains control skeletons to control objects. adds message attributes to self.pivot to store controller names for ik/fk switch.
        # parents fk controls in correct hierarchy. also duplicates pole vector as self.fk_poleVectorGuide and parents to fk_top.
        applyCtrl(self.fkTopCtrl,self.fk_top,0,1,1)
        applyCtrl(self.fkMidCtrl,self.fk_mid,0,1,1)
        applyCtrl(self.fkBotCtrl,self.fk_bot,0,1,1)
        applyCtrl(self.ik_ctrl,self.ik_botHandle,1,0,0)
        applyCtrl(self.ik_ctrl,self.ik_bot,0,1,1)
        applyCtrl(self.ik_pvCtrl,self.ik_poleVector,1,0,0)
        cmds.parent(self.curveCtrl,w=1)
        cmds.parent(self.curveCtrl,self.midClusterTrackerGrp)
        cmds.makeIdentity(self.curveCtrl,a=1,t=1,r=1,s=1)
        cmds.delete(self.curveCtrl,ch=1)
        cmds.parent(self.midClusterInnerGrp,self.curveCtrl)
        # reset the pivot of curveCtrl to match the elbow exactly.
        v0,v1,v2 = getWorldSpace(self.fk_mid)
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
        # the curveCtrl will control all the curve and ik/fk switchy stuff, instead of self.pivot. so make those connections.
        cmds.addAttr(self.curveCtrl,ln='IK_FK_switch',at='bool')
        cmds.addAttr(self.curveCtrl,ln='midCurveScale',at='float',min=0,max=2)
        cmds.addAttr(self.curveCtrl,ln='topCurveScale',at='float',min=0,max=2)
        cmds.addAttr(self.curveCtrl,ln='botCurveScale',at='float',min=0,max=2)
        cmds.addAttr(self.curveCtrl,ln='minStretch',at='float',min=0.01,max=1,dv=1)
        cmds.addAttr(self.curveCtrl,ln='maxStretch',at='float',min=1,dv=1)
        cmds.addAttr(self.curveCtrl,ln='preserveVolume',at='float',min=0,max=1,dv=1)
        cmds.addAttr(self.curveCtrl,ln='volumeCoefficient',at='float',min=0.01,max=1,dv=0.5)
        chans = ['IK_FK_switch','midCurveScale','topCurveScale','botCurveScale']
        for i in chans:
            cmds.setAttr(self.curveCtrl+'.'+i,cb=1)
            cmds.setAttr(self.curveCtrl+'.'+i,k=1)
            cmds.connectAttr(self.curveCtrl+'.'+i,self.pivot+'.'+i)
        print 'controls applied for limb %s!' % (self.name)
        
    # once controls are applied we can activate squash/stretch.
    
    def makeStretchy(self,min=1,max=3,*args):
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
        chans = ['minStretch','maxStretch','preserveVolume','volumeCoefficient']
        for i in chans:
            cmds.setAttr(self.curveCtrl+'.'+i,cb=1)
            cmds.setAttr(self.curveCtrl+'.'+i,k=1)
            cmds.connectAttr(self.curveCtrl+'.'+i,self.pivot+'.'+i)
        print 'stretchy setup complete for limb %s' % (self.name)
        
    def cleanupRig(self,*args):
        # post-rigging operations.
        cmds.delete(self.topTemplate)
        cmds.delete(self.midTemplate)
        print 'cleanup complete for limb %s' % (self.name)

def getWorldSpace(target,*args):
    # use a locator and a parent constraint to quickly get the worldspace coordinates of an object.
    loc = cmds.spaceLocator()[0]
    pc = cmds.parentConstraint(target,loc)
    tx = cmds.getAttr(loc+'.tx')
    ty = cmds.getAttr(loc+'.ty')
    tz = cmds.getAttr(loc+'.tz')
    cmds.delete(loc)
    return (tx,ty,tz)
    
def getVectorMult(v0,v1,ratio,*args):
    # apply scalar 'ratio' to vectors v0 and v1, return result.
    outX = ((v1[0]-v0[0])*ratio)+v0[0]
    outY = ((v1[1]-v0[1])*ratio)+v0[1]
    outZ = ((v1[2]-v0[2])*ratio)+v0[2]
    return (outX,outY,outZ)

def makeCurve(curveType,name,target='',matchAxes=True,color=0,*args):
    # generate a simple control curve based on curveType.
    # if target is defined, point constraint the curve's parent group to the target.
    # if matchAxes is true, orient the curve's parent group to match the rotation axes of target.
    curve = ''
    if curveType=='arrow':
        curve = cmds.curve(d=1,p=[(0,0.6724194,0.4034517),(0,0,0.4034517),(0,0,0.6724194),(0,-0.4034517,0),(0,0,-0.6724194),(0,0,-0.4034517),(0,0.6724194,-0.4034517),(0,0.6724194,0.4034517)],k=[0,1,2,3,4,5,6,7])
        cmds.setAttr(curve+'.rz',90)
        cmds.setAttr(curve+'.ry',90)
        cmds.setAttr(curve+'.sx',1.5)
        cmds.setAttr(curve+'.sy',1.5)
        cmds.setAttr(curve+'.sz',1.5)
    elif curveType=='cross':
        curve = cmds.curve(d=1,p=[(1,0,-1),(2,0,-1),(2,0,1),(1,0,1),(1,0,2),(-1,0,2),(-1,0,1),(-2,0,1),(-2,0,-1),(-1,0,-1),(-1,0,-2),(1,0,-2),(1,0,-1)],k=[0,1,2,3,4,5,6,7,8,9,10,11,12])
        cmds.setAttr(curve+'.rx',90)
    elif curveType=='snow':
        curve = cmds.curve(d=1,p=[(4.4408920985006262e-01,-0.0015683700000006517,2),(1.0000000000000004,-6.6613381477509392e-016,1.9999999999999998),(1.0000000000000002,-4.4408920985006257e-016,0.99999999999999978),(2,-6.6613381477509383e-016,0.99999999999999956),(2,0,-0.0015683700000002077),(2,1,-2.2204460492503131e-016),(1,1,-2.2204460492503131e-016),(1,2,-4.4408920985006262e-016),(-1,2,-4.4408920985006262e-016),(-1,1,-2.2204460492503131e-016),(-2,1,-2.2204460492503131e-016),(-2,-1,2.2204460492503131e-016),(-1,-1,2.2204460492503131e-016),(-1,-2,4.4408920985006262e-016),(1,-2,4.4408920985006262e-016),(1,-1,2.2204460492503131e-016),(2,-1,2.2204460492503131e-016),(2,0,-0.0015683700000002077),(2,-6.6613381477509383e-016,0.99999999999999956),(1.0000000000000002,-4.4408920985006257e-016,0.99999999999999978),(1.0000000000000004,-6.6613381477509392e-016,1.9999999999999998),(0.099999999999998312,-0.0014115330000006563,2),(4.4408920985006262e-016,-0.0015683700000006517,2),(-0.10000000000000098,-0.0014115330000006067,2),(-0.99999999999999956,-2.2204460492503136e-016,2.0000000000000004),(-0.99999999999999978,-4.9303806576313238e-032,1.0000000000000002),(-1.9999999999999998,2.2204460492503121e-016,1.0000000000000004),(-2,6.6613381477509383e-016,-0.99999999999999956),(-1.0000000000000002,4.4408920985006257e-016,-0.99999999999999978),(-1.0000000000000004,6.6613381477509392e-016,-1.9999999999999998),(0.99999999999999956,2.2204460492503136e-016,-2.0000000000000004),(0.99999999999999978,4.9303806576313238e-032,-1.0000000000000002),(1.9999999999999998,-2.2204460492503121e-016,-1.0000000000000004),(2,-6.6613381477509383e-016,0.99999999999999956),(1.0000000000000002,-4.4408920985006257e-016,0.99999999999999978),(1.0000000000000004,-6.6613381477509392e-016,1.9999999999999998),(0.099999999999998312,-0.0014115330000006563,2),(4.4408920985006262e-016,-0.0015683700000006517,2),(3.9968028886505572e-016,-0.10141153300000205,2),(0,-1.0000000000000004,1.9999999999999998),(-2.2204460492503131e-016,-1.0000000000000002,0.99999999999999978),(-6.6613381477509392e-016,-2,0.99999999999999956),(-1.1102230246251565e-015,-1.9999999999999998,-1.0000000000000004),(-6.6613381477509392e-016,-0.99999999999999978,-1.0000000000000002),(-8.8817841970012523e-016,-0.99999999999999956,-2),(0,1.0000000000000004,-1.9999999999999998),(2.2204460492503131e-016,1.0000000000000002,-0.99999999999999978),(6.6613381477509392e-016,2,-0.99999999999999956),(1.1102230246251565e-015,1.9999999999999998,1.0000000000000004),(6.6613381477509392e-016,0.99999999999999978,1.0000000000000002),(8.8817841970012523e-016,0.99999999999999956,2),(0.0015683700000006517,-4.4443745794708893e-016,2),(4.4408920985006262e-016,-0.0015683700000006517,2)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52])
        cmds.setAttr(curve+'.sx',0.5)
        cmds.setAttr(curve+'.sy',0.5)
        cmds.setAttr(curve+'.sz',0.5)
    elif curveType=='square':
        curve = cmds.curve(d=1,p=[(-1,0,1),(1,0,1),(1,0,-1),(-1,0,-1),(-1,0,1)],k=[0,1,2,3,4])
        cmds.setAttr(curve+'.rx',90)
    elif curveType=='circle':
        curve = cmds.curve(d=3,p=[(-0.50525882489399365,0,-0.83512503818809947),(0.022313365804565437,0,-0.96744341986682636),(0.71031056148790783,0,-0.71031056148790783),(1,0,0),(0.71031056148790783,0,0.71031056148790783),(0,0,1),(-0.71031056148790783,0,0.71031056148790783),(-0.98309609442669621,0,0.0077060138797057087),(-0.81476494957991508,0,-0.54554155937325666),(-0.50525882489399365,0,-0.83512503818809947),(0.022313365804565437,0,-0.96744341986682636),(0.71031056148790783,0,-0.71031056148790783)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13])
        cmds.setAttr(curve+'.rx',90)
    elif curveType=='cube':
        curve = cmds.curve(d=1,p=[(-0.5,0.5,0.5),(0.5,0.5,0.5),(0.5,0.5,-0.5),(-0.5,0.5,-0.5),(-0.5,0.5,0.5),(-0.5,-0.5,0.5),(-0.5,-0.5,-0.5),(0.5,-0.5,-0.5),(0.5,-0.5,0.5),(-0.5,-0.5,0.5),(0.5,-0.5,0.5),(0.5,0.5,0.5),(0.5,0.5,-0.5),(0.5,-0.5,-0.5),(-0.5,-0.5,-0.5),(-0.5,0.5,-0.5)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
        cmds.setAttr(curve+'.sx',2)
        cmds.setAttr(curve+'.sy',2)
        cmds.setAttr(curve+'.sz',2)
    elif curveType=='roundCube':
        curve = cmds.curve(d=1,p=[(-0.5009066471890149,0.60793641188909775,0.73118575537458508),(0.50090664718901801,0.82865315865866107,0.87846330410159157),(0.50090664718901801,0.97968935442399785,0.44742662270877043),(0.50090664718901801,1.0202129758943719,1.1245241575642032e-015),(0.50090664718901801,0.97968935442399829,-0.44742662270876832),(0.50090664718901801,0.82865315865866107,-0.87846330410158957),(-0.5009066471890149,0.60793641188909775,-0.73118575537458297),(-0.5009066471890149,0.60793641188909775,0.73118575537458508),(-0.50090664718901501,-0.6079364118891063,0.73118575537458508),(-0.50090664718901501,-0.6079364118891063,-0.73118575537458297),(0.5009066471890179,-0.82865315865866929,-0.87846330410158957),(0.5009066471890179,-0.97968935442400651,-0.44742662270876832),(0.5009066471890179,-1.0202129758943803,1.0238432495687358e-015),(0.5009066471890179,-0.97968935442400651,0.44742662270877043),(0.5009066471890179,-0.82865315865866929,0.87846330410159157),(-0.50090664718901501,-0.6079364118891063,0.73118575537458508),(0.5009066471890179,-0.82865315865866929,0.87846330410159157),(0.5009066471890179,-0.42205688324657348,1.042971853654209),(0.5009066471890179,-4.0646663654151772e-015,1.0784992010176448),(0.5009066471890179,0.42205688324656521,1.042971853654209),(0.50090664718901801,0.82865315865866107,0.87846330410159157),(0.50090664718901801,0.97968935442399785,0.44742662270877043),(0.50090664718901801,1.0202129758943719,1.1245241575642032e-015),(0.50090664718901801,0.97968935442399829,-0.44742662270876832),(0.50090664718901801,0.82865315865866107,-0.87846330410158957),(0.50090664718901801,0.42205688324656515,-1.0429718536542065),(0.5009066471890179,-4.090379302991285e-015,-1.0784992010176429),(0.5009066471890179,-0.42205688324657353,-1.0429718536542065),(0.5009066471890179,-0.82865315865866929,-0.87846330410158957),(-0.50090664718901501,-0.6079364118891063,-0.73118575537458297),(-0.5009066471890149,0.60793641188909775,-0.73118575537458297)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30])
        cmds.setAttr(curve+'.rx',90)
        cmds.setAttr(curve+'.ry',0)
        cmds.setAttr(curve+'.rz',180)
        cmds.setAttr(curve+'.tx',0.5)
        cmds.move(-0.5,0,0,curve+'.scalePivot',r=1)
        cmds.move(-0.5,0,0,curve+'.rotatePivot',r=1)
    elif curveType=='flatCube':
        curve = cmds.curve(d=1,p=[(-1.4454197399737647,0.074786005662381347,0.33859391820135609),(-0.0011382759774108964,0.18032561162967517,0.5),(-0.0011382759774108964,0.18032561162967517,-0.5),(-1.4454197399737647,0.074786005662381347,-0.33859391820135609),(-1.4454197399737647,0.074786005662381347,0.33859391820135609),(-1.4454197399737647,-0.074786005662381347,0.33859391820135609),(-1.4454197399737647,-0.074786005662381347,-0.33859391820135609),(-0.0011382759774108964,-0.18032561162967517,-0.5),(-0.0011382759774108964,-0.18032561162967517,0.5),(-1.4454197399737647,-0.074786005662381347,0.33859391820135609),(-0.0011382759774108964,-0.18032561162967517,0.5),(-0.0011382759774108964,0.18032561162967517,0.5),(-0.0011382759774108964,0.18032561162967517,-0.5),(-0.0011382759774108964,-0.18032561162967517,-0.5),(-1.4454197399737647,-0.074786005662381347,-0.33859391820135609),(-1.4454197399737647,0.074786005662381347,-0.33859391820135609)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
        cmds.setAttr(curve+'.rx',90)
        cmds.setAttr(curve+'.ry',0)
        cmds.setAttr(curve+'.rz',180)
    elif curveType=='orient':
        curve = cmds.curve(d=3,p=[(0.0959835,0.604001,-0.0987656),(0.500783,0.500458,-0.0987656),(0.751175,0.327886,-0.0987656),(0.751175,0.327886,-0.0987656),(0.751175,0.327886,-0.336638),(0.751175,0.327886,-0.336638),(1.001567,0,0),(1.001567,0,0),(0.751175,0.327886,0.336638),(0.751175,0.327886,0.336638),(0.751175,0.327886,0.0987656),(0.751175,0.327886,0.0987656),(0.500783,0.500458,0.0987656),(0.0959835,0.604001,0.0987656),(0.0959835,0.604001,0.0987656),(0.0959835,0.500458,0.500783),(0.0959835,0.327886,0.751175),(0.0959835,0.327886,0.751175),(0.336638,0.327886,0.751175),(0.336638,0.327886,0.751175),(0,0,1.001567),(0,0,1.001567),(-0.336638,0.327886,0.751175),(-0.336638,0.327886,0.751175),(-0.0959835,0.327886,0.751175),(-0.0959835,0.327886,0.751175),(-0.0959835,0.500458,0.500783),(-0.0959835,0.604001,0.0987656),(-0.0959835,0.604001,0.0987656),(-0.500783,0.500458,0.0987656),(-0.751175,0.327886,0.0987656),(-0.751175,0.327886,0.0987656),(-0.751175,0.327886,0.336638),(-0.751175,0.327886,0.336638),(-1.001567,0,0),(-1.001567,0,0),(-0.751175,0.327886,-0.336638),(-0.751175,0.327886,-0.336638),(-0.751175,0.327886,-0.0987656),(-0.751175,0.327886,-0.0987656),(-0.500783,0.500458,-0.0987656),(-0.0959835,0.604001,-0.0987656),(-0.0959835,0.604001,-0.0987656),(-0.0959835,0.500458,-0.500783),(-0.0959835,0.327886,-0.751175),(-0.0959835,0.327886,-0.751175),(-0.336638,0.327886,-0.751175),(-0.336638,0.327886,-0.751175),(0,0,-1.001567),(0,0,-1.001567),(0.336638,0.327886,-0.751175),(0.336638,0.327886,-0.751175),(0.0959835,0.327886,-0.751175),(0.0959835,0.327886,-0.751175),(0.0959835,0.500458,-0.500783),(0.0959835,0.604001,-0.0987656)],
        k=[0,0,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,53,53])
        cmds.setAttr(curve+'.rx',90)
    elif curveType=='bendedDoubleArrow':
        curve = cmds.curve(d=3,p=[(0.095983499999999999,0.60400100000000012,-0.098765600000000009),(0.095983499999999999,0.60400100000000012,0.098765600000000009),(0.095983499999999999,0.60400100000000012,0.098765600000000009),(0.095983499999999999,0.50045799999999996,0.50078300000000009),(0.095983499999999999,0.32788600000000001,0.75117500000000004),(0.095983499999999999,0.32788600000000001,0.75117500000000004),(0.33663799999999999,0.32788600000000001,0.75117500000000004),(0.33663799999999999,0.32788600000000001,0.75117500000000004),(0,0,1.0015670000000001),(0,0,1.0015670000000001),(-0.33663799999999999,0.32788600000000001,0.75117500000000004),(-0.33663799999999999,0.32788600000000001,0.75117500000000004),(-0.095983499999999999,0.32788600000000001,0.75117500000000004),(-0.095983499999999999,0.32788600000000001,0.75117500000000004),(-0.095983499999999999,0.50045799999999996,0.50078300000000009),(-0.095983499999999999,0.60400100000000012,0.098765600000000009),(-0.095983499999999999,0.60400100000000012,0.098765600000000009),(-0.095983499999999999,0.60400100000000012,-0.098765600000000009),(-0.095983499999999999,0.60400100000000012,-0.098765600000000009),(-0.095983499999999999,0.50045799999999996,-0.50078300000000009),(-0.095983499999999999,0.32788600000000001,-0.75117500000000004),(-0.095983499999999999,0.32788600000000001,-0.75117500000000004),(-0.33663799999999999,0.32788600000000001,-0.75117500000000004),(-0.33663799999999999,0.32788600000000001,-0.75117500000000004),(0,0,-1.0015670000000001),(0,0,-1.0015670000000001),(0.33663799999999999,0.32788600000000001,-0.75117500000000004),(0.33663799999999999,0.32788600000000001,-0.75117500000000004),(0.095983499999999999,0.32788600000000001,-0.75117500000000004),(0.095983499999999999,0.32788600000000001,-0.75117500000000004),(0.095983499999999999,0.50045799999999996,-0.50078300000000009),(0.095983499999999999,0.60400100000000012,-0.098765600000000009)],
        k=[0,0,0,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,41,42,43,44,45,46,47,48,49,50,51,52,53,53,53])
        cmds.setAttr(curve+'.rx',90)
        cmds.setAttr(curve+'.rz',-90)
    elif curveType=='spike':
        curve = cmds.curve(d=1,p=[(-0.26962052657709101,0.26962052657709457,3.978142725902245e-006),(0.26962052657709101,0.26962052657709457,3.978142725902245e-006),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-0.26962052657709101,0.26962052657709457,3.978142725902245e-006),(-0.26962052657709101,-0.26962052657708835,3.978142725902245e-006),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(0.26962052657709101,-0.26962052657708835,3.978142725902245e-006),(-0.26962052657709101,-0.26962052657708835,3.978142725902245e-006),(0.26962052657709101,-0.26962052657708835,3.978142725902245e-006),(0.26962052657709101,0.26962052657709457,3.978142725902245e-006),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432)],
        k=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
        cmds.setAttr(curve+'.rx',180)
        cmds.setAttr(curve+'.ry',90)
    # create a group at the origin to contain the control.
    curve = cmds.rename(curve,name)
    cmds.makeIdentity(curve,a=1,t=1,r=1,s=1)
    ctrlGrp = cmds.group(em=1,n=name+'_grp',w=1,r=1)
    pc = cmds.pointConstraint(curve,ctrlGrp)
    cmds.delete(pc)
    cmds.parent(curve,ctrlGrp)
    if target != '':
        # constrain the ctrlGrp to the target, then delete the constraint.
        # if matchAxes=True, also orient constraint.
        pc = cmds.pointConstraint(target,ctrlGrp)[0]
        cmds.delete(pc)
        if matchAxes:
            oc = cmds.orientConstraint(target,ctrlGrp)[0]
            cmds.delete(oc)
        cmds.makeIdentity(curve,a=1,t=1,r=1,s=1)
    # the controller is fitted and in place. now let the user fuck with it until they're ready to apply the constraints.
    cmds.select(curve)
    if color != 0:
        curveShape = cmds.listRelatives(curve,s=1)[0]
        cmds.setAttr(curveShape+'.overrideEnabled',1)
        cmds.setAttr(curveShape+'.drawOverride.overrideColor',color)
    return curve
    
def swapCurve(curve,newType,*args):
    # replace an existing control curve with a new one.
    curveParent = cmds.listRelatives(curve,p=1)[0]
    curveShape = cmds.listRelatives(curve,s=1)[0]
    color = cmds.getAttr(curveShape+'.drawOverride.overrideColor')
    newCurve = makeCurve(newType,curve+'_replace',curveParent,True,color)
    # match xforms from curve to newCurve.
    tx,ty,tz = cmds.getAttr(curve+'.tx'),cmds.getAttr(curve+'.ty'),cmds.getAttr(curve+'.tz')
    rx,ry,rz = cmds.getAttr(curve+'.rx'),cmds.getAttr(curve+'.ry'),cmds.getAttr(curve+'.rz')
    sx,sy,sz = cmds.getAttr(curve+'.sx'),cmds.getAttr(curve+'.sy'),cmds.getAttr(curve+'.sz')
    cmds.setAttr(newCurve+'.tx',tx)
    cmds.setAttr(newCurve+'.ty',ty)
    cmds.setAttr(newCurve+'.tz',tz)
    cmds.setAttr(newCurve+'.rx',rx)
    cmds.setAttr(newCurve+'.ry',ry)
    cmds.setAttr(newCurve+'.rz',rz)
    cmds.setAttr(newCurve+'.sx',sx)
    cmds.setAttr(newCurve+'.sy',sy)
    cmds.setAttr(newCurve+'.sz',sz)
    cmds.delete(curveParent)
    newCurve = cmds.rename(newCurve,curve)
    newCurveParent = cmds.listRelatives(curve,p=1)[0]
    cmds.rename(newCurveParent,newCurve+'_grp')
    return newCurve
    
    
def applyCtrl(curve,target,point=True,orient=True,scale=True):
    # make them constraints. easy enough.
    # first, if the control has been moved, shift the pivot so that it matches the pivot of its parent group.
    tx,ty,tz = cmds.getAttr(curve+'.tx'),cmds.getAttr(curve+'.ty'),cmds.getAttr(curve+'.tz')
    cmds.setAttr(curve+'.rotatePivotX',tx*-1.0)
    cmds.setAttr(curve+'.rotatePivotY',ty*-1.0)
    cmds.setAttr(curve+'.rotatePivotZ',tz*-1.0)
    cmds.setAttr(curve+'.scalePivotX',tx*-1.0)
    cmds.setAttr(curve+'.scalePivotY',ty*-1.0)
    cmds.setAttr(curve+'.scalePivotZ',tz*-1.0)
    cmds.makeIdentity(curve,a=1,t=1,r=1,s=1)
    if point and orient:
        cmds.parentConstraint(curve,target,mo=1)
    elif point and not orient:
        cmds.parentConstraint(curve,target,sr=['x','y','z'],mo=1)
    elif orient and not point:
        cmds.parentConstraint(curve,target,st=['x','y','z'],mo=1)
    if scale:
        cmds.scaleConstraint(curve,target,mo=1)
        
def removeRig(*args):
    # completely remove a rig while preserving the original skeleton.
    # select the attachPivot group and run this function.
    attachPivot = cmds.ls(sl=1)[0]
    # test this object to make sure it's a valid rig.
    if not cmds.attributeQuery('hfRig',node=attachPivot,ex=1):
        cmds.error('Please select the pivot group of the rig you want to remove.')
    gutsGrp = cmds.listConnections(attachPivot+'.hfRig')[0]
    fkTopJnt = cmds.listConnections(attachPivot+'.fkTopJnt')[0]
    fkMidJnt = cmds.pickWalk(fkTopJnt,direction='down')[0]
    fkBotJnt = cmds.pickWalk(fkMidJnt,direction='down')[0]
    cmds.delete(fkTopJnt,cn=1)
    cmds.delete(fkMidJnt,cn=1)
    cmds.delete(fkBotJnt,cn=1)
    newTop = cmds.duplicate(fkTopJnt,po=1)[0]
    newMid = cmds.duplicate(fkMidJnt,po=1)[0]
    newBot = cmds.duplicate(fkBotJnt,po=1)[0]
    cmds.parent(newTop,w=1)
    cmds.parent(newMid,newTop)
    cmds.parent(newBot,newMid)
    # now that the old skeleton is preserved, we'll nuke everything else.
    cmds.delete(attachPivot)
    cmds.delete(gutsGrp)
    print 'removed selected rig.'
    
def snapSwitch(setKeys=1,findNode=0,*args):
    # from a selected object, traverse the DAG until we find the pivot object, figure out the current control state,
    # then swap to the opposite state and set a key on the ik/fk switch.
    # if findNode==1, then just select the pivot object so the user can look at current switch keyframes.
    testObj = cmds.ls(sl=1)[0]
    attachPivot = ''
    messageConns = cmds.listConnections(testObj+'.message')
    for i in messageConns:
        if cmds.attributeQuery('hfRig',node=i,ex=1):
            attachPivot = i
    if attachPivot == '':
        cmds.error("Couldn't find the control node from the selected object. Try selecting a controller.")
    if findNode:
        cmds.select(attachPivot)
        return
    # now the hard work. from attachPivot, we can get the names of all our controls and bones.
    ikCtrl = cmds.listConnections(attachPivot+'.ik_ctrl')[0]
    ik_pvCtrl = cmds.listConnections(attachPivot+'.ik_pvCtrl')[0]
    ik_fk_switch = cmds.getAttr(attachPivot+'.IK_FK_switch')
    fkTopCtrl = cmds.listConnections(attachPivot+'.fkTopCtrl')[0]
    fkMidCtrl = cmds.listConnections(attachPivot+'.fkMidCtrl')[0]
    fkBotCtrl = cmds.listConnections(attachPivot+'.fkBotCtrl')[0]
    fkPoleVectorGuide = cmds.listConnections(attachPivot+'.fk_poleVectorGuide')[0]
    ik_top = cmds.listConnections(attachPivot+'.ik_top')[0]
    ik_mid = cmds.listConnections(attachPivot+'.ik_mid')[0]
    ik_bot = cmds.listConnections(attachPivot+'.ik_bot')[0]
    fk_bot = cmds.listConnections(attachPivot+'.fk_bot')[0]
    curveCtrl = cmds.listConnections(attachPivot+'.curveCtrl')[0]
    # based on whether we are currently in FK mode or IK mode, get the values of the objects we want and then move the other set of controls.
    if ik_fk_switch == 1:
        # ik to fk. easy.
        top_rotate = cmds.getAttr(ik_top+'.rotate')[0]
        mid_rotate = cmds.getAttr(ik_mid+'.rotate')[0]
        bot_rotate = cmds.getAttr(ik_bot+'.rotate')[0]
        top_scale = cmds.getAttr(ik_top+'.scale')[0]
        mid_scale = cmds.getAttr(ik_mid+'.scale')[0]
        m0,m1,m2 = getWorldSpace(curveCtrl)
        curveRotate = cmds.xform(curveCtrl,q=1,ws=1,ro=1)
        # set attributes on the fk controllers, then set a key.
        cmds.setAttr(fkTopCtrl+'.rx',top_rotate[0])
        cmds.setAttr(fkTopCtrl+'.ry',top_rotate[1])
        cmds.setAttr(fkTopCtrl+'.rz',top_rotate[2])         
        cmds.setAttr(fkMidCtrl+'.rx',mid_rotate[0])
        cmds.setAttr(fkMidCtrl+'.ry',mid_rotate[1])
        cmds.setAttr(fkMidCtrl+'.rz',mid_rotate[2])       
        cmds.setAttr(fkBotCtrl+'.rx',bot_rotate[0])
        cmds.setAttr(fkBotCtrl+'.ry',bot_rotate[1])
        cmds.setAttr(fkBotCtrl+'.rz',bot_rotate[2])
        cmds.setAttr(fkTopCtrl+'.sx',top_scale[0])
        cmds.setAttr(fkMidCtrl+'.sx',mid_scale[0])
        cmds.setAttr(curveCtrl+'.IK_FK_switch',0)
        # check the midpoint and make sure it didn't shift.
        if setKeys:
            cmds.setKeyframe(fkTopCtrl+'.rx')
            cmds.setKeyframe(fkTopCtrl+'.ry')
            cmds.setKeyframe(fkTopCtrl+'.rz')
            cmds.setKeyframe(fkTopCtrl+'.sx')
            cmds.setKeyframe(fkMidCtrl+'.rx')
            cmds.setKeyframe(fkMidCtrl+'.ry')
            cmds.setKeyframe(fkMidCtrl+'.rz')
            cmds.setKeyframe(fkMidCtrl+'.sx')
            cmds.setKeyframe(fkBotCtrl+'.rx')
            cmds.setKeyframe(fkBotCtrl+'.ry')
            cmds.setKeyframe(fkBotCtrl+'.rz')
            cmds.setKeyframe(curveCtrl+'.IK_FK_switch')
        # now doublecheck the midpoint.
        n0,n1,n2 = getWorldSpace(curveCtrl)
        if m0!=n0 or m1!=n1 or m2!=n2:
            cmds.xform(curveCtrl,ws=1,t=[m0,m1,m2])
            cmds.xform(curveCtrl,ws=1,ro=[curveRotate[0],curveRotate[1],curveRotate[2]])
            if setKeys:
                chans = ['tx','ty','tz','rx','ry','rz']
                for c in chans:
                    cmds.setKeyframe(curveCtrl+'.'+c)
    else:
        # fk to ik. a little trickier. start by getting the translate value of fk_bot, then get the translate of fkPoleVectorGuide.
        # use these values to position the ikCtrl and ik_pvCtrl.
        # the midpoint controller is the tricky part... if the fk joints are not evenly scaled, the ik won't match unless the midpoint
        # controller ends up in the exact same place. get its worldspace coords before and after the snap. if they don't match,
        # snap the controller into the correct place and set a key.
        b0,b1,b2 = getWorldSpace(fkBotCtrl)
        g0,g1,g2 = getWorldSpace(fkPoleVectorGuide)
        m0,m1,m2 = getWorldSpace(curveCtrl)
        curveRotate = cmds.xform(curveCtrl,q=1,ws=1,ro=1)
        cmds.xform(ikCtrl,ws=1,t=[b0,b1,b2])
        cmds.xform(ik_pvCtrl,ws=1,t=[g0,g1,g2])
        # now set rotations. the wrist isn't going to get rotations in quite the same way because the parenting structure is a little different.
        # use a temporary orient constraint.
        # rx,ry,rz = cmds.getAttr(fkBotCtrl+'.rx'),cmds.getAttr(fkBotCtrl+'.ry'),cmds.getAttr(fkBotCtrl+'.rz')
        # cmds.setAttr(ikCtrl+'.rx',rx)
        # cmds.setAttr(ikCtrl+'.ry',ry)
        # cmds.setAttr(ikCtrl+'.rz',rz)
        cmds.setAttr(curveCtrl+'.IK_FK_switch',1)
        oc = cmds.orientConstraint(fkBotCtrl,ikCtrl)
        cmds.delete(oc)
        if setKeys:
            chans = ['tx','ty','tz','rx','ry','rz']
            for c in chans:
                cmds.setKeyframe(ikCtrl+'.'+c)
            chans = ['tx','ty','tz']
            for c in chans:
                cmds.setKeyframe(ik_pvCtrl+'.'+c)
            cmds.setKeyframe(curveCtrl+'.IK_FK_switch')
        # now we need to compare the curveCtrl's current xforms against its previous xforms. if different, move to the original coordinates
        # and set a keyframe.
        n0,n1,n2 = getWorldSpace(curveCtrl)
        if m0!=n0 or m1!=n1 or m2!=n2:
            cmds.xform(curveCtrl,ws=1,t=[m0,m1,m2])
            cmds.xform(curveCtrl,ws=1,ro=[curveRotate[0],curveRotate[1],curveRotate[2]])
            if setKeys:
                chans = ['tx','ty','tz','rx','ry','rz']
                for c in chans:
                    cmds.setKeyframe(curveCtrl+'.'+c)
    # reselect whatever we had selected.
    cmds.select(testObj)