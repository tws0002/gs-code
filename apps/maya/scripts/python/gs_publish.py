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

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget) 

import gs_core, os, sys

class GSPublishSceneWindow(MayaQWidgetBaseMixin,QWidget):
    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSPublishSceneWindow, self).__init__(parent=parent, *args, **kwargs) 

        self.proj = gs_core.projects.ProjectController('{0}/projects.yml'.format(os.environ['GSCONFIG']))
        self.p_dict = self.proj.pathParser.parsePath('{0}/production'.format(os.environ['GSPROJECT']))

        self.title = "Publish Scene v0.2a"
        self.setWindowTitle(self.title)

        self.resize(600, 300)

        self.main_lyt = QVBoxLayout(self)

        self.gridlyt = QGridLayout()
        self.gridlyt.setColumnStretch(2,2)
        self.gridlyt.setColumnStretch(1,1)
        self.projectlbl = QLabel('Project:')
        self.project = QLineEdit()
        self.stagelbl = QLabel('Stage:')
        self.stage = QLineEdit()
        self.assetliblbl = QLabel('Location:')
        self.assetlib = QLineEdit()
        self.assetgrplbl = QLabel('Group:')
        self.assetgrp = QLineEdit()
        self.assetnamelbl = QLabel('Asset:')
        self.assetname = QLineEdit()
        self.scenenamelbl = QLabel('SceneName:')
        self.scenename = QLineEdit()
        self.versionlbl = QLabel('Version:')
        self.version = QLineEdit()

        self.asset_list = QTreeView()
        self.asset_list.setUniformRowHeights(True)
        self.asset_model = QStandardItemModel(self.asset_list)
        self.asset_model.setHorizontalHeaderLabels(['Output Item', 'Export Type', 'New Version', 'Previous Version', 'Range'])
        

        self.asset_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.asset_list.setModel(self.asset_model)
        self.asset_list.setColumnWidth(0,200)

        rangeEditGroup = QBoxLayout(QBoxLayout.LeftToRight)
        
        self.rangeLbl1 = QLabel('Start:')
        rangeEditGroup.addWidget(self.rangeLbl1)
        self.rangeLE1 = QSpinBox()
        self.rangeLE1.setRange(0, 100000)
        self.rangeLE1.setValue(101)
        
        rangeEditGroup.addWidget(self.rangeLE1)
        self.rangeLbl2 = QLabel('End:')
        rangeEditGroup.addWidget(self.rangeLbl2)
        self.rangeLE2 = QSpinBox()
        self.rangeLE2.setRange(0, 100000)
        self.rangeLE2.setValue(201)
        
        rangeEditGroup.addWidget(self.rangeLE2)
        self.rangeLbl3 = QLabel('Step:')
        rangeEditGroup.addWidget(self.rangeLbl3)
        self.rangeLE3 = QSpinBox()
        self.rangeLE3.setRange(1, 100)
        self.rangeLE3.setValue(1)
        rangeEditGroup.addWidget(self.rangeLE3)
        optionsGroup = QBoxLayout(QBoxLayout.LeftToRight)
        
        self.uvCB = QCheckBox('Export UVs')
        optionsGroup.addWidget(self.uvCB)
        self.fhCB = QCheckBox('Flatten Hierarchy')
        self.fhCB.setChecked(1)
        optionsGroup.addWidget(self.fhCB)
        self.gsCB = QCheckBox('Globalspace')
        self.gsCB.setChecked(1)
        optionsGroup.addWidget(self.gsCB)
        pathEditGroup = QBoxLayout(QBoxLayout.LeftToRight)
        
        self.pathLbl = QLabel('Output Path:')
        self.nameLE = QLineEdit()
        pathEditGroup.addWidget(self.pathLbl)
        pathEditGroup.addWidget(self.nameLE)

        self.footer = QBoxLayout(QBoxLayout.LeftToRight)
        self.publishbtn = QPushButton("Publish Scene")
        self.cancelbtn = QPushButton("Cancel")

        #### LAYOUT #####
        self.gridlyt.addWidget(self.projectlbl,0,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.project,0,2)
        self.gridlyt.addWidget(self.stagelbl,1,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.stage,1,2)
        self.gridlyt.addWidget(self.assetliblbl,2,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.assetlib,2,2)
        self.gridlyt.addWidget(self.assetgrplbl,3,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.assetgrp,3,2)
        self.gridlyt.addWidget(self.assetnamelbl,4,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.assetname,4,2)
        self.gridlyt.addWidget(self.scenenamelbl,5,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.scenename,5,2)
        self.gridlyt.addWidget(self.versionlbl,6,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.version,6,2)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.publishbtn)
        
        self.main_lyt.addLayout(self.gridlyt)
        self.main_lyt.addLayout(rangeEditGroup)
        self.main_lyt.addLayout(optionsGroup)
        self.main_lyt.addLayout(pathEditGroup)
        self.main_lyt.addWidget(self.asset_list)
        self.main_lyt.addLayout(self.footer)

        # Set up slots and signals.
        self.publishbtn.clicked.connect(self.doPublishScene)
        self.cancelbtn.clicked.connect(self.doCancel)

        self.updateUi()

    def updateUi(self):

        current_scene = str(cmds.file(q=1,sn=1))
        f_data = self.proj.pathParser.parsePath(current_scene)

        self.project.setText('/'.join([f_data['server'],f_data['share'],f_data['job']]))
        self.stage.setText(f_data['stage'])
        self.assetlib.setText(f_data['asset_type'])
        self.assetgrp.setText(f_data['asset_grp'])
        self.assetname.setText(f_data['asset'])
        self.scenename.setText(f_data['scenename'])
        self.version.setText(f_data['version'])

        # populate list with assets found in scene
        assets = self.getInSceneAssets()
        r = 0
        for a in assets:
            item = QStandardItem(a)
            print (assets[a]['latest_cache'])
            ver = QStandardItem(assets[a]['latest_cache'])
            item.setCheckable(True)
            #item.setCheckState(Qt.CheckState)
            self.asset_model.appendRow(item)
            self.asset_model.setItem(r,2,ver)
            r = r + 1
        return

    def exportAlembicUI(self):
        print("exporting alembics")
        # get the assets from the UI as text strings
        asset_list = []
        for index in xrange(self.asset_model.rowCount()):
            asset_list.append(self.asset_model.item(index))
        asset_names = [str(i.text()) for i in asset_list]

        # get the export flags
        out_path = str(self.nameLE.text())
        in_frame = str(self.rangeLE1.value())
        out_frame = str(self.rangeLE2.value())
        step = str(self.rangeLE3.value())
        exportAlembicCache(out_path=out_path,asset_list=asset_names,in_frame=in_frame,out_frame=out_frame,step=step)
        self.parent.close()

    def getInSceneAssets(self):
        asset_list = []
        
        ref_nodes = cmds.file(q=1,r=1)
        for r in ref_nodes:
            ref_path = cmds.referenceQuery(r,f=1,wcn=1)
            ref_ns = cmds.file(r,q=1,namespace=1)
            asset_list.append((r, ref_path, ref_ns))

        return asset_list

    def getOutputItems(self, publish_type):
        # populate the item list with a dictionary
        current_scene = str(cmds.file(q=1,sn=1))
        output_list = [('Scene','MayaBinary','','','static')]

        if publish_type == 'animation':
            # add a list of cameras
            # add a playblast
            # list of assets - alembic cache sequence
            # list of assets - animation curves
            pass

        if publish_type == 'asset':
            # alembic cache static
            # optional add a list of shaders
            # optional render
            pass

        if publish_type == 'render':
            # list of render layers
            pass

            # get a list
        return output_list
    
    # project, asset_lib, asset, task, package, scenename, version

    def doPreflightCheck(self, preflight_type):
        return

    def doPostPublish(self):

        return
    
    def doPublishScene(self):
        self.publishScene()

    def publishScene(self):
        # gather options
        current_scene = str(cmds.file(q=1,sn=1))
        #f_data = self.proj.pathParser.parsePath(current_scene)
        
        #pub_root, pub_files = self.proj.getScenefileList(upl_dict=f_data, scene_type='publish', latest_version=True)
        next_path, next_file = self.proj.getScenefileList(upl=current_scene, scene_type='workscene', latest_version=True, new_version=True)
        pub_scene = '{0}/{1}'.format(next_path,next_file[0])
        cmds.file(rename=pub_scene)
        cmds.file(save=True, force=True, options="v=0", typ="mayaBinary")
        return

    def exportScene(self):
        return
    
    def exportAlembic(self, startFrame, endFrame):
        return
    
    def exportCurves(self):
        return

    def exportShaders(self):
        return

    def doCancel(self):
        self.parent.close()
        

def main():
    wind = GSPublishSceneWindow()
    wind.show()
    windMayaName = wind.objectName()

# output list queue includes
# 1. this scenefile, export type (scene|cache|curves|shaders|playblast|render)
# 2. camera
# 3. assetA | renderlayer
# 4. assetB | renderlayer
# 5. assetC | renderlayer
# 6. localGeo

# publish types are defined and can be run based on department
# each publish method is defined, and publish_templates define
# 
# things that need publishing...
# model publish - maya scene, static alembic
# lookdev publish - maya scene, static alembic, shaders
# animation - alembic cache, animation-curves (sequences) per asset
# clothsim - alembic cache, nCloth cache
# hairsim - alembic cache, nhair cache
# effects - alembic cache, particle cache (sequences) per asset
# lighting publish - render
# comp publish - render

# export scene level
# export asset level (each asset has an output)

#publish methods
# 1. copy of scenefile
# 2. export of scenefile nodes
# 3. export alembic cache (static)
# 4. export of anim curves
# 5. export of shaders
# 6. export of nCache
# 7. export of nHair
# 8. export of xgen data
# 
