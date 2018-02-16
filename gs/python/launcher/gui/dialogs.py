
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from settings import *
from widgets import *
import gs_core

import yaml


# validator prevents uppercase
class LRegExpValidator(QRegExpValidator):
    def validate(self, string, pos):
        result = super(LRegExpValidator, self).validate(string, pos)

        #return QValidator.Acceptable, string.toUpper(), pos
        # for old code still using QString, use this instead
        #string.replace(0, string.count(), string.toUpper())
        return result[0], pos

class LauncherDialog(QDialog):
    """
    Base class for Launcher Dialogs, supports frameless window and standardized style sheet loading
    """

    def __init__(self, parent=None):
        super(LauncherDialog, self).__init__(parent)

        self.parent = parent
        # load appearance style
        self.loadStyle()
        #self.setWindowFlags(Qt.FramelessWindowHint)
        #self.setAttribute(Qt.WA_TranslucentBackground)
        #self.shadow = QGraphicsDropShadowEffect(self)
        #sh_colr = QColor(0,0,0,50)
        #self.shadow.setColor(sh_colr)
        #self.shadow.setOffset(5,5)
        #self.shadow.setBlurRadius(25)
        #self.setGraphicsEffect(self.shadow)

    def loadStyle(self):
        branch = 'base'
        try:
            branch = os.environ['GSBRANCH'].split('/')[-1]
        except:
            pass

        if branch == 'dev':
            ssh_file = '/'.join([os.path.dirname(__file__),'res','dev.qss'])
        else:
            ssh_file = '/'.join([os.path.dirname(__file__),'res','style.qss'])

        fh = open(ssh_file,"r")
        qstr = QString(fh.read())
        self.setStyleSheet(qstr)

class LauncherMessage(LauncherDialog):

    def __init__(self, parent=None, title='Launcher Message', message=''):
        super(LauncherMessage, self).__init__(parent)


        self.setWindowTitle(title)

        self.footer = QHBoxLayout()
        self.okbtn = QPushButton('OK')

        # ui control layout
        self.layout = QVBoxLayout(self)
        self.body = QHBoxLayout()
        self.message = QLabel(message)
        self.footer = QHBoxLayout()

        self.layout.addLayout(self.body)
        self.layout.addLayout(self.footer)
        self.body.addWidget(self.message)
        self.footer.addWidget(self.okbtn)

        self.okbtn.clicked.connect(self.doOk)

    def doOk(self):
        self.close()

