#!/usr/bin/env python
__author__ = "Adam Burke"
__version__ = "0.7.0"
__maintainer__ = "Adam Burke"
__email__ = "adam@adamburke.net"

'''makes things into props'''

import os, sys, math, glob, re
import yaml

# import maya
from maya import cmds
from maya import mel
from maya import OpenMayaUI as omui 
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin, MayaQWidgetDockableMixin

try:
  from PySide2.QtCore import * 
  from PySide2.QtGui import * 
  from PySide2.QtWidgets import *
  from PySide2 import __version__
  from shiboken2 import wrapInstance 
except ImportError:
  from PySide.QtCore import * 
  from PySide.QtGui import * 
  from PySide import __version__
  from shiboken import wrapInstance 

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget) 

import gs_core


############ global pointers to prevent garbage collection until unload
###########wind=None
###########widg=None
###########wind_lyt=None

class LIgnoreValidator(QValidator):
    def validate(self, string, pos):
        #super(LIgnoreValidator, self).validate(string, pos)
        #string.replace(pos-1, string.count()-pos, '')
        #print ("ingoring validity")
        return QValidator.Invalid, pos

# validator for Initials (uppsercase 2 letters only)
class LRegExpValidator(QRegExpValidator):
    def validate(self, string, pos):
        result = super(LRegExpValidator, self).validate(string, pos)

        #return QValidator.Acceptable, string.toUpper(), pos
        # for old code still using QString, use this instead
        #string.replace(0, string.count(), string.toUpper())
        return result[0], pos


