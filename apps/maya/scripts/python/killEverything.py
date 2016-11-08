# killEverything.py v1.01 by henry foster (henry@toadstorm.com), 01/02/2012
#
# this is an asset cleanup checklist for objects that are going to be referenced into a render scene.
# this was originally a separate script outside of Mustache that's since been incorporated. there is some ugly shit
# happening in here because of that... i was not good at understanding lambda functions and variable scope when this was
# written. what you gonna do?


import maya.cmds as cmds
import maya.mel as mel
import hfFixShading as hfFBS
# lightTypes = ['spotLight', 'pointLight', 'areaLight', 'ambientLight', 'directionalLight', 'volumeLight']
# VRayLightTypes = ['VRayLightSphereShape', 'VRayLightDomeShape', 'VRayLightRectShape', 'VRayLightIESShape']

class KillEverythingUI():
    def __init__(self,mustacheAM='',asset=''):
        self.name = 'killEverythingUI'
        self.title = 'ASSET CLEANUP JAMBOREE'
        if(cmds.window(self.name, q=1, exists=1)): cmds.deleteUI(self.name)
        self.window = cmds.window(self.name, title=self.title)
        # control layout
        self.form = cmds.formLayout()
        self.kCleanBtn = cmds.button(l='run cleanup', w=100, h=75, c=lambda *x: self.runCleanup(mustacheAM,asset))
        self.kCloseBtn = cmds.button(l='done', w=100, h=75, c=self.close)
        self.kCol = cmds.columnLayout()
        self.kCameras = cmds.checkBox(l='kill cameras', v=1)
        self.kLights = cmds.checkBox(l='kill lights', v=0)
        self.kRefs = cmds.checkBox(l='kill references', v=1)
        self.kLayers = cmds.checkBox(l='kill duplicate render layers', v=1)
        self.kUnk = cmds.checkBox(l='kill unknown nodes', v=1)
        self.kNamespaces = cmds.checkBox(l='remove namespaces', v=1)
        self.kCompShading = cmds.checkBox(l='fix bad shading connections (WARNING! check render layers! bad with instances!)', v=1)
        self.kOverrides = cmds.checkBox(l='remove layer overrides (WARNING! completely wipes render layers!)', v=0)
        self.kLinks = cmds.checkBox(l='remove light links', v=1)
        self.kLockdown = cmds.checkBox(l='lockdown scene', v=0)
        self.kRename = cmds.checkBox(l='rename duplicates', v=1)
        self.kIntermediate = cmds.checkBox(l='kill unused intermediate objects', v=0)
        self.kSmoothing = cmds.checkBox(l='kill smooth preview', v=1)
        self.kNormals = cmds.checkBox(l='toggle normals view mode', v=0, cc=self.normalsView)
        cmds.formLayout(self.form,e=1,attachForm=[(self.kCol, 'top', 10),(self.kCol, 'left', 10)])
        cmds.formLayout(self.form,e=1,attachForm=[(self.kCleanBtn, 'top', 290),(self.kCleanBtn, 'left', 10),(self.kCloseBtn, 'top', 290),(self.kCloseBtn, 'left', 120)])
        cmds.showWindow(self.window)
        cmds.window(self.window, e=1, w=500, h=380)

    def killNode(self,type='unknown',xform=1,force=1,*args):
        """ blow up a type of node. if xform is on, search for xforms and kill that too. """
        deathCount = []
        for node in cmds.ls(type=type):
            if xform==1:
                death = cmds.listRelatives(node,p=1)
                if force==1: cmds.lockNode(death,lock=0)
                try:
                    deathCount.extend(death)
                    cmds.delete(death)
                except TypeError:
                    # there isn't actually an xform here, so delete the original node.
                    deathCount.append(node)
                    cmds.delete(node)
            else:
                if force==1: cmds.lockNode(node,lock=0)
                deathCount.append(node)
                cmds.delete(node)
        # some nodes can't be deleted. let's try not to return bullshit values.
        try:
            deathCount.remove('persp')
            deathCount.remove('top')
            deathCount.remove('front')
            deathCount.remove('side')
        except:
            pass
        return deathCount

    def killRefs(self,*args):
        deadRefs = []
        refs = cmds.file(q=1,r=1)
        for ref in refs:
            cmds.file(ref, rr=1)
            deadRefs.append(ref)
        return deadRefs

    def killImportedLayers(self,*args):
        """ remove useless duplicate render layers that have been imported from a reference. """
        deadLayers = []
        layers = cmds.ls(type='renderLayer')
        for layer in layers:
            if layer.count(':') > 0:
                # this guy is namespaced and should be deleted if possible.
                deadLayers.append(layer)
                cmds.delete(layer)
        return deadLayers

    def killOverrides(self,*args):
        """ remove all render layer overrides in the asset. """
        # for each render layer, list all adjustments, then attempt to remove each one.
        deadOvers = []
        for rlayer in cmds.ls(type='renderLayer'):
            adjs = cmds.editRenderLayerAdjustment(rlayer, q=1, lyr=1)
            if adjs != None:
                for adj in cmds.editRenderLayerAdjustment(rlayer, q=1, lyr=1):
                    try:
                        deadOvers.append(adj)
                        cmds.editRenderLayerAdjustment(adj,r=1,lyr=rlayer)
                    except:
                        deadOvers.append(adj+' (FAILED)')
        return deadOvers

    def killLightLinks(self,*args):
        """ remove all connections to all lightLinker nodes in the scene. """
        deadLinks = []
        for linker in cmds.ls(type='lightLinker'):
            try:
                for conn in cmds.listConnections(linker,c=1,p=1):
                    deadLinks.append(conn)
                    cmds.delete(conn,icn=1)
            except:
                pass
        return deadLinks

    def killNamespaces(self,*args):
        """ empty namespaces of objects and then remove them. """
        cmds.namespace(set=':') # go to root
        namespaces = cmds.namespaceInfo(lon=1)
        deathCount = []
        for ns in namespaces:
            # we do NOT want to fuck with 'UI' or 'shared.' this will crash maya.
            if ns != 'UI' and ns != 'shared':
                # remove all objects from this namespace.
                cmds.namespace(mv=(ns,':'),force=1)
                try:
                    cmds.namespace(rm=ns)
                    deathCount.append(ns)
                except:
                    print('couldn\'t remove namespace: '+ns)
        return deathCount

    def normalsView(self,*args):
        """ switch the current modelPanel to a view that clearly shows bad normals. """
        currPanel = cmds.getPanel(wf=1)
        try:
            tsl = cmds.modelEditor(currPanel,q=1,twoSidedLighting=1)
            udm = cmds.modelEditor(currPanel,q=1,useDefaultMaterial=1)
            if tsl==1 and udm == 1: udm=0
            cmds.modelEditor(currPanel,e=1,twoSidedLighting=not(tsl),useDefaultMaterial=not(udm),displayAppearance='smoothShaded')
        except RuntimeError:
            # switch back to previous mode
            currMode = cmds.checkBox(self.kNormals,q=1,v=1)
            cmds.checkBox(self.kNormals,e=1,v=not(currMode))
            cmds.error('you need to select a modeling panel')

    def renameDuplicates(self,padding=3,*args):
        # get all xforms. if an xform name contains a '|', it's appearing more than once and we'll have to rename it.
        badXforms = [f for f in cmds.ls() if '|' in f]
        badXformsUnlock = [f for f in badXforms if cmds.lockNode(f,q=1,lock=1)[0] == False]
        count = 0
        # we need to somehow sort this list by the number of '|' appearing in each name. this way we can edit names from the bottom of the hierarchy up,
        # and not worry about losing child objects from the list.
        countDict = {}
        for f in badXformsUnlock:
            countDict[f] = f.count('|')
        # now sort the dictionary by value, in reverse, and start renaming.
        for key,value in sorted(countDict.iteritems(),reverse=True, key=lambda (key,value): (value,key)):
            # okay, now we can start actually renaming objects in order.
            n = 1
            # print '\ndebug: renaming object %s' % (key)
            newObj = cmds.rename(key,key.split('|')[-1]+'_'+str(n).zfill(padding))
            while newObj.count('|') > 0:
                # INFINITE LOOP PROBLEM: if the transform and the shape are named the same, this will go on forever.
                # we need to write some kind of exception to prevent this from happening.
                n += 1
                basename = newObj.split('|')[-1]
                newName = '_'.join(basename.split('_')[0:-1])+'_'+str(n).zfill(padding)
                newObj = cmds.rename(newObj,newName)
            print 'renamed %s to %s' % (key,newObj)
            count = count+1
        if count < 1:
            return 'No duplicate names found.'
        else:
            return 'Found and renamed '+str(count)+' objects with duplicate names. Check script editor for details.'

    def killSmoothing(self,*args):
        # remove smooth preview from all polygon objects.
        meshes = cmds.ls(type='mesh')
        if meshes:
            cmds.displaySmoothness(meshes,du=0,dv=0,pw=4,ps=1,po=1)

    def killIntermediates(self,*args):
        # look for intermediate object nodes. if it's a shape, see if it plugs directly into another shape. if so, delete it.
        # these bullshit nodes can be caused by deleting a polySmooth node, for example, instead of deleting history. they can
        # stick around and break scenes.
        interm = cmds.ls(io=1)
        deaths = []
        if len(interm) > 0:
            for x in interm:
                if x in cmds.ls(s=1):
                    outMeshCons = cmds.listConnections(x+'.outMesh',s=0,d=1,sh=1)
                    try:
                        for con in outMeshCons:
                            if cmds.objectType(con) == 'mesh':
                                deaths.append(con)
                                cmds.delete(x)
                                continue
                    except TypeError:
                        pass
        return deaths


    def runCleanup(self, mustacheAM='',asset='',*args):
        # pick up checkbox values.
        cams = cmds.checkBox(self.kCameras,q=1,v=1)
        lights = cmds.checkBox(self.kLights,q=1,v=1)
        refs = cmds.checkBox(self.kRefs,q=1,v=1)
        layers = cmds.checkBox(self.kLayers,q=1,v=1)
        unk = cmds.checkBox(self.kUnk,q=1,v=1)
        namespaces = cmds.checkBox(self.kNamespaces,q=1,v=1)
        compShading = cmds.checkBox(self.kCompShading,q=1,v=1)
        links = cmds.checkBox(self.kLinks,q=1,v=1)
        overrides = cmds.checkBox(self.kOverrides,q=1,v=1)
        lockdown = cmds.checkBox(self.kLockdown,q=1,v=1)
        rename = cmds.checkBox(self.kRename,q=1,v=1)
        intermediate = cmds.checkBox(self.kIntermediate,q=1,v=1)
        smoothing = cmds.checkBox(self.kSmoothing,q=1,v=1)
        shit = [f for f in cmds.ls() if 'vrayEnvironmentPreviewTm' in f]
        for i in shit:
            try:
                cmds.delete(shit)
            except TypeError:
                pass
        resultStr = ""
        if rename == True:
            ren = self.renameDuplicates()
            resultStr = resultStr + '---Duplicate nodes renamed---\n' + ren + '\n\n'
        if cams == True:
            cams = self.killNode(type='camera')
            resultStr = resultStr + ('---CAMERAS REMOVED---\n') + '\n'.join(cams) + '\n\n'
        if lights == True:
            # check for vray plugin.
            lightTypes = ['spotLight', 'pointLight', 'areaLight', 'ambientLight', 'directionalLight', 'volumeLight']
            if cmds.pluginInfo('vrayformaya.mll',q=1,l=1) == 1:
                VRayLightTypes = ['VRayLightSphereShape', 'VRayLightDomeShape', 'VRayLightRectShape', 'VRayLightIESShape']
                lightTypes.extend(VRayLightTypes)
            lights = self.killNode(type=lightTypes)
            resultStr = resultStr + '---LIGHTS REMOVED---\n' + '\n'.join(lights) + '\n\n'
        if refs == True:
            refs = self.killRefs()
            resultStr = resultStr + '---REFERENCES REMOVED---\n' + '\n'.join(refs) + '\n\n'
        if layers == True:
            layers = self.killImportedLayers()
            resultStr = resultStr + '---LAYERS REMOVED---\n' + '\n'.join(layers) + '\n\n'
        if unk == True:
            unk = self.killNode(type='unknown',xform=0)
            resultStr = resultStr + '---UNKNOWN NODES REMOVED---\n' + '\n'.join(unk) + '\n\n'
        if namespaces == True:
            namespaces = self.killNamespaces()
            resultStr = resultStr + '---NAMESPACES REMOVED---\n' + '\n'.join(namespaces) + '\n\n'
        if compShading == True:
            compShading = hfFBS.hfFixBadShading()
            if compShading != 0:
                resultStr = resultStr + '---COMPONENT SHADING FIXED---\n' + '\n'.join(compShading) + '\n\n'
            else:
                resultStr = resultStr + '---COMPONENT SHADING FIXED---\n' + '\nNo component shading detected.\n\n'
        if links == True:
            links = self.killLightLinks()
            resultStr = resultStr + '---LIGHT LINKS REMOVED---\n' + str(links) + '\n\n'
        if overrides == True:
            overrides = self.killOverrides()
            resultStr = resultStr + '---LAYER OVERRIDES REMOVED---\n' + '\n'.join(overrides) + '\n\n'
        if lockdown == True:
            initLockdown(1)
            resultStr = resultStr + '---Scene lockdown active---\n\n'
        if intermediate == True:
            interm = self.killIntermediates()
            resultStr = resultStr + '---UNUSED INTERMEDIATE SHAPES REMOVED---\n' + '\n'.join(interm) + '\n\n'
        if smoothing == True:
            self.killSmoothing()
            resultStr = resultStr + '---REMOVED POLYGON SMOOTHING---\n\n\n'
        # get and post results
        self.resultsName = 'resultsWindow'
        self.resultsTitle = 'CLEANUP RESULTS'
        if cmds.window(self.resultsName,q=1,exists=1): cmds.deleteUI(self.resultsName)
        self.resultsWindow = cmds.window(self.resultsName, title=self.resultsTitle)
        self.resultsForm = cmds.formLayout()
        self.resultsScroll = cmds.scrollField(w=400,h=500,tx=str(resultStr))
        cmds.deleteUI(self.window)
        cmds.showWindow(self.resultsWindow)
        cmds.window(self.resultsWindow,e=1,w=410,h=510)
        cmds.select(cl=1)
        cmds.warning('\nAsset cleanup complete. See results window for details.')
        if mustacheAM != '':
            # this procedure was called by mustache asset manager. run the mastering script!
            mustacheAM.masterAsset(asset)

    def close(self, *args):
        cmds.deleteUI(self.window)

