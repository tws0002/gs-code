"""
Mustache v0.40 by henry foster (henry@toadstorm.com), 3/07/2012
Requires:
    mustache_AM.py Mustache asset manager.
    mustache_SM.py Mustache scene manager.
    m_analyzeScene.py standalone reference analyzer for Mustache
    m_massAssetEdit.py standalone render layer editor for Mustache
    mustache_submit.py Mustache interface for Muster render client.
    natsort.py natural sorting algorithm.
    killEverything.py scene cleanup utility.
    hfFixShading.py component shading removal utility. (required by killEverything module)

Include the following lines in your userSetup.py:
import mustache
mustache.init()

To-do list:

-warn when mastering if meshes and their parents exist outside a VROP
-administrative mode to allow checkout override (in case some asshole checks out a file you're working on)
+submitter is having problems with mental ray scenes being named incorrectly, possibly only after submitting a previous render from the same scene
+this problem could be due to scenes with multiple render engines set via override. vray is being detected as the render engine instead of mr,
 which throws off a number of scripts querying vray as the current render engine if the current layer is not a mr layer.
-write new VROP matte generator that correctly sets multimatte element overrides, names elements and filename suffixes based on asset name
+add name search filter for asset list
-delete TEMP_SCREENSHOT panel after screenshot is done
-mustache returns 'could not save file' error when trying to version up or master if there are any references, loaded or unloaded, in the scene
+automatically release assets and shots upon exit
+FOR MAYA 2013: replaced imf_copy.exe with imconvert.exe

"""
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
import os
import re
import sys
import mustache_SM as SM
import mustache_AM as AM
import mustache_submit as MSUB
import mustache_DB as DB
M = 'mustache not initialized'

try:
    GSCODEBASE = os.environ['GSCODEBASE']
    print 'Using code repository: %s' %( GSCODEBASE )
except:
    GSCODEBASE = '//scholar/code'
GSTOOLS = os.path.join(GSCODEBASE,'base','apps')
GSBIN = os.path.join(GSCODEBASE,'bin')

def init(*args):
    global M
    M = Mustache()
    return M