class GSAssetMakerWindow(MayaQWidgetBaseMixin,QWidget):

    data_model = {}
    obj_list_model = None
    renameShader = True

    def __init__(self, parent=None, *args, **kwargs):
        super(GSAssetMakerWindow, self).__init__(parent=parent, *args, **kwargs) 

        
        #####self.parent = parent
        main_lyt = QBoxLayout(QBoxLayout.LeftToRight)
        self.setLayout(main_lyt)
        iconsize = QSize(48,48)
        
        tabwidget = QTabWidget(self)
        createTab = QWidget()
        modifyTab = QWidget()
        tabwidget.addTab(createTab,"Create")
        tabwidget.addTab(modifyTab,"Modify")
        main_lyt.addWidget(tabwidget)
        vertical = QVBoxLayout()
        createTab.setLayout(vertical)

        self.setWindowTitle('GS AssetMaker v0.3a')

        self.startAsset = QPushButton("Start New Asset")
        vertical.addWidget(self.startAsset)

        pathEditGroup = QBoxLayout(QBoxLayout.LeftToRight)
        vertical.addLayout(pathEditGroup)
        self.pathLbl = QLabel('Asset Name:')
        self.nameLE = QLineEdit()

        font = self.nameLE.font()
        font.setPointSize(12)
        self.nameLE.setFont(font)

        regexp = QRegExp('^[A-Za-z](?:_?[A-Za-z]+)*$')
        validator = LRegExpValidator(regexp)
        self.nameLE.setValidator(validator)

        pathEditGroup.addWidget(self.pathLbl)
        pathEditGroup.addWidget(self.nameLE)

        # list of objects and attached shaders
        self.obj_list = QTreeView()
        self.obj_list.setUniformRowHeights(True)
        self.obj_list_model = QStandardItemModel(self.obj_list)
        self.obj_list.setModel(self.obj_list_model)
        self.obj_list.setAlternatingRowColors(True)
        #self.obj_list_model.setHorizontalHeaderLabels(['Assets', 'Current Cache', 'Latest Cache', 'Date'])
        vertical.addWidget(self.obj_list)
        self.obj_list.setIndentation(8)

        bottomLyt = QBoxLayout(QBoxLayout.LeftToRight)
        bottomLyt.addStretch(1)
        vertical.addLayout(bottomLyt)
        self.removeButton = QPushButton('Remove')
        self.addButton = QPushButton("Add Sel")
        bottomLyt.addWidget(self.removeButton)
        bottomLyt.addWidget(self.addButton)

        optionsGroup = QBoxLayout(QBoxLayout.LeftToRight)
        vertical.addLayout(optionsGroup)
        self.uvCB = QCheckBox('Clear History')
        optionsGroup.addWidget(self.uvCB)
        self.fhCB = QCheckBox('Flatten Hierarchy')
        self.fhCB.setChecked(0)
        optionsGroup.addWidget(self.fhCB)
        self.gsCB = QCheckBox('Include Shaders')
        self.gsCB.setChecked(1)
        optionsGroup.addWidget(self.gsCB)

        self.localAsset = QPushButton("Convert to Asset")
        self.jobAsset = QPushButton("Convert to Referenced Asset")

        vertical.addWidget(self.localAsset)
        vertical.addWidget(self.jobAsset)

        #self.bossMode = QPushButton("Boss Mode")
        #vertical.addWidget(self.bossMode) # aka Im feeling lucky aka do it fast

        # Set up slots and signals.
        self.startAsset.clicked.connect(self.doAssetStart)
        self.localAsset.clicked.connect(self.doCreateAssetLocal)
        self.jobAsset.clicked.connect(self.doCreateAssetRef)

        #self.updateUi()

    def updateUi(self):

        # populate list with assets found in scene
        assets = get_assets_in_scene()
        r = 0
        for a in assets:
            item = QStandardItem(a)
            print (assets[a]['latest_cache'])
            ver = QStandardItem(assets[a]['latest_cache'])
            item.setCheckable(True)
            item.setCheckState(2)
            self.obj_list_model.appendRow(item)
            self.obj_list_model.setItem(r,2,ver)
            r = r + 1
        return

    def doAssetStart(self):
        print("starting asset")
        # start an asset by creating the locator with an initial name but without namespace
        str(self.nameLE.text())

        cmds.namespace(set=":")

        sl = cmds.ls(sl=True,l=True)
        #self.addItemToObjList(item='Geometry',parent='')
        self.data_model = {}
        #self.addChildren('',sl)
        for ea in sl:
            ch = cmds.listRelatives(ea,ad=True,f=True)
            ch_xform = cmds.ls(ch,type='transform',l=True)
            ch_xform.append(ea)
            self.addItemsFromDagPaths(self.data_model,ch_xform)

        #self.addItemToObjList(item='Shaders',parent='')
        print(self.data_model)
        self.updateViewModelFromDict(self.data_model)

        bbox = cmds.exactWorldBoundingBox(sl,ii=True)
        center = [(bbox[3] - bbox[0]) * .5+bbox[0], bbox[1], (bbox[5] - bbox[2])*.5+bbox[2]]
        if cmds.objExists("AssetMaker_asset_xform"):
            cmds.delete("AssetMaker_asset_xform")
        new_loc = cmds.spaceLocator(n="AssetMaker_asset_xform")

        cmds.move(center[0], center[1], center[2], new_loc[0])

    def clearCreateAsset(self):
        self.data_model = {}
        self.updateViewModelFromDict(self.data_model)
        self.nameLE.setText('')

    def addChildren(self, parent, child_list):
        ''' iterate through all children and add them to the model'''
        for c in child_list:
            print ('adding item {0} to parent {1}'.format(c,parent))
            self.addItemToObjList(c,parent)
            sub_children = cmds.listRelatives(c)
            if sub_children:
                self.addChildren(c,sub_children)
            
        
    def suggestAssetName(self):

        # look for the highest level objects
        # strip out and suffixes ("_grp", _GRP, GEO, )
        # strip out any "p" (poly prefixes)
        # comapre against avail asset names
        return result


    def doCreateAssetLocal(self):
        print("Creating Asset")
        cmds.undoInfo(openChunk=True,chunkName="GSAssetMakerPrepAsset")
        ns = str(self.nameLE.text())
        createAssetBase(str(self.nameLE.text()))

        # for geometry in list
        # check if geometry is referenced or already in a namespace
        sel_list = []
        for key in self.data_model:
            onm = str(self.data_model[key]['geom'])
            self.replace_lambert1([onm])
            rn = self.add_namespace_to_children(ns,[onm])
            sel_list.extend(rn)

        temp_grp = cmds.createNode('transform',n="{0}:g_offset".format(ns))
        cmds.parent(sel_list,temp_grp)

        if cmds.objExists("AssetMaker_asset_xform"):
            asset_t = cmds.getAttr("AssetMaker_asset_xform.translate")[0]
            asset_r = cmds.getAttr("AssetMaker_asset_xform.rotate")[0]
            asset_s = cmds.getAttr("AssetMaker_asset_xform.scale")[0]
            cmds.move(asset_t[0]*-1, asset_t[1]*-1, asset_t[2]*-1, temp_grp)
            cmds.rotate(asset_r[0]*-1, asset_r[1]*-1, asset_r[2]*-1, temp_grp)
            cmds.scale(1/asset_s[0], 1/asset_s[1], 1/asset_s[2], temp_grp)
            nl = cmds.rename("AssetMaker_asset_xform","{0}_placement".format(ns))
            cmds.parent(temp_grp,"{0}:g_geo".format(ns))
            cmds.parent("{0}:root".format(ns),nl)
        else:
            cmds.parent(temp_grp,"{0}:g_geo".format(ns))

        cmds.undoInfo(closeChunk=True)

        self.clearCreateAsset()
        return ns

    def doCreateAssetRef(self):
        asset_name = self.doCreateAssetLocal()
        asset_root = self.doExportAsset(asset_name)

    def doExportAsset(self, namespace):
        ## eventually this will need to work with new pipeline
        # 1. prep the asset for exporting
        #   gather all the connected shaders for exporting
        #   disconnect animation curves
        #   set controllers to default/orig locations
        #   determine what is in the model / rig / shading partition
        # 2. export each partition of the rig to the appropriate work location
        # 3. compile the rig & lookdev from scratch

        print("Creating Asset")
        # get asset placer
        placer = '{0}_placement'.format(namespace)
        asset_name = str(namespace)
        if not cmds.objExists(placer):
            placer = ''


        # get asset root
        asset_root  = '{0}:{0}_grp'.format(namespace)
        if not cmds.objExists(placer):
            print ('Hmm something went wrong, I was looking for asset root:{0}. Check to make sure asset exists in scene before exporting').format(asset_root)
            return

        striped_asset_root = '{0}_grp'.format(namespace)

        # store a list of objects in the asset for later deletion
        nodes_to_delete = cmds.ls('{0}:*'.format(namespace))

        # select root node as well as rigset and cacheset
        cmds.select(nodes_to_delete, ne=True)

        # strip namespace
        cmds.namespace(mergeNamespaceWithRoot=True, removeNamespace=namespace)

        # export asset root to scenefile
        cmds.parent(striped_asset_root,w=True)

        asset_path = self.createAssetDir(job='',asset_name=namespace)
        asset_version = 'v000'
        artists = os.environ['GSINITIALS']
        file_name = '{0}.mb'.format(asset_name)
        print ('RefAsset: {0}:{1}'.format(file_name,asset_path))
        asset_scenefile = os.path.join(asset_path,file_name)
        asset_scenefile_versioned =os.path.join(asset_path,'_versions','{0}_{1}_{2}.mb'.format(asset_name,asset_version,artists))



        cmds.file(asset_scenefile,force=True, options="v=0", typ="mayaBinary", pr=True, es=True)
        cmds.file(asset_scenefile_versioned,force=True, options="v=0", typ="mayaBinary", pr=True, es=True)

        # delete nodes unless they are referenced, unlock nodes if necessary
        #for n in nodes_to_delete:
        #    n_striped = n.split[]
        #    if cmds.objExits(n):
        #        cmds.lockNode(n,l=False)
        #        cmds.delete(n)

        # make sure asset is deleted
        if cmds.namespace(exists=namespace):
            cmds.namespace(deleteNamespaceContent=True, removeNamespace=namespace)

        # create a reference to the asset
        cmds.file(asset_scenefile,r=True, typ='mayaBinary',ignoreVersion=True, gl=True, namespace=namespace,options='v=0;')

        # find the asset root and parent it to the placement locator
        if cmds.objExists(asset_root):
            cmds.parent(asset_root,placer)

        return asset_root


    def verifyAssetName():
        # check against job asset names
        # check against local namespaces
        # always starts with uppercase
        # doesn't end in digits 0-9
        return

    def createAssetDir(self, job, asset_name):
        asset_path = ''
        ''' wrapper function for creating assets, this should be adapted to the pipeline way of creating things'''
        if job == '':
            if 'GSPROJECT' in os.environ:
                job = os.environ['GSPROJECT']

        asset_dir = os.path.join(job,'production','01_cg','01_MAYA','scenes','01_cg_elements','01_models')
        if not os.path.exists(asset_dir):
            print ('Could not find asset lib path {0}'.format(asset_dir))
            return

        asset_path = os.path.join(asset_dir,asset_name)
        if os.path.exists(asset_path):
            print ('Asset Already Exists, {0} Please Rename Your Asset Namespace '.format(asset_path))
            return
        else :
            os.mkdir(os.path.join(asset_path))
            os.mkdir(os.path.join(asset_path,'_pipeline'))
            os.mkdir(os.path.join(asset_path,'_scrap'))
            os.mkdir(os.path.join(asset_path,'_versions'))


        return asset_path

    def replace_lambert1(self,geom_list):
        for o in geom_list:
            sg = ''
            shapes = cmds.listRelatives(o,shapes=True,f=True,ni=True)
            if shapes:
                sgs = cmds.listConnections(shapes[0]+'.instObjGroups[0]')
                sg = str(sgs[0])
            print ('checking for lambert1 sg={0}'.format(sg))
            if str(sg) == 'initialShadingGroup':
                new_sg = 'base_lambertSG'
                new_sh = 'base_lambert'
                if not cmds.objExists(new_sg):
                    new_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=new_sg) 
                    new_sh = cmds.shadingNode('lambert',asShader=True,n=new_sh)
                    cmds.connectAttr((new_sh+'.outColor'),(new_sg+'.surfaceShader'))
                print ('Reassigning initialShadingGroup on {0} to {1}'.format(o,new_sg))
                cmds.sets(shapes,e=True,forceElement=new_sg)


    def add_namespace_to_children(self, namespace, child_list):
        ''' iterate through all children and rename them with the new namespace'''
        ren_list = []
        if child_list:
            for c in child_list:
                sub_children = cmds.listRelatives(c,f=True,typ="transform",ni=True)
                if sub_children:
                    print ('renaming children')
                    self.add_namespace_to_children(namespace,sub_children)
                sn = cmds.ls(c,sn=1)[0]
                no_ns = sn.split(":")[-1]
                nn = '{0}:{1}'.format(namespace,str(no_ns))
                print "Renaming {0} to {1}".format(str(c),nn)
                new_name = cmds.rename(str(c),nn)
                ren_list.append(new_name)
                new_dagName = cmds.ls(new_name,l=True)
                print ("new_dagName = {0}".format(new_dagName))
                if self.renameShader:
                    self.add_namespace_to_shaders(namespace,new_dagName)
        return ren_list


    def add_namespace_to_shaders(self, namespace, geom_list):
        # get sg nodes but remove duplicates by casting to a set()
        sh_nodes = list(set(self.get_shading_nodes(geom_list)))
        for n in sh_nodes:
            if n != 'initialShadingGroup' and n != 'lambert1':
                no_ns = n.split(":")[-1]
                nn = '{0}:{1}'.format(namespace,str(no_ns))
                print ('renaming shader {0} to {1}'.format(str(n),nn))
                cmds.rename(n,nn)

    def get_shading_nodes(self, obj_list, force_dupe=False):
        print ("shading object list")
        print obj_list
        # isolate the upstream network for renaming
        sgroups = []
        shaders = []
        sh_nodes = []
        all_sg_nodes = []
        response = 'dupilicate'

        for o in obj_list:
            shapes = cmds.listRelatives(o,shapes=True,f=True)
            if shapes:
                sgs = cmds.listConnections(shapes[0]+'.instObjGroups[0]')
                if sgs:
                    sgroups.append(sgs[0])
                    shdrs = cmds.listConnections(sgs[0]+'.surfaceShader')
                    if shdrs:
                        shaders.append(shdrs[0])

        # determine if connected to other non-asset geom, 
        # if so give warning (continue, duplicate shader, cancel)
        has_shared_shader = False
        for sg in sgroups:
            connected_shapes = cmds.sets(sg,q=True) #cmds.listConnections(sg+'.dagSetMembers')
            connected = cmds.listRelatives(connected_shapes,p=True)
            for c in connected:
                if c not in obj_list:
                    has_shared_shader = True
            if has_shared_shader:
                #if not force_dupe:
                    ###response = cmds.prompt("")
                if response == 'duplicate':
                    for c in connected:
                        if c in obj_list:
                            shdrs = cmds.listConnections(sgs[0]+'.surfaceShader') 
                            new_shader = cmds.duplicate(shdrs[0],upstreamNodes=True)
                            ###new_shader = cmds.duplicate(shdrs[0],ch=True,shading=True)
                            ###cmds.sets(-fc new_shader)
                elif response == 'cancel':
                    return

        # check all sg_nodes for downstream connections to non-asset nodes
        for s in shaders:
            shaderHistory = cmds.listHistory(s,ac=True)
            sh_nodes.extend(shaderHistory) 
        #    for n in shaderHistory:

        all_sg_nodes.extend(sgroups)
        all_sg_nodes.extend(shaders)
        all_sg_nodes.extend(sh_nodes)
        print ("all_sg_nodes={0}".format(all_sg_nodes))
        return all_sg_nodes


    def doCancel(self):
        self.parent.close()

    # need to fix issue with parent only working on the root level
    def addItemToObjList(self, item, parent=''):

        if parent == '':
            self.data_model[item] = {'geom':item,'shader':''}
        else:
            print ("adding to model: {0} parent={1})".format(item,parent))
            if parent in self.data_model:
                if 'children' not in self.data_model[parent]:
                    self.data_model[parent]['children'] = {}
                if item not in self.data_model[parent]['children']:
                    self.data_model[parent]['children'][item] = {'geom':item,'shader':''}

    def addItemsFromDagPaths(self, model_dict, paths):

        cp = os.path.commonprefix(paths)
        last = '|{0}'.format(cp.split('|')[-1])
        # add back the last element of the common prefix
        cp = cp[:len(cp)-len(last)]
        for o in sorted(paths):
            unique_path = o[len(cp):]
            h = unique_path.split('|')
            # skip the zero element since it defines the dag root
            if h[1] not in model_dict:
                model_dict[h[1]] = {'geom':h[1],'shader':'','children':{}}
                model_dict[h[1]]['shader'] = self.getShaderFromObj(o)
                model_dict[h[1]]['dagpath'] = str(o)
            d = model_dict[h[1]]
            if len(h)>2:
                for i in range(2,len(h)):
                    if h[i] not in d['children']:
                        d['children'][h[i]] = {'geom':h[i],'shader':'','children':{}}
                        # get shader
                        d['children'][h[i]]['shader'] = self.getShaderFromObj(o)
                        d['children'][h[i]]['dagpath'] = str(o)
                    d = d['children'][h[i]]

    
    def getSGFromObj (self, obj_name):
        result = ''
        try:
            shapes = cmds.listRelatives(obj_name,shapes=True,f=True,ni=True)
            if shapes:
                sgs = cmds.listConnections(shapes[0]+'.instObjGroups[0]')
                result = str(sgs[0])
        except:
            print('Failed to get shading group from "{0}"'.format(obj_name))
        return result        

    def getShaderFromSG (self, sg_name):
        result = ''
        try:
            shdrs = cmds.listConnections(sg_name+'.surfaceShader')
            if shdrs:
                result = str(shdrs[0])
        except:
            print('Failed to get shader from SG "{0}"'.format(sg_name))
        return result

    def getShaderFromObj (self, obj_name):
        result = ''
        sg = self.getSGFromObj(obj_name)
        result = self.getShaderFromSG(sg)
        return result
        #result = ''
        #shapes = cmds.listRelatives(obj_name,shapes=True,f=True,ni=True)
        #if shapes:
        #    sgs = cmds.listConnections(shapes[0]+'.instObjGroups[0]')
        #    if sgs:
        #        shdrs = cmds.listConnections(sgs[0]+'.surfaceShader')
        #        result = str(shdrs[0])
        #return result


    def procLoadDictToQItem(self, parent_item, headers_list, modelDict):

        for key in sorted(modelDict):
            subitem_list = []
            for header in headers_list:
                qsubitem = None
                if header in modelDict[key]:
                    qsubitem = QStandardItem(str(modelDict[key][header]))
                else:
                    qsubitem = QStandardItem('')
                qsubitem.setSizeHint(QSize(60,20))
                subitem_list.append(qsubitem)
            parent_item.appendRow(subitem_list)

            
            #if type(parent_item) == type(QStandardItem()):
            #    index = self.obj_list_model.indexFromItem(parent_item)
            #    self.obj_list.setExpanded(index,True) 

            # recurse on any children dictionaries
            if 'children' in modelDict[key]:
                self.procLoadDictToQItem(subitem_list[0],headers_list,modelDict[key]['children'])



    def updateViewModelFromDict(self, modelDict):
        ''' given a dictionary, parse through each key and fill the item model with the data
            this is a quickway to set lots of data with minimal QT CustomSortFilterProxyModel
        '''
        self.obj_list_model.clear()

        # get list of headers
        headers_list = ['geom','shader']
        for key in sorted(modelDict):
            item = sorted(modelDict[key])
            for subkey in item:
                if subkey not in headers_list and subkey != 'children' and subkey != 'dagpath':
                    headers_list.append(subkey)

        # recursively load the dict and any children items
        item_list = self.procLoadDictToQItem(self.obj_list_model,headers_list,modelDict)

        # make nice title names for headers
        for i in range(len(headers_list)):
            headers_list[i] = headers_list[i].title()

        self.obj_list_model.setHorizontalHeaderLabels(headers_list)
        self.obj_list.setColumnWidth(0, 200)

        #for col in range(1,len(headers_list),1):
        #    self.obj_list.setColumnHidden(col,True)

