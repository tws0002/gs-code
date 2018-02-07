w__author__ = 'adamb'

import sys

from settings import *
from utils import *
#from widgets import *
from dialogs import *
import launcher, core
import functools

import yaml

from PyQt4.QtCore import *
from PyQt4.QtGui import *
elapsed_time = time.time() - START_TIME
print("Launcher PyQt loaded in {0} sec".format(elapsed_time))

class LauncherApp(QApplication):
    def __init__(self, parent=None):
        super(LauncherApp, self).__init__(parent)


class LauncherWindow(QMainWindow):

    #os.environ['QT_AUTO_SCREEN_SCALE_FACTOR '] = 'TRUE'
    a_data = {}
    w_data = {}
    p_data = {}
    
    def __init__(self, parent=None):

        super(LauncherWindow, self).__init__(parent)

        elapsed_time = time.time() - START_TIME
        print("Launcher window init start in {0} sec".format(elapsed_time))


        # this is the UI Model for storing the present display state of the UI
        # any change signals should modify these values and then call the appropriate signals to update the UI
        # any calls to change the data should also update the ui to reflect the active data state
        self.active_data = {
            'file_share':'',
            'server':'',
            'share':'',
            'job':'',
            'stage':'production',
            'asset_type':'',
            'asset_grp':'',
            'asset':'',
            'task':'',
            'version':'',
            'filetype':'',
            'filename':'',
            'filepath':'',
        }
        # caches the active data's path for quick references
        self.active_path = dict(self.active_data)

        #self.load_project_config("")
        self.update_gui = False
        self.resize(1100, 600)
        self.app_layouts = {}
        self.isLaunching = False
        self.lastLaunch = ''

        # animation init
        #self.timeline = QTimeLine(1000)
        #self.timeline.setFrameRange(0,100)

        # pyQT settings framework (stores in user registry)
        self.settings = QSettings('gs', 'launcher')


        self.controller = core.CoreController()

        # OLD load Style Sheet for overall UI appearance
        # sStyleSheet = StyleSheet().styleSheet(1)
        # self.setStyleSheet(sStyleSheet)

        #pixmap_icon = QPixmap(os.path.join(RES, "pink.ico"))
        #self.setWindowIcon(QIcon(pixmap_icon))

        # parent.setMargin(50)

        # init ui elements
        self.icon_size = QSize(48, 48)
        self.title = "GS Launcher"
        #QPixmapCache.setCacheLimit(20480)

        # stores handles to UI objects created
        self.ui = {}
        self.ui['lyt'] = {}
        self.ui['wdgt'] = {}
        self.ui['lbl'] = {}
        self.ui['mdl'] = {}

        # main window frame, (central widget)
        self.loadStyle()
        elapsed_time = time.time() - START_TIME
        print("Launcher loading style in {0} sec".format(elapsed_time))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.shadow = QGraphicsDropShadowEffect(self)
        sh_colr = QColor(0,0,0,50)
        self.shadow.setColor(sh_colr)
        self.shadow.setOffset(5,5)
        self.shadow.setBlurRadius(25)
        self.setGraphicsEffect(self.shadow)

        self.ui['frm'] = LchrTitlebar(self, self.title)
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

        # setup projects sidebar
        self.ui['wdgt']['sidebar'] = QWidget()
        #self.ui['wdgt']['sidebar'].setHidden(True)

        self.ui['wdgt']['sidebar_list'] = QListWidget()
        self.ui['wdgt']['sidebar_list'].setObjectName('Sidebar')
        self.ui['wdgt']['sidebar_list'].setMaximumHeight(30)
        self.ui['wdgt']['sidebar_list'].setFlow(QListView.LeftToRight)
        self.ui['lyt']['sidebar_layout'] = QVBoxLayout(self.ui['wdgt']['sidebar'])

        # project list
        #self.ui['lbl']['workgroup_label'] = QLabel("Projects")
        self.ui['wdgt']['project_list'] = LchrTreeList()
        self.ui['wdgt']['project_list'].setTitle("Projects")


        
        self.ui['lyt']['sidebar_layout'].addWidget(self.ui['wdgt']['sidebar_list'])
        #self.ui['lyt']['sidebar_layout'].addWidget(self.ui['lbl']['workgroup_label'])
        self.ui['lyt']['sidebar_layout'].addWidget(self.ui['wdgt']['project_list'])

        self.ui['wdgt']['sp1'].addWidget(self.ui['wdgt']['sidebar'])
        self.ui['wdgt']['stack_widget'] = QStackedWidget()
        self.ui['wdgt']['sp1'].addWidget(self.ui['wdgt']['stack_widget'])
        self.ui['wdgt']['sp1'].setSizes([160, 500])


        # create sidebar items that show various launcher views
        sidebar_items = ['Apps','Design','Production']
        self.ui['lyt']['stack_layouts'] = {}
        i = 0
        # create a stack panel for each widget
        for package in sidebar_items:
            package = package.title()
            item = QListWidgetItem(package)
            #item.setIcon(QIcon(os.path.join(RES, ("list_"+package+".png"))))
            self.ui['wdgt']['sidebar_list'].addItem(item)
            self.ui['lyt']['stack_layouts'][package] = QWidget()
            self.ui['wdgt']['stack_widget'].addWidget(self.ui['lyt']['stack_layouts'][package])
            self.ui['lyt']['stack_layouts'][package].page_index = i
            i+=1

        # setup project
        self.ui['wdgt']['proj_cat'] = {}
        self.ui['wdgt']['proj_cat']['Recent'] = QStandardItem('Recent')
        self.ui['wdgt']['proj_cat']['Az'] = QStandardItem('A-Z')

        # load projects from core
        self.updateServerShares('job_share')

        self.ui['lyt']['tab1_layout'] = QVBoxLayout(self.ui['lyt']['stack_layouts']['Apps'])
        self.ui['lyt']['tab2_layout'] = QVBoxLayout(self.ui['lyt']['stack_layouts']['Design'])
        self.ui['lyt']['tab3_layout'] = QVBoxLayout(self.ui['lyt']['stack_layouts']['Production'])

        ## Production Tab View
        #splitter
        self.ui['wdgt']['sp2'] = QSplitter()
        self.ui['wdgt']['asset_pane'] = QWidget()
        self.ui['wdgt']['file_pane'] = QWidget()
        self.ui['wdgt']['sp2'].addWidget(self.ui['wdgt']['asset_pane'])
        self.ui['wdgt']['sp2'].addWidget(self.ui['wdgt']['file_pane'])
        self.ui['wdgt']['sp2'].setSizes([200,400])
        self.ui['lyt']['tab3_layout'].addWidget(self.ui['wdgt']['sp2'])

        # asset_pane layout
        self.ui['lyt']['item_layout'] = QVBoxLayout(self.ui['wdgt']['asset_pane'])
        self.ui['wdgt']['asset_tabs'] = QTabWidget()
        self.ui['lyt']['item_layout'].addWidget(self.ui['wdgt']['asset_tabs'])

        # file_pane layout (tabs showing Tasks, Scenefiles views)
        self.ui['lyt']['file_layout'] = QVBoxLayout(self.ui['wdgt']['file_pane'])
        self.ui['wdgt']['file_tabs'] = QTabWidget()

        # task_pane layout sublayout of file_pane
        self.ui['wdgt']['task_widget'] = QWidget()
        self.ui['lyt']['task_layout'] = QVBoxLayout(self.ui['wdgt']['task_widget'])
        self.ui['wdgt']['task_tabs'] = QTabWidget()

        # scene_pane layout sublayout of file_pane
        self.ui['wdgt']['scene_widget'] = QWidget()
        self.ui['lyt']['scene_layout'] = QVBoxLayout(self.ui['wdgt']['scene_widget'])
        self.ui['wdgt']['scene_list'] = LchrTreeList()
        self.ui['wdgt']['scene_list'].tvw.setAlternatingRowColors(True)

        self.ui['lyt']['launch_lyt'] = QHBoxLayout()
        self.ui['wdgt']['launch_btn'] = QPushButton('Launch')

        self.ui['lyt']['file_layout'].addWidget(self.ui['wdgt']['file_tabs'])
        self.ui['lyt']['task_layout'].addWidget(self.ui['wdgt']['task_tabs'])
        self.ui['wdgt']['file_tabs'].addTab(self.ui['wdgt']['task_widget'],'Tasks')
        self.ui['wdgt']['file_tabs'].addTab(self.ui['wdgt']['scene_widget'],'Scenefiles')
        self.ui['lyt']['scene_layout'].addWidget(self.ui['wdgt']['scene_list'])
        self.ui['lyt']['scene_layout'].addLayout(self.ui['lyt']['launch_lyt'])
        self.ui['lyt']['launch_lyt'].addWidget(self.ui['wdgt']['launch_btn'])


        ## Old UI Tab View

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
        font.setStyleStrategy(QFont.PreferAntialias)
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
        font.setStyleStrategy(QFont.PreferAntialias)
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
        font.setStyleStrategy(QFont.PreferAntialias)
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

        # setup app context menu
        if isAdmin():
            self.ui['wdgt']['buttons_grid'].setContextMenuPolicy(Qt.CustomContextMenu)
            self.ui['wdgt']['buttons_grid'].connect(self.ui['wdgt']['buttons_grid'], SIGNAL("customContextMenuRequested(QPoint)" ), self.listItemMenuClicked)

        # connect up signals
        self.ui['wdgt']['sidebar_list'].itemClicked.connect(self.stackChange)
        self.ui['wdgt']['project_combo'].currentIndexChanged.connect(self.projectComboChange)
        self.ui['wdgt']['dispgroup_combo'].currentIndexChanged.connect(self.displayGroupComboChange)
        self.ui['wdgt']['buttons_grid'].itemDoubleClicked.connect(self.launchApp)

        # connect button signals
        self.ui['wdgt']['project_list'].titlebtn1.clicked.connect(self.showCreateJob)


        self.ui['wdgt']['launch_btn'].clicked.connect(self.launchScenefile)

        # set the project
        # self.ui['wdgt']['project_list'].selectionModel().selectionChanged.connect(self.proj_list_change)
        self.ui['wdgt']['project_list'].selectionChanged.connect(self.projectListSelectionChange)
        # set the shot object
        ## self.ui['wdgt']['shot_list'].selectionChanged.connect(self.item_list_change)
        ##self.ui['wdgt']['asset_list'].selectionChanged.connect(self.asset_list_change)

        elapsed_time = time.time() - START_TIME
        print("Launcher updating UI in {0} sec".format(elapsed_time))

        self.updateUI()
        self.readSettings()

    def updateUI(self):
        # prevent signals from being called while updating entire ui
        self.ui['wdgt']['project_combo'].blockSignals(True)
        self.updateProjectsCombo()
        #self.update_disp_groups()
        #self.update_apps()
        self.ui['wdgt']['project_combo'].blockSignals(False)

    def loadStyle(self):
        branch = 'base'
        try:
            print ("GSBRANCH={0}".format(os.environ['GSBRANCH'].split('/')[-1]))
            branch = os.environ['GSBRANCH'].split('/')[-1]
        except KeyError:
            pass

        if branch == 'dev':
            print ("Launching DEV UI")
            ssh_file = '/'.join([os.path.dirname(__file__),'res','dev.qss'])
        else:
            ssh_file = '/'.join([os.path.dirname(__file__),'res','style.qss'])

        fh = open(ssh_file,"r")
        qstr = QString(fh.read())
        self.setStyleSheet(qstr)

    def showCreateJob(self):
        rslt = LauncherCreateJob.doIt(self)
        # update the project list ui
        if rslt != '':
            self.updateProjectsList()


    def showCreateAsset(self):
        rslt = LauncherCreateAsset.doIt(self)
        # update the project list ui
        if rslt != '':
            self.updateAssetList(self.active_path['job'],self.active_data['asset_type'])

    def showCreateScene(self):
        d = LauncherCreateScene(self)
        d.exec_()

    def setActiveFile(self, filename):
        """
        this allows the active state of the ui to be set by a filepath. this allows the launcher to quickly navigate to
        the correct project given only a recent file path.
        :param filename: the filepath to determine the active state
        :return:
        """
        # TODO ask the path parser for the asset info for the file, then update the self.active_data
        # TODO update the ui to reflect the active data
        return

    def updateProjectsCombo(self):
        ''' this is for the old combobox project list. should be deprecated'''
        # clear the item model and init a new one
        self.ui['mdl']['project_mdl'].clear()
        # new way (temp disabled) # job_list = self.controller.get_projects_list('job_share')  #
        job_list = core.list_jobs('jobs')
        if job_list:
            for j in sorted(job_list,key=lambda v: v.upper()):
                item = QStandardItem(j)
                font = item.font()
                font.setPointSize(20)
                font.setStyleStrategy(QFont.PreferAntialias);
                item.setFont(font)
                # need to append full project path in column
                self.ui['mdl']['project_mdl'].appendRow(item)
        else:
            print("Could not Find Jobs Server. Please check the path for 'Servers:jobs' in config/studio.yml")

    def updateServerShares(self,share_name):
        share_list = self.controller.getFileShares(share_name)
        if len(share_list):
            self.active_data['file_share'] = share_name
            self.active_path['file_share'] = share_list[0]
        else:
            print ("Could not locate shares of type {0}".format(share_name))
        self.updateProjectsList()

    def updateProjectsList(self):
        item_list = self.controller.getProjectsList(self.active_data['file_share'])
        # setup app context menu
        if isAdmin():
            self.ui['wdgt']['project_list'].setContextMenuPolicy(Qt.CustomContextMenu)
            self.ui['wdgt']['project_list'].connect(self.ui['wdgt']['project_list'], SIGNAL("customContextMenuRequested(QPoint)" ), self.projectListContextMenuClicked)

        # load projects from core
        item_dict = {}
        item_dict['grp_a'] = {'name':'Recent','children':{}}
        item_dict['grp_b'] = {'name':'A-Z','children':{}}
        for item in sorted(item_list):
            key = item.split('/')[-1]
            item_dict['grp_b']['children'][key] = {}
            item_dict['grp_b']['children'][key]['name'] = item.split('/')[-1]
            item_dict['grp_b']['children'][key]['filepath'] = item
            item_dict['grp_b']['children'][key]['status'] = "Active"

        # loads the above dictionary into a treeview as standard items
        self.ui['wdgt']['project_list'].loadViewModelFromDict(item_dict)

    def updateAssetsTabs(self, project_path):
        '''
        :param project_path: the path to the project to query for asset libraries
        :return:
        '''
        # clear any current tabs
        self.ui['wdgt']['asset_tabs'].clear()

        self.ui['wdgt']['asset_tabs'].currentChanged.connect(self.assetTabChanged)
        # for each asset template type, create a tab widget for it
        asset_type_list = self.controller.proj_controller.getAssetTypeList()
        # update each asset type
        START_TIME = time.time()
        for asset_type, dname in asset_type_list:
            # create the widget if it doesn't exist
            if not asset_type in self.ui['wdgt']:
                self.ui['wdgt'][asset_type] = LchrTreeList()
                self.ui['wdgt'][asset_type].tvw.setIndentation(15)
                self.ui['wdgt'][asset_type].tvw.setRootIsDecorated(True)
                self.ui['wdgt'][asset_type].selectionChanged.connect(self.assetListChange)
                self.ui['wdgt'][asset_type].setFilterParents(True)
                self.ui['wdgt'][asset_type].asset_type = asset_type
                print "setting current path to {0}".format(dname)
                # TODO current_path should store the asest lib path by calling pathParser
                self.ui['wdgt'][asset_type].current_path = ''
                self.ui['wdgt'][asset_type].tvw.setAlternatingRowColors(True)
                self.ui['wdgt'][asset_type].titlebtn1.clicked.connect(self.showCreateAsset)

            self.ui['wdgt']['asset_tabs'].addTab(self.ui['wdgt'][asset_type],dname)
            self.updateAssetList(project_path, asset_type)

        elapsed_time = time.time() - START_TIME
        print("core.projects.getAssetsList() ran in {0} sec".format(elapsed_time))

        self.assetTabChanged(0)

    def assetTabChanged(self, i):

        vis_item = self.ui['wdgt']['asset_tabs'].currentWidget()
        if vis_item:
            self.active_path['asset_type'] = vis_item.current_path
            self.active_data['asset_type'] = vis_item.asset_type
        return

    def updateAssetList(self, project_path, asset_type):

        # get top level assets
        item_tuple = self.controller.proj_controller.getAssetsList(upl_dict=self.active_data, asset_type=asset_type)
        # load projects from core

        item_dict = {}
        #item_dict[asset_type] = {'name':asset_type,'children':{}}
        for item in sorted(item_tuple[1]):
            split_name = item.split('/')
            if not split_name[0] in item_dict:
                item_dict[split_name[0]] = {}
                item_dict[split_name[0]]['name'] = split_name[0]
                item_dict[split_name[0]]['filepath'] = '/'.join([item_tuple[0],split_name[0]])
                item_dict[split_name[0]]['status'] = "Active"
                item_dict[split_name[0]]['is_group'] = False
                item_dict[split_name[0]]['group'] = ''
                item_dict[split_name[0]]['children'] = {}
            if len(split_name) > 1:
                item_dict[split_name[0]]['is_group'] = True
                item_dict[split_name[0]]['children'][split_name[1]] = {}
                item_dict[split_name[0]]['children'][split_name[1]]['name'] = split_name[1]
                item_dict[split_name[0]]['children'][split_name[1]]['filepath'] = '/'.join([item_tuple[0],split_name[0],split_name[1]])
                item_dict[split_name[0]]['children'][split_name[1]]['status'] = "Active"
                item_dict[split_name[0]]['children'][split_name[1]]['is_group'] = False
                item_dict[split_name[0]]['children'][split_name[1]]['group'] = split_name[0]

        print ("Asset_Type:{0} Asset_Data{1}".format(asset_type,item_tuple))
        # loads the above dictionary into a treeview as standard items
        self.ui['wdgt'][asset_type].loadViewModelFromDict(item_dict)
        self.ui['wdgt'][asset_type].current_path = item_tuple[0]

    def updateTaskTabs(self, project_path, asset_path):
        '''
        :param project_path: the path to the project to query for asset libraries
        :return:
        '''
        # clear any current tabs
        self.ui['wdgt']['task_tabs'].clear()

        self.ui['wdgt']['task_tabs'].currentChanged.connect(self.taskTabChanged)
        # for each asset template type, create a tab widget for it
        task_type_list = self.controller.proj_controller.getTaskList(upl=asset_path)
        print ('task_type_list={0}'.format(task_type_list))
        # update each asset type
        for task_type in task_type_list[1]:
            # create the widget if it doesn't exist
            if not task_type in self.ui['wdgt']:
                self.ui['wdgt'][task_type] = LchrTreeList()
                self.ui['wdgt'][task_type].tvw.setIndentation(15)
                self.ui['wdgt'][task_type].tvw.setRootIsDecorated(True)
                self.ui['wdgt'][task_type].selectionChanged.connect(self.taskListChanged)
                self.ui['wdgt'][task_type].setFilterParents(True)
                self.ui['wdgt'][task_type].task_type = task_type
                self.ui['wdgt'][task_type].current_path = ''
                self.ui['wdgt'][task_type].titlebtn1.clicked.connect(self.showCreateScene)

            self.ui['wdgt'][task_type].tvw.setAlternatingRowColors(True)
            self.ui['wdgt']['task_tabs'].addTab(self.ui['wdgt'][task_type],task_type.title())

            self.active_path['task'] = task_type
            self.updateTaskList(task_type)

        self.taskTabChanged(0)

    def taskTabChanged(self, i):

        vis_item = self.ui['wdgt']['task_tabs'].currentWidget()
        if vis_item:
            self.active_path['task'] = vis_item.current_path
            self.active_data['task'] = vis_item.task_type
        return

    def updateTaskList(self, task_type):
        #item_list = core.core.list_shots('jobs',project_name)

        # get top level list of packages for the given task
        item_tuple = self.controller.proj_controller.getTaskScenesList(upl_dict=self.active_data, task_type=task_type)
        # load projects from core
        item_dict = {}
        #item_dict[asset_type] = {'name':asset_type,'children':{}}
        for item in sorted(item_tuple[1]):
            split_name = item.split('/')
            if not split_name[0] in item_dict:
                item_dict[split_name[0]] = {}
                item_dict[split_name[0]]['name'] = split_name[0]
                item_dict[split_name[0]]['filepath'] = '/'.join([item_tuple[0],split_name[0]])
                item_dict[split_name[0]]['status'] = "Active"
                item_dict[split_name[0]]['is_group'] = False
                item_dict[split_name[0]]['children'] = {}
            if len(split_name) > 1:
                the_rest = '/'.join(split_name[1:])
                item_dict[split_name[0]]['is_group'] = True
                item_dict[split_name[0]]['children'][the_rest] = {}
                item_dict[split_name[0]]['children'][the_rest]['name'] = the_rest
                item_dict[split_name[0]]['children'][the_rest]['filepath'] = '/'.join([item_tuple[0],split_name[0],the_rest])
                item_dict[split_name[0]]['children'][the_rest]['status'] = "Active"
                item_dict[split_name[0]]['children'][the_rest]['is_group'] = False

        print ("Task_Data:{0}".format(item_tuple))
        # loads the above dictionary into a treeview as standard items
        self.ui['wdgt'][task_type].loadViewModelFromDict(item_dict)
        self.ui['wdgt'][task_type].current_path = item_tuple[0]
        print ("setting task  tab:{0}".format(task_type))
        return

    def taskListChanged(self):
        return

    def updateScenesList(self, asset_path):

        item_list = self.controller.proj_controller.getScenesList(filepath=asset_path, file_types='mb')

        item_dict = {}
        #item_dict[asset_type] = {'name':asset_type,'children':{}}
        for item in sorted(item_list):
            rel_name = item[0]
            full_path = item[1]
            if not rel_name in item_dict:
                item_dict[item[1]] = {}
                item_dict[item[1]]['name'] = item[1]
                item_dict[item[1]]['filepath'] = item[0]
                item_dict[item[1]]['status'] = "Active"
                item_dict[item[1]]['is_group'] = False


        self.ui['wdgt']['scene_list'].loadViewModelFromDict(item_dict)   

    def getProjectConfig(self, project='', config_type='workgroup'):

        proj_config = os.path.join(STUDIO['servers']['jobs']['root_path'],project,"03_production",".pipeline","config","{0}.yml".format(config_type))
        #print ("Testing Project Config = {0}".format(proj_config))
        found_config = ''
        if os.path.isfile(proj_config):
            found_config = proj_config
            #print ("GS Launcher: loading local project {1} config:{0}").format(found_config,config_type)
        return found_config 

    def appendConfigFile(self, filepath, config_type):
        dataMap = self.getConfigFile(filepath)
        origMap = None
        if config_type == 'app':
            origMap = self.a_data
        elif config_type == 'workgroups':
            origMap = self.w_data
        if type(origMap) == type(dict()):
            print ("Appending Config File = {0}".format(filepath))
            # need to parse the new datamap and only overwrite key,value pairs, do not overwrite entire key,dict pairs
            self.configMerge(origMap, dataMap)

            #origMap.update(dataMap)

    def configMerge(self, orig_dict, new_dict):
        #print new_dict
        for key, val in new_dict.iteritems():
            if key in orig_dict:
                if type(val) == type(dict()):
                    self.configMerge(orig_dict[key], val)
                else:
                    orig_dict[key] = val
            else:
                orig_dict[key] = val


    def getConfigFile(self, filepath):
        f = open(filepath)
        # use safe_load instead load
        dataMap = yaml.load(f, Loader=yaml.CLoader)
        f.close()
        #print ("Loaded Config File = {0}".format(filepath))
        return dataMap

    def loadProjectConfig(self, project_name):
        #print ("CHECKING FOR NEW CONFIG")
        wrkgrp_config = CONFIG+'/workgroups.yml'
        app_config = CONFIG+'/app.yml'
        mod_config = CONFIG+'/modules.yml'

        #job_wrkgrp_config = os.path.join("\\\\scholar","projects",project_name,"03_production",".pipeline","config","workgroups.yml")
        #if os.path.isfile(job_wrkgrp_config):
        #    wrkgrp_config = job_wrkgrp_config
        #    print ("GS Launcher: loading local project workgroup config:{0}").format(wrkgrp_config)
        #else:
        #    wrkgrp_config = CONFIG+'/workgroups.yml'
        #    #print ("GS Launcher: loading studio workgroup config:{0}").format(wrkgrp_config)
        #
        #job_app_config = os.path.join("\\\\scholar","projects",project_name,"03_production",".pipeline","config","app.yml")
        #if os.path.isfile(job_app_config):
        #    app_config = job_app_config
        #    print ("GS Launcher: loading local project app config:{0}").format(app_config)
        #else:
        #    app_config = CONFIG+'/app.yml'
        #    #print ("GS Launcher: loading studio app config:{0}").format(app_config)

        ###load the apps dictionary
        ##f = open(wrkgrp_config)
        ##self.w_data = None
        ##self.w_data = yaml.safe_load(f)
        ##f.close()

        self.w_data = self.getConfigFile(wrkgrp_config)
        proj_workgrp = self.getProjectConfig(project_name, 'workgroups')
        if (os.path.isfile(proj_workgrp)):
            #print ("Found Project Workgroup Config = {0}".format(proj_workgrp))
            self.appendConfigFile(proj_workgrp, 'workgroups')
        
        ###load the modules dictionary
        ##f = open(CONFIG+"/modules.yml")
        ##MODULES = yaml.safe_load(f)
        ##f.close()
        self.m_data = self.getConfigFile(mod_config)
        
        ###load the workgroups dictionary
        ##f = open(app_config)
        ##self.a_data = None
        ##self.a_data = yaml.safe_load(f)
        ##f.close()
        self.a_data = self.getConfigFile(app_config)
        proj_app = self.getProjectConfig(project_name, 'app')
        if (os.path.isfile(proj_app)):
            #print ("Project App Config = {0}".format(proj_app))
            self.appendConfigFile(proj_app, 'app')

    def setProjectCombo(self, project_name):
        try:
            #print ('Setting to Project: '+project_name)  
            #print (self.ui['wdgt']['project_combo'].currentText())
            old_p = self.ui['wdgt']['project_combo'].currentText()
    
            index = self.ui['wdgt']['project_combo'].findText(project_name)
            if index > -1:
                self.ui['wdgt']['project_combo'].setCurrentIndex(index)
    
            # if project didn't change, still fire a signal so that the ui is updated
            if (old_p == project_name):
                self.projectComboChange(index)
    
            #self.load_project_config(project_name)
            #self.update_disp_groups()
            #self.update_apps()
        except:
            print ('Project: {0} not found'.format(project_name))

    def updateDisplayGroups(self, workgroup='default', project='default'):
        # todo: after project is set, check for workgroups to merge
        # clear the item model and init a new one
        # get the current value for restoring value after refresh
        
        self.ui['mdl']['display_groups_mdl'].clear()
        workgroup_list = self.w_data
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

    def setDisplayGroup(self, display_grp):
        #print 'Setting to Workgroup: {0}'.format(display_grp)
        try:
            index = self.ui['wdgt']['dispgroup_combo'].findText(display_grp)
            if index > -1:
                self.ui['wdgt']['dispgroup_combo'].setCurrentIndex(index)
        except:
            print 'Display Group: {0} not found'.format(display_grp)

    def updateAppsList(self, workgroup='default', display_grp='Generalist'):
        self.app_layouts.clear();

        # resize the launcher window based on the amount of apps to show
        app_ct = len (self.w_data[workgroup]['display_groups'][display_grp])
        app_rows = int(app_ct / 6.0 - .1)
        win_w = self.frameGeometry().width()
        win_h = 400 + (app_rows*110)

        # disabled autosize since we are now able to resize window
        #self.resize(win_w, win_h)
        
        self.ui['wdgt']['buttons_grid'].clear()
        for package_full in self.w_data[workgroup]['display_groups'][display_grp]:
            pkg_and_mode = package_full.split('-')
            package = pkg_and_mode[0]

            app = package
            if 'app' in self.w_data[workgroup]['packages'][package]:
                app = self.w_data[workgroup]['packages'][package]['app']
            
            title = package
            if 'title' in self.w_data[workgroup]['packages'][package]:
                title = self.w_data[workgroup]['packages'][package]['title']

            mode = 'ui'
            if len(pkg_and_mode) > 1:
                mode = pkg_and_mode[1]
            if mode != 'ui':
                title += ' {0}'.format(mode)

            if app in self.a_data and self.a_data[app]['show']:

                self.app_layouts[package_full] = QListWidgetItem(title.title())  # QPushButton(package)

                # set the tooltip to show version and modules configured
                tooltip = str(app+' '+self.w_data[workgroup]['packages'][package]['version'])
                if 'modules' in self.w_data[workgroup]['packages'][package]:
                    tooltip += '\n\nMODULES:'
                    for mod in self.w_data[workgroup]['packages'][package]['modules']:
                        mod_ver = self.w_data[workgroup]['packages'][package]['modules'][mod]
                        tooltip += '\n'+ mod.ljust(10) + '\t' + mod_ver
                self.app_layouts[package_full].setToolTip(tooltip)

                # pixmap caching
                if os.path.exists(os.path.join(RES,(package_full+".png"))):
                    value = os.path.join(RES, (package_full+".png"))
                elif os.path.exists(os.path.join(RES,(package+".png"))):
                    value = os.path.join(RES, (package+".png"))
                elif os.path.exists(os.path.join(RES,(app+".png"))):
                    value = os.path.join(RES, (app+".png"))
                else:
                    value = os.path.join(RES, ("gs.png"))

                #print 'dev: loading image: {0}'.format(value)

                key = "image:%s"% value
                pixmap = QPixmap()
                if not QPixmapCache.find(key, pixmap):  # loads pixmap from cache if its not already loaded

                    pixmap = QPixmap(value)
                    QPixmapCache.insert(key, pixmap)

                icon = QIcon(pixmap)
                self.app_layouts[package_full].setIcon(icon)
                self.ui['wdgt']['buttons_grid'].setIconSize(self.icon_size)

                self.ui['wdgt']['buttons_grid'].addItem(self.app_layouts[package_full])
                version = self.w_data[workgroup]['packages'][package]['version']
                install_path = ""
                try:
                    install_path = os.path.expandvars(os.path.join(self.a_data[app]['versions'][version]['path'][sys.platform]))
                except KeyError:
                    print 'Could not locate App:{0} Version:{1} in app.yml'.format(package, version)

                # BUG: not working if app path has an env var that only exist during runtime
                if not os.path.exists(install_path):
                    #print ("Not Installed: "+install_path)
                    self.app_layouts[package_full].setFlags(Qt.ItemIsSelectable)
                    self.app_layouts[package_full].setToolTip(tooltip+' (Not Installed)')
                    #self.appLayouts[package].setEnabled(False)

    def listItemMenuClicked(self, QPos):
        self.item_menu= QMenu()
        # TODO HACK: need to replace this with actual data reference not using the UI label as a keyname
        
        item = currentItemName=self.ui['wdgt']['buttons_grid'].currentItem()
        currentItemName=str(item.text())
        package = currentItemName.lower()
        app = package

        for name, button in self.app_layouts.iteritems():
            if item == button:
                button_name = name
                pkg_and_mode = name.split('-')
                package = pkg_and_mode[0]
                app = package

        menu_item = {}
        menu_item['launch'] = self.item_menu.addAction("Launch {0}".format(currentItemName))
        self.connect(menu_item['launch'], SIGNAL("triggered()"), lambda: self.menuItemClicked(cmd='launch', package=package, version=''))
        self.ver_menu = self.item_menu.addMenu('Versions')
        self.item_menu.addSeparator()
        #menu_item['config'] = self.item_menu.addAction("Config")

        # add alt versions
        for ver in sorted(self.a_data[app]['versions'],key=lambda v: v.upper()):
            menu_item[(package+"_"+ver)] = self.ver_menu.addAction(ver)
            self.connect(menu_item[(package+"_"+ver)], SIGNAL("triggered()"), functools.partial(self.menuItemClicked, 'launch', package, ver))

        # TODO add alt modes
        parentPosition = self.ui['wdgt']['buttons_grid'].mapToGlobal(QPoint(0, 0))        
        self.item_menu.move(parentPosition + QPos)
        self.item_menu.show()

    def menuItemClicked(self, cmd='', package='', version=''):
        currentItemName=str(self.ui['wdgt']['buttons_grid'].currentItem().text())
        action = self.sender()
        if cmd == 'launch':
            if version == '':
                self.launchApp(self.ui['wdgt']['buttons_grid'].currentItem())
            else:
                self.launchApp(item=self.ui['wdgt']['buttons_grid'].currentItem(), version=version)
        
        print("item={0} cmd={1} package={2} version={3}".format(currentItemName,cmd,package,version))

    def projectComboChange(self, i):
        # check for project config file and merge config if it exists
        
        p = str(self.ui['wdgt']['project_combo'].currentText())
        self.p_data['project_name'] = p
        self.loadProjectConfig(p)
        d_grp = str(self.ui['wdgt']['dispgroup_combo'].currentText())

        # update display groups but don't execute signals
        self.ui['wdgt']['dispgroup_combo'].blockSignals(True)
        self.updateDisplayGroups()
        self.setDisplayGroup(d_grp)
        d_grp = str(self.ui['wdgt']['dispgroup_combo'].currentText())
        self.ui['wdgt']['dispgroup_combo'].blockSignals(False)
        self.updateAppsList(display_grp=d_grp)


