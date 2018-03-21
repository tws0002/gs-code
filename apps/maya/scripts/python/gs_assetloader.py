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

omui.MQtUtil.mainWindow()    

import os, sys, re
import gscore
import time, datetime
from collections import OrderedDict
import yaml

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget) 

class GSAssetLoaderWindow(MayaQWidgetBaseMixin,QWidget):

    data_model = {}
    obj_list_model = None
    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSAssetLoaderWindow, self).__init__(parent=parent, *args, **kwargs) 

        self.resize(900, 500)

        # setup the core handler
        # initialize the project controller. specify a project.yml file to load as the template file
        self.proj = gscore.projects.ProjectController('{0}/projects.yml'.format(os.environ['GSCONFIG']))
        self.p_dict = self.proj.pathParser.parsePath('{0}/production'.format(os.environ['GSPROJECT']))

        self.title = "Asset Loader v0.2a"
        self.setWindowTitle(self.title)

        self.ui_state = {
            'f_data': {},
            'version': '',
            'camera': '',
            'start': 0,
            'end': 0,
            'step': 1,
            'asset_tab': 'asset_3d',
            'asset_item': '',
            'task_combo': ''
        }

        # main layout
        self.main_layout = QVBoxLayout(self)
        self.locationlyt = QHBoxLayout()

        #self.main_layout.addSpacing(40)
        self.pane_split = QSplitter()

        # location bar
        spl = self.p_dict['job'].split('_')
        scene_name = cmds.file(q=1,sn=1,shn=1).split('.')[0]
        proj_nice_name = '{0} {1}  |  {2}'.format(spl[0].title(),spl[1].title(),scene_name)
        self.projectlbl = QLabel(proj_nice_name)
        font = self.projectlbl.font()
        font.setPointSize(12)
        self.projectlbl.setFont(font)

        self.asset_lib_tab = QTabWidget()
        # asset loader
        self.asset_lib = GSAssetLoaderAssetLib(self)
        self.lr_del = LargeRowDelegate()
        self.asset_lib.tree_list.tvw.setItemDelegate(self.lr_del)

        self.shot_lib = GSAssetLoaderAssetLib(self)
        self.shot_lib.tree_list.tvw.setItemDelegate(self.lr_del)        

        self.in_scene_list = GSAssetLoaderInSceneList(self)
        self.in_scene_list.tree_list.tvw.setItemDelegate(self.lr_del)
        self.in_scene_list.tree_list.hidden_headers = ['filepath','is_group','5:ref_node','status', 'group']
        self.editorDelegate = ComboBoxDelegate()
        self.in_scene_list.tree_list.tvw.setItemDelegate(self.editorDelegate)
        #self.asset_lib.parent_class = self

        #### LAYOUT ####

        self.asset_lib_tab.addTab(self.asset_lib,'3D Assets')
        self.asset_lib_tab.addTab(self.shot_lib,'Shots')

        self.locationlyt.addWidget(self.projectlbl)

        self.main_layout.addLayout(self.locationlyt)
        self.main_layout.addWidget(self.pane_split)
        self.main_layout.setStretchFactor(self.pane_split,1)

        self.pane_split.addWidget(self.asset_lib_tab)
        self.pane_split.addWidget(self.in_scene_list)
        self.pane_split.setSizes([100, 500])

        self.asset_lib.asset_type = 'asset_3d'
        self.updateAssetList('asset_3d')
        self.updateAssetTaskCombo('asset_3d')
        self.shot_lib.asset_type = 'shot'
        self.updateAssetList('shot')
        self.updateAssetTaskCombo('shot')

        self.asset_lib_tab.currentChanged.connect(self.assetTabChanged)
        
        self.updateInSceneAssets()


    def updateAssetList(self, asset_type='asset_3d'):

        # get a python dictionary that parses the shot properties from the file
        
        # get a list of shots for a stage of production
        asset_lib, asset_names = self.proj.getAssetsList(upl_dict=self.p_dict, asset_type=asset_type)   
        item_dict = {}
        #item_dict[asset_type] = {'name':asset_type,'children':{}}
        for item in sorted(asset_names):
            split_name = item.split('/')
            if not split_name[0] in item_dict:
                item_dict[split_name[0]] = {}
                item_dict[split_name[0]]['name'] = split_name[0]
                item_dict[split_name[0]]['filepath'] = '/'.join([asset_lib,split_name[0]])
                item_dict[split_name[0]]['status'] = "Active"
                item_dict[split_name[0]]['is_group'] = False
                item_dict[split_name[0]]['group'] = ''
                item_dict[split_name[0]]['children'] = {}
            if len(split_name) > 1:
                item_dict[split_name[0]]['is_group'] = True
                item_dict[split_name[0]]['children'][split_name[1]] = {}
                item_dict[split_name[0]]['children'][split_name[1]]['name'] = split_name[1]
                item_dict[split_name[0]]['children'][split_name[1]]['filepath'] = '/'.join([asset_lib,split_name[0],split_name[1]])
                item_dict[split_name[0]]['children'][split_name[1]]['status'] = "Active"
                item_dict[split_name[0]]['children'][split_name[1]]['is_group'] = False
                item_dict[split_name[0]]['children'][split_name[1]]['group'] = split_name[0]

        print ("Asset_Type:{0} Asset_Data:({1},{2})".format(asset_type,asset_lib,asset_names))
        # loads the above dictionary into a treeview as standard items
        if asset_type == 'asset_3d':
            self.asset_lib.tree_list.loadViewModelFromDict(item_dict)
            self.asset_lib.tree_list.current_path = asset_lib
        elif asset_type == 'shot':
            self.shot_lib.tree_list.loadViewModelFromDict(item_dict)
            self.shot_lib.tree_list.current_path = asset_lib

    def assetTabChanged(self):
        vis_item = self.asset_lib_tab.currentWidget()
        if vis_item:
            self.ui_state['asset_tab'] = vis_item.asset_type

    def updateAssetTaskCombo(self, asset_type='asset_3d'):
        default_tasks = self.proj.getDefaultTasks(asset_type=asset_type)
        valid_tasks = ['model', 'rig', 'lookdev', 'anim', 'effects', 'layout']
        print default_tasks
        for name in default_tasks:
            if name != '' and name in valid_tasks:
                item = QStandardItem(name)
                if asset_type == 'asset_3d':
                    self.asset_lib.typecombo.model().appendRow(item)
                elif asset_type == 'shot':
                    self.shot_lib.typecombo.model().appendRow(item)

    def addReference(self, asset_type='asset_3d'):

        print 'Current Tab is {0}'.format(self.ui_state['asset_tab'])
        if self.ui_state['asset_tab'] == 'asset_3d':
            sel_item = self.asset_lib.tree_list.getSelectedItems()
            task = str(self.asset_lib.typecombo.currentText())
        elif self.ui_state['asset_tab'] == 'shot':
            sel_item = self.shot_lib.tree_list.getSelectedItems()
            task = str(self.shot_lib.typecombo.currentText())
        
        if len(sel_item):
            a_name = str(sel_item[0].text())
            a_path = str(sel_item[1].text())
            print ('selected asset={0} {1}'.format(a_name,a_path))
            
            #ad = dict(self.p_dict)
            f_data = self.proj.pathParser.parsePath(a_path)
            #if 'task' not in f_data:
            #    print ("Could not determine shot location {0}".format(f_data))
            #    return

            f_data['task'] = task
            print ('task={0}'.format(f_data['task']))
            f_data['scenename'] = 'main'
            f_data['package'] = 'maya'
            f_data['layer'] = 'publish'
            f_data['ext'] = 'mb'

            # get the latest version of publish path
            print f_data
            pub_root, pub_files = self.proj.getScenefileList(upl_dict=f_data, scene_type='publish', latest_version=True)
            print ('latest_publish={0} {1}'.format(pub_root,pub_files))

            if not os.path.isdir(pub_root):
                cmds.confirmDialog( title='Publish Not Found:', message='Publish Not Found: {0} {1} Check to make sure it has been published'.format(a_name,f_data['task']), button=['Ok'], defaultButton='Ok', cancelButton='Ok', dismissString='Ok' )
                #cmds.error('No publish found for Asset: Looking for {0}'.format(pub_root))
                return
            else:
                if self.ui_state['asset_tab'] == 'asset_3d':
                    asset_scenefile = '/'.join([pub_root,pub_files[0]])
                    namespace = a_name
                    # TODO if a_name exists and ends with a number, lets add an underscore num (iPhone8_1) instead of just incrementing the 8
                    cmds.file(asset_scenefile,r=True, typ='mayaBinary',ignoreVersion=True, gl=True, namespace=namespace,options='v=0;')
                elif self.ui_state['asset_tab'] == 'shot':
                    assembly_file = '/'.join([pub_root,'{0}.yml'.format(pub_files[0])])
                    self.buildFromAssemblyFile(assembly_file)
                self.updateInSceneAssets()

    def buildFromAssemblyFile(self,filepath, substitute=['rig>lookdev','model>lookdev']):
        try:
            cmds.loadPlugin( 'AbcExport.mll' )
            cmds.loadPlugin( 'AbcImport.mll' )
        except:
            pass
        if os.path.exists(filepath):
            assembly_data = self.getAssemblyData(filepath)
            if 'output_data' in assembly_data:
                for o in assembly_data['output_data']:
                    # TODO check if namespace exists first
                    out_type = str(assembly_data['output_data'][o]['type'])
                    out_name = str(assembly_data['output_data'][o]['name'])
                    out_path = str(assembly_data['output_data'][o]['out_path'])
                    if out_type.startswith("Alembic"):
                        if out_name.startswith("Camera:"):
                            a = assembly_data['output_data'][o]['name'].split(":")[-1]
                            print "cmds.AbcImport({0}, mode='import', connect='{1}')".format(out_path,a)
                            cmds.AbcImport(out_path, mode='import')    
                        else:
                            a = assembly_data['output_data'][o]['name']
                            namespace = assembly_data['asset_data'][a]['namespace']
                            asset_scenefile = assembly_data['asset_data'][a]['filepath']
                            cache_path = assembly_data['asset_data'][a]['cache_path']
                            subst_path = asset_scenefile

                            # load shot location info
                            f_data = self.proj.pathParser.parsePath(asset_scenefile)
                            print ("LOADING ASSET: FDATA:{0}".format(f_data))
                            apply_cache = False
                            if f_data['task'] == 'rig':
                                f_data['task'] = 'lookdev'
                                f_data['layer'] = 'publish'
                                f_data['ext'] = 'mb'
                                pub_root, pub_files = self.proj.getScenefileList(upl_dict=f_data, scene_type='publish', latest_version=True)
                                print ('latest_publish={0} {1}'.format(pub_root,pub_files))
                                if len(pub_files) > 0:
                                    asset_scenefile = '/'.join([pub_root,pub_files[0]])
                                else:
                                    print ("No lookdev publish found for asset {0}".format(a))
                                apply_cache = True

                            #for ea in substitute:
                            #    find_repl = ea.split('>')
                            #    subst_path = subst_path.replace(find_repl[0], find_repl[1])
                            #if os.path.exists (subst_path):
                            #    asset_scenefile = subst_path
                            #else:
                            #    print ("Could not find substuted paths: {0}".format(subst_path))
                            ## TODO if a_name exists and ends with a number, lets add an underscore num (iPhone8_1) instead of just incrementing the 8
                            cmds.file(asset_scenefile,r=True, typ='mayaBinary',ignoreVersion=True, gl=True, namespace=namespace,options='v=0;')   
                            if apply_cache:
                                if os.path.exists(cache_path):
                                    self.attachAlembicCache(namespace, cache_path)
                                else:
                                    print ("Cache for {0} not found: {1}".format(a,cache_path))
                            else:
                                print ("Cache skipped for model asset: {0}".format(a))
                # set camera abc up
                # set frame range
                cmds.playbackOptions(e=1,min=assembly_data['start_frame'],max=assembly_data['end_frame'])
                
        else:
            print ("Could not Locate Assembly File: {0}".format(filepath))

    # AbcImport -mode import -connect "testCharA:g_root|testCharA:g_geo" "C:/projects/ab_testjob/production/shots/s01/005_00/anim/publish/main/v006/s01_005_00_anim_main_v006_testCharA.abc";
    def attachAlembicCache(self, asset_ns, cache_path):

        cache_nodes = cmds.sets("{0}:s_cache".format(asset_ns),q=1)
        print "cmds.AbcImport({0}, mode='import', connect='{1}')".format(cache_path, ' '.join(cache_nodes))
        cmds.AbcImport(cache_path, mode='import', connect=' '.join(cache_nodes))

    def getAssemblyData(self, filepath):
        f = open(filepath)
        # use safe_load instead load
        #dataMap = yaml.safe_load(f)
        try:
            dataMap = yaml.load(f, Loader=yaml.CLoader)
        except AttributeError:
            dataMap = yaml.load(f, Loader=yaml.Loader)
        f.close()
        return dataMap

    def getInSceneAssets(self):
        asset_list = []
        
        ref_nodes = cmds.file(q=1,r=1)
        for r in ref_nodes:
            ref_path = cmds.referenceQuery(r,f=1,wcn=1)
            ref_node = cmds.referenceQuery(r,rfn=1)
            ref_ns = cmds.file(r,q=1,namespace=1)
            asset_list.append((ref_node, ref_path, ref_ns))

        return asset_list

    def updateInSceneAssets(self):
        # populate list with assets found in scene
        assets = self.getInSceneAssets()
        asset_data = {}
        for node, path, namespace in assets:
            print('Asset name is '+namespace)
            f_data = self.proj.pathParser.parsePath(path)
            asset_data[namespace] = {}
            asset_data[namespace]['name'] = namespace
            asset_data[namespace]['filepath'] = path
            asset_data[namespace]['3:Version'] = f_data['version']
            asset_data[namespace]['2:Type'] = f_data['task']
            asset_data[namespace]['4:Applied Cache'] = 'None'
            asset_data[namespace]['5:ref_node'] = node
            asset_data[namespace]['status'] = "Active"
            asset_data[namespace]['is_group'] = False
            asset_data[namespace]['group'] = f_data['asset_grp']

        self.in_scene_list.tree_list.loadViewModelFromDict(asset_data)

    def getSelectedRefs(self):
        sel_refs = self.in_scene_list.tree_list.getSelectedList()
        print ("SELECTED REFS={0}").format(sel_refs)
        # TODO this is terrible way to do this
        return [(sel_refs[4], sel_refs[0], sel_refs[5])]

    def getAlembicInScene(self):
        abc_list = []
        abc_nodes = cmds.ls(type='AlembicFile',long=1)
        for abc in abc_nodes:
            abc_node = abc
            abc_ns = cmds.ls(abc,sns=1)[-1]
            abc_path = cmds.getAttr((abc+'.abc_File'))
            f_data = self.proj.pathParser.parsePath(abc_path)
            abc_version = f_data['version']
            abc_list.append((abc_node, abc_ns, abc_path, abc_version))
        return abc_list

    def doRemoveAsset(self):
        result = cmds.confirmDialog( 
            title='Confirm Asset Remove:', 
            message='This action is not undoable. Please Confirm you want to remove', 
            button=['Remove Asset', 'Cancel'], 
            defaultButton='Remove Asset', 
            cancelButton='Cancel', 
            dismissString='Cancel' )
        if result == 'Remove Asset':
            for ref_n, ref_ns, ref_path in self.getSelectedRefs():
                fp = cmds.referenceQuery(ref_n, filename=1)
                cmds.file(fp, rr=1)
                if cmds.namespace(exists=ref_ns):
                    cmds.namespace(rm=ref_ns, dnc=True)
                print 'Removed Reference: {0}'.format(ref_n)
            self.updateInSceneAssets()
        return

    def doRenameAsset(self):
        return

    def doReloadAsset(self):
        return

    def doUnloadAsset(self):
        return

