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

    data_model = {}
    obj_list_model = None
    renameShader = True
    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSPublishSceneWindow, self).__init__(parent=parent, *args, **kwargs) 

        self.proj = gs_core.projects.ProjectController('{0}/projects.yml'.format(os.environ['GSCONFIG']))
        self.p_dict = self.proj.pathParser.parsePath('{0}/production'.format(os.environ['GSPROJECT']))

        self.title = "Publish Scene v0.2a"
        self.setWindowTitle(self.title)

        self.resize(400, 200)

        self.asset_location = QLineEdit()

        self.main_lyt = QVBoxLayout(self)

        self.scenelyt = QHBoxLayout()

        self.gridlyt = QGridLayout()
        self.gridlyt.setColumnStretch(2,2)
        self.gridlyt.setColumnStretch(1,1)
        self.projectlbl = QLabel('Project:')
        self.project = QComboBox()
        self.stagelbl = QLabel('Stage:')
        self.stage = QComboBox()
        self.assetliblbl = QLabel('Location:')
        self.assetlib = QComboBox()
        self.assetgrplbl = QLabel('Group:')
        self.assetgrp = QComboBox()
        self.assetnamelbl = QLabel('Asset:')
        self.assetname = QComboBox()
        self.scenenamelbl = QLabel('SceneName:')
        self.scenename = QComboBox()
        self.versionlbl = QLabel('Version:')
        self.version = QComboBox()

        self.vnum = QLineEdit()
        self.vnum.setMaxLength(4)
        self.vnum.setEnabled(False)


        self.noteslbl = QLabel('Notes:')
        self.notes = QPlainTextEdit()
        #self.notes.setPlaceholderText('What has changed with this version?')

        self.cancelbtn = QPushButton('Cancel')
        self.savebtn = QPushButton('Publish This Version')

        self.footer = QHBoxLayout()

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
        self.footer.addWidget(self.savebtn)

        self.main_lyt.addLayout(self.gridlyt)
        self.main_lyt.addLayout(self.footer)

        self.file_dest = ''

        #self.updateUI()

        ##### SIGNALS #######
        self.savebtn.clicked.connect(self.doPublishScene)
        self.cancelbtn.clicked.connect(self.doCancel)
    

    
    
    # project, asset_lib, asset, task, package, scenename, version
    
    def doPublishScene(self):
        return
    
    def publish_almebic_scene(self):
        return
    
    def publish_alembic_asset(self):
        return
    
    def publish_anim_curves(self):
        return

    def doCancel(self):
        self.parent.close()
        

def main():
    wind = GSPublishSceneWindow()
    wind.show()
    windMayaName = wind.objectName()