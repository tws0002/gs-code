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

class GSQuickSaveWindow(MayaQWidgetBaseMixin,QWidget):

    data_model = {}
    obj_list_model = None
    renameShader = True
    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSQuickSaveWindow, self).__init__(parent=parent, *args, **kwargs) 

    	self.proj = gs_core.projects.ProjectController('//scholar/pipeline/dev/config/projects.yml')
        self.p_dict = self.proj.pathParser.parsePath('{0}/production'.format(os.environ['GSPROJECT']))

        self.title = "Quick Save v0.2a"
        self.setWindowTitle(self.title)

        self.resize(400, 200)

        self.asset_location = QLineEdit()

        self.main_lyt = QVBoxLayout(self)

        self.scenelyt = QHBoxLayout()

        self.assetlbl = QLabel('Scene:')
        self.asset_name = QLineEdit()
        self.asset_name.setEnabled(False)
        self.vnum = QLineEdit()
        self.vnum.setMaxLength(4)
        self.vnum.setEnabled(False)


        self.noteslbl = QLabel('Notes:')
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText('What has changed with this version?')

        self.cancelbtn = QPushButton('Cancel')
        self.savebtn = QPushButton('Save New Version')

        self.footer = QHBoxLayout()

        self.scenelyt.addWidget(self.assetlbl)
        self.scenelyt.addWidget(self.asset_name)
        self.scenelyt.addWidget(self.vnum)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.savebtn)

        self.main_lyt.addLayout(self.scenelyt)
        self.main_lyt.addWidget(self.noteslbl)
        self.main_lyt.addWidget(self.notes)
        self.main_lyt.addLayout(self.footer)

        self.file_dest = ''

        self.updateUI()

        ##### SIGNALS #######
        self.savebtn.clicked.connect(self.doIncrementalSave)
        self.cancelbtn.clicked.connect(self.doCancel)

    def updateUI(self):
    	# get the current scene's info and set the ui widget values
    	current_scene = str(cmds.file(q=1,sn=1))
    	# verify this is a valid work scene
    	o_data = f_data = self.proj.pathParser.parsePath(current_scene)
    	if 'version' not in o_data and 'scenename' not in o_data:
    		cmds.error('The Scene does not appear to be a valid pipeline workscene: {0}'.format(current_scene))
    		return

    	#new_scene = self.proj.getNewVersion(upl=current_scene)
    	next_path, next_file = self.proj.getScenefileList(upl=current_scene, scene_type='workscene', latest_version=True, new_version=True)
    	fp = '/'.join([next_path,next_file[0]])
    	print "file to write= {0}".format(current_scene)
    	print "file to write= {0}".format(fp)

    	f_data = self.proj.pathParser.parsePath(fp, exists=False)
    	print 'o_data={0}'.format(o_data)
    	print 'f_data={0}'.format(f_data)

    	if 'version' in f_data and 'scenename' in f_data:
    		# get the next avail versions
    		scene_minus_ver = '_'.join([f_data['asset_grp'],f_data['asset'],f_data['scenename']])
    		self.asset_name.setText(scene_minus_ver)
    		self.vnum.setText(f_data['version'])
    		self.file_dest = fp
    
    	else:
    		cmds.error('Scenefile does not appear to be in the pipeline: {0}'.format(current_scene))

    def doIncrementalSave(self):
    	cmds.file(rename=self.file_dest)
    	cmds.file(save=True, force=True, options="v=0", typ="mayaBinary")
    	#proj.newSceneVersion(upl=new_scene)
    	self.close()
    	return

    def doCancel(self):
    	self.close()
    	return

def main():
	wind = GSQuickSaveWindow()
	wind.show()
	windMayaName = wind.objectName()