def exportAsset(filePath, keepHistory=True, keepShaders=True):
    # export the shader
    return


def createAssetBase(namespace=":"):
    cns = cmds.namespaceInfo( currentNamespace=True )
    valid_ns = ""
    if cns != namespace:
        if cmds.namespace(exists=namespace):
            cmds.warning("{0} namespace already exists. Please choose another".format(namespace))
            return
        valid_ns = cmds.namespace(add=namespace)
        valid_ns = cmds.namespace(set=valid_ns)
    #try:
    groups = []
    groups.append(cmds.group(em=1, n='g_geo'))
    groups.append(cmds.group(em=1, n='g_rig'))
    groups.append(cmds.group(em=1, n='g_guts'))
    cmds.select(groups, add=1)
    groups.append(cmds.group(n='root'))
    axes = ['x', 'y', 'z']
    chans = ['t', 'r', 's']
    for a in axes:
        for b in chans:
            for group in groups:
                cmds.setAttr(group + '.' + b + a, lock=1)

    #for g in groups:
        #cmds.lockNode(group, lock=True)

    keyable = cmds.sets(n='s_keyable', em=1)
    cacheset = cmds.sets(n='s_cache', em=1)
    
    subd = cmds.sets(n='s_subd', em=1)
    obj = cmds.sets(n='s_obj', em=1)
    creases = cmds.sets(n='s_creases', em=1)
    render = cmds.sets(subd,obj,creases,n='s_render')
    rigset = cmds.sets(n='s_rig', em=1)

    cmds.sets( keyable, cacheset, render, rigset, n="sets")
    #cmds.lockNode(cacheset, lock=1)
    #cmds.lockNode(rigset, lock=1)
    #except:
    #    cmds.warning("Couldn't create default DAG groups for asset.")

    cmds.namespace(set=cns)

