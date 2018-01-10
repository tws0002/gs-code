
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

class LauncherCreateJob(QDialog):

    def __init__(self, parent=None):
        super(LauncherCreateJob, self).__init__(parent)

        self.parent = parent
        # load appearance style
        self.load_style()
        #self.setWindowFlags(Qt.FramelessWindowHint)
        #self.setAttribute(Qt.WA_TranslucentBackground)
        #self.shadow = QGraphicsDropShadowEffect(self)
        #sh_colr = QColor(0,0,0,50)
        #self.shadow.setColor(sh_colr)
        #self.shadow.setOffset(5,5)
        #self.shadow.setBlurRadius(25)
        #self.setGraphicsEffect(self.shadow)

        self.setWindowTitle("Create New Project")

        self.proj_name = QLineEdit()
        regexp = QRegExp('^[A-Za-z](?:_?[A-Za-z]+)*$')
        validator = LRegExpValidator(regexp)
        self.proj_name.setValidator(validator)
        self.proj_name.setPlaceholderText('untitled_project')

        self.proj_share = QComboBox()
        self.update_file_shares()

        self.prod_cb = QCheckBox('Create Production Folder')
        self.prod_cb.setChecked(1)
        self.previs_cb = QCheckBox('Create Previs Folder')
        self.previs_cb.setChecked(1)
        self.footer = QHBoxLayout()
        self.okbtn = QPushButton('Create')
        self.cancelbtn = QPushButton('Cancel')

        # ui control layout
        self.layout = QVBoxLayout(self)
        self.type_grp = QHBoxLayout()
        self.type_grp.addWidget(QLabel("Server Share:"))
        self.type_grp.addWidget(self.proj_share)

        self.proj_grp = QHBoxLayout()
        self.proj_grp.addWidget(QLabel("Project Name:"))
        self.proj_grp.addWidget(self.proj_name)

        self.layout.addLayout(self.type_grp)
        self.layout.addLayout(self.proj_grp)
        self.layout.addWidget(self.prod_cb)
        self.layout.addWidget(self.previs_cb)
        self.layout.addLayout(self.footer)

        self.footer.addWidget(self.cancelbtn)
        self.footer.addWidget(self.okbtn)


        self.cancelbtn.clicked.connect(self.do_cancel)
        self.okbtn.clicked.connect(self.do_create)

    def update_file_shares(self):
        # clear the item model and init a new one
        self.proj_share.model().clear()
        file_share_list = self.parent.controller.get_file_shares('job_share')
        for j in sorted(file_share_list,key=lambda v: v.upper()):
            item = QStandardItem(j)
            self.proj_share.model().appendRow(item)

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

    def do_create(self):
        core.projects.new(str(self.proj_name.text()))


    def do_cancel(self):
        self.close()


class LauncherCreateAsset(QDialog):

    def __init__(self, parent=None):
        super(LauncherCreateAsset, self).__init__(parent)
        # this should be a combo box + line edit
        self.assetGroupName = QLineEdit()
        self.assetName = QLineEdit()
        self.assetType = QCombobox()
        self.okbtn = QPushButton('Create')
        self.cancelbtn = QPushButton('Cancel')


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