class GSAssetLoaderAssetLib(MayaQWidgetBaseMixin,QWidget):
    data_model = {}
    obj_list_model = None

    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSAssetLoaderAssetLib, self).__init__(parent=parent, *args, **kwargs) 

        self.parent_class = None

        self.main_lyt = QVBoxLayout()
        self.main_lyt.setContentsMargins(0,0,0,0)
        self.setLayout(self.main_lyt)

        self.headerlyt = QHBoxLayout()
        self.headerlyt.setContentsMargins(0,0,0,0)
        self.footerlyt = QHBoxLayout()
        self.footerlyt.setContentsMargins(5,5,5,5)

        self.title = QLabel('')
        self.tree_list = GSAssetLoaderTreeList()
        self.tree_list.tvw.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.typelbl = QLabel('Type:')
        self.typecombo = QComboBox()
        self.ref_btn = QPushButton('Add To Scene >>')

        font = self.typelbl.font()
        font.setPointSize(12)
        self.typelbl.setFont(font)
        self.typecombo.setFont(font)
        self.ref_btn.setFont(font)
        #self.qtblyt.addWidget(self.titlebtn2)

        self.main_lyt.addLayout(self.headerlyt)
        self.main_lyt.addWidget(self.tree_list)
        self.main_lyt.addLayout(self.footerlyt)
        self.headerlyt.addWidget(self.title)
        self.headerlyt.setStretchFactor(self.title,1)
        self.footerlyt.addWidget(self.typelbl)
        self.footerlyt.addWidget(self.typecombo)
        self.footerlyt.addWidget(self.ref_btn)
        
        #####################
        ###### SIGNALS#######

        self.ref_btn.clicked.connect(self.parent().addReference)
        