def get_assets_in_scene():
    obj_list = {}
    
    ref_nodes = cmds.file(q=1,r=1)
    for r in ref_nodes:

        ref_path = cmds.referenceQuery(r,f=1,wcn=1)
        # NEED TO ADD: check if the reference is within an asset library
        ref_ns = cmds.file(r,q=1,namespace=1)
        ref_cacheset = cmds.ls((ref_ns+':CACHEset'),type='objectSet')
        asset_name = ref_ns

        # search for attached cache
        found_cache = ''
        abc_nodes = cmds.ls((ref_ns)+(':*'),type='ExocortexAlembicFile',r=1,long=1)
        if len(abc_nodes)>0:
            file_path = cmds.getAttr(abc_nodes[0]+'.fileName')
            found_cache = get_shot_version(file_path,'cache','current',False,asset_name=asset_name)

        print('Asset name is '+asset_name)
        obj_list[asset_name] = {}
        obj_list[asset_name]['cache_set'] = ref_cacheset
        obj_list[asset_name]['ref_node'] = r
        obj_list[asset_name]['file_path'] = ref_path
        obj_list[asset_name]['current_cache'] = found_cache
        obj_list[asset_name]['latest_cache'] = get_shot_version(cmds.file(q=1,sn=1),'cache','latest',False,asset_name=asset_name,dept='animation')
        #except:
        #   print (a+' is not a referenced asset, skipping')

    return obj_list

