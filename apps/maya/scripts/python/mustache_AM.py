import maya.cmds as cmds
import maya.standalone as stand
import maya.mel as mel
import os
import natSort
import pickle
import glob
import subprocess
import time, random
import re
import shutil
import killEverything as hfKE

class AssetManager:

    def __init__(self):
        self.selectedAsset = ''
        self.selectedFile = ''
        self.checkedAsset = ''
        self.M = ''
        self.isClean = False
        self.t = 1380585600
        print 'init assetManager'

    def getAssetPaths(self, asset, *args):
        masterFile = self.M.assetsDir + asset + '/' + asset + '.mb'
        versionsFolder = self.M.assetsDir + asset + '/_versions/'
        pipelineFolder = self.M.assetsDir + asset + '/_pipeline/'
        return (masterFile, versionsFolder, pipelineFolder)

    def createAssetUI(self, *args):
        windowName = 'createAssetUI'
        windowTitle = '}MUSTACHE{ - Create New Asset'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        textLabel = cmds.text(l='Enter the new asset name:')
        textEntry = cmds.textField(w=200)
        okBtn = cmds.button(l='OK', w=100, h=50, c=lambda x: self.createAsset(cmds.textField(textEntry, q=1, text=1), window))
        cancelBtn = cmds.button(l='Cancel', w=100, h=50, c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(textLabel, 'top', 10),
         (textLabel, 'left', 10),
         (textEntry, 'top', 8),
         (textEntry, 'left', 150),
         (okBtn, 'top', 45),
         (okBtn, 'left', 60),
         (cancelBtn, 'top', 45),
         (cancelBtn, 'left', 215)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=400, h=110)

    def createAsset(self, name, killUI = '', ext = '.mb', saveFile = True, *args):
        if cmds.file(q=1, mf=1) == 1:
            confirm = cmds.confirmDialog(title='Unsaved changes', message='Your scene has been modified. Save this scene first?', icon='warning', button=['save', 'continue without saving', 'cancel'], defaultButton='cancel', cancelButton='cancel', dismissString='cancel')
            if confirm == 'cancel':
                return
            if confirm == 'save':
                try:
                    cmds.file(s=1, f=1, type='mayaBinary')
                except RuntimeError:
                    pass

        owner = self.M.user
        name.strip()
        newfile = ''
        print 'validating asset name: %s' % name
        rePattern = '^[a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9_]$'
        search = re.findall(rePattern, name)
        if len(search) == 0:
            cmds.error('Invalid asset name: %s' % name)
            return False
        if 'CACHE' in name:
            cmds.error('Invalid asset name: %s.' % name)
            return False
        if not os.path.exists(self.M.assetsDir + name):
            os.mkdir(self.M.assetsDir + name)
            os.mkdir(self.M.assetsDir + name + '/_pipeline')
            os.mkdir(self.M.assetsDir + name + '/_scrap')
            os.mkdir(self.M.assetsDir + name + '/_versions')
        else:
            confirm = cmds.confirmDialog(title='asset directory already exists', message="It looks like there's already a directory for this asset. Are you sure you want to continue?", icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return
            try:
                os.mkdir(self.M.assetsDir + name + '/_pipeline')
            except WindowsError:
                print 'Path already exists: %s' % (self.M.assetsDir + name + '/_pipeline')

            try:
                os.mkdir(self.M.assetsDir + name + '/_scrap')
            except WindowsError:
                print 'Path already exists: %s' % (self.M.assetsDir + name + '/_scrap')

            try:
                os.mkdir(self.M.assetsDir + name + '/_versions')
            except WindowsError:
                print 'Path already exists: %s' % (self.M.assetsDir + name + '/_versions')

        template = self.M.sceneTemplate
        if not os.path.exists(template):
            cmds.warning("Couldn't find template file: " + template)
            cmds.file(new=1, force=1)
        else:
            cmds.file(template, o=1, force=1)
        try:
            groups = []
            groups.append(cmds.group(em=1, n='GEOgrp'))
            groups.append(cmds.group(em=1, n='RIGgrp'))
            groups.append(cmds.group(em=1, n='GUTSgrp'))
            cmds.select(['GEOgrp', 'RIGgrp', 'GUTSgrp'], add=1)
            groups.append(cmds.group(n=name + '_GRP'))
            axes = ['x', 'y', 'z']
            chans = ['t', 'r', 's']
            for a in axes:
                for b in chans:
                    for group in groups:
                        cmds.setAttr(group + '.' + b + a, lock=1)

            for g in groups:
                cmds.lockNode(group, lock=True)

        except:
            cmds.warning("Couldn't create default DAG groups for asset.")

        cacheset = cmds.sets(n='CACHEset', em=1)
        rigset = cmds.sets(n='RIGset', em=1)
        cmds.lockNode(cacheset, lock=1)
        cmds.lockNode(rigset, lock=1)
        if saveFile == True:
            cmds.file(rename=self.M.assetsDir + name + '/_versions/' + name + '_v000_' + owner + ext)
            if ext == '.mb':
                newfile = cmds.file(save=1, type='mayaBinary')
            else:
                newfile = cmds.file(save=1, type='mayaAscii')
            self.checkOutAsset(name)
        if killUI != '':
            cmds.deleteUI(killUI)
        self.assetManagerUI()
        return newfile

    def checkOutAsset(self, asset, *args):
        user = self.M.user
        master, versions, pipeline = self.getAssetPaths(asset)
        if self.checkedAsset != '':
            self.releaseAsset(self.checkedAsset)
        checkFile = open(pipeline + 'checkout.txt', 'w')
        pickle.dump(user, checkFile)
        checkFile.close()
        self.checkedAsset = asset
        print 'checking out asset: %s' % self.checkedAsset

    def releaseAsset(self, asset, warning = False, *args):
        if self.checkedAsset == '':
            cmds.warning('No asset is checked out?')
        if warning == True:
            prompt = cmds.confirmDialog(title='Release asset?', message='Releasing this asset will unload the scene. Are you sure you want to do this?', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if prompt == 'no':
                return
        master, versions, pipeline = self.getAssetPaths(asset)
        checkFile = open(pipeline + 'checkout.txt', 'w')
        pickle.dump('', checkFile)
        checkFile.close()
        self.checkedAsset = ''
        if warning == True:
            cmds.file(new=1, force=1)
        print 'releasing asset: %s' % asset

    def isChecked(self, asset, *args):
        master, versions, pipeline = self.getAssetPaths(asset)
        if os.path.exists(os.path.join(pipeline, 'checkout.txt')):
            checkFile = open(pipeline + 'checkout.txt', 'r')
            initials = pickle.load(checkFile)
            checkFile.close()
            if initials == '':
                return False
            else:
                return initials
        else:
            warnString = 'no checkout file found for asset %s!' % asset
            cmds.warning(warnString)
            return False

    def editAsset(self, filename, *args):
        if cmds.file(q=1, mf=1) == 1:
            confirm = cmds.confirmDialog(title='Unsaved changes', message='Your scene has been modified. Save this scene first?', icon='warning', button=['save', 'continue without saving', 'cancel'], defaultButton='cancel', cancelButton='cancel', dismissString='cancel')
            if confirm == 'cancel':
                return
            if confirm == 'save':
                try:
                    cmds.file(s=1, f=1, type='mayaBinary')
                except RuntimeError:
                    pass

        user = self.M.user
        if not os.path.exists(filename):
            cmds.error('Please select a file to edit!')
        fileSplit = os.path.basename(filename).split('_')
        asset = '_'.join(fileSplit[0:-2])
        if self.isChecked(asset) != user and self.isChecked(asset) != False:
            confirm = cmds.confirmDialog(title='asset is already checked out!', message='This asset is already checked out by ' + self.isChecked(asset) + '. edit anyways?', icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return
        if self.checkedAsset != asset and self.checkedAsset != '':
            confirm = cmds.confirmDialog(title='you already have an asset checked out!', message='You already have the asset ' + self.checkedAsset + ' checked out. You will need to release it to continue. Okay?', icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return
        self.checkOutAsset(asset)
        self.isClean = False
        cmds.file(filename, open=1, force=1)
        cmds.file(filename, rts=1)
        hfKE.initLockdown(0)

    def quickSave(self, *args):
        self.updateAssetUI(1)

    def updateAsset(self, asset, notes, ext = '.mb', release = False, updateUI = '', quickSave = 0, *args):
        user = self.M.user
        master, versions, pipeline = self.getAssetPaths(asset)
        if self.isChecked(asset) != user:
            cmds.error('Update asset denied: Asset %s is not checked out by current user %s.' % (asset, user))
        topVersion = 0
        try:
            okExtensions = ['.mb', '.ma']
            files = [ f for f in os.listdir(versions) if os.path.splitext(f)[-1] in okExtensions ]
            for f in files:
                try:
                    ver = int(f.split('_')[-2][1:])
                    if ver > topVersion:
                        topVersion = ver
                except IndexError as ValueError:
                    pass

            topVersion += 1
        except IndexError:
            print "can't find v000, cloned asset...?"

        newCam = cmds.camera()
        cmds.setAttr(newCam[0] + '.rotateX', -35)
        cmds.setAttr(newCam[0] + '.rotateY', 45)
        cmds.viewFit(newCam[0], all=1)
        cmds.viewClipPlane(newCam[0], acp=1)
        modelEditor = cmds.playblast(activeEditor=1)
        modelPanel = cmds.modelEditor(modelEditor, q=1, pnl=1)
        cmds.modelPanel(modelPanel, e=1, cam=newCam[0])
        cmds.modelEditor(modelEditor, e=1, da='smoothShaded')
        screenPath = pipeline + asset + '_v' + str(topVersion).zfill(3) + '_' + user + '.iff'
        cmds.playblast(st=1, et=1, w=640, h=400, fmt='image', cf=screenPath)
        cmds.modelEditor(modelEditor, e=1, displayTextures=0)
        cmds.delete(newCam[0])
        cmds.editRenderLayerGlobals(crl='defaultRenderLayer')
        print 'attempting to save new version number: %s' % str(topVersion)
        newFilename = versions + asset + '_v' + str(topVersion).zfill(3) + '_' + user + ext
        newFile = cmds.file(rename=newFilename)
        saveFile = ''
        if ext == '.mb':
            saveFile = cmds.file(save=1, type='mayaBinary')
        else:
            saveFile = cmds.file(save=1, type='mayaAscii')
        print (self.M.binDir + 'imf_copy.exe ' + screenPath + ' ' + screenPath[:-4] + '.jpg')
        convertProc = subprocess.Popen(self.M.binDir + 'imf_copy.exe ' + screenPath + ' ' + screenPath[:-4] + '.jpg', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = convertProc.communicate()
        os.remove(screenPath)
        notesFile = open(pipeline + asset + '_v' + str(topVersion).zfill(3) + '_' + user + '.txt', 'w')
        pickle.dump(notes, notesFile)
        notesFile.close()
        evalString = 'Asset updated! New filename: %s' % saveFile
        if release == True:
            self.releaseAsset(asset)
            cmds.file(new=1, force=1)
        if updateUI != '':
            cmds.deleteUI(updateUI)
        self.isClean = False
        if quickSave == 0:
            self.buildVersionList(self.editAssetMultiList, self.editVersionMultiList)
        mel.eval('print \n"' + evalString + '"')

    def updateAssetUI(self, quickSave = 0, *args):
        user = self.M.user
        asset = self.checkedAsset
        if asset == '':
            cmds.error('No asset is currently checked out. Aborting.')
        master, versions, pipeline = self.getAssetPaths(asset)
        if self.isChecked(asset) != user:
            cmds.error('Update asset denied: Asset %s is not checked out by current user %s.' % (asset, user))
        windowName = 'updateAssetWindow'
        windowTitle = '}MUSTACHE{ - Update Asset'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        assetLabelString = 'UPDATING ASSET %s' % asset
        assetLabel = cmds.text(l=assetLabelString, fn='boldLabelFont')
        notesLabel = cmds.text(l="Anything you'd like to say about this version?")
        notesEntry = cmds.scrollField(w=400, h=150, ww=1)
        releaseCheck = cmds.checkBox(l='Release asset after update', v=0)
        okBtn = cmds.button(w=100, h=50, l='OK', c=lambda x: self.updateAsset(asset, cmds.scrollField(notesEntry, q=1, text=1), '.mb', cmds.checkBox(releaseCheck, q=1, v=1), window, quickSave))
        cancelBtn = cmds.button(w=100, h=50, l='Cancel', c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(assetLabel, 'top', 10),
         (assetLabel, 'left', 10),
         (notesLabel, 'left', 10),
         (notesLabel, 'top', 40),
         (notesEntry, 'left', 10),
         (notesEntry, 'top', 60),
         (okBtn, 'left', 10),
         (okBtn, 'top', 240),
         (cancelBtn, 'left', 130),
         (cancelBtn, 'top', 240),
         (releaseCheck, 'top', 215),
         (releaseCheck, 'left', 10)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=450, h=300)

    def masterAsset(self, asset):
        user = self.M.user
        if asset == '':
            cmds.error('No asset is checked out to master!')
        if self.isClean == False:
            hfKE.KillEverythingUI(self, asset)
            self.isClean = True
            cmds.warning('Please run the asset cleanup utility and then master the asset.')
            return
        layers = cmds.ls(type='renderLayer')
        for layer in layers:
            cmds.setAttr(layer + '.renderable', 0)

        master, versions, pipeline = self.getAssetPaths(asset)
        if self.isChecked(asset) != user:
            cmds.error('Master asset denied: Asset %s is not checked out by current user %s.' % (asset, user))
        confirm = cmds.confirmDialog(title='}MUSTACHE{ - Master Asset', message='Are you sure you want to overwrite the master file for %s?' % asset, button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
        if confirm == 'no':
            return
        cmds.editRenderLayerGlobals(crl='defaultRenderLayer')
        confirm = cmds.confirmDialog(title='}MUSTACHE{ - Master Asset', message='Save a new version of this file before mastering?', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
        if confirm == 'no':
            pass
        else:
            self.updateAsset(asset, 'Autosaved before mastering')
        oldFileName = cmds.file(q=1, sn=1)
        cmds.file(rename=master)
        cmds.file(save=1, force=1)
        if self.detectCacheSet() == True:
            confirm = cmds.confirmDialog(title='Write CACHE asset?', message='It looks like this asset has objects in the CACHEset. Do you want to write out a cacheable master?', icon='question', button=['yes', 'no'], defaultButton='yes', cancelButton='no', dismissString='no')
            if confirm == 'yes':
                cacheMaster = os.path.splitext(master)[0] + '_CACHE' + '.mb'
                self.prepCacheAsset()
                cmds.file(rename=cacheMaster)
                cmds.file(save=1, force=1)
                print 'CACHE master asset updated for asset %s! %s' % (asset, cacheMaster)
                cmds.file(oldFileName, open=1, force=1)
        cmds.file(rename=oldFileName)
        evalString = 'Master asset updated for asset %s! %s' % (asset, master)
        mel.eval('print \n"' + evalString + '"')

    def cloneAsset(self, asset, sourceFile, ext = '.mb', window = ''):
        user = self.M.user
        if self.checkedAsset != '':
            confirm = cmds.confirmDialog(title='you already have an asset checked out!', message='You already have the asset ' + self.checkedAsset + ' checked out. You will need to release it to continue. Okay?', icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return False
        confirm = cmds.confirmDialog(title='clone this asset?', message='Your current file will be unloaded. Do you want to clone this asset?', icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
        if confirm == 'no':
            return False
        if self.createAsset(asset, '', '.mb', False) == False:
            return
        cmds.file(sourceFile, open=1, force=1)
        oldFileName = os.path.splitext(os.path.basename(sourceFile))[0]
        oldAssetName = '_'.join(oldFileName.split('_')[0:-2])
        cmds.select(cl=1)
        cmds.pickWalk('GEOgrp', direction='up')
        mainGroup = cmds.ls(sl=1)
        cmds.lockNode(mainGroup, lock=0)
        newname = cmds.rename(mainGroup, asset + '_GRP')
        cmds.lockNode(newname, lock=1)
        self.checkOutAsset(asset)
        if window != '':
            cmds.deleteUI(window)
        self.updateAsset(asset, 'cloned from: ' + sourceFile)
        self.assetManagerUI()

    def cloneAssetUI(self, *args):
        if self.selectedFile == '':
            cmds.error('Please select a file to clone!')
        windowName = 'cloneAssetUI'
        windowTitle = '}MUSTACHE{ - Clone Asset'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        oldAssetLabel = cmds.text(l='Cloning new asset from file:\n' + self.selectedFile, align='left')
        textLabel = cmds.text(l='Enter the new asset name:')
        textEntry = cmds.textField(w=200)
        okBtn = cmds.button(l='OK', w=100, h=50, c=lambda x: self.cloneAsset(cmds.textField(textEntry, q=1, text=1), self.selectedFile, '.mb', window))
        cancelBtn = cmds.button(l='Cancel', w=100, h=50, c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(textLabel, 'top', 60),
         (textLabel, 'left', 10),
         (textEntry, 'top', 58),
         (textEntry, 'left', 150),
         (okBtn, 'top', 95),
         (okBtn, 'left', 60),
         (cancelBtn, 'top', 95),
         (cancelBtn, 'left', 215),
         (oldAssetLabel, 'top', 10),
         (oldAssetLabel, 'left', 10)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=700, h=160)

    def buildAssetList(self, assetControl, filterName = '', filterBtn = '', *args):
        assetList = [ f for f in os.listdir(self.M.assetsDir) if os.path.isdir(os.path.join(self.M.assetsDir, f)) and f != '_TRASH' and os.path.exists(os.path.join(self.M.assetsDir, f, '_pipeline')) ]
        if filterBtn != '' and cmds.symbolButton(filterBtn, q=1, i=1) == 'filtersOn.png':
            cmds.symbolButton(filterBtn, e=1, i='filtersOff.png')
            filterName = ''
        if filterName != '':
            assetList = [ f for f in assetList if filterName in f ]
            cmds.symbolButton(filterBtn, e=1, i='filtersOn.png')
        elif filterBtn != '':
            cmds.symbolButton(filterBtn, e=1, i='filtersOff.png')
        sortedList = natSort.natsorted(assetList)
        cmds.textScrollList(assetControl, e=1, ra=1)
        self.selectedAsset = ''
        for asset in sortedList:
            cmds.textScrollList(assetControl, e=1, a=asset)

    def buildVersionList(self, assetControl, versionControl, checkout = '', screenshot = '', *args):
        try:
            asset = cmds.textScrollList(assetControl, q=1, si=1)[0]
        except TypeError:
            return

        self.selectedAsset = asset
        master, versions, pipeline = self.getAssetPaths(asset)
        versionsList = glob.glob(versions + '*.m?')
        shortList = sorted([ os.path.basename(f) for f in versionsList ])
        cmds.textScrollList(versionControl, e=1, ra=1)
        for f in shortList:
            cmds.textScrollList(versionControl, e=1, a=f)

        self.selectedFile = ''
        if checkout != '':
            if self.isChecked(asset):
                cmds.text(checkout, e=1, l='*** CHECKED OUT BY ' + self.isChecked(asset) + ' ***')
            else:
                cmds.text(checkout, e=1, l='')
            topVersionFile = ''
            topVersionIndex = 0
            pipeList = [ f for f in os.listdir(pipeline) if os.path.splitext(f)[-1] == '.jpg' ]
            for f in pipeList:
                try:
                    version = f.split('_')[-2].strip('v')
                    if int(version) > topVersionIndex:
                        topVersionIndex = int(version)
                        topVersionFile = f
                except TypeError as IndexError:
                    pass

        if screenshot != '':
            screenPath = os.path.join(pipeline, topVersionFile)
            if os.path.exists(screenPath):
                cmds.image(screenshot, e=1, vis=1, image=screenPath)
            else:
                cmds.image(screenshot, e=1, vis=0)

    def getAssetInfo(self, versionControl, screenshot, timestamp, checkout, notes, *args):
        filename = cmds.textScrollList(versionControl, q=1, si=1)[0]
        asset = self.selectedAsset
        master, versions, pipeline = self.getAssetPaths(asset)
        self.selectedFile = versions + filename
        screenPath = pipeline + os.path.splitext(os.path.basename(self.selectedFile))[0] + '.jpg'
        if os.path.exists(screenPath):
            cmds.image(screenshot, e=1, vis=1, image=screenPath)
        else:
            cmds.image(screenshot, e=1, vis=1, image=self.M.defaultImage)
            print 'Screenshot not found: %s' % screenPath
        initials = self.selectedFile.split('_')[-1].split('.')[0]
        seconds = os.path.getmtime(self.selectedFile)
        lastMod = time.strftime('%Y-%m-%d %H:%M', time.localtime(seconds))
        timestampString = 'Last modified: %s by %s' % (lastMod, initials)
        cmds.text(timestamp, e=1, l=timestampString)
        labelString = ''
        if self.isChecked(asset):
            labelString = '*** CHECKED OUT BY %s ***' % self.isChecked(asset)
        cmds.text(checkout, e=1, l=labelString)
        notesPath = pipeline + os.path.splitext(os.path.basename(self.selectedFile))[0] + '.txt'
        if os.path.exists(notesPath):
            notesLoad = open(notesPath, 'r')
            notesText = pickle.load(notesLoad)
            cmds.scrollField(notes, e=1, tx='Version notes: \n%s' % notesText)
        else:
            print 'Notes not found: %s' % notesPath
            cmds.scrollField(notes, e=1, tx='No version notes found')

    def assetManagerUI(self, *args):
        user = self.M.user
        if user == '':
            cmds.error('No user detected. Restart Mustache.')
        editName = 'editAssetUI'
        editTitle = '}MUSTACHE{ - ASSET MANAGER'
        if cmds.window(editName, q=1, exists=1):
            cmds.deleteUI(editName)
        editWindow = cmds.window(editName, title=editTitle)
        masterLayout = cmds.formLayout()
        editProjectEntry = cmds.textField(tx=self.M.project, w=340, en=0, ann='Shows your current project. Press "Change Project" to select a new one.')
        editProjectChange = cmds.button(l='Change project...', w=110, h=25, c=lambda x: self.M.setProjectUI(True))
        editUserChange = cmds.button(l='Change user...', w=110, h=25, c=lambda x: self.M.setUserUI(False, True))
        editUserEntry = cmds.textField(tx=self.M.user, w=35, en=0, ann='Shows the current user.')
        cmds.formLayout(masterLayout, e=1, attachForm=[(editUserChange, 'top', 5),
         (editUserChange, 'left', 485),
         (editUserEntry, 'left', 600),
         (editUserEntry, 'top', 8),
         (editProjectEntry, 'top', 8),
         (editProjectEntry, 'left', 120),
         (editProjectChange, 'top', 5),
         (editProjectChange, 'left', 5)])
        tabLayout = cmds.tabLayout()
        cmds.formLayout(masterLayout, e=1, attachForm=[(tabLayout, 'top', 40), (tabLayout, 'left', 5)])
        editLayout = cmds.formLayout(parent=tabLayout)
        editAssetLabel = cmds.text(l='ASSETS')
        editVersionLabel = cmds.text(l='VERSIONS')
        editCheckoutAlert = cmds.text(l='', fn='boldLabelFont')
        self.editAssetMultiList = cmds.textScrollList(w=180, h=500, ams=0, fn='boldLabelFont', sc=lambda *x: self.buildVersionList(self.editAssetMultiList, self.editVersionMultiList, editCheckoutAlert, editScreenShot), ann='Shows all assets in your project. Select one to view versions, rename or delete.')
        assetFilterCtrl = cmds.textField(w=150, h=24, aie=1, ec=lambda *x: self.buildAssetList(self.editAssetMultiList, cmds.textField(assetFilterCtrl, q=1, tx=1), assetFilterBtn))
        assetFilterBtn = cmds.symbolButton(i='filtersOff.png', w=24, h=24, c=lambda *x: self.buildAssetList(self.editAssetMultiList, cmds.textField(assetFilterCtrl, q=1, tx=1), assetFilterBtn))
        self.editVersionMultiList = cmds.textScrollList(w=180, h=500, ams=0, sc=lambda *x: self.getAssetInfo(self.editVersionMultiList, editScreenShot, editTimestamp, editCheckoutAlert, editNotes), ann='Shows all versions of the selected asset. Select one to edit or clone.')
        editScreenShot = cmds.image(w=320, h=200, ann='Screen capture of the selected asset.')
        editTimestamp = cmds.text(l='Last modified: ', ann='Shows when the selected file was last modified.')
        editNotes = cmds.scrollField(w=320, h=250, tx='Version notes: ', ww=1, ann='Version notes for the selected file.')
        editNewBtn = cmds.button(l='New', w=100, h=80, c=self.createAssetUI, ann='Create a new asset from scratch.')
        editEditBtn = cmds.button(l='Edit', w=100, h=80, bgc=[0.7, 1.0, 0.6], c=lambda x: self.editAsset(self.selectedFile), ann='Edit the selected asset version.')
        editCloneBtn = cmds.button(l='Clone selected', w=100, h=35, c=self.cloneAssetUI, ann='Create a new asset out of the currently selected asset version.')
        editMergeBtn = cmds.button(l='Merge selected', w=100, h=35, c=lambda *x: self.mergeAssets(self.selectedFile), ann='Import the selected asset into the currently open asset.')
        editUpdateBtn = cmds.button(l='Version up', w=100, h=80, bgc=[0.6, 0.7, 1.0], c=self.updateAssetUI, ann='Save a new version of the open file.')
        editMasterBtn = cmds.button(l='Clean /\nMaster', w=100, h=80, c=lambda x: self.masterAsset(self.checkedAsset), ann='Save the open file as the master version for the asset.')
        editCheckInBtn = cmds.button(l='Release', w=100, h=80, c=lambda x: self.releaseAsset(self.checkedAsset, True), ann='Release the asset you currently have checked out.')
        editRenameBtn = cmds.button(l='Rename', w=100, h=80, c=lambda *x: self.renameAsset(self.editAssetMultiList, self.editVersionMultiList), ann='Rename the selected asset. WARNING: This could potentially break existing references to the asset.')
        editDeleteBtn = cmds.button(l='Delete', w=100, h=80, bgc=[1.0, 0.6, 0.7], c=lambda *x: self.deleteAsset(self.editAssetMultiList, self.editVersionMultiList), ann='Delete the selected asset.')
        cmds.formLayout(editLayout, e=1, attachForm=[(self.editAssetMultiList, 'top', 50),
         (self.editAssetMultiList, 'left', 5),
         (self.editVersionMultiList, 'left', 220),
         (self.editVersionMultiList, 'top', 50),
         (editScreenShot, 'top', 50),
         (editScreenShot, 'left', 430),
         (editTimestamp, 'top', 260),
         (editTimestamp, 'left', 430),
         (editNotes, 'top', 300),
         (editNotes, 'left', 430),
         (editAssetLabel, 'top', 35),
         (editAssetLabel, 'left', 5),
         (editVersionLabel, 'top', 35),
         (editVersionLabel, 'left', 220),
         (editUpdateBtn, 'top', 560),
         (editUpdateBtn, 'left', 5),
         (editEditBtn, 'top', 560),
         (editEditBtn, 'left', 115),
         (editCloneBtn, 'top', 560),
         (editCloneBtn, 'left', 225),
         (editNewBtn, 'top', 560),
         (editNewBtn, 'left', 335),
         (editCheckInBtn, 'top', 560),
         (editCheckInBtn, 'left', 445),
         (editMasterBtn, 'top', 560),
         (editMasterBtn, 'left', 555),
         (editCheckoutAlert, 'top', 280),
         (editCheckoutAlert, 'left', 430),
         (editRenameBtn, 'top', 560),
         (editRenameBtn, 'left', 665),
         (editDeleteBtn, 'top', 560),
         (editDeleteBtn, 'left', 775),
         (assetFilterBtn, 'top', 5),
         (assetFilterBtn, 'left', 5),
         (assetFilterCtrl, 'top', 5),
         (assetFilterCtrl, 'left', 37),
         (editMergeBtn, 'top', 603),
         (editMergeBtn, 'left', 225)])
        self.buildAssetList(self.editAssetMultiList)
        self.selectedAsset = ''
        self.selectedFile = ''
        massEditLayout = cmds.formLayout(parent=tabLayout)
        assetListLabel = cmds.text(fn='boldLabelFont', l='ASSET LIST')
        assetListCtrl = cmds.textScrollList(w=180, h=500, ams=1, fn='boldLabelFont', ann='Choose one or more assets to apply edits to.')
        layerNameLabel = cmds.text(fn='boldLabelFont', l='LAYER ADD/EDIT')
        materialLabel = cmds.text(fn='boldLabelFont', l='MATERIAL OVERRIDE')
        overrideLabel = cmds.text(fn='boldLabelFont', l='SHAPE OVERRIDES')
        self.buildAssetList(assetListCtrl)
        layerSets = []
        for i in range(0, 8):
            row = cmds.rowLayout(parent=massEditLayout, nc=7, cw=[(1, 160),
             (2, 210),
             (3, 40),
             (4, 40),
             (5, 40),
             (6, 40),
             (7, 40)])
            layerNameCtrl = cmds.textField(w=150, ann='Render layer to add or edit')
            materialCtrl = cmds.textField(w=200, ann='Material to apply to layer')
            csCtrl = cmds.checkBox(v=1, l='CS', ann='Casts shadows')
            rsCtrl = cmds.checkBox(v=1, l='RS', ann='Receives shadows')
            pvCtrl = cmds.checkBox(v=1, l='PV', ann='Primary visibility')
            rflCtrl = cmds.checkBox(v=1, l='RFL', ann='Visible in reflections')
            rfrCtrl = cmds.checkBox(v=1, l='RFR', ann='Visible in refractions')
            layerSets.append((layerNameCtrl,
             materialCtrl,
             csCtrl,
             rsCtrl,
             pvCtrl,
             rflCtrl,
             rfrCtrl))
            cmds.formLayout(massEditLayout, e=1, attachForm=[(row, 'top', i * 30 + 20), (row, 'left', 200)])

        goBtn = cmds.button(parent=massEditLayout, w=150, h=75, bgc=[0.6, 0.7, 1.0], c=lambda *x: self.massAssetEditCallback(assetListCtrl, layerSets, cmds.checkBox(masterCheck, q=1, v=1), melCtrl, pythonCtrl, cmds.checkBox(overridesCheck, q=1, v=1)), l='Edit selected', ann='Add/edit render layers, materials and overrides to all selected assets. This could take a while.')
        masterCheck = cmds.checkBox(parent=massEditLayout, v=0, l='Master edited assets', ann='Save edited assets as master versions.')
        overridesCheck = cmds.checkBox(parent=massEditLayout, v=0, l='Apply shape overrides', ann='Enable changes to shape overrides for render layers (e.g. Primary Visibility)')
        setOwnerLabel = cmds.text(l='Set asset owner:', parent=massEditLayout)
        setOwnerCtrl = cmds.textField(w=50, h=25, parent=massEditLayout)
        setOwnerBtn = cmds.button(l='Apply', w=75, h=25, parent=massEditLayout, c=lambda *x: self.massEditAssetOwner(cmds.textScrollList(assetListCtrl, q=1, si=1), cmds.textField(setOwnerCtrl, q=1, tx=1)))
        scriptLabel = cmds.text(parent=massEditLayout, fn='boldLabelFont', l='RUN SCRIPT')
        scriptForm = cmds.tabLayout(parent=massEditLayout, ann='Run MEL or Python script on all selected assets.')
        melForm = cmds.formLayout(parent=scriptForm)
        melCtrl = cmds.scrollField(w=650, h=200, fn='smallFixedWidthFont')
        pythonForm = cmds.formLayout(parent=scriptForm)
        pythonCtrl = cmds.scrollField(w=650, h=200, fn='smallFixedWidthFont')
        cmds.tabLayout(scriptForm, e=1, tabLabel=[(melForm, 'MEL'), (pythonForm, 'Python')])
        cmds.formLayout(massEditLayout, e=1, attachForm=[(assetListLabel, 'top', 5),
         (assetListLabel, 'left', 5),
         (assetListCtrl, 'top', 20),
         (assetListCtrl, 'left', 5),
         (layerNameLabel, 'top', 5),
         (layerNameLabel, 'left', 200),
         (materialLabel, 'top', 5),
         (materialLabel, 'left', 363),
         (overrideLabel, 'top', 5),
         (overrideLabel, 'left', 573),
         (scriptForm, 'top', 300),
         (scriptForm, 'left', 200),
         (scriptLabel, 'top', 285),
         (scriptLabel, 'left', 200),
         (goBtn, 'top', 540),
         (goBtn, 'left', 700),
         (masterCheck, 'top', 620),
         (masterCheck, 'left', 700),
         (overridesCheck, 'top', 285),
         (overridesCheck, 'left', 573),
         (setOwnerLabel, 'top', 540),
         (setOwnerLabel, 'left', 200),
         (setOwnerCtrl, 'top', 540),
         (setOwnerCtrl, 'left', 300),
         (setOwnerBtn, 'top', 540),
         (setOwnerBtn, 'left', 355)])
        cmds.tabLayout(tabLayout, e=1, tabLabel=[(editLayout, 'ASSET BROWSER'), (massEditLayout, 'MASS ASSET EDITOR')])
        cmds.showWindow(editWindow)
        cmds.window(editWindow, e=1, w=900, h=680)

    def massEditAssetOwner(self, assets, owner, *args):
        if not assets:
            cmds.error('Select at least one asset to modify the owner.')
            return False
        if owner != '' and owner.isalpha() == False:
            cmds.error('Invalid username.')
            return False
        user = owner.upper().strip()[0:3]
        for asset in assets:
            master, versions, pipeline = self.getAssetPaths(asset)
            if os.path.exists(os.path.join(pipeline, 'checkout.txt')):
                checkFile = open(pipeline + 'checkout.txt', 'w')
                initials = pickle.dump(user, checkFile)
                checkFile.close()

        returnStr = 'Set owner of assets %s to user %s.' % (','.join(assets), user)
        cmds.warning(returnStr)

    def renameAsset(self, assetListCtrl, versionListCtrl, *args):
        asset = cmds.textScrollList(assetListCtrl, q=1, si=1)[0]
        chk = self.isChecked(asset)
        if chk:
            cmds.error("Can't rename asset: currently checked out by user " + chk)
            return False
        confirm = cmds.confirmDialog(title='Really rename asset?', ma='left', message='Renaming an asset could potentially break references throughout the entire project, and generally cause all kinds of terrible problems. It will also seriously piss off anyone working on that asset right now. Do you really want to do this?', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no', icon='critical')
        if confirm == 'no':
            return
        prompt = cmds.promptDialog(t='Enter a new asset name...', ma='left', message='Enter a new name for ' + asset, button=['ok', 'cancel'], defaultButton='cancel', cancelButton='cancel', dismissString='cancel')
        if prompt == 'cancel':
            return
        name = cmds.promptDialog(q=1, tx=1)
        print 'validating asset name: %s' % name
        rePattern = '^[a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9_]$'
        search = re.findall(rePattern, name)
        if len(search) == 0:
            cmds.error('Invalid asset name: %s' % name)
            return False
        if os.path.exists(os.path.join(self.M.assetsDir, name)):
            cmds.error('There is already another asset by that name. Aborting.')
        assetPath = os.path.join(self.M.assetsDir, asset)
        for root, dirs, files in os.walk(assetPath):
            for file in files:
                newFilename = file.replace(asset, name)
                oldFilePath = os.path.join(root, file)
                newFilePath = os.path.join(root, newFilename)
                os.rename(oldFilePath, newFilePath)

        newAssetPath = assetPath.replace(asset, name)
        os.rename(assetPath, newAssetPath)
        self.buildAssetList(assetListCtrl)
        self.buildVersionList(assetListCtrl, versionListCtrl)
        cmds.warning('Renamed asset ' + asset + ' to ' + name)

    def deleteAsset(self, assetList, versionList, *args):
        asset = cmds.textScrollList(assetList, q=1, si=1)[0]
        confirm = cmds.confirmDialog(t='DELETE asset?', ma='left', icon='critical', message='Deleting this asset will break all existing references to it. You can restore a deleted asset by moving it outside the "_TRASH" subfolder of your assets directory. Do you really want to delete ' + asset + '?', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
        if confirm == 'no':
            return
        if self.isChecked(asset) == self.M.user:
            self.releaseAsset(asset)
        master, versions, pipeline = self.getAssetPaths(asset)
        files = os.listdir(versions)
        if cmds.file(q=1, sn=1, shn=1) in files:
            cmds.file(new=1, f=1)
        if not os.path.exists(os.path.join(self.M.assetsDir, '_TRASH')):
            os.mkdir(os.path.join(self.M.assetsDir, '_TRASH'))
        if os.path.exists(os.path.join(self.M.assetsDir, '_TRASH', asset)):
            shutil.rmtree(os.path.join(self.M.assetsDir, '_TRASH', asset))
        shutil.move(os.path.join(self.M.assetsDir, asset), os.path.join(self.M.assetsDir, '_TRASH', asset))
        self.buildAssetList(assetList)
        self.buildVersionList(assetList, versionList)
        cmds.warning('DELETED asset ' + asset + '!')

    def massAssetEditCallback(self, assetListCtrl, overridesList, masterFlag, melScriptCtrl, pyScriptCtrl, doOverrides, *args):
        assetList = cmds.textScrollList(assetListCtrl, q=1, si=1)
        try:
            a = len(assetList)
        except TypeError:
            cmds.error('Please select one or more assets to edit!')

        layers = []
        materials = []
        overrides = []
        melScript = pickle.dumps(cmds.scrollField(melScriptCtrl, q=1, tx=1))
        pyScript = pickle.dumps(cmds.scrollField(pyScriptCtrl, q=1, tx=1))
        for layer, material, cs, rs, pv, rfl, rfr in overridesList:
            if cmds.textField(layer, q=1, tx=1) != '':
                layers.append(cmds.textField(layer, q=1, tx=1))
                materials.append(cmds.textField(material, q=1, tx=1))
                overrides.append((cmds.checkBox(cs, q=1, v=1),
                 cmds.checkBox(rs, q=1, v=1),
                 cmds.checkBox(pv, q=1, v=1),
                 cmds.checkBox(rfl, q=1, v=1),
                 cmds.checkBox(rfr, q=1, v=1)))

        self.doMassAssetEdit(assetList, layers, materials, overrides, masterFlag, melScript, pyScript, doOverrides)

    def doMassAssetEdit(self, assetList, newLayers, newMats, newOverrides, masterFlag, melScript, pyScript, doOverrides):
        print 'new layers: %s' % ','.join(newLayers)
        print 'new mats: %s' % ','.join(newMats)
        warnings = []
        fileList = []
        for asset in assetList:
            masterFile, versionsFolder, pipelineFolder = self.getAssetPaths(asset)
            initials = self.isChecked(asset)
            if initials != False and initials != self.M.user:
                warningString = 'Asset %s is currently checked out by user %s!' % (asset, initials)
                warnings.append(warningString)
            topFile = ''
            topVersion = 0
            for f in os.listdir(versionsFolder):
                try:
                    ver = int(f.split('_')[-2][1:])
                    if ver > topVersion:
                        topVersion = ver
                        topFile = f
                except IndexError:
                    pass

            fileList.append(os.path.join(versionsFolder, topFile))

        if len(warnings) > 0:
            message = '\n'.join(warnings) + '\n\nThe above assets are checked out! Are you sure you want to make changes to them?'
            confirm = cmds.confirmDialog(t='Some assets are checked out!', icon='warning', ma='left', message=message, button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return
        dummy = cmds.polySphere(name='massAssetEditGEO')
        cmds.select(dummy[0], r=1)
        exportLayers = []
        exportFiles = []
        layersCheck = ''.join(newLayers)
        if layersCheck != '':
            for index, layer in enumerate(newLayers):
                exportMat = newMats[index]
                print 'NEW LAYER: %s' % layer
                print 'LAYER MATERIAL: %s' % exportMat
                cs, rs, pv, rfl, rfr = newOverrides[index]
                print 'OVERRIDES: %d %d %d %d %d' % (cs,
                 rs,
                 pv,
                 rfl,
                 rfr)
                new = cmds.createRenderLayer(mc=1, n='EXPORT_' + layer)
                exportLayers.append(new)
                cmds.hyperShade(assign=exportMat)
                dummyShape = cmds.listRelatives(dummy[0], s=1)[0]
                cmds.setAttr(dummyShape + '.castsShadows', cs)
                cmds.setAttr(dummyShape + '.receiveShadows', rs)
                cmds.setAttr(dummyShape + '.primaryVisibility', pv)
                cmds.setAttr(dummyShape + '.visibleInReflections', rfl)
                cmds.setAttr(dummyShape + '.visibleInRefractions', rfr)
                tempFilePath = os.path.join(self.M.scenesDir, 'massAssetEdit_' + self.M.user + '_EXPORT_' + layer + '.mb')
                cmds.select(dummy[0], r=1)
                butt = cmds.file(tempFilePath, es=1, f=1, type='mayaBinary')
                exportFiles.append(butt)

        else:
            exportMat = 'initialShadingGroup'
            new = cmds.createRenderLayer(mc=1, n='EXPORT_defaultRenderLayer')
            exportLayers.append(new)
            tempFilePath = os.path.join(self.M.scenesDir, 'massAssetEdit_' + self.M.user + 'EXPORT_defaultRenderLayer.mb')
            cmds.select(dummy[0], r=1)
            butt = cmds.file(tempFilePath, es=1, f=1, type='mayaBinary')
            exportFiles.append(butt)
        fileListDump = pickle.dumps(fileList)
        exportFileDump = pickle.dumps(exportFiles)
        if masterFlag == True:
            masterFlag = '1'
        else:
            masterFlag = '0'
        if doOverrides == True:
            doOverrides = '1'
        else:
            doOverrides = '2'
        print 'sending vars to massAssetEdit: exportLayers: %s \nexportFiles: %s \nmelPickle: %s \npyPickle: %s' % (','.join(exportLayers),
         ','.join(exportFiles),
         str(melScript),
         str(pyScript))
        runScript = subprocess.Popen(os.path.join(self.M.mayaDir, 'mayapy.exe') + ' ' + os.path.join(self.M.scriptsDir, '..', 'python', 'm_massAssetEdit.py') + ' ' + fileListDump + ' ' + exportFileDump + ' ' + masterFlag + ' ' + self.M.user + ' "' + melScript + '" "' + pyScript + '" ' + doOverrides)
        stdout, stderr = runScript.communicate()
        print 'stdout: %s' % stdout
        print 'stderr: %s' % stderr
        print 'added render layer(s) %s to selected assets!' % newLayers
        for file in exportFiles:
            os.remove(file)

        cmds.editRenderLayerGlobals(crl='defaultRenderLayer')
        for layer in exportLayers:
            cmds.delete(layer)

        cmds.delete(dummy)

    def prepCacheAsset(self, *args):
        import maya.mel as mel
        mel.eval('DeleteAllHistory')
        try:
            mel.eval('MLdeleteUnused')
        except:
            print "Couldn't delete unused nodes? Check Script Editor"

        cmds.lockNode('RIGgrp', lock=0)
        cmds.lockNode('GUTSgrp', lock=0)
        try:
            cmds.delete('RIGgrp')
            cmds.delete('GUTSgrp')
        except:
            pass

    def detectCacheSet(self, *args):
        cacheset = []
        if cmds.objExists('CACHEset'):
            cacheset = cmds.sets('CACHEset', q=1)
            if cacheset:
                return True
        return False

    def mergeAssets(self, inputAsset, *args):
        if self.checkedAsset == '':
            cmds.error('You must have an asset open in order to merge.')
        if not inputAsset or inputAsset == '':
            cmds.error('You need to select an asset version to merge into this file.')
        if not os.path.exists(inputAsset):
            errorStr = "Can't find file: %s" % inputAsset
            cmds.error(errorStr)
        cmds.namespace(set=':')
        namesp = os.path.splitext(os.path.basename(inputAsset))[0]
        cmds.file(inputAsset, i=1, ra=1, ns=namesp)
        groupsToRemove = ['GEOgrp', 'RIGgrp', 'GUTSgrp']
        setsToRemove = ['RIGset', 'CACHEset']
        xformChans = ['tx',
         'ty',
         'tz',
         'sx',
         'sy',
         'sz',
         'rx',
         'ry',
         'rz']
        mainParent = ''
        if cmds.objExists(namesp + ':GEOgrp'):
            parent = cmds.listRelatives(namesp + ':GEOgrp', p=1)
            if parent:
                mainParent = parent[0]
        for thing in groupsToRemove:
            oldParent = namesp + ':' + thing
            if cmds.objExists(oldParent):
                children = cmds.listRelatives(oldParent, c=1)
                if children:
                    for child in children:
                        for i in xformChans:
                            cmds.setAttr(child + '.' + i, lock=0)

                        cmds.parent(child, thing)

                cmds.lockNode(oldParent, lock=0)
                cmds.delete(oldParent)

        for thing in setsToRemove:
            oldSet = namesp + ':' + thing
            if cmds.objExists(oldSet):
                members = cmds.sets(oldSet, q=1)
                cmds.lockNode(oldSet, lock=0)
                if members:
                    cmds.sets(members, rm=oldSet)
                    cmds.sets(members, add=thing)
                cmds.delete(oldSet)

        if mainParent:
            cmds.lockNode(mainParent, lock=0)
            cmds.delete(mainParent)
        namespaces = cmds.namespaceInfo(lon=1)
        for ns in namespaces:
            if ns != 'UI' and ns != 'shared':
                cmds.namespace(mv=(ns, ':'), force=1)
                try:
                    cmds.namespace(rm=ns)
                    deathCount.append(ns)
                except:
                    print "couldn't remove namespace: " + ns

        print 'Merged file %s with current asset %s' % (inputAsset, self.checkedAsset)