class GSAssetLoaderInSceneList(MayaQWidgetBaseMixin,QWidget):

    data_model = {}
    obj_list_model = None

    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSAssetLoaderInSceneList, self).__init__(parent=parent, *args, **kwargs) 

        #### WIDGET CREATE ####
        self.main_lyt = QVBoxLayout()
        self.main_lyt.setContentsMargins(0,0,0,0)
        self.setLayout(self.main_lyt)

        self.toolslyt = QHBoxLayout()
        self.toolslyt.setContentsMargins(0,0,0,0)

        self.footerlyt = QHBoxLayout()
        self.footerlyt.setContentsMargins(0,0,0,0)

        self.refresh = QPushButton('Refresh List')
        self.updateallbtn = QPushButton('Check for Updates')
        self.publishbtn = QPushButton('Publish Anim')
        self.loadbtn = QPushButton('Load from Pubish')


        self.removebtn = QPushButton('Remove')
        self.renamebtn = QPushButton('Rename')
        self.replacebtn = QPushButton('Replace')
        self.reloadbtn = QPushButton('Reload')
        self.unloadbtn = QPushButton('Unload')

        font = self.removebtn.font()
        font.setPointSize(12)
        self.removebtn.setFont(font)
        self.renamebtn.setFont(font)
        self.replacebtn.setFont(font)
        self.reloadbtn.setFont(font)
        self.unloadbtn.setFont(font)

        self.tree_list = GSAssetLoaderTreeList()
        self.tree_list.tvw.setHeaderHidden(False)
        self.tree_list.showFirstColOnly = False

        self.toolslyt.addWidget(self.refresh)
        self.toolslyt.addWidget(self.updateallbtn)
        self.toolslyt.addWidget(self.publishbtn)
        self.toolslyt.addWidget(self.loadbtn)

        #####  WIDGET LAYOUT ######
        self.main_lyt.addWidget(self.tree_list)
        self.footerlyt.addWidget(self.removebtn)
        self.footerlyt.addWidget(self.renamebtn)
        self.footerlyt.addWidget(self.replacebtn)
        self.footerlyt.addWidget(self.reloadbtn)
        self.footerlyt.addWidget(self.unloadbtn)
        self.main_lyt.addWidget(QLabel("In Scene Assets:"))
        self.main_lyt.addWidget(self.tree_list)
        self.main_lyt.addLayout(self.toolslyt)
        self.main_lyt.addLayout(self.footerlyt)

        #### WIDGET SIGNALS #####
        self.removebtn.clicked.connect(self.parent().doRemoveAsset)
        self.renamebtn.clicked.connect(self.parent().doRenameAsset)
        self.reloadbtn.clicked.connect(self.parent().doReloadAsset)
        self.unloadbtn.clicked.connect(self.parent().doUnloadAsset)
        self.refresh.clicked.connect(self.parent().updateInSceneAssets)


class CustomSortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent, title=""):
        super(CustomSortFilterProxyModel, self).__init__(parent)

        self.filter_parents = True

    def filterAcceptsRow(self, row_num, source_parent):
        ''' Overriding the parent function '''
        # Check if the current row matches
        if self.filterAcceptsRowItself(row_num, source_parent):
            return True
        # Traverse up all the way to root and check if any of them match
        if self.filterAcceptsAnyParent(source_parent):
           return True
        # Finally, check if any of the children match
        return self.hasAcceptedChildren(row_num, source_parent)

    def filterAcceptsRowItself(self, row_num, parent):
        return super(CustomSortFilterProxyModel, self).filterAcceptsRow(row_num, parent)

    def filterAcceptsAnyParent(self, parent):
        ''' Traverse to the root node and check if any of the
            ancestors match the filter
        '''
        result = False
        if self.filter_parents == True:
            while parent.isValid():
                if self.filterAcceptsRowItself(parent.row(), parent.parent()):
                    result = True
                parent = parent.parent()
        else:
            result = False
        return result

    def hasAcceptedChildren(self, row_num, parent):
        ''' Starting from the current node as root, traverse all
            the descendants and test if any of the children match
        '''
        model = self.sourceModel()
        source_index = model.index(row_num, 0, parent)
     
        children_count =  model.rowCount(source_index)
        for i in xrange(children_count):
            if self.filterAcceptsRow(i, source_index):
                return True
        return False

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
        string.replace(0, string.count(), string.toUpper())
        return result[0], pos

