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

import gscore, os, sys
import time, datetime
from collections import OrderedDict
import yaml

class GSQuickSaveWindow(MayaQWidgetBaseMixin,QWidget):

    data_model = {}
    obj_list_model = None
    renameShader = True
    
    def __init__(self, parent=None, *args, **kwargs):
        super(GSQuickSaveWindow, self).__init__(parent=parent, *args, **kwargs) 

        self.proj = gs_core.projects.ProjectController('{0}/projects.yml'.format(os.environ['GSCONFIG']))
        self.p_dict = self.proj.pathParser.parsePath('{0}/production'.format(os.environ['GSPROJECT']))

        self.title = "Quick Save v0.2a"
        self.setWindowTitle(self.title)

        self.ui_state = {
            'f_data': {},
            'note':'',
            'version': '',
            'camera': '',
            'start': 1,
            'end': 100,
            'step': 1,
            'file_dest': ''
        }

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

        self.noteslbl = QLabel('Notes: (What has changed with this version?)')
        self.notes = QPlainTextEdit()
        #self.notes.setPlaceholderText('What has changed with this version?')

        self.cancelbtn = QPushButton('Cancel')
        self.cancelbtn.setMinimumHeight(36)
        self.savebtn = QPushButton('Save New Version')
        self.savebtn.setMinimumHeight(36)
        font = self.savebtn.font()
        font.setPointSize(12)
        self.savebtn.setFont(font)
        self.cancelbtn.setFont(font)

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

        self.updateUI()

        ##### SIGNALS #######
        self.savebtn.clicked.connect(self.doIncrementalSave)
        self.cancelbtn.clicked.connect(self.doCancel)

    def updateUI(self):
        # get the current scene's info and set the ui widget values
        current_scene = str(cmds.file(q=1,sn=1))
        # verify this is a valid work scene
        o_data = f_data = self.proj.pathParser.parsePath(current_scene)
        self.ui_state['f_data'] = f_data
        if 'version' not in o_data and 'scenename' not in o_data:
            cmds.error('The Scene does not appear to be a valid pipeline workscene: {0}'.format(current_scene))
            return

        #new_scene = self.proj.getNewVersion(upl=current_scene)
        print (current_scene)
        next_path, next_file = self.proj.getScenefileList(upl=current_scene, scene_type='workscene', latest_version=True, new_version=True)
        fp = '/'.join([next_path,next_file[0]])
        print "file to write= {0}".format(current_scene)
        print "file to write= {0}".format(fp)

        f_data = self.proj.pathParser.parsePath(fp, exists=False)
        print 'o_data={0}'.format(o_data)
        print 'f_data={0}'.format(f_data)

        if 'version' in f_data and 'scenename' in f_data:
            # get the next avail versions
            scene_minus_ver = '_'.join([f_data['asset_grp'],f_data['asset'],f_data['task'],f_data['scenename']])
            self.asset_name.setText(scene_minus_ver)
            self.vnum.setText(f_data['version'])
            self.ui_state['version'] = f_data['version']
            self.ui_state['file_dest'] = fp
    
        else:
            cmds.error('Scenefile does not appear to be in the pipeline: {0}'.format(current_scene))

    def doViewportSnapshot(self):
        img_w = 500
        img_h = 282
        output_path = ""
        print "thumbnailPath={0}".format(output_path)

        img_format = 'png'
        fcurFrame = cmds.currentTime(q=1)

        # get the active model editor viewport
        print (cmds.playblast(ae=1))
        model_view = cmds.playblast(ae=1)

        active_panel = cmds.getPanel(withFocus=1) 
        cam_name = cmds.modelPanel(q=1, camera=active_panel)
        # setup the playblast as a command string for deferred evaluation
        cmd = ("playblast  -format iff -completeFilename \""+output_path+"\" -frame "+curFrame+" -forceOverwrite -sequenceTime 0 -clearCache 1 -viewer 0 -showOrnaments 0 -percent 100 -widthHeight "+img_w+" "+img_h+";")
        
        #if cmds.about(version=1) == "2012 x64" or cmds.about(version=1) == "2012":
        #    cmd = ("playblast  -format iff -filename \""+output_path+"\" -frame "+curFrame+" -fp 0 -forceOverwrite -sequenceTime 0 -clearCache 1 -viewer 0 -showOrnaments 0 -percent 100 -compression \"png\" -widthHeight "+img_w+" "+img_h+";")
        #    cmd += ("sysFile -rename \""+output_path+"\" \""+output_path+".0.png\";")
        
        print (cmd)
        cmds.evalDeferred(cmd)        

    def doIncrementalSave(self):
        self.ui_state['note'] = str(self.notes.toPlainText())
        cmds.file(rename=self.ui_state['file_dest'])
        cmds.file(save=True, force=True, options="v=0", typ="mayaBinary")
        self.exportVersionData(self.ui_state['file_dest'])
        #proj.newSceneVersion(upl=new_scene)
        self.close()
        return

    def exportVersionData(self, out_path=''):
        """ writes out the asset work scene information as a yaml file

        """
        assets = self.getInSceneAssets()
        output_data = {}
        cam_list = self.getInSceneCameras()

        asset_data = {}
        for r, ref_path, ref_ns in assets:
            asset_data[ref_ns]={
                'filepath': ref_path,
                'fileindex': r,
                'namespace': ref_ns,
            }
        camera_info = {}
        for cam in cam_list:
            camera_info[cam] = {
                'camera_name': cam,
                'focal_length': cmds.getAttr('{0}.focalLength'.format(cam)),
                'h_aperture': cmds.getAttr('{0}.horizontalFilmAperture'.format(cam)),
                'v_aperture': cmds.getAttr('{0}.verticalFilmAperture'.format(cam)),
            }

        assembly_info = {
            'gs_core': 1.0,
            'gs_mayaTools': 1.0,
            'source_scene': cmds.file(q=1,sn=1),
            'publish_date': datetime.datetime.now(),
            'username': os.environ['USERNAME'],
            'host_machine': os.environ['COMPUTERNAME'],
            'version': self.ui_state['version'],
            'note': self.ui_state['note'], 
            'camera_info': camera_info,
            'start_frame': cmds.playbackOptions(q=1, min=1),
            'end_frame': cmds.playbackOptions(q=1, max=1),
            'step': 1,
            'asset_data': asset_data,
            'frame_rate': cmds.currentUnit(q=1, time=1)
        }

        if out_path != '':
            split = os.path.split(out_path)
            out_file ='/'.join([split[0],'{0}.yml'.format(split[-1])])

            with open(out_file, 'w') as f:
                f.write( yaml.safe_dump(assembly_info, default_flow_style=False, encoding='utf-8', allow_unicode=False) )

    def getInSceneCameras(self):
        defaultCams = ['top','side','front','persp']
        camShapes = cmds.ls(type='camera')
        camXforms = []
        for shape in camShapes:
            xforms = cmds.listRelatives(shape, p=1)
            try:
                camXforms.extend(xforms)
            except TypeError:
                pass

        finalCams = [ f for f in camXforms if f not in defaultCams ]
        return finalCams

    def getInSceneAssets(self):
        asset_list = []
        ref_nodes = cmds.file(q=1,r=1)
        for r in ref_nodes:
            ref_path = cmds.referenceQuery(r,f=1,wcn=1)
            ref_ns = cmds.file(r,q=1,namespace=1)
            asset_list.append((r, ref_path, ref_ns))
        return asset_list

    def doCancel(self):
        self.close()
        return

def main():
    wind = GSQuickSaveWindow()
    wind.show()
    windMayaName = wind.objectName()