class LauncherCreateJob(LauncherDialog):

    def __init__(self, parent=None):
        super(LauncherCreateJob, self).__init__(parent)

        self.result = ''

        self.setWindowTitle("Create New Project")

        self.client_name = QLineEdit()
        regexp = QRegExp('^[A-Za-z]([A-Za-z]+)*$')
        validator = LRegExpValidator(regexp)
        self.client_name.setValidator(validator)
        self.client_name.setPlaceholderText('client name')

        self.proj_name = QLineEdit()
        regexp = QRegExp('^[A-Za-z](?:_?[A-Za-z]+)*$')
        validator = LRegExpValidator(regexp)
        self.proj_name.setValidator(validator)
        self.proj_name.setPlaceholderText('untitled')

        self.proj_share = QComboBox()
        self.updateFileShares()

        self.prod_cb = QCheckBox('Create Production Folder')
        self.prod_cb.setChecked(1)
        self.previs_cb = QCheckBox('Create Previs Folder')
        self.previs_cb.setChecked(0)
        self.footer = QHBoxLayout()
        self.okbtn = QPushButton('Create')
        self.cancelbtn = QPushButton('Cancel')

        # ui control layout

        self.client_grp = QHBoxLayout()
        self.client_grp.addWidget(QLabel("Client:"))
        self.client_grp.addWidget(self.client_name)

        self.proj_grp = QHBoxLayout()
        self.proj_grp.addWidget(QLabel("Project:"))
        self.proj_grp.addWidget(self.proj_name)

        self.layout = QVBoxLayout(self)
        self.type_grp = QHBoxLayout()
        self.type_grp.addWidget(QLabel("Location:"))
        self.type_grp.addWidget(self.proj_share)


        self.layout.addLayout(self.client_grp)
        self.layout.addLayout(self.proj_grp)
        self.layout.addLayout(self.type_grp)
        self.layout.addWidget(self.prod_cb)
        self.layout.addWidget(self.previs_cb)
        self.layout.addLayout(self.footer)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.okbtn)


        self.cancelbtn.clicked.connect(self.doCancel)
        self.okbtn.clicked.connect(self.doCreate)

    def updateFileShares(self):
        # clear the item model and init a new one
        self.proj_share.model().clear()
        file_share_list = self.parent.controller.getFileShares('job_share')
        for j in sorted(file_share_list,key=lambda v: v.upper()):
            item = QStandardItem(j)
            self.proj_share.model().appendRow(item)

    def doCreate(self):
        """
        TODO this may need to have an argument to switch which parser to use to create the project. this allows multiple
        templates. it may be too confusing for the front end user. (not worth making configurable)
        TODO this should list existing jobs as a dropdown list and should turn text red if the job exists, and disable
        the Create Button
        :return:
        """

        #upl = '/'.join([str(self.proj_share.currentText()),str(self.proj_name.text())])
        # define a project dictionary to pass to the project controller (it will interpret the dict using project.yml)
        s_share = str(self.proj_share.currentText())
        share = s_share.split('/')[-1]
        server = s_share[:-(len(share)+1)]
        folder_name = "_".join([str(self.client_name.text()),str(self.proj_name.text())])
        stages = []

        d = {
            'server': server,
            'share': share,
            'job': folder_name,
        }
        if self.prod_cb.isChecked():
            stages.append('production')
        if self.previs_cb.isChecked():
            stages.append('previs')

        self.result = self.parent.controller.proj_controller.newProject(d, add_stages=stages)
        (success, response, result) = self.result
        if success:
            m = LauncherMessage(self, "Job Created", "Successfully created job: {0}".format(result))
            m.exec_()
            self.close()
        else:
            m = LauncherMessage(self, "Job Creation Failed", 'Job Creation Failed: {0}'.format(response))
            m.exec_()


    def doCancel(self):
        self.close()

    def getStatus(self):
        return self.result

    # static method to create the dialog and return result
    @staticmethod
    def doIt(parent=None):
        dialog = LauncherCreateJob(parent)
        result = dialog.exec_()
        status = dialog.getStatus()
        return status