def lockObject(obj,lock,*args):
    attrs = cmds.listAttr(obj,k=1)
    # also (un)lock pivots.
    pivotAttrs = ['rotatePivotX','rotatePivotY','rotatePivotZ','rotatePivotTranslateX','rotatePivotTranslateY','rotatePivotTranslateZ','scalePivotX','scalePivotY','scalePivotZ']
    if attrs:
        attrs.extend(pivotAttrs)
        for attr in attrs:
            try:
                cmds.setAttr(obj+'.'+attr,e=1,lock=lock)
            except RuntimeError:
                pass

def initLockdown(lock,*args):
    # activate/deactivate scene lockdown. locks all transforms that aren't direct parents of NURBS controllers.
    # is the scene already locked down?
    if not cmds.objExists('hfLockdownInfo'):
        cmds.createNode('lambert',n='hfLockdownInfo')
        cmds.addAttr('hfLockdownInfo',ln='sceneLocked',at='bool')
    cmds.lockNode('hfLockdownInfo',lock=1)
    # first, get all the xforms we want to leave alone.
    nurbsCamsShapes = cmds.ls(type=('nurbsCurve','camera'))
    exemptList = []
    for obj in nurbsCamsShapes:
        xforms = cmds.listRelatives(obj,p=1)
        try:
            exemptList.extend(xforms)
        except TypeError:
            pass
    objsToLock = [f for f in cmds.ls(type='transform') if f not in exemptList]
    if lock==False: print 'unlocking scene'
    if lock==True: print 'locking scene'
    for obj in objsToLock:
        lockObject(obj,lock)
    if lock==False: cmds.warning('Scene is now unlocked.')
    if lock==True: cmds.warning('Scene is now locked.')
