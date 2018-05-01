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

class GSLoaderWindow(MayaQWidgetDockableMixin, QWidget):

    def __init__(self, node=None, *args, **kwargs):
        super(GSLoaderWindow, self).__init__(*args, **kwargs)
        #self.resize(300, 100)
        self.title = "Loader v0.2a"
        self.setWindowTitle(self.title)
        self.ui_state = {
            'f_data': {},
            'version': '',
            'asset_tab': 'asset_3d',
            'asset_item': '',
            'task_combo': ''
        }
        # main layout
        self.main_layout = QVBoxLayout(self)
        self.locationlyt = QHBoxLayout()
        self.loadButton = QPushButton('Load')
        
        self.typelbl = QLabel('Current:')
        self.main_layout.addLayout(self.locationlyt)
        self.currentShot = QComboBox()
        self.locationlyt.addWidget(self.typelbl)
        self.locationlyt.addWidget(self.currentShot)
        self.locationlyt.addWidget(self.loadButton)

def main():
    wind = GSLoaderWindow()
    wind.show(dockable=True, verticalTitlebar=True, floating=True)
    #wind.setFeatures(QDockWidget.DockWidgetVerticalTitleBar)
    windMayaName = wind.objectName()

##QDockWidget dockWidget = QDockWidget()
##if dockWidget.features() & QDockWidget.DockWidgetVerticalTitleBar:
##    # I need to be vertical
##else:
##    # I need to be horizontal