def get_output_from_scene():
    ''' returns the output path from the currently open scenefile'''
    scenefile = cmds.file(q=1,sn=1)
    shot_info = get_shot_info_from_path(scenefile)
    return get_alembic_output_path(shot_info)

def get_shot_info_from_path(file_path=''):
    ''' returns shot information based on the file path '''
    shot_info = {}
    shot_info['valid'] = False
    if file_path == '':
        file_path = cmds.file(q=1,sn=1)

    if file_path != '':
        basename = os.path.basename(file_path)
        ext = basename.split('.')[-1]
        dir_folder = os.path.dirname(file_path)
        server_split = os.path.splitunc(file_path)
        #print ("server split="+server_split[1])
        shot_info['server'] = server_split[0].replace('/','\\')
        shot_info['job'] = server_split[1].split('/')[1]
        shot_info['shot'] = server_split[1].split('/')[7]
        shot_info['dept'] = server_split[1].split('/')[8]
        try: 
            shot_info['cam_version'] = basename.split('_')[1] 
            shot_info['anim_version'] = basename.split('_')[2]
            shot_info['light_version'] = basename.split('_')[3]
        except:
            shot_info['cam_version'] = ''
            shot_info['anim_version'] = ''
            shot_info['light_version'] = '' 
        shot_info['valid'] = True
        #except:
        #   print("Not a valid shot")
    return shot_info

