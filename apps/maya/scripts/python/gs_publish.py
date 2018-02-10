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

class GSPublishSceneWindow(MayaQWidgetBaseMixin,QWidget):

    data_model = {}
    obj_list_model = None
    renameShader = True
    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSPublishSceneWindow, self).__init__(parent=parent, *args, **kwargs) 
    
    
    # project, asset_lib, asset, task, package, scenename, version
    
    def publishScene(self):
        return
    
    def publish_almebic_scene(self):
        return
    
    def publish_alembic_asset(self):
        return
    
    def publish_anim_curves(self):
        return
        


wind = GSPublishSceneWindow()
wind.show()
windMayaName = wind.objectName()