class LauncherCreateAsset(LauncherDialog):

    def __init__(self, parent=None):
        super(LauncherCreateAsset, self).__init__(parent)

        self.resize(700, 400)

        self.ui_state = {
            'asset_type':'',
            'group':'',
            'name':'',
            'task_preset':'',
            'task_list':[]
        }

        self.setWindowTitle("Create New Shot/Asset")

        self.asset_typelbl = QLabel("Location:")
        self.asset_type_cb = QComboBox()

        self.asset_grplbl = QLabel("Group:")
        self.asset_grp = QComboBox()
        self.asset_grp.setEditable(True)

        self.asset_namelbl = QLabel("Name:")
        self.asset_name = QLineEdit()
        regexp = QRegExp('^[A-Za-z0-9](?:_?[A-Za-z0-9]+)*$')
        validator = LRegExpValidator(regexp)
        self.asset_name.setValidator(validator)


        self.deftasks_cb = QCheckBox('Create Default Tasks')
        self.deftasks_cb.setChecked(1)

        self.taskpresetlbl = QLabel("Task Presets:")
        self.taskpresets = QComboBox()

        self.task_list = QTreeView()
        self.task_list.setUniformRowHeights(True)
        self.task_model = QStandardItemModel(self.task_list)
        self.task_model.setHorizontalHeaderLabels(['Task', 'SceneName', 'Package'])

        self.task_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.task_list.setModel(self.task_model)
        self.task_list.setColumnWidth(0, 100)

        self.footer = QHBoxLayout()
        self.okbtn = QPushButton('Create')
        self.cancelbtn = QPushButton('Cancel')

        #### LAYOUT ####
        # ui control layout
        self.layout = QVBoxLayout(self)
        self.presetgrp = QHBoxLayout()
        self.presetgrp.addWidget(self.taskpresetlbl)
        self.presetgrp.addWidget(self.taskpresets)

        self.gridlyt = QGridLayout()
        self.gridlyt.setColumnStretch(2,2)
        self.gridlyt.setColumnStretch(1,1,)

        self.gridlyt.addWidget(self.asset_typelbl,0,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.asset_type_cb,0,2)
        self.gridlyt.addWidget(self.asset_grplbl,1,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.asset_grp,1,2)
        self.gridlyt.addWidget(self.asset_namelbl,2,1,Qt.AlignRight)
        self.gridlyt.addWidget(self.asset_name,2,2)

        self.layout.addLayout(self.gridlyt)
        self.layout.addLayout(self.presetgrp)
        self.layout.addWidget(self.task_list)
        self.layout.addLayout(self.footer)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.okbtn)

        self.asset_type_cb.currentIndexChanged.connect(self.assetTypeChanged)

        self.cancelbtn.clicked.connect(self.doCancel)
        self.okbtn.clicked.connect(self.doCreate)

        self.updateUI()

    def updateUI(self):
        self.updateTypes()
        self.ui_state['asset_type'] = self.parent.active_data['asset_type']
        self.ui_state['group'] = self.parent.active_data['asset_grp']

        self.updateLocation()
        self.updateTaskPresets()

    def updateLocation(self):

        #self.asset_type_cb.model().clear()
        print ("Looking for type:{0} group:{1}".format(self.ui_state['asset_type'], self.ui_state['group']))
        asset_type_list = self.parent.controller.proj_controller.getAssetTypeList()
        for asset_type, dname in asset_type_list:
            print ("asset_type={0}".format(asset_type))
            if self.ui_state['asset_type'] == asset_type:
                i = self.asset_type_cb.findText(dname, Qt.MatchFixedString)
                if i >= 0:
                    self.asset_type_cb.setCurrentIndex(i)

        self.updateGroups()
        g=''
        if self.ui_state['asset_type'] == '':
            g = "<None>"
        i = self.asset_grp.findText(g, Qt.MatchFixedString)
        if i >= 0:
            self.asset_grp.setCurrentIndex(i)

        if self.ui_state['asset_type'].startswith('asset'):
            self.asset_grplbl.setText('Category')
            self.asset_namelbl.setText('Asset Name')
            self.asset_name.setPlaceholderText('AssetNameA')
        elif self.ui_state['asset_type'].startswith('shot'):
            self.asset_grplbl.setText('Sequence')
            self.asset_namelbl.setText('Shot Name')
            self.asset_name.setPlaceholderText('001_00')

    def updateTypes(self):
        # clear the item model and init a new one
        self.asset_type_cb.model().clear()
        asset_type_list = self.parent.controller.proj_controller.getAssetTypeList()
        for path, name in sorted(asset_type_list):
            item = QStandardItem(name)
            self.asset_type_cb.model().appendRow(item)

    def updateGroups(self):
        # clear the item model and init a new one
        self.asset_grp.model().clear()

        # add a <None> group item
        item = QStandardItem("<None>")
        self.asset_grp.model().appendRow(item)
        print (self.parent.active_data)
        asset_grp_list = self.parent.controller.proj_controller.getAssetsList(upl_dict=self.parent.active_data, asset_type=self.ui_state['asset_type'], groups_only=True)
        print 'asset_grp_list={0}'.format(asset_grp_list)
        for name in asset_grp_list[1]:
            if name != '':
                item = QStandardItem(name)
                self.asset_grp.model().appendRow(item)
        return

    def updateTaskPresets(self):
        preset_list = ['3D Production', '2D Production', 'Cel Production','VFX Production']
        for name in preset_list:
            if name != '':
                item = QStandardItem(name)
                self.taskpresets.model().appendRow(item)
        return

    def assetTypeChanged(self):
        #self.ui_state['asset_type'] = str(self.asset_type_cb.currentText())
        if self.ui_state['asset_type'].startswith('asset'):
            self.asset_grplbl.setText('Category')
            self.asset_namelbl.setText('Asset Name')
            self.asset_name.setPlaceholderText('AssetNameA')
        elif self.ui_state['asset_type'].startswith('shot'):
            self.asset_grplbl.setText('Sequence')
            self.asset_namelbl.setText('Shot Name')
            self.asset_name.setPlaceholderText('001_00')
        self.updateGroups()

    def updateTaskList(self):
        return

    def doCreateAssetGroup(self):
        pass

    def doCreate(self):

        # translate UI values to proper asset_type and group names
        at = self.asset_type_cb.currentText()
        asset_type_list = self.parent.controller.proj_controller.getAssetTypeList()
        for asset_type, dname in asset_type_list:
            print ("asset_type={0}".format(asset_type))
            if at == dname:
                at = asset_type
        g =self.asset_grp.currentText()
        if g == "<None>":
            g = ''

        d = dict(self.parent.active_data)
        d['asset_type'] = at
        d['asset_grp'] = g
        d['asset'] = str(self.asset_name.text())


        add_tasks = self.parent.controller.proj_controller.getDefaultTasks(at) if self.deftasks_cb.isChecked() else []

        self.result = self.parent.controller.proj_controller.newAsset(d, add_tasks=add_tasks)
        (success, response, result) = self.result
        if success:
            m = LauncherMessage(self, "Asset Created", "Successfully created asset: {0}".format(result))
            m.exec_()
            self.close()
        else:
            m = LauncherMessage(self, "Asset Creation Failed", 'Asset Creation Failed: {0}'.format(response))
            m.exec_()

    def doCancel(self):
        self.close()

    def getStatus(self):
        return self.result

    # static method to create the dialog and return result
    @staticmethod
    def doIt(parent=None):
        dialog = LauncherCreateAsset(parent)
        result = dialog.exec_()
        status = dialog.getStatus()
        return status