def get_shot_version(file_path='', type='', which='latest',full_path=False, asset_name='', dept=''):
    ''' Given a file path, determine shot info and return the latest found version
    type=cache||work||publish||master) version=A001||latest||current'''

    shot_info = get_shot_info_from_path(file_path)
    if dept != '':
        shot_info['dept'] =  dept
    ext, subd, dir_name, file_name = '', '', '', ''

    if type == 'cache':
        subd = 'cache'
        ext = 'abc'
    elif type == 'work': 
        subd = ''
        ext = 'mb'

    # gather information based on file path given
    if shot_info['valid'] == True:
        if shot_info['dept'] != '':
            search_path = os.path.join(shot_info['server'],shot_info['job'],'03_production','01_cg','01_MAYA','scenes','02_cg_scenes',shot_info['shot'],shot_info['dept'],subd)

            # determine which version info is of interest and set it to input if avail
            v_str, v_prefix, ver_placement = '', '', 1
            if shot_info['dept'] == 'camera':
                ver_placement = 2
                v_prefix = 'C'
                v_str = shot_info['cam_version'] 
            elif shot_info['dept'] == 'animation':
                ver_placement = 2
                v_prefix = 'A'
                v_str = shot_info['anim_version'] 
            elif shot_info['dept'] == 'lighting':
                ver_placement = 3
                v_prefix = 'L'
                v_str = shot_info['light_version'] 
            
            file_name = (shot_info['shot']+'_*.'+ext)

            # if its a cache we need to search within a subfolder so lets add it to the glob search <scene_name>/<scene_name>_<asset>.abc
            if type == 'cache':
                if which == 'latest':
                    file_name = (shot_info['shot']+'_*')
                elif which == 'current':
                    file_name = '_'.join((shot_info['shot'],shot_info['cam_version'],shot_info['anim_version'],shot_info['light_version']))
                if asset_name != '':
                    file_name += ('/'+shot_info['shot']+'_*_'+asset_name+'.'+ext)

            glob_path = os.path.join(search_path,file_name)
            file_list = glob.glob(glob_path)    
            print ('Searching Glob: '+glob_path)
            print (file_list)

            # if latest found version is requested
            if which == 'latest':
                max_ver, max_file, f = 0, '', ''
                for f in file_list:
                    bn = os.path.basename(f)
                    v = bn.split('_')[ver_placement]
                    num_only = re.search(r'[0-9]+', v).group(0)
                    v_int = int(num_only)
                    if v_int > max_ver:
                        max_ver = v_int
                        max_file = f
                    v_str = (v_prefix+str(max_ver).zfill(3))

            if full_path == True:
                return f #os.path.join(search_path,max_file)
            else:
                return v_str

        else:
            print ("Could not determine Department from shot_info:")
            print shot_info
            return ''
    else:
        print ("Not a valid shot")
        return ''