class Mustache:

    def __init__(self):
        self.mayaDir = os.path.split(sys.executable)[0]+'\\'
        self.binDir = '%s/maya/bin/' %( GSTOOLS )
        self.scriptsDir = '%s/maya/scripts/mel/' %( GSTOOLS )
        self.projectsBase = '//scholar/projects/'
        self.assetsBase = 'scenes/01_cg_elements/01_models/'
        self.shotsBase = 'scenes/02_cg_scenes/'
        self.mayaProjectFolder = '/03_production/01_cg/01_MAYA/'
        self.assetsLib = '//scholar/assets/3D/MUSTACHEDB'
        self.assetsDatabase = '//scholar/assets/3D/MUSTACHEDB/mustache_assets_db.xml'
        self.assetsBlacklist = '//scholar/assets/3D/MUSTACHEDB/mustache_assets_blacklist.xml'
        self.animExportFolder = 'data/animExport'
        self.imagesDir = 'images/'
        self.defaultImage = os.path.join(self.scriptsDir, 'm_defaultImage.jpg')
        self.sceneTemplate = ''
        self.user = ''
        self.project = ''
        self.assetsDir = ''
        self.scenesDir = ''
        self.AM = AM.AssetManager()
        self.SM = SM.SceneManager()
        self.MSUB = MSUB.Submitter()
        self.DB = DB.MustacheDB()
        self.pushVars(self)
        cmds.scriptJob(e=['quitApplication', self.autoRelease])
        print '}MUSTACHE{ v0.41 initialized'

    def autoRelease(self, *args):
        if self.AM.checkedAsset != '':
            self.AM.releaseAsset(self.AM.checkedAsset)
        if self.SM.checkedShot != '':
            self.SM.releaseShot()

    def pushVars(self, *args):
        self.AM.M = self
        self.SM.M = self
        self.MSUB.M = self
        self.DB.M = self

    def debug(self):
        print 'mayaDir: %s' % self.mayaDir
        print 'projects base: %s' % self.projectsBase
        print 'user: %s' % self.user
        print 'project: %s' % self.project
        print 'assetsDir: %s' % self.assetsDir
        print 'scenesDir: %s' % self.scenesDir
        print 'isClean: %s' % self.AM.isClean
        print 'checkedAsset: %s' % self.AM.checkedAsset
        print 'selectedAsset: %s' % self.AM.selectedAsset
        print 'selectedFile: %s' % self.AM.selectedFile

    def setProjectUI(self, loadAM = False, loadSM = False, *args):
        projWindowName = 'mustacheProjectUI'
        if cmds.window(projWindowName, q=1, exists=1):
            cmds.deleteUI(projWindowName)
        projWindow = cmds.window(projWindowName, t='Select a project...')
        projForm = cmds.formLayout()
        projLister = cmds.textScrollList(ams=0, w=280, h=500)
        allProjects = sorted([ f for f in os.listdir(self.projectsBase) if os.path.isdir(os.path.join(self.projectsBase, f)) == True ], key=str.lower)
        for f in allProjects:
            cmds.textScrollList(projLister, e=1, a=f.split('/')[-1])

        projBtn = cmds.button(l='OK', w=280, h=75, c=lambda x: self.setProject(projLister, projWindow, loadAM, loadSM))
        cmds.formLayout(projForm, e=1, attachForm=[(projLister, 'top', 5),
         (projLister, 'left', 5),
         (projBtn, 'top', 510),
         (projBtn, 'left', 5)])
        cmds.showWindow(projWindow)
        cmds.window(projWindow, e=1, w=300, h=600)

    def setProject(self, projectList, projectWindow = '', loadAM = False, loadSM = False, *args):
        if cmds.file(q=1, mf=1) == 1:
            confirm = cmds.confirmDialog(title='Unsaved changes', message='You have unsaved changes in this scene. Do you want to save the current scene before continuing?', button=['yes', 'no'], defaultButton='yes', cancelButton='no', dismissString='no', icon='warning')
            if confirm == 'yes':
                try:
                    cmds.file(s=1, f=1)
                except:
                    pass

        if self.AM.checkedAsset != '':
            self.AM.releaseAsset(self.AM.checkedAsset)
        if self.SM.checkedShot != '':
            self.SM.releaseShot()
        self.projectName = cmds.textScrollList(projectList, q=1, si=1)[0]
        self.project = os.path.join(self.projectsBase, self.projectName + self.mayaProjectFolder)
        mel.eval('setProject "' + self.project + '"')
        self.assetsDir = self.project + self.assetsBase
        self.scenesDir = self.project + self.shotsBase
        self.sceneTemplate = os.path.join(self.project, 'scenes', 'TEMPLATE.mb')
        if projectWindow != '':
            cmds.deleteUI(projectWindow)
        print 'project set to: %s' % self.project
        if loadAM == True:
            self.AM.assetManagerUI()
        if loadSM == True:
            self.SM.sceneManagerUI()
        return self.project

    def setUserUI(self, setProj = False, loadAM = False, loadSM = False, *args):
        userWindowName = 'mustacheUserUI'
        if cmds.window(userWindowName, q=1, exists=1):
            cmds.deleteUI(userWindowName)
        userWindow = cmds.window(userWindowName, t='Welcome to }MUSTACHE{ DEVELOPER')
        userForm = cmds.formLayout()
        userEntry = cmds.textField(width=30)
        userLabel = cmds.text(l='Please enter your initials:')
        userBtn = cmds.button(l='OK', w=120, h=40, c=lambda x: self.setUser(userEntry, userWindow, setProj, loadAM, loadSM))
        cmds.formLayout(userForm, e=1, attachForm=[(userLabel, 'top', 20),
         (userLabel, 'left', 50),
         (userEntry, 'top', 18),
         (userEntry, 'left', 190),
         (userBtn, 'top', 50),
         (userBtn, 'left', 80)])
        cmds.showWindow(userWindow)
        cmds.window(userWindow, e=1, w=300, h=100)

    def setUser(self, userEntry, userWindow = '', setProj = False, loadAM = False, loadSM = False, *args):
        userRaw = cmds.textField(userEntry, q=1, text=1)
        err = 0
        if not userRaw.isalpha():
            cmds.error('Invalid username.')
        try:
            user = userRaw.upper().strip()[0:3]
            self.user = user
            print 'user set to: %s' % self.user
            if setProj == True:
                self.setProjectUI()
            if loadAM == True:
                self.AM.assetManagerUI()
            if loadSM == True:
                self.SM.sceneManagerUI()
        except:
            cmds.error('Invalid username.')
            err = 1

        if err == 0:
            execStr = 'import maya.cmds as cmds\ncmds.deleteUI(%s)' % userWindow
            cmds.deleteUI(userWindow)

    def quickSave(self, *args):
        filename = cmds.file(q=1, sn=1)
        if self.assetsBase in filename:
            self.AM.quickSave()
        elif self.shotsBase in filename:
            self.SM.quickSave()
        else:
            cmds.error("I have no idea what this scene is so I can't quicksave.")