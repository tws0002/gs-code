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

        self.type_list = ['Static Cache','Maya Rig','LookDev', 'Animated Cache','Render']

        self.ui_state = {
            'f_data': {},
            'version':'',
            'camera': '',
            'start': 1,
            'end': 100,
            'step':1,
            'publish_type':'',
            'output_list':[],
        }

        self.resize(400, 600)

        self.main_lyt = QVBoxLayout(self)

        self.gridlyt = QGridLayout()
        self.gridlyt.setColumnStretch(2,2)
        self.gridlyt.setColumnStretch(1,1)
        self.projectlbl = QLabel('Project:')
        self.project = QLineEdit()
        self.project.setEnabled(False)
        self.stagelbl = QLabel('Stage:')
        self.stage = QLineEdit()
        self.stage.setEnabled(False)
        self.assetliblbl = QLabel('Location:')
        self.assetlib = QLineEdit()
        self.assetlib.setEnabled(False)
        self.assetgrplbl = QLabel('Group:')
        self.assetgrp = QLineEdit()
        self.assetgrp.setEnabled(False)
        self.assetnamelbl = QLabel('Asset:')
        self.assetname = QLineEdit()
        self.assetname.setEnabled(False)
        self.tasklbl = QLabel('Task:')
        self.taskname = QLineEdit()
        self.taskname.setEnabled(False)
        self.scenenamelbl = QLabel('SceneName:')
        self.scenename = QLineEdit()
        self.scenename.setEnabled(False)
        self.versionlbl = QLabel('Version:')
        self.version = QLineEdit()
        self.version.setEnabled(False)
        self.cameralbl = QLabel('Camera:')
        self.camera = QComboBox()

        self.gridlyt2 = QGridLayout()
        self.gridlyt2.setColumnStretch(2,2)
        self.gridlyt2.setColumnStretch(1,1)

        self.outputslbl = QLabel('Publish Outputs:')
        self.publishtypelbl = QLabel('Publish Type:')
        self.publishtype = QComboBox()

        self.asset_list = QTreeView()
        self.asset_list.setUniformRowHeights(True)
        self.asset_list.setAlternatingRowColors(True)
        self.asset_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.asset_model = QStandardItemModel(self.asset_list)

        self.asset_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.asset_list.setModel(self.asset_model)
        self.asset_list.setRootIsDecorated(False)

        rangeEditGroup = QBoxLayout(QBoxLayout.LeftToRight)
        
        self.rangelbl = QLabel('Range:')
        self.rangeLbl1 = QLabel('Start:')
        rangeEditGroup.addWidget(self.rangeLbl1,Qt.AlignRight)
        self.rangeLE1 = QSpinBox()
        self.rangeLE1.setRange(0, 100000)
        self.rangeLE1.setValue(1)
        
        rangeEditGroup.addWidget(self.rangeLE1)
        self.rangeLbl2 = QLabel('End:')
        rangeEditGroup.addWidget(self.rangeLbl2,Qt.AlignRight)
        self.rangeLE2 = QSpinBox()
        self.rangeLE2.setRange(0, 100000)
        self.rangeLE2.setValue(100)
        
        rangeEditGroup.addWidget(self.rangeLE2)

        self.rangeLbl3 = QLabel('Step:')
        rangeEditGroup.addWidget(self.rangeLbl3,Qt.AlignRight)
        self.rangeLE3 = QSpinBox()
        self.rangeLE3.setRange(1, 100)
        self.rangeLE3.setValue(1)
        rangeEditGroup.addWidget(self.rangeLE3)
        optionsGroup = QBoxLayout(QBoxLayout.LeftToRight)

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
        self.gridlyt.addWidget(self.tasklbl,5,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.taskname,5,2)
        self.gridlyt.addWidget(self.scenenamelbl,6,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.scenename,6,2)
        self.gridlyt.addWidget(self.versionlbl,7,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.version,7,2)
        self.gridlyt.addWidget(self.cameralbl,8,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.camera,8,2)
        self.gridlyt.addWidget(self.rangelbl,9,1,Qt.AlignRight)
        self.gridlyt.addLayout(rangeEditGroup,9,2)

        self.gridlyt2.addWidget(self.outputslbl,0,1,Qt.AlignRight)
        self.gridlyt2.addWidget(self.publishtypelbl,0,2,Qt.AlignRight)
        self.gridlyt2.addWidget(self.publishtype,0,3)
        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.publishbtn)
        
        self.main_lyt.addLayout(self.gridlyt)
        self.main_lyt.addLayout(self.gridlyt2)
        self.main_lyt.addWidget(self.asset_list)
        self.main_lyt.addLayout(self.footer)

        #### SIGNALS ####
        self.publishtype.currentIndexChanged.connect(self.publishTypeChanged)
        self.camera.currentIndexChanged.connect(self.cameraComboChanged)
        self.publishbtn.clicked.connect(self.doPublishScene)
        self.cancelbtn.clicked.connect(self.doCancel)


        self.updateUi()

    def updateUi(self):

        current_scene = str(cmds.file(q=1,sn=1))
        f_data = self.proj.pathParser.parsePath(current_scene)


        self.ui_state['f_data'] = dict(f_data)
        self.ui_state['version'] = str(f_data['version'])
        print self.ui_state['f_data']

        self.project.setText('/'.join([f_data['server'],f_data['share'],f_data['job']]))
        self.stage.setText(f_data['stage'])
        self.assetlib.setText(f_data['asset_type'])
        self.assetgrp.setText(f_data['asset_grp'])
        self.assetname.setText(f_data['asset'])
        self.taskname.setText(f_data['task'])
        self.scenename.setText(f_data['scenename'])
        self.version.setText(f_data['version'])

        # update labels depending on shot or asset
        if f_data['asset_type'].startswith('asset'):
            self.assetgrplbl.setText('Category')
            self.assetnamelbl.setText('Asset Name')
        elif f_data['asset_type'].startswith('shot'):
            self.assetgrplbl.setText('Sequence')
            self.assetnamelbl.setText('Shot')

        self.updateCamList()
        self.updatePublishTypeList()
        
        # set publish type by task type
        if f_data['task'] == 'model':
            self.setPublishType('Static Cache')
        elif f_data['task'] == 'rig':
            self.setPublishType('Maya Rig')
        elif f_data['task'] == 'lookdev':
            self.setPublishType('LookDev')
        elif f_data['task'] == 'anim':
            self.setPublishType('Animated Cache')
        elif f_data['task'] == 'effects':
            self.setPublishType('Animated Cache')
        elif f_data['task'] == 'light':
            self.setPublishType('Render')
        elif f_data['task'] == 'comp':
            self.setPublishType('Render')

        self.updateOutputList()

    def setPublishType(self, publish_type):
        i = self.publishtype.findText(publish_type, Qt.MatchFixedString)
        if i >= 0:
            self.publishtype.setCurrentIndex(i)        
        return


    def updateOutputList(self):

        self.asset_model.clear()
        self.asset_model.setHorizontalHeaderLabels(['Output Item', 'Type', 'Version'])
        self.asset_list.setColumnWidth(0,150)
        self.asset_list.setColumnWidth(1,150)
        self.asset_list.setColumnWidth(2,50)
        self.ui_state['output_list'] = []

        
        item = QStandardItem('Entire Scene')
        item.setCheckable(True)
        item.setCheckState(Qt.Checked)
        exp_type = QStandardItem('MayaBinary')
        ver = QStandardItem(self.ui_state['version'])
        self.asset_model.appendRow([item,exp_type,ver])  
        self.ui_state['output_list'].append(('Entire Scene','MayaBinary',self.ui_state['version']))      

        # add camera
        if self.ui_state['publish_type'] == 'Animated Cache':
            item = QStandardItem('Camera ({0})'.format(self.ui_state['camera']))
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            exp_type = QStandardItem('Alembic ( Start/End )')
            ver = QStandardItem(self.ui_state['version'])
            self.asset_model.appendRow([item,exp_type,ver])   
            self.ui_state['output_list'].append(('Camera ({0})'.format(self.ui_state['camera']),'Alembic ( Start/End )',self.ui_state['version']))  

        # populate list with assets found in scene
        if self.ui_state['publish_type'] == 'Animated Cache':
            assets = self.getInSceneAssets()
            for r, ref_path, ref_ns in assets:
                item = QStandardItem(ref_ns)
                item.setCheckable(True)
                item.setCheckState(Qt.Checked)
                exp_type = QStandardItem('Alembic ( Start/End )')
                ver = QStandardItem(self.ui_state['version'])
                self.asset_model.appendRow([item,exp_type,ver])
                self.ui_state['output_list'].append((ref_ns,'Alembic ( Start/End )',self.ui_state['version'])) 
                #self.asset_model.setItem(r,2,ver)

        if self.ui_state['publish_type'] == 'Static Cache':
            item = QStandardItem('Local Geometry')
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            exp_type = QStandardItem('Alembic ( Static )')
            ver = QStandardItem(self.ui_state['version'])
            self.asset_model.appendRow([item,exp_type,ver]) 
            self.ui_state['output_list'].append(('Local Geometry','Alembic ( Static )',self.ui_state['version'])) 

        # add playblast
        if self.ui_state['publish_type'] == 'Animated Cache':
            render_layers = self.getInSceneRenderLayers()
            for r, enabled in render_layers:
                item = QStandardItem(r)
                item.setCheckable(True)
                if enabled:
                    item.setCheckState(Qt.Checked)
                exp_type = QStandardItem('Playblast ( Start/End )')
                ver = QStandardItem(self.ui_state['version'])
                self.asset_model.appendRow([item,exp_type,ver])
                self.ui_state['output_list'].append((r,'Playblast ( Start/End )',self.ui_state['version'])) 

        if self.ui_state['publish_type'] == 'Render' or self.ui_state['publish_type'] == 'LookDev':
            render_layers = self.getInSceneRenderLayers()
            for r, enabled in render_layers:
                item = QStandardItem(r)
                item.setCheckable(True)
                if enabled:
                    item.setCheckState(Qt.Checked)
                exp_type = QStandardItem('Farm Render ( Start/End )')
                ver = QStandardItem(self.ui_state['version'])
                self.asset_model.appendRow([item,exp_type,ver])
                self.ui_state['output_list'].append((r,'Farm Render ( Start/End )',self.ui_state['version'])) 
                #self.asset_model.setItem(r,2,ver)

        return

    def updateCamList(self):
        # clear the item model and init a new one
        self.camera.model().clear()
        cam_list = self.getInSceneCameras()
        for name in cam_list:
            if name != '':
                item = QStandardItem(name)
                self.camera.model().appendRow(item)
        return

    def cameraComboChanged(self):
        self.ui_state['camera'] = str(self.camera.currentText())
        self.updateOutputList()

    def updatePublishTypeList(self):
        # clear the item model and init a new one
        self.publishtype.model().clear()
        for name in self.type_list:
            if name != '':
                item = QStandardItem(name)
                self.publishtype.model().appendRow(item)
        return

    def publishTypeChanged(self, out_path):
        self.ui_state['publish_type'] = str(self.publishtype.currentText())
        self.updateOutputList()


    def getInSceneAssets(self):
        asset_list = []
        
        ref_nodes = cmds.file(q=1,r=1)
        for r in ref_nodes:
            ref_path = cmds.referenceQuery(r,f=1,wcn=1)
            ref_ns = cmds.file(r,q=1,namespace=1)
            asset_list.append((r, ref_path, ref_ns))

        return asset_list

    def getInSceneRenderLayers(self):
        rlayers = cmds.ls(type='renderLayer')
        layers = []
        for layer in rlayers:
            if not layer.endswith(':defaultRenderLayer'):
                if cmds.getAttr(layer + '.renderable') == 1:
                    layers.append((layer,True))
                else:
                    layers.append((layer,False))
        return layers

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
    
    # project, asset_lib, asset, task, package, scenename, version

    def doPreflightCheck(self, preflight_type):
        return

    def doPostPublish(self):

        return
    
    def doPublishScene(self):
        self.publishScene()

    def publishScene(self):
        print 'starting publ;is'
        # gather information about export
        current_scene = str(cmds.file(q=1,sn=1))
        f_data = self.proj.pathParser.parsePath(current_scene)

        self.ui_state['start'] = float(self.rangeLE1.value())
        self.ui_state['end'] = float(self.rangeLE2.value())
        self.ui_state['step'] = float(self.rangeLE3.value())

        print 'current_scene={0}'.format(current_scene)
        print self.ui_state['output_list']
        # for each item in the output list export the appropriate data
        for item, exp_type, ver in self.ui_state['output_list']:
            if exp_type == 'Alembic ( Start/End )':
                print ('exporting animated alembic')
                d = dict(f_data)
                d['layer'] = item
                d['ext'] = 'abc'
                pub_root, pub_files = self.proj.getScenefileList(upl_dict=d, scene_type='publish')
                if len(pub_files) > 0:
                    out_scene = '/'.join([pub_root,pub_files[0]])
                    self.exportAlembicCache(out_path=out_scene, asset_list=[item], in_frame=self.ui_state['start'], out_frame=self.ui_state['end'],step=self.ui_state['step'])
                else:
                    print ("{0}: Could not determine publish path: {1} {2}".format(exp_type,pub_root, pub_files))
            elif exp_type == 'Alembic ( Static )':
                print ('exporting static alembic')
                d = dict(f_data)
                d['layer'] = 'publish'
                d['ext'] = 'abc'
                pub_root, pub_files = self.proj.getScenefileList(upl_dict=d, scene_type='publish')
                if len(pub_files) > 0:
                    out_scene = '/'.join([pub_root,pub_files[0]])
                    self.exportAlembicCache(out_path=out_scene, asset_list=[d['layer']], in_frame=1, out_frame=1,step=1)
                else:
                    print ("{0}: Could not determine publish path: {1} {2}".format(exp_type,pub_root, pub_files))
            elif exp_type == 'MayaBinary':
                print ('exporting maya scene')
                d = dict(f_data)
                d['layer'] = 'publish'
                pub_root, pub_files = self.proj.getScenefileList(upl_dict=d, scene_type='publish')
                if len(pub_files) > 0:
                    out_scene = '/'.join([pub_root,pub_files[0]])
                    self.saveSceneCopy(out_path=out_scene,create_dir=True)
                else:
                    print ("{0}: Could not determine publish path: {1} {2}".format(exp_type,pub_root, pub_files))
            #elif out_type == 'Maya Export':
            #    self.exportScene()
            #elif out_type == 'Maya nCache':
            #    self.exportScene()
            
            # export the publish data
            #self.exportPublishData(out_path)
        return

    def exportScene(self):
        return
    

    def get_alembic_output_path(self):
        ''' given a shot_info (returned from a call to get_shot_info_from_path()) this will return an abc output path '''
        output_path = ''
        if len(shot_info) > 1:
            dir_name = "_".join((shot_info['shot'],shot_info['cam_version'],shot_info['anim_version'],shot_info['light_version']))
            file_name = (dir_name+'.abc')
            output_path = os.path.join(shot_info['server'],shot_info['job'],'03_production','01_cg','01_MAYA','scenes','02_cg_scenes',shot_info['shot'],shot_info['dept'],'cache',dir_name)
        return output_path


    def exportAlembicCache(self, out_path='', asset_list=[], in_frame=1, out_frame=100, step=1):
        """ exports the alembic cache to a preconfigured location """
        job_strings = []
        print asset_list
        try:
            cmds.loadPlugin( 'AbcExport.mll' )
            cmds.loadPlugin( 'AbcImport.mll' )
        except:
            pass

        for a in asset_list:
            cache_set = ''
            if a == 'publish':
                cache_set = 'cache'
            else:
                cache_set = '{0}:cache'.format(a)
            if cmds.objExists(cache_set):
                obj_list = cmds.sets(str(cache_set),q=1)
            else:
                obj_list = cmds.ls('')
            obj_str= ','.join(obj_list)
            out_filename = os.path.basename(out_path)+'_'+a+'.abc'
            asset_out_path = os.path.join(out_path,out_filename)
            try: 
                os.makedirs(os.path.join(out_path))
            except OSError:
                if not os.path.isdir(os.path.join(out_path)):
                    raise

            job_str = (' -file '+out_path)
            job_str += (' -root '+obj_str)
            job_str += (' -uvWrite')
            job_str += (' -worldSpace')
            job_str += ' -framerange {0} {1}'.format(in_frame,out_frame)
            job_str += (' -dataFormat ogawa')
            job_strings.append(job_str)
   
            # exocortex method
            #job_str = ('filename='+asset_out_path+';')
            #job_str += ('objects='+obj_str+';')
            #job_str += ('uvs=0;')
            #job_str += ('globalspace=1;')
            #job_str += ('withouthierarchy=1;')
            #job_str += ('in='+in_frame+';')
            #job_str += ('out='+out_frame+';')
            #job_str += ('step='+step+';')
            #job_str += ('ogawa=1')
            #job_strings.append(job_str)
        #cmds.ExocortexAlembic_export(j=job_strings)

        #AbcExport -j "-frameRange 1 50 -uvWrite -worldSpace -dataFormat ogawa -root |testCharA1:_UNKNOWN_REF_NODE_fosterParent1|testCharA1:dad_model_grp -file C:/projects/ab_testjob/production/shots/s01/005_00/anim/work/maya/cache/alembic/test.abc";
        cmds.AbcExport(j=job_strings)
        
    def exportPlayblast(self):
        return

    def exportPublishData(self, out_path='', asset_list=[]):
        asset_info = get_assets_in_scene()
        remove_assets = []
        # remove any asset data that isn't in the asset_list argument
        for a in asset_info:
            if any(a in s for s in asset_list):
                remove_assets.append(str(a))

        for a in remove_assets:
            del asset_info[a]

        if out_path != '':
            out_filename = os.path.basename(out_path)+'.yml'
            out_file =os.path.join(out_path,out_filename)
            with open(out_file, 'w') as f:
                f.write( yaml.safe_dump(asset_info, default_flow_style=False, encoding='utf-8', allow_unicode=False) )

    def saveSceneCopy(self, out_path='', create_dir=False):
        print ("SAVING SCENE COPY:{0}".format(out_path))
        if create_dir:
            dir_name = os.path.dirname(out_path)
            if not os.path.isdir(dir_name):
                os.makedirs(dir_name)
        current_scene = str(cmds.file(q=1,sn=1))
        cmds.file(rename=out_path)
        cmds.file(save=True, force=True, options="v=0", typ="mayaBinary")
        cmds.file(rename=current_scene)

    def exportScenePartial(self, out_path):
        # gather options
        current_scene = str(cmds.file(q=1,sn=1))
        #f_data = self.proj.pathParser.parsePath(current_scene)
        
        #pub_root, pub_files = self.proj.getScenefileList(upl_dict=f_data, scene_type='publish', latest_version=True)
        next_path, next_file = self.proj.getScenefileList(upl=current_scene, scene_type='publish', latest_version=True, new_version=True)
        pub_scene = '{0}/{1}'.format(next_path,next_file[0])
        cmds.file(rename=pub_scene)
        cmds.file(save=True, force=True, options="v=0", typ="mayaBinary")
    
    def exportCurves(self):
        return

    def exportShaders(self):
        return

    def doCancel(self):
        self.close()        

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

# model publish post process
# update 

# lookdev tools
#  - publish and update model changes
#    - first make sure you have the model version up to date

# rigging tools
#  - publish and update model changes
#lookdev publish post process
# [] update model task and publish