def get_alembic_output_path(shot_info={}):
    ''' given a shot_info (returned from a call to get_shot_info_from_path()) this will return an abc output path '''
    output_path = ''
    if len(shot_info) > 1:
        dir_name = "_".join((shot_info['shot'],shot_info['cam_version'],shot_info['anim_version'],shot_info['light_version']))
        file_name = (dir_name+'.abc')
        output_path = os.path.join(shot_info['server'],shot_info['job'],'03_production','01_cg','01_MAYA','scenes','02_cg_scenes',shot_info['shot'],shot_info['dept'],'cache',dir_name)
    return output_path


def exportAlembicCache(out_path='', obj_list=[], in_frame=101, out_frame=201, step=1):
    """ exports the alembic cache to a preconfigured location """
    job_strings = []
    print obj_list

    for a in obj_list:
        cache_set = (a+':CACHEset')
        try:
            obj_list = cmds.sets(str(cache_set),q=1)
        except:
            obj_list = ()
        obj_str= ','.join(obj_list)
        out_filename = os.path.basename(out_path)+'_'+a+'.abc'
        asset_out_path = os.path.join(out_path,out_filename)
        try: 
            os.makedirs(os.path.join(out_path))
        except OSError:
            if not os.path.isdir(os.path.join(out_path)):
                raise

        job_str = ('filename='+asset_out_path+';')
        job_str += ('objects='+obj_str+';')
        job_str += ('uvs=0;')
        job_str += ('globalspace=1;')
        job_str += ('withouthierarchy=1;')
        job_str += ('in='+in_frame+';')
        job_str += ('out='+out_frame+';')
        job_str += ('step='+step+';')
        job_str += ('ogawa=1')
        job_strings.append(job_str)
    cmds.ExocortexAlembic_export(j=job_strings)
    writeAssetDetails(out_path)


def writeAssetDetails(out_path='', obj_list=[]):
    asset_info = get_assets_in_scene()
    remove_assets = []
    # remove any asset data that isn't in the obj_list argument
    for a in asset_info:
        if any(a in s for s in obj_list):
            remove_assets.append(str(a))

    for a in remove_assets:
        del asset_info[a]

    if out_path != '':
        out_filename = os.path.basename(out_path)+'.yml'
        out_file =os.path.join(out_path,out_filename)
        with open(out_file, 'w') as f:
            f.write( yaml.safe_dump(asset_info, default_flow_style=False, encoding='utf-8', allow_unicode=False) )