############
    def projectListSelectionChange(self, selected, deselected):
        ''' this updates the current project '''

        items = self.ui['wdgt']['project_list'].getSelectedItems()
        for i in items:
            print 'sel_item:{0}'.format(i.text())
        if len(items):
            p_name = str(items[0].text())
            p_path = str(items[1].text())
            print ('setting project to {0}'.format(p_path))

            # this appears to be a little slow!
            self.loadProjectConfig(p_path)
            #self.set_project_combo(p)
            self.p_data['project_name'] = p_path
            d_grp = str(self.ui['wdgt']['dispgroup_combo'].currentText())

            # update display groups but don't execute signals
            self.ui['wdgt']['dispgroup_combo'].blockSignals(True)
            self.updateDisplayGroups()
            self.setDisplayGroup(d_grp)
            d_grp = str(self.ui['wdgt']['dispgroup_combo'].currentText())
            self.ui['wdgt']['dispgroup_combo'].blockSignals(False)
            self.updateAppsList(display_grp=d_grp)

            # TODO switch from a hardcoded test for which project.yml to load to something more elegant
            # check if its an old project struct
            if os.path.isdir('{0}/03_production'.format(p_path)):
                config_path = '{0}/projects_old.yml'.format(CONFIG)
                self.controller.proj_controller.setConfig(config_path)
            else:
                config_path = '{0}/projects.yml'.format(CONFIG)
                self.controller.proj_controller.setConfig(config_path)

            self.resetActiveData()

            #update selected dict
            self.active_data['job'] = p_name
            self.active_path['job'] = p_path

            # update the active data by parsing the project
            p_data = self.controller.proj_controller.pathParser.parsePath(p_path)
            for key, val in p_data.iteritems():
                self.active_data[key] = val

            print (p_data)
            #self.update_items_list(p,'shot_3d')
            #self.update_assets_list(p,'asset_3d')`
            self.ui['wdgt']['scene_list'].clearAllItems()
            self.ui['wdgt']['task_tabs'].clear()
            self.updateAssetsTabs(p_path)


            #{
            #    'server': '//{0}'.split(p_path)[0],
            #    'project': str(p_name)
            #}

    def assetListChange(self, selected, deselected):
        ''' slot receiver for asset_list selection changes signal

        :param selected: QItemSelection new selection
        :param deselected: QItemSelection
        :return:
        '''
        # from selectionModel returns QProxyFilterModel index
        item_indx = selected.indexes()
        #item_indx = self.sender().selectedIndexes() # old way of doing this
        if len(item_indx):
            # convert/remap QProxyFilterModel index to StandardItemModel index to get the actual item
            src_index = item_indx[0].model().mapToSource(item_indx[0])
            item =  item_indx[0].model().sourceModel().itemFromIndex(src_index)
            s = str(item.text())
            src_index = item_indx[1].model().mapToSource(item_indx[1])
            item =  item_indx[1].model().sourceModel().itemFromIndex(src_index)
            a = str(item.text())
            src_index = item_indx[2].model().mapToSource(item_indx[2])
            item =  item_indx[2].model().sourceModel().itemFromIndex(src_index)
            g = str(item.text())
            print ('Setting shot/asset to {0}, group to {1}'.format(s,g))
            self.active_data['asset'] = s
            self.active_path['asset'] = a
            self.active_data['asset_grp'] = g
            # TODO set active_path  asset correctly
            #self.active_path['asset'] =

            self.updateScenesList(a)
            self.updateTaskTabs(self.active_path['job'],self.active_path['asset'])
        else:
            print ('Selection Empty')
            self.active_path['asset'] = ''
            self.active_data['asset'] = ''
            self.active_data['asset_grp'] = ''


    def displayGroupComboChange(self, i):
        # check for project config file and merge config if it exists
        display_grp = str(self.ui['wdgt']['dispgroup_combo'].currentText())
        if display_grp == '':
            display_grp = 'generalist'
        self.updateAppsList(display_grp=display_grp)
        # clear widget layout


    def stackChange(self):
        sender = self.sender()
        page = str(sender.currentItem().text())
        self.ui['wdgt']['stack_widget'].setCurrentIndex(self.ui['lyt']['stack_layouts'][page].page_index)

    def toggleLaunchStatus(self, widget, text):
        widget.setText(text)

    def projectListContextMenuClicked(self, QPos):
        self.proj_menu = QMenu()

        # get the list item that is selected
        # TODO HACK: need to replace this with actual data reference not using the UI label as a keyname

        menu_item = {}
        menu_item['config_job'] = self.proj_menu.addAction("Configure Job")
        self.proj_menu.addSeparator()
        menu_item['add_stage'] = self.stage_menu = self.proj_menu.addMenu('Add Project Stage')
        stages = self.controller.proj_controller.getStageList()
        for stage in stages:
            menu_item[stage[0]] = self.stage_menu.addAction("Add {0}".format(stage[1]))
        menu_item['rename'] = self.proj_menu.addAction("Rename Job")
        menu_item['clone'] = self.proj_menu.addAction("Duplicate Job")
        self.proj_menu.addSeparator()
        menu_item['explore'] = self.proj_menu.addAction("Open in Explorer")

        parentPosition = self.sender().mapToGlobal(QPoint(0, 0))
        self.proj_menu.move(parentPosition + QPos)
        self.proj_menu.show()

    def projectListMenuItemClicked(self, cmd='', package='', version=''):
        currentItemName = str(self.ui['wdgt']['buttons_grid'].currentItem().text())
        action = self.sender()
        if cmd == 'launch':
            if version == '':
                self.launchApp(self.ui['wdgt']['buttons_grid'].currentItem())
            else:
                self.launchApp(item=self.ui['wdgt']['buttons_grid'].currentItem(), version=version)

        print("item={0} cmd={1} package={2} version={3}".format(currentItemName, cmd, package, version))

    def launchScenefile(self):
        ''' launches the selected scenefile in the scenefile list'''

        btn = self.sender()

        initials = str(self.ui['wdgt']['initials_le'].text())
        project = '' # = str(self.ui['wdgt']['project_combo'].currentText())
        workgroup = 'default' #str(self.ui['wdgt']['dispgroup_combo'].currentText())

        # get the filepath from teh scenefile list
        item = self.ui['wdgt']['scene_list'].getSelectedItems()
        if len(item):
            print "ITEM={0}".format(item)
            filepath = str(item[1].text())
            if os.path.exists(filepath):

                #print 'UI Launching {0} version: {1}'.format(app,version)
                print "Launching Filepath={0}".format(filepath)
                launcher.launch_app(app='', workgroup=workgroup, initials=initials,  mode='ui', project=project, filepath=filepath)

                text = str(self.sender().text())
                btn.setText("Starting...")
                test_timer = QTimer()
                test_timer.singleShot(4000, lambda: self.toggleLaunchStatus(btn, text))

                self.addRecentProject(project)

    def launchApp(self, item, app='', version='', mode='ui'):

        initials = str(self.ui['wdgt']['initials_le'].text())
        # TODO needs to be the whole path to the share in the new pipeline
        project = str(self.ui['wdgt']['project_combo'].currentText())
        workgroup = 'default' #str(self.ui['wdgt']['dispgroup_combo'].currentText())
        button = ''
        button_name = ''
        filepath=''

        #print ('item: {0} app:{1} version:{2} mode:{3}'.format(item, app, version,mode))
        for name, button in self.app_layouts.iteritems():
            #print 'item:{0} button:{1}'.format(item, button)
            if item == button:
                #print ('item={0} naee={1} button={2}'.format(item,name,button))
                button_name = name
                pkg_and_mode = name.split('-')
                package = pkg_and_mode[0]
                app = package
                if 'app' in self.w_data[workgroup]['packages'][package]:
                    app = self.w_data[workgroup]['packages'][package]['app']
                if len(pkg_and_mode) > 1:
                    mode = pkg_and_mode[1]
                if version == '':
                    version = self.w_data[workgroup]['packages'][package]['version']

        #print 'UI Launching {0} version: {1}'.format(app,version)
        launcher.launch_app(app, version=version, mode=mode, wrkgrp_config='', workgroup=workgroup, initials=initials, project=project, filepath=filepath)

        text = str(self.app_layouts[button_name].text())
        self.app_layouts[button_name].setText("Starting...")
        test_timer = QTimer()
        test_timer.singleShot(4000, lambda: self.toggleLaunchStatus(self.app_layouts[button_name], text))

        self.addRecentProject(project)

        return

    def installApp(self):
        pass


    def toggleLaunching():
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

    def resetActiveData(self):
        self.active_data = {
            'file_share':'',
            'server':'',
            'share':'',
            'job':'',
            'stage':'production',
            'asset_type':'',
            'asset_grp':'',
            'asset':'',
            'task':'',
            'version':'',
            'filetype':'',
            'filename':'',
            'filepath':'',
        }
        # caches the active data's path for quick references
        self.active_path = dict(self.active_data)

    def initSettings(self):
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

    def addRecentProject(self, project):
        self.settings.setValue('prev_project4', self.settings.value('prev_project3'))
        self.settings.setValue('prev_project3', self.settings.value('prev_project2'))
        self.settings.setValue('prev_project2', self.settings.value('prev_project1'))
        self.settings.setValue('prev_project1', project)        

    def saveSettings(self):

        print ('Saving settings...')
        try:
            initials = str(self.ui['wdgt']['initials_le'].text())
            project = str(self.ui['wdgt']['project_combo'].currentText())
            display_grp = str(self.ui['wdgt']['dispgroup_combo'].currentText())


            self.settings.setValue('initials', initials)
            self.settings.setValue('role', display_grp)
        except:
            print "Unable to save settings"

    def readSettings(self):
        print ("loading user settings")
        try:
            initials = str(self.settings.value('initials',type=str))
            project = str(self.settings.value('prev_project1',type=str))
            display_grp = str(self.settings.value('role',type=str))
            self.setProjectCombo(project)
            self.ui['wdgt']['initials_le'].setText(initials)
            self.setDisplayGroup(display_grp)
        except:
            "initializing settings"
            self.initSettings()

        print ("checking active directory for initials")
        #try:
        initials = get_initials()
        self.ui['wdgt']['initials_le'].setText(initials)
       #except:
       #    print ("could not connect to active directory")
       #    pass

    def closeEvent(self, event):
        #print ('Running close event')
        self.saveSettings()




#if __name__ == '__main__':
#    app = QApplication(sys.argv)
#    wind = Launcher()
#    wind.setWindowTitle('Gentleman Scholar Launcher')
#    wind.show()
#    app.exec_()#