class GSAssetLoaderTreeList(MayaQWidgetBaseMixin,QWidget):
    ''' Creates a TreeView as well as a line edit that filters the internal model and proxy model
        Also uses a custom proxy model class that allows for searches to work with heirarchies
    '''

    sm = None
    pm = None
    le = None
    tvw = None
    qlyt = None

    # remapped signals
    selectionChanged = None

    def __init__(self, parent=None, *args, **kwargs):
        super(GSAssetLoaderTreeList, self).__init__(parent=parent, *args, **kwargs) 

        self.hidden_headers = []

        # config flags
        self.alwaysExpand = True
        self.showFirstColOnly = True
        self.parent_class = None

        self.qlyt = QVBoxLayout(self)

        self.le = QLineEdit()
        self.tvw = QTreeView()
        model = QStandardItemModel(self.tvw)
        
        self.qlyt.addWidget(self.le)
        self.qlyt.addWidget(self.tvw)

        self.le.setObjectName('LchrListFilter')
        self.le.setPlaceholderText('Search')
        self.tvw.setUniformRowHeights(True)
        self.tvw.setIndentation(8)
        self.tvw.setRootIsDecorated(True)
        self.tvw.setExpandsOnDoubleClick(True)
        self.tvw.setHeaderHidden(True)
        self.tvw.setItemsExpandable(True)
        self.tvw.setAlternatingRowColors(True)
        #self.tvw.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setModel(model)

        # map signal functions
        self.selectionChanged = self.tvw.selectionModel().selectionChanged

        # connect internal signals
        self.le.textChanged.connect(self.filterListEditChanged)

    def sourceModel(self):
        return self.sm

    def proxyModel(self):
        return self.pm

    def treeView(self):
        return self.tvw

    def lineEdit(self):
        return self.le

    def setColumnPersistentEditor(self, column):
        # setup persistant comboboxes
        for row in range(0, self.tvw.model().rowCount()):
            self.tvw.openPersistentEditor(self.tvw.model().index(row, column))
        return

    def setTitle(self,title):
        self.title.setText(title)

    def setFilterParents(self,state):
        self.pm.filter_parents = state

    def setModel(self, stdItemModel):
        self.sm = stdItemModel
        # create an internal proxy model and connect that instead
        self.pm = CustomSortFilterProxyModel(self.tvw)
        self.pm.setSourceModel(self.sm)
        self.pm.setDynamicSortFilter(False)
        self.pm.setFilterRegExp(QRegExp(''))
        self.tvw.setModel(self.pm)
        #super(LchrTreeList, self).__init__(self.pm)

    def setFilterRegExpStr(self, regExpStr):
        self.tvw.clearSelection()
        qregex = QRegExp(regExpStr)
        self.pm.setFilterRegExp(qregex)
        self.tvw.expandAll()

        # set persietent editors on certain columns
        self.setColumnPersistentEditor(1)
        self.setColumnPersistentEditor(2)
        self.setColumnPersistentEditor(3)        
        
    def filterListEditChanged(self):
        regstr = self.le.text()
        if len(regstr) < 2 and len(regstr) > 0:
            regstr = '^{0}'.format(regstr)

        self.setFilterRegExpStr(regstr)

    def getSelectedItems(self):
        items = []
        for index in self.tvw.selectionModel().selectedIndexes():
            # index of selectedModel is for the proxy filter model only, we have to map to the source model to get valid item
            src_index = self.pm.mapToSource(index)
            item = self.sm.itemFromIndex(src_index)
            items.append(item)
        return items

    def getSelectedList(self):
        items = []
        for index in self.tvw.selectionModel().selectedIndexes():
            # index of selectedModel is for the proxy filter model only, we have to map to the source model to get valid item
            src_index = self.pm.mapToSource(index)
            item = self.sm.itemFromIndex(src_index)
            items.append(item.text())
        return items

    def expandItem(self, qStandardItem):
        try:
            index = self.sm.indexFromItem(qStandardItem)
            index = self.pm.mapFromSource(index)
            self.tvw.setExpanded(index,True)   
        except:
            pass

    def procLoadDictToQItem(self, parent_item, headers_list, modelDict):

        for key in sorted(modelDict):
            subitem_list = []
            for header in headers_list:
                qsubitem = None
                if header in modelDict[key]:
                    qsubitem = QStandardItem(str(modelDict[key][header]))
                else:
                    qsubitem = QStandardItem('')
                subitem_list.append(qsubitem)

            parent_item.appendRow(subitem_list)
            if self.alwaysExpand:
                self.expandItem(parent_item)

                
            # recurse on any children dictionaries
            if 'children' in modelDict[key]:
                self.procLoadDictToQItem(subitem_list[0],headers_list,modelDict[key]['children'])

    def clearAllItems(self):
        self.sm.clear()

    def loadViewModelFromDict(self, modelDict):
        ''' given a dictionary, parse through each key and fill the item model with the data
            this is a quickway to set lots of data with minimal QT CustomSortFilterProxyModel
        '''
        self.sm.clear()
        #print(modelDict)
        # get list of headers
        headers_list = ['name']
        for grp in sorted(modelDict):
            if 'children' in modelDict[grp]:
                #item = sorted(modelDict[grp]['children'])
                for item in sorted(modelDict[grp]['children']):
                    for header in sorted(modelDict[grp]['children'][item]):
                        if header not in headers_list and header != 'children':
                            headers_list.append(header)
            for header in sorted(modelDict[grp]):
                if header not in headers_list and header != 'children':
                    headers_list.append(header)



        #print ("HEADERS LIST = {0}".format(headers_list))
        # recursively load the dict and any children items
        item_list = self.procLoadDictToQItem(self.sm,headers_list,modelDict)
        self.sm.setHorizontalHeaderLabels(headers_list)

        if self.showFirstColOnly:
            for col in range(1,len(headers_list),1):
                self.tvw.setColumnHidden(col,True)
        else:
            col = 0
            for header in headers_list:
                if header in self.hidden_headers:
                    self.tvw.setColumnHidden(col,True)
                col += 1

        # set persietent editors on certain columns
        self.setColumnPersistentEditor(1)
        #self.setColumnPersistentEditor(2)
        #self.setColumnPersistentEditor(3)

        self.tvw.setColumnWidth(0,250)
        self.tvw.setColumnWidth(1,100)
        self.tvw.setColumnWidth(2,75)
        self.tvw.setColumnWidth(3,75)

