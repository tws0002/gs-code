__author__ = 'adamb'

from settings import *
import launcher
from utils import *

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import urllib2
import subprocess
import functools

from environment import *
from gsqt.widgets import *
from gsqt.stylesheets import *

import yaml
import core.project

# TODO LIST
# add project level workgroup config merging/overwrite
# add feedback for uninstalled applications
# add icon resize based on amount of apps loaded

class Launcher(QMainWindow):

    
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR '] = 'TRUE'
    
    def __init__(self, parent=None):

        super(Launcher, self).__init__(parent)

        self.update_gui = False
        self.resize(710, 450)
        self.app_layouts = {}
        self.isLaunching = False
        self.lastLaunch = ''

        # animation init
        self.timeline = QTimeLine(1000)
        self.timeline.setFrameRange(0,100)

        # pyQT settings framework (stores in user registry)
        self.settings = QSettings('gs', 'launcher')

        # OLD load Style Sheet for overall UI appearance
        # sStyleSheet = StyleSheet().styleSheet(1)
        # self.setStyleSheet(sStyleSheet)

        pixmap_icon = QPixmap(os.path.join(RES, "pink.ico"))
        self.setWindowIcon(QIcon(pixmap_icon))

        # parent.setMargin(50)

        # init ui elements
        self.icon_size = QSize(96, 96)
        self.title = "GS Launcher"
        QPixmapCache.setCacheLimit(20480)

        # stores handles to UI objects created
        self.ui = {}
        self.ui['lyt'] = {}
        self.ui['wdgt'] = {}
        self.ui['lbl'] = {}
        self.ui['mdl'] = {}

        # main window frame, (central widget)
        self.load_style()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.shadow = QGraphicsDropShadowEffect(self)
        sh_colr = QColor(0,0,0,50)
        self.shadow.setColor(sh_colr)
        self.shadow.setOffset(5,5)
        self.shadow.setBlurRadius(25)
        self.setGraphicsEffect(self.shadow)

        self.ui['frm'] = GSTitleBar(self, self.title)
        # self.ui['frm'] = QFrame()
        self.ui['frm'].setObjectName('launcherAppFrame')
        self.ui['frm'].setFrameStyle(QFrame.NoFrame)
        self.setCentralWidget(self.ui['frm'])

        # main layout
        self.ui['lyt']['main'] = QVBoxLayout()
        self.ui['lyt']['main'].addSpacing(40)
        self.ui['frm'].setLayout(self.ui['lyt']['main'])
        self.ui['wdgt']['sp1'] = QSplitter()
        self.ui['lyt']['main'].addWidget(self.ui['wdgt']['sp1'])

        # setup sidebar
        self.ui['wdgt']['sidebar'] = QWidget()
        self.ui['wdgt']['sidebar'].setHidden(True)
        self.ui['wdgt']['sidebar_list'] = QListWidget()
        self.ui['lyt']['sidebar_layout'] = QVBoxLayout(self.ui['wdgt']['sidebar'])
        self.ui['lbl']['workgroup_label'] = QLabel("MAIN")
        self.ui['lyt']['sidebar_layout'].addWidget(self.ui['lbl']['workgroup_label'])
        self.ui['lyt']['sidebar_layout'].addWidget(self.ui['wdgt']['sidebar_list'])
        self.ui['wdgt']['sp1'].addWidget(self.ui['wdgt']['sidebar'])
        self.ui['wdgt']['stack_widget'] = QStackedWidget()
        self.ui['wdgt']['sp1'].addWidget(self.ui['wdgt']['stack_widget'])

        sidebar_items = ['Apps','Projects','Workgroups']
        self.ui['lyt']['stack_layouts'] = {}
        i = 0
        for package in sidebar_items:
            package = package.title()
            item = QListWidgetItem(package)
            item.setIcon(QIcon(os.path.join(RES, ("list_"+package+".png"))))
            self.ui['wdgt']['sidebar_list'].addItem(item)
            self.ui['lyt']['stack_layouts'][package] = QWidget()
            self.ui['wdgt']['stack_widget'].addWidget(self.ui['lyt']['stack_layouts'][package])
            self.ui['lyt']['stack_layouts'][package].page_index = i
            i+=1

        self.ui['lyt']['tab1_layout'] = QVBoxLayout(self.ui['lyt']['stack_layouts']['Apps'])
        self.ui['lyt']['tab2_layout'] = QVBoxLayout(self.ui['lyt']['stack_layouts']['Projects'])
        self.ui['lyt']['tab3_layout'] = QVBoxLayout(self.ui['lyt']['stack_layouts']['Workgroups'])

        ## SETUP PROJECTS GROUP ###
        self.ui['wdgt']['project_grp'] = QGroupBox()
        self.ui['wdgt']['project_grp'].setObjectName('lblGroup')
        self.ui['lyt']['tab1_layout'].addWidget(self.ui['wdgt']['project_grp'])
        self.ui['lyt']['project_lyt'] = QHBoxLayout(self.ui['wdgt']['project_grp'])
        self.ui['lbl']['project'] = QLabel('Project  |')
        self.ui['wdgt']['project_combo'] = QComboBox()
        # self.ui['wdgt']['project_combo'].setEditable(True)
        ignoreValid = LIgnoreValidator()
        self.ui['wdgt']['project_combo'].setValidator(ignoreValid)
        # self.ui['wdgt']['project_combo'].completer().setCompletionMode(QCompleter.PopupCompletion)
        font = self.ui['wdgt']['project_combo'].font()
        font.setPointSize(20)
        font.setStyleStrategy(QFont.PreferAntialias);
        self.ui['wdgt']['project_combo'].setFont(font)
        self.ui['mdl']['project_mdl'] = self.ui['wdgt']['project_combo'].model()
        self.ui['lyt']['project_lyt'].addWidget(self.ui['lbl']['project'])
        self.ui['lyt']['project_lyt'].addWidget(self.ui['wdgt']['project_combo'])
        self.ui['lyt']['project_lyt'].setStretchFactor(self.ui['wdgt']['project_combo'], 1)

        ## SETUP ARTISTS GROUP ##
        self.ui['lyt']['artist_lyt'] = QHBoxLayout()
        self.ui['lyt']['tab1_layout'].addSpacing(15)
        self.ui['lyt']['tab1_layout'].addLayout(self.ui['lyt']['artist_lyt'])

        # Initials Grp
        self.ui['wdgt']['initials_grp'] = QGroupBox()
        self.ui['wdgt']['initials_grp'].setObjectName('lblGroup')
        self.ui['lyt']['initials_lyt'] = QHBoxLayout(self.ui['wdgt']['initials_grp'])
        self.ui['lbl']['initials'] = QLabel('Initials   |')
        self.ui['wdgt']['initials_le'] = QLineEdit('ZZ')
        regexp = QRegExp('^([A-z]?[A-z])$')
        validator = LRegExpValidator(regexp)
        self.ui['wdgt']['initials_le'].setValidator(validator)
        self.ui['wdgt']['initials_le'].setFixedWidth(50)
        font = self.ui['wdgt']['initials_le'].font()
        font.setPointSize(16)
        font.setStyleStrategy(QFont.PreferAntialias);
        self.ui['wdgt']['initials_le'].setFont(font)
        self.ui['lyt']['initials_lyt'].addWidget(self.ui['lbl']['initials'])
        self.ui['lyt']['initials_lyt'].addWidget(self.ui['wdgt']['initials_le'])
        self.ui['lyt']['artist_lyt'].addWidget(self.ui['wdgt']['initials_grp'])

        # Workgroup Grp
        self.ui['wdgt']['dispgroup_grp'] = QGroupBox()
        self.ui['wdgt']['dispgroup_grp'].setObjectName('lblGroup')     
        self.ui['lyt']['dispgroup_lyt'] = QHBoxLayout(self.ui['wdgt']['dispgroup_grp'])   
        self.ui['lbl']['task'] = QLabel('Group  |')
        self.ui['wdgt']['dispgroup_combo'] = QComboBox()
        font = self.ui['wdgt']['dispgroup_combo'].font()
        font.setPointSize(20)
        font.setStyleStrategy(QFont.PreferAntialias);
        self.ui['wdgt']['dispgroup_combo'].setFont(font)
        self.ui['mdl']['display_groups_mdl'] = self.ui['wdgt']['dispgroup_combo'].model()
        self.ui['lyt']['dispgroup_lyt'].addWidget(self.ui['lbl']['task'])
        self.ui['lyt']['dispgroup_lyt'].addWidget(self.ui['wdgt']['dispgroup_combo'])
        self.ui['lyt']['dispgroup_lyt'].setStretchFactor(self.ui['wdgt']['dispgroup_combo'], 1)
        self.ui['lyt']['artist_lyt'].addSpacing(15)
        self.ui['lyt']['artist_lyt'].addWidget(self.ui['wdgt']['dispgroup_grp'])
        self.ui['lyt']['artist_lyt'].setStretchFactor(self.ui['wdgt']['dispgroup_grp'], 1)

        # SETUP APPS GROUP #####
        self.ui['wdgt']['buttons_grp'] = QGroupBox('Apps')
        self.ui['lyt']['tab1_layout'].addSpacing(15)
        self.ui['lyt']['tab1_layout'].addWidget(self.ui['wdgt']['buttons_grp'])
        self.ui['lyt']['buttons_lyt'] = QVBoxLayout(self.ui['wdgt']['buttons_grp'])
        self.ui['lyt']['buttons_lyt'].addSpacing(15)
        self.ui['wdgt']['buttons_grid'] = QListWidget(self.ui['wdgt']['buttons_grp'])

        self.ui['lyt']['buttons_lyt'].addWidget(self.ui['wdgt']['buttons_grid'])
        self.ui['wdgt']['buttons_grid'].setViewMode(QListView.IconMode)
        self.ui['wdgt']['buttons_grid'].setMovement(QListView.Static)
        self.ui['wdgt']['buttons_grid'].setResizeMode(QListView.Adjust)

        # self.ui['lyt']['buttons_grid'] = GridLayout(rows=3, cols=5)
        self.ui['wdgt']['buttons_grp'].setLayout(self.ui['lyt']['buttons_lyt'])
        self.ui['lyt']['tab1_layout'].setStretchFactor(self.ui['wdgt']['buttons_grp'], 1)
        # self.ui['wdgt']['jobs_list_box']  = QListWidget()

        # setup context menu
        self.ui['wdgt']['buttons_grid'].setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui['wdgt']['buttons_grid'].connect(self.ui['wdgt']['buttons_grid'],SIGNAL("customContextMenuRequested(QPoint)" ), self.list_item_menu_clicked)

        # connect up signals
        self.ui['wdgt']['sidebar_list'].itemClicked.connect(self.stack_change)
        # self.ui['wdgt']['project_combo'].currentIndexChanged.connect(self.projChange)
        self.ui['wdgt']['dispgroup_combo'].currentIndexChanged.connect(self.disp_grp_change)

        self.ui['wdgt']['buttons_grid'].itemDoubleClicked.connect(self.launch_app)

        self.update_ui()
        self.read_settings()

    def update_ui(self):
        
        self.update_projects()
        self.update_disp_groups()
        self.update_apps()

    def load_style(self):
        ssh_file = '/'.join([os.path.dirname(__file__),'res','style.qss'])
        fh = open(ssh_file,"r")
        qstr = QString(fh.read())
        self.setStyleSheet(qstr)

    def update_projects(self):
        # clear the item model and init a new one
        self.ui['mdl']['project_mdl'].clear()
        job_list = core.project.list_jobs('jobs')
        if job_list:
            for j in sorted(job_list,key=lambda v: v.upper()):
                item = QStandardItem(j)
                font = item.font()
                font.setPointSize(20)
                font.setStyleStrategy(QFont.PreferAntialias);
                item.setFont(font)
                self.ui['mdl']['project_mdl'].appendRow(item)
        else:
            print("Could not Find Jobs Server. Please check the path for 'Servers:jobs' in config/studio.yml")

    def set_project(self, project_name):
        try:
            #print ('Setting to Project: '+project_name)  
            #print (self.ui['wdgt']['project_combo'].currentText())
            index = self.ui['wdgt']['project_combo'].findText(project_name)
            if index > -1:
                self.ui['wdgt']['project_combo'].setCurrentIndex(index)
        
        except:
            print ('Project: {0} not found'.format(project_name))

    def update_disp_groups(self, workgroup='default', project='default'):
        # todo: after project is set, check for workgroups to merge
        # clear the item model and init a new one
        self.ui['mdl']['display_groups_mdl'].clear()
        workgroup_list = WORKGRP
        if workgroup_list:
            for j in sorted(workgroup_list[workgroup]['display_groups'],key=lambda v: v.upper()):
                item = QStandardItem(j)
                font = item.font()
                font.setPointSize(20)
                font.setStyleStrategy(QFont.PreferAntialias);
                item.setFont(font)
                self.ui['mdl']['display_groups_mdl'].appendRow(item)
        else:
            print("Could not Find Workgroups. Please check in config/workgroups.yml")

    def set_disp_grp(self, display_grp):
        #print 'Setting to Workgroup: {0}'.format(display_grp)
        try:
            index = self.ui['wdgt']['dispgroup_combo'].findText(display_grp)
            if index > -1:
                self.ui['wdgt']['dispgroup_combo'].setCurrentIndex(index)
        except:
            print 'Display Group: {0} not found'.format(display_grp)

    def update_apps(self, workgroup='default', display_grp='generalist'):
        self.app_layouts.clear();

        # resize the launcher window based on the amount of apps to show
        app_ct = len (WORKGRP[workgroup]['display_groups'][display_grp])
        app_rows = int(app_ct / 6.0 - .1)
        win_w = self.frameGeometry().width()
        win_h = 400 + (app_rows*105)
        self.resize(win_w, win_h)
        
        self.ui['wdgt']['buttons_grid'].clear()
        for package_full in WORKGRP[workgroup]['display_groups'][display_grp]:
            pkg_and_mode = package_full.split('-')
            package = pkg_and_mode[0]
            mode = 'ui'
            title = package
            if len(pkg_and_mode) > 1:
                mode = pkg_and_mode[1]
            if mode != 'ui':
                title += ' {0}'.format(mode)

            if package in APPS and APPS[package]['show']:


                self.app_layouts[package_full] = QListWidgetItem(title.title())  # QPushButton(package)

                tooltip = str(package+' '+WORKGRP[workgroup]['packages'][package]['version'])
                if 'modules' in WORKGRP[workgroup]['packages'][package]:
                    tooltip += '\n\nMODULES:'
                    for mod in WORKGRP[workgroup]['packages'][package]['modules']:
                        mod_ver = WORKGRP[workgroup]['packages'][package]['modules'][mod]
                        tooltip += '\n'+ mod.ljust(10) + '\t' + mod_ver
                self.app_layouts[package_full].setToolTip(tooltip)

                # pixmap caching
                if os.path.exists(os.path.join(RES,(package+".png"))):
                    value = os.path.join(RES, (package+".png"))
                else: 
                    value = os.path.join(RES, ("gs.png"))

                key = "image:%s"% value
                pixmap = QPixmap()
                if not QPixmapCache.find(key, pixmap):  # loads pixmap from cache if its not already loaded
                    pixmap = QPixmap(value)
                    QPixmapCache.insert(key, pixmap)

                icon = QIcon(pixmap)
                self.app_layouts[package_full].setIcon(icon)
                self.ui['wdgt']['buttons_grid'].setIconSize(self.icon_size)

                self.ui['wdgt']['buttons_grid'].addItem(self.app_layouts[package_full])
                version = WORKGRP[workgroup]['packages'][package]['version']
                try:
                    install_path = os.path.expandvars(os.path.join(APPS[package]['versions'][version]['path'][sys.platform]))
                except KeyError:
                    print 'Could not locate App:{0} Version:{1} in app.yml'.format(package, version)

                # BUG: not working if app path has an env var that only exist during runtime
                if not os.path.exists(install_path):
                    print ("Not Installed: "+install_path)
                    self.app_layouts[package_full].setFlags(Qt.ItemIsEnabled)
                    #self.appLayouts[package].setEnabled(False)

    def list_item_menu_clicked(self, QPos):
        self.item_menu= QMenu()
        # HACK: need to replace this with actual data reference not using the UI label as a keyname
        currentItemName=str(self.ui['wdgt']['buttons_grid'].currentItem().text())
        package = currentItemName.lower()
        menu_item = {}
        menu_item['launch'] = self.item_menu.addAction("Launch {0}".format(currentItemName))
        self.connect(menu_item['launch'], SIGNAL("triggered()"), lambda: self.menu_item_clicked(cmd='launch',package=package,version=''))
        self.ver_menu = self.item_menu.addMenu('Versions')
        self.item_menu.addSeparator()
        #menu_item['config'] = self.item_menu.addAction("Config")

        # add alt versions
        for ver in sorted(APPS[package]['versions'],key=lambda v: v.upper()):
            menu_item[(package+"_"+ver)] = self.ver_menu.addAction(ver)
            self.connect(menu_item[(package+"_"+ver)], SIGNAL("triggered()"), functools.partial(self.menu_item_clicked,'launch',package,ver))

        # add alt modes

        parentPosition = self.ui['wdgt']['buttons_grid'].mapToGlobal(QPoint(0, 0))        
        self.item_menu.move(parentPosition + QPos)
        self.item_menu.show() 

    def menu_item_clicked(self, cmd='', package='', version=''):
        currentItemName=str(self.ui['wdgt']['buttons_grid'].currentItem().text())
        action = self.sender()
        if cmd == 'launch':
            if version == '':
                self.launch_app(self.ui['wdgt']['buttons_grid'].currentItem())
            else:
                self.launch_app(item=self.ui['wdgt']['buttons_grid'].currentItem(), version=version)
        
        print("item={0} cmd={1} package={2} version={3}".format(currentItemName,cmd,package,version))

    def proj_change(self, i):
        # check for project config file and merge config if it exists
        self.update_ui()
        pass

    def disp_grp_change(self, i):
        # check for project config file and merge config if it exists
        display_grp = str(self.ui['wdgt']['dispgroup_combo'].currentText())
        if display_grp == '':
            display_grp = 'generalist'
        self.update_apps(display_grp=display_grp)
        # clear widget layout
        pass

    def stack_change(self):
        sender = self.sender()
        page = str(sender.currentItem().text())
        self.ui['wdgt']['stack_widget'].setCurrentIndex(self.ui['lyt']['stack_layouts'][page].page_index)

    def launch_app(self, item, app='', version='', mode='ui'):


        initials = str(self.ui['wdgt']['initials_le'].text())
        project = str(self.ui['wdgt']['project_combo'].currentText())
        workgroup = 'default' #str(self.ui['wdgt']['dispgroup_combo'].currentText())

        #print ('item: {0} app:{1} version:{2} mode:{3}'.format(item, app, version,mode))
        for name, button in self.app_layouts.iteritems():
            #print 'item:{0} button:{1}'.format(item, button)
            if item == button:
                print ("BUTTON FOUND")
                pkg_and_mode = name.split('-')
                app = pkg_and_mode[0]
                if len(pkg_and_mode) > 1:
                    mode = pkg_and_mode[1]
                if version == '':
                    version = WORKGRP[workgroup]['packages'][app]['version']
        #print 'UI Launching {0} version: {1}'.format(app,version)
        launcher.launch_app(app, version=version, mode=mode, wrkgrp_config='', workgroup=workgroup, initials=initials, project=project)

        return

    def launch_util(self, util=None, version=None):
        #sender = self.sender()
        #
        #for name, button in self.utilLayouts.iteritems():
        #    if sender == button:
        #        util = name
        #        version = UTILITIES[util]['versions'].keys()[0]
        #
        #executable = os.path.join(UTILITIES[util]['versions'][version]['path'][sys.platform], UTILITIES[util]['versions'][version]['modes']['ui'][sys.platform])
        #print executable
        #env = dict(os.environ.items() + self.studio_env.vars.items())
        #
        #si = subprocess.STARTUPINFO()
        #si.dwFlags = subprocess.STARTF_USESTDHANDLES
        #subprocess.Popen(executable, env=env, startupinfo=si)
        return

    def install_app(self):
        pass


    def toggle_launching():
        # if is loading is true 
        if (self.isLaunching):
            # get the app and set its icon to normal
            self.timeline.stop()
            self.isLaunching = False

        # turn on launching status
        else:
            self.isLaunching = True
            item = None#
            self.a = QtGui.QGraphicsItemAnimation()
            self.a.setItem(item)
            self.a.setTimeLine(self.timeline)
            #self.a.setPosAt(0, QtCore.QPointF(0, -10))
            self.a.setRotationAt(1, 360)
            self.timeline.start()



    def init_settings(self):
        print ('Loading settings...')
        try:
            self.settings.setValue('prev_project1', '')
            self.settings.setValue('prev_project2', '')
            self.settings.setValue('prev_project3', '')
            self.settings.setValue('prev_project4', '')
            self.settings.setValue('initials', 'AA')
            self.settings.setValue('role', 'default')
        except:
            print "Unable to Initialize Launcher Settings"

    def save_settings(self):

        print ('Saving settings...')
        try:
            initials = str(self.ui['wdgt']['initials_le'].text())
            project = str(self.ui['wdgt']['project_combo'].currentText())
            display_grp = str(self.ui['wdgt']['dispgroup_combo'].currentText())

            self.settings.setValue('prev_project4', self.settings.value('prev_project3'))
            self.settings.setValue('prev_project3', self.settings.value('prev_project2'))
            self.settings.setValue('prev_project2', self.settings.value('prev_project1'))
            self.settings.setValue('prev_project1', project)
            self.settings.setValue('initials', initials)
            self.settings.setValue('role', display_grp)
        except:
            print "Unable to save settings"

    def read_settings(self):
        print ("loading user settings")
        try:
            initials = str(self.settings.value('initials',type=str))
            project = str(self.settings.value('prev_project1',type=str))
            display_grp = str(self.settings.value('role',type=str))
            self.set_project(project)
            self.ui['wdgt']['initials_le'].setText(initials)
            self.set_disp_grp(display_grp)
        except:
            "initializing settings"
            self.init_settings()

    def close_event(self, event):
        #print ('Running close event')
        self.save_settings()

#if __name__ == '__main__':
#    app = QApplication(sys.argv)
#    wind = Launcher()
#    wind.setWindowTitle('Gentleman Scholar Launcher')
#    wind.show()
#    app.exec_()#