
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from settings import *
from widgets import *
import core

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

        self.setWindowTitle("Create New Shot/Asset")

        self.asset_name = QLineEdit()
        regexp = QRegExp('^[A-Za-z0-9](?:_?[A-Za-z0-9]+)*$')
        validator = LRegExpValidator(regexp)
        self.asset_name.setValidator(validator)
        self.asset_name.setPlaceholderText('001_00')

        self.asset_grp = QComboBox()

        self.asset_type_cb = QComboBox()
        self.updateTypes()
        self.updateGroups()

        self.prod_cb = QCheckBox('Create Default Tasks')
        self.prod_cb.setChecked(1)
        self.footer = QHBoxLayout()
        self.okbtn = QPushButton('Create')
        self.cancelbtn = QPushButton('Cancel')

        # ui control layout
        self.layout = QVBoxLayout(self)

        self.grp_grp = QHBoxLayout()

        self.type_grp = QHBoxLayout()
        self.type_grp.addWidget(QLabel("Type:"))
        self.type_grp.addWidget(self.asset_type_cb)

        self.grp_grp.addWidget(QLabel("Group:"))
        self.grp_grp.addWidget(self.asset_grp)
        self.grp_grp.addWidget(QPushButton("New"))

        self.name_grp = QHBoxLayout()
        self.name_grp.addWidget(QLabel("Name:"))
        self.name_grp.addWidget(self.asset_name)

        self.layout.addLayout(self.type_grp)
        self.layout.addLayout(self.grp_grp)
        self.layout.addLayout(self.name_grp)
        self.layout.addWidget(self.prod_cb)
        self.layout.addLayout(self.footer)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.okbtn)


        self.cancelbtn.clicked.connect(self.doCancel)
        self.okbtn.clicked.connect(self.doCreate)

    def updateTypes(self):
        # clear the item model and init a new one
        self.asset_type_cb.model().clear()
        asset_type_list = self.parent.controller.proj_controller.getAssetTypeList()
        for path, name in sorted(asset_type_list):
            item = QStandardItem('{0} ({1})'.format(name,path))
            self.asset_type_cb.model().appendRow(item)

    def updateGroups(self):
        # clear the item model and init a new one
        upl = self.parent.active_path['job']
        self.asset_grp.model().clear()
        print (self.parent.active_data)
        asset_grp_list = self.parent.controller.proj_controller.getAssetsList(upl_dict=self.parent.active_data, asset_type=self.parent.active_data['asset_type'], groups_only=True)
        print 'asset_grp_list={0}'.format(asset_grp_list)
        for name in asset_grp_list[1]:
            if name != '':
                item = QStandardItem(name)
                self.asset_grp.model().appendRow(item)
        return

    def doCreateAssetGroup(self):
        pass

    def doCreate(self):
        #upl = '/'.join([str(self.proj_share.currentText()),str(self.proj_name.text())])
        # define a project dictionary to pass to the project controller (it will interpret the dict using project.yml)
        d = dict(self.parent.active_data)
        d = {'asset_type': '//' + str(self.asset_type_cb.currentText()),
             'asset_grp': str(self.asset_grp.currentText()),
             'asset': str(self.asset_name.text())
             }

        # if type is asset

        self.parent.controller.proj_controller.newAsset(d)

    def doCancel(self):
        self.close()

class LauncherCreateTask(LauncherDialog):

    def __init__(self, parent=None):
        super(LauncherCreateTask, self).__init__(parent)


        self.setWindowTitle("Create New Task")

        self.asset_name = QLineEdit()
        regexp = QRegExp('^[A-Za-z0-9](?:_?[A-Za-z0-9]+)*$')
        validator = LRegExpValidator(regexp)
        self.asset_name.setValidator(validator)
        self.asset_name.setPlaceholderText('001_00')

        self.asset_grp = QComboBox()

        self.asset_type_cb = QComboBox()
        self.updateTypes()
        self.updateGroups()

        self.prod_cb = QCheckBox('Create Default Tasks')
        self.prod_cb.setChecked(1)
        self.footer = QHBoxLayout()
        self.okbtn = QPushButton('Create')
        self.cancelbtn = QPushButton('Cancel')

        # ui control layout
        self.layout = QVBoxLayout(self)

        self.type_grp = QHBoxLayout()
        self.type_grp.addWidget(QLabel("Type:"))
        self.type_grp.addWidget(self.asset_type_cb)

        self.grp_grp = QHBoxLayout()
        self.grp_grp.addWidget(QLabel("Group:"))
        self.grp_grp.addWidget(self.asset_grp)
        self.grp_grp.addWidget(QPushButton("New"))



        self.name_grp = QHBoxLayout()
        self.name_grp.addWidget(QLabel("Name:"))
        self.name_grp.addWidget(self.asset_name)

        self.layout.addLayout(self.type_grp)
        self.layout.addLayout(self.grp_grp)
        self.layout.addLayout(self.name_grp)
        self.layout.addWidget(self.prod_cb)
        self.layout.addLayout(self.footer)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.okbtn)


        self.cancelbtn.clicked.connect(self.doCancel)
        self.okbtn.clicked.connect(self.doCreate)

    def updateTypes(self):
        # clear the item model and init a new one
        self.asset_type_cb.model().clear()
        asset_type_list = self.parent.controller.proj_controller.getAssetTypeList()
        for path, name in sorted(asset_type_list):
            item = QStandardItem('{0} ({1})'.format(name,path))
            self.asset_type_cb.model().appendRow(item)

    def updateGroups(self):
        # clear the item model and init a new one
        upl = self.parent.active_paths['job']
        self.asset_grp.model().clear()
        a_type = self.parent.active_asset_type
        asset_grp_list = self.parent.controller.proj_controller.getAssetGroupsList(upl, a_type)
        for path, name in sorted(asset_grp_list):
            if name != '':
                item = QStandardItem(name)
                self.asset_grp.model().appendRow(item)

    def doCreateAssetGroup(self):
        pass

    def doCreate(self):
        #upl = '/'.join([str(self.proj_share.currentText()),str(self.proj_name.text())])
        # define a project dictionary to pass to the project controller (it will interpret the dict using project.yml)
        d = {'server': '//' + str(self.proj_share.currentText().split('/', 1)[0]),
             'job': str(self.proj_name.text()),
             'stage': 'production',
             'asset_grp': str(self.groupName.text()),
             'asset': str(self.asset_name.text())
             }

        # if type is asset

        self.parent.controller.proj_controller.newAsset(d)

    def doCancel(self):
        self.close()



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