class LauncherCreateScene(LauncherDialog):

    def __init__(self, parent=None):
        super(LauncherCreateScene, self).__init__(parent)

        self.setWindowTitle("Create New Task/Scene")

        self.scene_name = QLineEdit()
        regexp = QRegExp('^[A-Za-z0-9](?:_?[A-Za-z0-9]+)*$')
        validator = LRegExpValidator(regexp)
        self.scene_name.setValidator(validator)
        self.scene_name.setPlaceholderText('main')

        self.task_type_dl = QComboBox()
        self.package_type_dl = QComboBox()

        self.footer = QHBoxLayout()
        self.okbtn = QPushButton('Create')
        self.cancelbtn = QPushButton('Cancel')

        # ui control layout
        self.layout = QVBoxLayout(self)


        self.task_type_grp = QHBoxLayout()
        self.task_type_grp.addWidget(QLabel("Task:"))
        self.task_type_grp.addWidget(self.task_type_dl)

        self.name_grp = QHBoxLayout()
        self.name_grp.addWidget(QLabel("Name:"))
        self.name_grp.addWidget(self.scene_name)

        self.package_grp = QHBoxLayout()
        self.package_grp.addWidget(QLabel("Package:"))
        self.package_grp.addWidget(self.package_type_dl)

        self.layout.addLayout(self.task_type_grp)
        self.layout.addLayout(self.name_grp)
        self.layout.addLayout(self.package_grp)
        self.layout.addLayout(self.footer)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.okbtn)

        self.cancelbtn.clicked.connect(self.doCancel)
        self.okbtn.clicked.connect(self.doCreate)

        self.updateUI()

    def updateUI(self):
        self.updateTaskTypes()
        at = self.parent.active_data['asset_type']
        g = self.parent.active_data['asset_grp']
        t = self.parent.active_data['task']

        # set the task to the active task in the ui
        #print ("Looking for type:{0} group:{1}".format(at, g))
        #asset_type_list = self.parent.controller.proj_controller.getAssetTypeList()
        #for asset_type, dname in asset_type_list:
        #    print ("asset_type={0}".format(asset_type))
        #    if at == asset_type:
        #        i = self.asset_type_cb.findText(dname, Qt.MatchFixedString)
        #        if i >= 0:
        #            self.asset_type_cb.setCurrentIndex(i)

        self.updatePackagesTypes()

        #if g == '':
        #    g = "<None>"
        #i = self.asset_grp.findText(g, Qt.MatchFixedString)
        #if i >= 0:
        #    self.asset_grp.setCurrentIndex(i)


    def updateTaskTypes(self):
        # clear the item model and init a new one
        self.task_type_dl.model().clear()
        task_type_list = self.parent.controller.proj_controller.getTaskTypesList()
        for name in sorted(task_type_list):
            item = QStandardItem(name)
            self.task_type_dl.model().appendRow(item)

    def updatePackagesTypes(self):
        # clear the item model and init a new one
        self.package_type_dl.model().clear()
        package_type_list = self.parent.controller.proj_controller.getPackageTypesList()
        print ('package type list {0}'.format(package_type_list))
        for name in sorted(package_type_list):
            item = QStandardItem(name)
            self.package_type_dl.model().appendRow(item)

    def doCreateAssetGroup(self):
        pass

    def doCreate(self):

        # translate UI values to proper asset_type and group names
        tt = str(self.task_type_dl.currentText())
        #task_type_list = self.parent.controller.proj_controller.getTaskTypesList()
        #for task_type in task_type_list:
        #    print ("task_type={0}".format(task_type))
        #    if tt == dname:
        #        tt = task_type
        pkg = str(self.package_type_dl.currentText())

        d = dict(self.parent.active_data)
        d['task'] = tt
        d['package'] = pkg
        d['scenename'] = str(self.scene_name.text())
        d['version'] = 'v000'
        d['ext'] = self.parent.controller.proj_controller.pathParser.getPackageExtension(pkg)


        print (d)

        self.result = self.parent.controller.proj_controller.newScenefile(d)

        (success, response, result) = self.result
        if success:
            m = LauncherMessage(self, "Asset Created", "Successfully created asset: {0}".format(result))
            m.exec_()
            self.close()
        else:
            m = LauncherMessage(self, "Asset Creation Failed", 'Asset Creation Failed: {0}'.format(response))
            m.exec_()

    def doCancel(self):
        self.close()

    def getStatus(self):
        return self.result

    # static method to create the dialog and return result
    @staticmethod
    def doIt(parent=None):
        dialog = LauncherCreateAsset(parent)
        result = dialog.exec_()
        status = dialog.getStatus()
        return status

