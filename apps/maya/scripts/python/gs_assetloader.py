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
import gs_core

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
        self.proj = gs_core.projects.ProjectController('{0}/projects.yml'.format(os.environ['GSCONFIG']))
        self.p_dict = self.proj.pathParser.parsePath('{0}/production'.format(os.environ['GSPROJECT']))

        self.title = "Asset Loader v0.2a"
        self.setWindowTitle(self.title)

        # main layout
        self.main_layout = QVBoxLayout(self)
        #self.main_layout.addSpacing(40)
        self.pane_split = QSplitter()
        self.main_layout.addWidget(self.pane_split)

        self.loader_tree = GSAssetLoaderAssetLib(parent=self)
        self.in_scene_list = GSAssetLoaderInSceneList(parent=self)
        self.in_scene_list.tree_list.hidden_headers = ['filepath','is_group','ref_node','status', 'group']
        #self.loader_tree.parent_class = self

        self.pane_split.addWidget(self.loader_tree)
        self.pane_split.addWidget(self.in_scene_list)
        self.pane_split.setSizes([100, 400])

        self.updateAssetList()
        self.updateAssetTaskCombo()
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
        self.loader_tree.tree_list.loadViewModelFromDict(item_dict)
        self.loader_tree.tree_list.current_path = asset_lib


    def updateAssetTaskCombo(self, asset_type='asset_3d'):
        default_tasks = self.proj.getDefaultTasks(asset_type=asset_type)
        print default_tasks
        for name in default_tasks:
            if name != '':
                item = QStandardItem(name)
                self.loader_tree.typecombo.model().appendRow(item)

    def createReference(self, asset_type='asset_3d'):

        sel_item = self.loader_tree.tree_list.getSelectedItems()
        
        if len(sel_item):
            a_name = str(sel_item[0].text())
            a_path = str(sel_item[1].text())
            print ('selected asset={0} {1}'.format(a_name,a_path))
            
            #ad = dict(self.p_dict)
            f_data = self.proj.pathParser.parsePath(a_path)
            f_data['task'] = str(self.loader_tree.typecombo.currentText())
            print ('task={0}'.format(f_data['task']))
            f_data['scenename'] = 'main'
            f_data['package'] = 'maya'
            f_data['ext'] = 'mb'

            # get the latest version of publish path
            pub_root, pub_files = self.proj.getScenefileList(upl_dict=f_data, scene_type='publish', latest_version=True)
            print ('latest_publish={0} {1}'.format(pub_root,pub_files))
            if not os.path.isdir(pub_root):
                cmds.error('No publish found for Asset: Looking for {0}'.format(pub_root))
                return
            else:
                asset_scenefile = '/'.join([pub_root,pub_files[0]])
                namespace = a_name
                # TODO if a_name exists and ends with a number, lets add an underscore num (iPhone8_1) instead of just incrementing the 8
                cmds.file(asset_scenefile,r=True, typ='mayaBinary',ignoreVersion=True, gl=True, namespace=namespace,options='v=0;')
                self.updateInSceneAssets()

    def getInSceneAssets(self):
        asset_list = []
        
        ref_nodes = cmds.file(q=1,r=1)
        for r in ref_nodes:
            ref_path = cmds.referenceQuery(r,f=1,wcn=1)
            ref_ns = cmds.file(r,q=1,namespace=1)
            asset_list.append((r, ref_path, ref_ns))

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
            asset_data[namespace]['version'] = f_data['version']
            asset_data[namespace]['type'] = f_data['task']
            asset_data[namespace]['latest_publish'] = f_data['version']
            asset_data[namespace]['ref_node'] = node
            asset_data[namespace]['status'] = "Active"
            asset_data[namespace]['is_group'] = False
            asset_data[namespace]['group'] = f_data['asset_grp']

        self.in_scene_list.tree_list.loadViewModelFromDict(asset_data)


class GSAssetLoaderAssetLib(MayaQWidgetBaseMixin,QWidget):
    data_model = {}
    obj_list_model = None

    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSAssetLoaderAssetLib, self).__init__(parent=parent, *args, **kwargs) 

        self.parent_class = None

        self.main_lyt = QVBoxLayout()
        self.setLayout(self.main_lyt)

        self.headerlyt = QHBoxLayout()
        self.headerlyt.setContentsMargins(0,0,0,0)
        self.footerlyt = QHBoxLayout()
        self.footerlyt.setContentsMargins(0,0,0,0)

        self.title = QLabel('3D Assets')
        self.tree_list = GSAssetLoaderTreeList()
        self.typelbl = QLabel('Type:')
        self.typecombo = QComboBox()
        self.ref_btn = QPushButton('Reference >>')

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

        self.ref_btn.clicked.connect(self.parent().createReference)
        

class GSAssetLoaderInSceneList(MayaQWidgetBaseMixin,QWidget):

    data_model = {}
    obj_list_model = None

    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSAssetLoaderInSceneList, self).__init__(parent=parent, *args, **kwargs) 

        #### WIDGET CREATE ####
        self.main_lyt = QVBoxLayout()
        self.setLayout(self.main_lyt)

        self.footerlyt = QHBoxLayout()
        self.footerlyt.setContentsMargins(0,0,0,0)

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

        #####  WIDGET LAYOUT ######
        self.main_lyt.addWidget(self.tree_list)
        self.footerlyt.addWidget(self.removebtn)
        self.footerlyt.addWidget(self.renamebtn)
        self.footerlyt.addWidget(self.replacebtn)
        self.footerlyt.addWidget(self.reloadbtn)
        self.footerlyt.addWidget(self.unloadbtn)
        self.main_lyt.addWidget(self.tree_list)
        self.main_lyt.addLayout(self.footerlyt)

        #### WIDGET SIGNALS #####
        


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
        self.tvw.setEditTriggers(QAbstractItemView.NoEditTriggers)

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
        

    def filterListEditChanged(self):
        regstr = self.le.text()
        if len(regstr) < 3 and len(regstr) > 0:
            regstr = '^{0}'.format(regstr)

        self.setFilterRegExpStr(regstr)

    def getSelectedItems (self):
        items = []
        for index in self.tvw.selectionModel().selectedIndexes():
            # index of selectedModel is for the proxy filter model only, we have to map to the source model to get valid item
            src_index = self.pm.mapToSource(index)
            item = self.sm.itemFromIndex(src_index)
            items.append(item)
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

def main():
    wind = GSAssetLoaderWindow()
    wind.show()
    windMayaName = wind.objectName()