# reimplement editable columns to allow for editing combo boxes
class GSInSceneItemModel(QStandardItemModel):

    def flags(self, index):
        if (index.column() > 0):
            return Qt.ItemIsEditable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled                

class LargeRowDelegate(QItemDelegate):
    def __init__(self, parent=None, *args, **kwargs):
        super(LargeRowDelegate, self).__init__(parent=parent, *args, **kwargs) 

    def sizeHint(self, option, index):
        print "size hint called"
        return QSize(100, 20)

# sets up and handles using a combobox as an item in the treeviewlist
class ComboBoxDelegate(QItemDelegate):

    def __init__(self, parent=None, *args, **kwargs):
        super(ComboBoxDelegate, self).__init__(parent=parent, *args, **kwargs) 

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        #editor.sizeHint(QSize(100, 20))
        self.connect(editor, SIGNAL("currentIndexChanged(int)"), self, SLOT("currentIndexChanged()"))
        return editor

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        #editor.setCurrentIndex(int(index.model().data(index)))
        data_str = index.model().data(index, Qt.EditRole)
        print ("setting data to{0}".format(data_str))
        i = editor.findText(data_str, Qt.MatchFixedString)
        if i < 1:
            editor.addItems([data_str])
            i = editor.findText(data_str, Qt.MatchFixedString)
        else:
            editor.setCurrentIndex(i) 

        editor.blockSignals(False)

    def setModelData(self, editor, model,index):
        model.setData(index, index.model().data(index, Qt.EditRole))
        #model.setData(index, editor.currentIndex())

    def updateEditorGeometry(self, editor, option, index):
        size = QRect(option.rect.x(),option.rect.y()+2,option.rect.width()-6,option.rect.height()-4)
        editor.setGeometry(size)

    #def setData(self, index, value, role=Qt.DisplayRole):
        #print "setData", index.row(), index.column(), value
    #    return

    def sizeHint(self, option, index):
        print "size hint called"
        return QSize(100, 24)
        # todo: remember the data

def main():
    wind = GSAssetLoaderWindow()
    wind.show()
    windMayaName = wind.objectName()