# this needs to be broken down to doing a single alembic cache at a time
# the UI is what should handle doing multiple assets
# given a file path, locate the relavent shot info
# determine if there is a newer version

def updateAlembicCache(in_path='', obj_list=[], add_missing=True, ref_replace='', version='latest'):
    # locate asset details.yml
    # shot_info = 
    abc_version = get_shot_version(in_path,'cache','latest',True)
    abc_filename = os.path.basename(abc_version)
    asset_details_file = os.path.join(abc_version,(abc_filename+".yml"))
    if not os.path.isfile(asset_details_file):
        cmds.error("Cache Header File not found. Are you in a pipeline scenefile?")
    try:
        f = open(asset_details_file)
        asset_details = yaml.safe_load(f)
        f.close()
    except:
        print ('Could not locate ' + asset_details_file)
        raise
    

    # go to the master layer
    # if no assets are specified, update all assets from the details file
    if len(obj_list) < 1:
        for a in asset_details:
            obj_list.append(a)

    # for each asset in obj_list
    for a in obj_list:
        cache_file = get_shot_version(in_path,'cache','latest',True,a)
        print ('CACHE FILE='+cache_file)
        # if add_missing is true
        if asset_details[a]:
            print ('checking for '+asset_details[a]['ref_node'])
            if not cmds.objExists(asset_details[a]['ref_node']):
                # create missing references
                anim_ref_path = asset_details[a]['file_path']
                light_ref_path = os.path.join(os.path.dirname(anim_ref_path),'shade',os.path.basename(anim_ref_path))
                cmds.file(light_ref_path,r=1,loadReferenceDepth='all',namespace=a,options="v=0")
                cmds.namespace(set=a)
                job_str = ('filename='+cache_file+';')
                job_str += ('attachToExisting=1;')
                job_str += ('uvs=0;')
                job_str += ('facesets=0;')
                job_str += ('search=(Deformed)|(Orig);')
                job_str += ('replace=(?1)(?2)')
                try:
                    cmds.ExocortexAlembic_import (j=job_str)
                except:
                    print ("Errors while running ExocortexAlembic_import")
                cmds.namespace(set=':')
            
            # if alembic node exists
            file_node = (a+":ExocortexAlembicFile1")
            if cmds.objExists(file_node):
                file_node_path = cmds.getAttr((file_node+'.fileName'))
                expanded_path =  cmds.workspace(expandName=file_node_path)
                if not expanded_path == cache_file:
                    cmds.setAttr((file_node+'.fileName'), cache_file, type='string');
                    print ("Remapped "+file_node+" to "+cache_file)
                else:
                    print ("Skipping "+file_node)
                # update to version
                # confirm alembic node connections to all geo
                # call alembic crate update Callback
            # else
                # call alembic crate attach function

def get_alembic_in_scene():
    abc_list = {}

    ea_file_nodes = cmds.ls(type='ExocortexAlembicFile',long=1)
    for e in ea_file_nodes:
        abc_ns = cmds.ls(e,sns=1)[-1]
        abc_list[e] = {}
        abc_list[e]['name_space'] = abc_ns
        abc_list[asset_name]['file_path'] = cmds.getAttr((e+'.fileName'))
        abc_list[asset_name]['latest_cache'] = get_shot_version(cmds.file(q=1,sn=1),'cache','latest',False,asset_name=abc_ns)

    return abc_list



#if __name__ == '__main__':
#   app = QApplication(sys.argv)
#   wind = StudioAlembicUIWindow()
#   wind.setWindowTitle(('Studio Tools -'+MODE))
#   wind.show()
#   app.exec_()



#def loadGSAssetMakerUI(standalone=False):
#    
#    if standalone:
#        wind = get_maya_window()
#        widg = GSAssetMakerWindow(parent=wind)
#        widg.setWindowFlags( Qt.FramelessWindowHint )
#
#    else:
#        wind = get_maya_window(window='GSAssetMakerWindow', title='GSAssetMaker')
#        wind_lyt = QHBoxLayout()
#        widg = GSAssetMakerWindow(wind)
#        wind_lyt.setContentsMargins(0,0,0,0)
#        wind_lyt.addWidget(widg)
#        wind.setLayout(wind_lyt)
#        cmds.showWindow('GSAssetMakerWindow')
#
#
#loadGSAssetMakerUI()
#if __name__ == '__main__':
def main():
    wind = GSAssetMakerWindow()
    wind.show()
    windMayaName = wind.objectName()