class LauncherConfig(QDialog):
    ''' dialog for configuring a job or task '''

    def __init__(self, parent=None):
        super(LauncherConfig, self).__init__(parent)
        # load appearance style
        self.load_style()

        self.layout = QVBoxLayout(self)
        self.setWindowTitle("Create New Project")

        self.proj_name = QLineEdit()
        regexp = QRegExp('^[A-Za-z](?:_?[A-Za-z]+)*$')
        validator = LRegExpValidator(regexp)
        self.proj_name.setValidator(validator)

        self.prod_cb = QCheckBox('Create Production Folder')
        self.prod_cb.setChecked(1)
        self.previs_cb = QCheckBox('Create Previs Folder')
        self.previs_cb.setChecked(1)
        self.footer = QHBoxLayout()
        self.okbtn = QPushButton('Create')
        self.cancelbtn = QPushButton('Cancel')

        self.layout.addWidget(self.proj_name)
        self.layout.addWidget(self.prod_cb)
        self.layout.addWidget(self.previs_cb)
        self.layout.addLayout(self.footer)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.okbtn)

        self.okbtn.clicked.connect(self.doOk)
        self.cancelbtn.clicked.connect(self.doCancel)

    def load_style(self):
        branch = 'base'
        try:
            branch = os.environ['GSBRANCH'].split('/')[-1]
        except:
            pass

        if branch == 'dev':
            ssh_file = '/'.join([os.path.dirname(__file__),'res','dev.qss'])
        else:
            ssh_file = '/'.join([os.path.dirname(__file__),'res','style.qss'])

        fh = open(ssh_file,"r")
        qstr = QString(fh.read())
        self.setStyleSheet(qstr)