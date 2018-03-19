import maya.cmds as cmds
import maya.standalone as stand
import maya.mel as mel
import os
import pickle
import re
import string
import natSort
import time, random
import shutil
import subprocess

class SceneManager:

    def __init__(self, *args):
        self.selectedScene = ''
        self.selectedFile = ''
        self.checkedShot = ''
        self.checkedShotType = ''
        self.camVersion = '000'
        self.animVersion = '000'
        self.lightVersion = '000'
        self.lastImportVersion = '000'
        self.t = 1380585600
        print 'init sceneManager'

    def getShotPaths(self, shot, *args):
        animScenes = os.path.join(self.M.scenesDir, shot, 'animation')
        animPipe = os.path.join(animScenes, '_pipeline')
        lightScenes = os.path.join(self.M.scenesDir, shot, 'lighting')
        lightPipe = os.path.join(lightScenes, '_pipeline')
        return (animScenes,
         animPipe,
         lightScenes,
         lightPipe)

    def getReferences(self, *args):
        allRefs = cmds.file(q=1, r=1)
        refsInfo = []
        for ref in allRefs:
            node = cmds.file(ref, q=1, rfn=1)
            namespace = cmds.file(ref, q=1, ns=1)
            filename = cmds.referenceQuery(node, q=1, f=1)
            refsInfo.append(node, namespace, filename)

        return refsInfo

    def parseSceneName(self, scene, *args):
        notInteger = re.compile('[^\\d]+')
        sceneSplit = os.path.splitext(scene)[0].split('_')
        shot = '_'.join(sceneSplit[0:-4])
        cam = notInteger.sub('', sceneSplit[-4])
        anim = notInteger.sub('', sceneSplit[-3])
        light = notInteger.sub('', sceneSplit[-2])
        owner = sceneSplit[-1]
        return (shot,
         cam,
         anim,
         light,
         owner)

    def isValidScene(self, scene, *args):
        ext = os.path.splitext(scene)[-1]
        if ext != '.mb' and ext != '.ma':
            return False
        sceneSplit = os.path.splitext(scene)[0].split('_')
        owner = sceneSplit[-1]
        if len(owner) < 1 or len(owner) > 3:
            return False
        if not owner.isalpha():
            return False
        light = sceneSplit[-2]
        if light[0] != 'L':
            return False
        if len(light) != 4:
            return False
        if not light[1:].isdigit():
            return False
        anim = sceneSplit[-3]
        if anim[0] != 'A':
            return False
        if len(anim) != 4:
            return False
        if not anim[1:].isdigit():
            return False
        cam = sceneSplit[-4]
        if cam[0] != 'C':
            return False
        if len(cam) != 4:
            return False
        if not cam[1:].isdigit():
            return False
        shot = '_'.join(sceneSplit[0:-4])
        return True

    def getHighestVersions(self, shot, *args):
        animScenes, animPipe, lightScenes, lightPipe = self.getShotPaths(shot)
        animFiles = []
        lightFiles = []
        animFiles = [ f for f in os.listdir(animScenes) if os.path.splitext(os.path.join(animScenes, f))[1] == '.mb' or os.path.splitext(os.path.join(animScenes, f))[1] == '.ma' ]
        lightFiles = [ f for f in os.listdir(lightScenes) if os.path.splitext(os.path.join(lightScenes, f))[1] == '.mb' or os.path.splitext(os.path.join(lightScenes, f))[1] == '.ma' ]
        animFiles = [ f for f in animFiles if self.isValidScene(f) ]
        lightFiles = [ f for f in lightFiles if self.isValidScene(f) ]
        hiCam = 0
        hiAnim = 0
        hiLight = 0
        if len(animFiles) > 0:
            for a in animFiles:
                shot, cam, anim, light, owner = self.parseSceneName(os.path.join(animScenes, a))
                if int(cam) > int(hiCam):
                    hiCam = cam
                if int(anim) > int(hiAnim):
                    hiAnim = anim
                if int(light) > int(hiLight):
                    hiLight = light

        if len(lightFiles) > 0:
            for a in lightFiles:
                shot, cam, anim, light, owner = self.parseSceneName(os.path.join(lightScenes, a))
                if int(cam) > int(hiCam):
                    hiCam = cam
                if int(anim) > int(hiAnim):
                    hiAnim = anim
                if int(light) > int(hiLight):
                    hiLight = light

        return (str(hiCam).zfill(3), str(hiAnim).zfill(3), str(hiLight).zfill(3))

    def getReferencedCameras(self, *args):
        refCams = [ cam for cam in cmds.ls(type='camera') if cmds.referenceQuery(cam, inr=1) == 1 ]
        camsDict = {}
        for cam in refCams:
            camsDict[cam] = cmds.referenceQuery(cam, f=1)

        return camsDict

    def refCamera(self, camRN, version, *args):
        baseName = os.path.splitext(os.path.basename(version))[0]
        self.camVersion = baseName.split('_C')[-1].zfill(3)
        versionExt = os.path.splitext(version)[-1]
        fileType = ''
        if versionExt == '.mb':
            fileType = 'mayaBinary'
        else:
            fileType = 'mayaAscii'
        if camRN != '':
            cmds.file(version, loadReference=camRN, type=fileType, op='v=0')
        else:
            cmds.file(version, r=1, ns=''.join(baseName.split('_C')[0:-2]))
        if camRN != '':
            print 'updated camera %s to version C%s' % (camRN, self.camVersion)
        else:
            print 'referenced new camera %s, version C%s' % (os.path.splitext(os.path.basename(version))[0], self.camVersion)

    def getExportedCameras(self, shot, *args):
        exportsBaseFolder = os.path.join(self.M.scenesDir, shot, 'cameras')
        getCams = []
        try:
            expCams = [ f for f in os.listdir(exportsBaseFolder) if os.path.splitext(f)[-1] == '.ma' or os.path.splitext(f)[-1] == '.mb' ]
            for i in expCams:
                try:
                    test = int(os.path.splitext(i.split('_C')[-1])[0])
                    getCams.append(i)
                except ValueError:
                    pass

        except WindowsError:
            pass

        return getCams

    def autoUpdateCams(self, refCamsList = '', *args):
        edits = 0
        shot = self.checkedShot
        exportedCams = self.getExportedCameras(shot)
        refCams = self.getReferencedCameras()
        uniqueCamsList = []
        for cam in exportedCams:
            camName = '_C'.join(cam.split('_C')[0:-1])
            uniqueCamsList.append(camName)

        uniqueCamsList = list(set(uniqueCamsList))
        latestCams = []
        for cam in uniqueCamsList:
            matchedCams = [ c for c in exportedCams if '_C'.join(c.split('_C')[0:-1]) == cam ]
            hiCam = sorted(matchedCams)[-1]
            latestCams.append(hiCam)

        for cam in latestCams:
            camName = '_C'.join(cam.split('_C')[0:-1])
            camVersion = os.path.splitext(cam.split('_C')[-1])[0]
            camFullPath = os.path.join(self.M.scenesDir, shot, 'cameras', cam)
            camToSub = ''
            for camShape, filename in refCams.iteritems():
                refCamBaseName = os.path.basename(filename)
                refCamName = '_C'.join(refCamBaseName.split('_C')[0:-1])
                refCamVersion = os.path.splitext(filename.split('_C')[-1])[0]
                if refCamName == camName:
                    if int(camVersion) > int(refCamVersion):
                        camToSub = camShape
                    else:
                        camToSub = False

            if camToSub != '' and camToSub != False:
                camToSubRN = cmds.referenceQuery(camToSub, rfn=1)
                self.refCamera(camToSubRN, camFullPath)
                if camVersion > self.camVersion:
                    self.camVersion = camVersion
                edits += 1
            elif camToSub != False:
                if int(camVersion) >= int(self.camVersion):
                    self.refCamera('', camFullPath)
                    self.camVersion = camVersion
                    edits += 1

        if edits > 0:
            print 'referenced/updated %d cameras.' % edits
        else:
            print 'all cameras up to date!'
        if refCamsList != '':
            self.popCamsList(refCamsList)

    def exportCams(self, cameras, start, end, UI = '', *args):
        camDupes = []
        for cam in cameras:
            print 'preparing to export camera %s' % cam
            camXforms = cmds.listRelatives(cam, p=1)
            print 'camera xform is named: %s' % camXforms[0]
            newCam = cmds.duplicate(camXforms[0], name=camXforms[0].split(':')[-1] + '_BAKED')
            try:
                cmds.parent(newCam[0], w=1)
            except RuntimeError:
                pass

            axes = ['x', 'y', 'z']
            chans = ['t', 'r', 's']
            for a in axes:
                for b in chans:
                    try:
                        cmds.setAttr(newCam[0] + '.' + b + a, lock=False)
                    except:
                        print "couldn't unlock channel: " + newCam[0] + '.' + b + a

            cmds.parentConstraint(camXforms[0], newCam[0])
            cmds.setAttr(newCam[0] + '.sx', 1)
            cmds.setAttr(newCam[0] + '.sy', 1)
            cmds.setAttr(newCam[0] + '.sz', 1)
            camDupes.append(newCam[0])

        mel.eval('setNamedPanelLayout "Single Perspective View"')
        perspPane = cmds.getPanel(vis=1)
        cmds.scriptedPanel('graphEditor1', e=1, rp=perspPane[0])
        cmds.select(cl=1)
        outFiles = []
        if len(camDupes) > 0:
            cmds.select(camDupes)
            cmds.bakeResults(simulation=1, cp=0, s=0, sb=1.0, t=(start, end))
            cmds.delete(camDupes, cn=1)
            writePath = os.path.join(self.M.scenesDir, self.checkedShot, 'cameras')
            if not os.path.exists(writePath):
                os.makedirs(writePath)
            for cam in camDupes:
                writeFile = cam.split(':')[-1] + '_C' + self.camVersion.zfill(3) + '.ma'
                while os.path.exists(os.path.join(writePath, writeFile)):
                    self.camVersion = str(int(self.camVersion) + 1)
                    writeFile = cam.split(':')[-1] + '_C' + self.camVersion.zfill(3) + '.ma'

                if os.path.exists(os.path.join(writePath, writeFile)):
                    messageString = 'File %s already exists. Do you want to overwrite?' % writeFile
                    confirm = cmds.confirmDialog(title='Camera version already exists!', message=messageString, button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
                    if confirm == 'no':
                        continue
                out = cmds.file(os.path.join(writePath, writeFile), es=1, f=1, type='mayaAscii')
                outFiles.append(out)
                print 'exported camera %s to file: %s' % (cam, out)
                cmds.delete(cam)

        if UI != '':
            cmds.deleteUI(UI)
        return outFiles

    def reloadCams(self, camsListCtrl, *args):
        camsList = self.parseCamsList(camsListCtrl)
        for camRN in camsList:
            file = cmds.referenceQuery(camRN, f=1)
            cmds.file(file, lr=camRN)

        self.popCamsList(camsListCtrl)

    def unloadCams(self, camsListCtrl, *args):
        camsList = self.parseCamsList(camsListCtrl)
        for camRN in camsList:
            cmds.file(ur=camRN)

        self.popCamsList(camsListCtrl)

    def removeCams(self, camsListCtrl, *args):
        camsList = self.parseCamsList(camsListCtrl)
        for camRN in camsList:
            file = cmds.referenceQuery(camRN, f=1)
            cmds.file(file, rr=1)

        self.popCamsList(camsListCtrl)

    def checkOutShot(self, shot, shotType, *args):
        user = self.M.user
        animScenes, animPipe, lightScenes, lightPipe = self.getShotPaths(shot)
        if self.checkedShot != '':
            self.releaseShot()
        checkPath = ''
        if shotType == 'animation':
            checkPath = animPipe
        else:
            checkPath = lightPipe
        writeFile = open(os.path.join(checkPath, 'checkout.txt'), 'w')
        pickle.dump(user, writeFile)
        writeFile.close()
        self.checkedShot = shot
        self.checkedShotType = shotType
        print 'checking out %s shot: %s' % (shotType, shot)

    def releaseShot(self, warning = False, *args):
        if self.checkedShot == '':
            cmds.error('No shot is checked out!')
        if warning == True:
            titleString = 'Release shot %s?' % self.checkedShot
            confirm = cmds.confirmDialog(title=titleString, message='Releasing this shot will unload the scene. Are you sure you want to do this?', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return
        animScenes, animPipe, lightScenes, lightPipe = self.getShotPaths(self.checkedShot)
        print 'releasing %s shot: %s' % (self.checkedShotType, self.checkedShot)
        checkPath = ''
        if self.checkedShotType == 'animation':
            checkPath = animPipe
        else:
            checkPath = lightPipe
        writeFile = open(os.path.join(checkPath, 'checkout.txt'), 'w')
        pickle.dump('', writeFile)
        writeFile.close()
        self.checkedShot = ''
        if warning == True:
            cmds.file(new=1, force=1)

    def newShot(self, name, ext = '.mb', checkOut = False, killUI = '', shotListCtrl = '', *args):
        if cmds.file(q=1, mf=1):
            confirm = cmds.confirmDialog(title='save your scene?', message='Your current scene has unsaved changes. Save before continuing?', button=['yes', 'no'], defaultButton='yes', cancelButton='no', dismissString='no')
            if confirm == 'yes':
                self.M.quickSave()
        user = self.M.user
        name.strip()
        newfile = ''
        print 'validating shot name: %s' % name
        rePattern = '^[a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9_]$'
        search = re.findall(rePattern, name)
        if len(search) == 0:
            cmds.error('Invalid shot name: %s' % name)
            return False
        if not os.path.exists(os.path.join(self.M.scenesDir, name)):
            os.makedirs(os.path.join(self.M.scenesDir, name))
            os.makedirs(os.path.join(self.M.scenesDir, name, 'animation', '_pipeline'))
            os.makedirs(os.path.join(self.M.scenesDir, name, 'animation', '_scrap'))
            os.makedirs(os.path.join(self.M.scenesDir, name, 'lighting', '_pipeline'))
            os.makedirs(os.path.join(self.M.scenesDir, name, 'lighting', '_scrap'))
        else:
            confirm = cmds.confirmDialog(title='shot folder already exists', message="There's already a shot here with the same name. Are you sure you want to continue?", icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return
            try:
                os.makedirs(os.path.join(self.M.scenesDir, name, 'animation', '_pipeline'))
            except WindowsError:
                print 'Path already exists: %s' % os.path.join(self.M.scenesDir, name, 'animation', '_pipeline')

            try:
                os.makedirs(os.path.join(self.M.scenesDir, name, 'animation', '_scrap'))
            except WindowsError:
                print 'Path already exists: %s' % os.path.join(self.M.scenesDir, name, 'animation', '_scrap')

            try:
                os.makedirs(os.path.join(self.M.scenesDir, name, 'lighting', '_pipeline'))
            except WindowsError:
                print 'Path already exists: %s' % os.path.join(self.M.scenesDir, name, 'lighting', '_pipeline')

            try:
                os.makedirs(os.path.join(self.M.scenesDir, name, 'lighting', '_scrap'))
            except WindowsError:
                print 'Path already exists: %s' % os.path.join(self.M.scenesDir, name, 'lighting', '_scrap')

        template = self.M.sceneTemplate
        if not os.path.exists(template):
            cmds.warning("Couldn't find template file: " + template)
            cmds.file(new=1, force=1)
        else:
            cmds.file(template, o=1, force=1)
        filename = os.path.join(self.M.scenesDir, name, 'lighting', name + '_C000_A000_L000_' + self.M.user + ext)
        cmds.file(rename=filename)
        if ext == '.mb':
            cmds.file(save=1, force=1, type='mayaBinary')
        else:
            cmds.file(save=1, force=1, type='mayaAscii')
        print 'Created new scene: %s' % filename
        filename = os.path.join(self.M.scenesDir, name, 'animation', name + '_C000_A000_L000_' + self.M.user + ext)
        cmds.file(rename=filename)
        if ext == '.mb':
            cmds.file(save=1, force=1, type='mayaBinary')
        else:
            cmds.file(save=1, force=1, type='mayaAscii')
        print 'Created new scene: %s' % filename
        if checkOut == True:
            self.checkOutShot(name, 'animation')
        if killUI != '':
            cmds.deleteUI(killUI)
        self.popShotsList(shotListCtrl)
        return filename

    def cloneShot(self, name, shotListCtrl, cloneUI = ''):
        name.strip()
        print 'validating shot name: %s' % name
        rePattern = '^[a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9_]$'
        search = re.findall(rePattern, name)
        if len(search) == 0:
            cmds.error('Invalid shot name: %s' % name)
            return False
        oldShot = cmds.textScrollList(shotListCtrl, q=1, si=1)[0]
        oldShotPath = os.path.join(self.M.scenesDir, oldShot)
        newShotPath = os.path.join(self.M.scenesDir, name)
        shutil.copytree(oldShotPath, newShotPath)
        animScenes, animPipe, lightScenes, lightPipe = self.getShotPaths(name)
        animCheck = open(os.path.join(animPipe, 'checkout.txt'), 'w')
        pickle.dump('', animCheck)
        animCheck.close()
        lightCheck = open(os.path.join(lightPipe, 'checkout.txt'), 'w')
        pickle.dump('', lightCheck)
        lightCheck.close()
        for root, dirs, files in os.walk(newShotPath):
            for file in files:
                newFilename = file.replace(oldShot, name)
                oldFilepath = os.path.join(root, file)
                newFilepath = os.path.join(root, newFilename)
                os.rename(oldFilepath, newFilepath)

        self.popShotsList(shotListCtrl)
        if cloneUI != '':
            cmds.deleteUI(cloneUI)
        message = 'Cloned new shot %s from source shot %s' % (name, oldShot)
        cmds.warning(message)

    def deleteShot(self, shotTypeCtrl, shotListCtrl, sceneListCtrl, *args):
        shot = ''
        try:
            shot = cmds.textScrollList(shotListCtrl, q=1, si=1)[0]
        except IndexError:
            cmds.error('Please select a single shot to delete.')

        messageString = "Are you sure you want to delete %s? You can restore a deleted shot by moving it out of the _TRASH folder in the project's scenes folder." % shot
        confirm = cmds.confirmDialog(t='DELETE shot?', ma='left', icon='critical', message=messageString, button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
        if confirm == 'no':
            return
        if not os.path.exists(os.path.join(self.M.scenesDir, '_TRASH')):
            os.mkdir(os.path.join(self.M.scenesDir, '_TRASH'))
        shutil.move(os.path.join(self.M.scenesDir, shot), os.path.join(self.M.scenesDir, '_TRASH', shot))
        self.popShotsList(shotListCtrl)
        self.popScenesList(shotTypeCtrl, shotListCtrl, sceneListCtrl)
        warnString = 'deleted shot %s!' % shot
        cmds.warning(warnString)

    def quickSave(self, *args):
        self.saveSceneUI()

    def updateScene(self, upCam, upAnim, upLight, notes, release = False, ext = '.mb', updateUI = '', shotType = '', *args):
        user = self.M.user
        if self.checkedShot == '' or self.checkedShotType == '':
            cmds.error('No shot is checked out! Try restarting Mustache.')
        if shotType == '':
            shotType = self.checkedShotType
        sceneFile = cmds.file(q=1, sn=1, shn=1)
        shot, cam, anim, light, owner = self.parseSceneName(sceneFile)
        newFileName = shot + '_C' + str(upCam).zfill(3) + '_A' + str(upAnim).zfill(3) + '_L' + str(upLight).zfill(3) + '_' + user + ext
        if os.path.exists(os.path.join(self.M.scenesDir, shot, shotType, newFileName)):
            messageString = 'A shot with the name %s already exists. Do you want to overwrite?' % newFileName
            confirm = cmds.confirmDialog(title='File already exists!', message=messageString, button=['yes', 'no'], cancelButton='no', dismissString='no', defaultButton='no')
            if confirm == 'no':
                return
        cmds.editRenderLayerGlobals(crl='defaultRenderLayer')
        screenWindowName = 'screenWindow'
        if cmds.window(screenWindowName, q=1, exists=1):
            cmds.deleteUI(screenWindowName)
        screenWindow = cmds.window(screenWindowName, w=960, h=540)
        playout = cmds.paneLayout()
        mpanel = cmds.modelPanel(l='TEMP_SCREENSHOT')
        cmds.showWindow(screenWindowName)
        getPanelName = cmds.getPanel(wl='TEMP_SCREENSHOT')
        cmds.setFocus(getPanelName)
        defaultCams = ['perspShape',
         'topShape',
         'frontShape',
         'sideShape']
        renderCams = []
        renderCams = [ f for f in cmds.ls(type='camera') if cmds.getAttr(f + '.renderable') == 1 and f not in defaultCams ]
        newCam = []
        newCam.append('0')
        newCam.append('0')
        usingBuiltInCam = 0
        if len(renderCams) > 0:
            newCam[1] = renderCams.pop()
            newCam[0] = cmds.listRelatives(newCam[1], p=1)[0]
            usingBuiltInCam = 1
        else:
            newCam = cmds.camera()
            cmds.setAttr(newCam[0] + '.rotateX', -35)
            cmds.setAttr(newCam[0] + '.rotateY', 45)
            cmds.viewFit(newCam[1], all=1)
            cmds.viewClipPlane(newCam[1], acp=1)
        cmds.modelPanel(mpanel, e=1, cam=newCam[1])
        modelEd = cmds.modelPanel(mpanel, q=1, me=1)
        cmds.modelEditor(modelEd, e=1, da='smoothShaded')
        screenPath = os.path.join(self.M.scenesDir, shot, shotType, '_pipeline', newFileName + '.iff')
        ct = cmds.currentTime(q=1)
        cmds.playblast(st=ct, et=ct, w=640, h=400, fmt='image', cf=screenPath)
        cmds.modelEditor(modelEd, e=1, dtx=0)
        try:
            cmds.deleteUI(mpanel)
        except:
            pass

        cmds.deleteUI(screenWindow)
        if usingBuiltInCam == 0:
            cmds.delete(newCam)
        convertProc = subprocess.Popen(self.M.binDir + 'imf_copy.exe ' + screenPath + ' ' + screenPath[:-4] + '.jpg', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = convertProc.communicate()
        print '\nIMGCONVERT STDOUT: '
        print stdout
        print '\nIMGCONVERT STDERR: '
        print stderr
        notesFile = open(screenPath[:-4] + '.txt', 'w')
        pickle.dump(notes, notesFile)
        notesFile.close()
        writePath = os.path.join(self.M.scenesDir, shot, shotType, newFileName)
        cmds.file(rename=writePath)
        saveType = ''
        if ext == '.mb':
            saveType = 'mayaBinary'
        else:
            saveType = 'mayaAscii'
        savedFile = cmds.file(save=1, force=1, type=saveType)
        self.camVersion = upCam
        self.animVersion = upAnim
        self.lightVersion = upLight
        print 'Updated shot %s! New scene is: %s' % (shot, savedFile)
        if updateUI != '':
            cmds.deleteUI(updateUI)
        return savedFile

    def editScene(self, shot, shotType, filename, loadRefs = 1, *args):
        if cmds.file(q=1, mf=1) == 1:
            confirm = cmds.confirmDialog(title='Unsaved changes', message='Your scene has been modified. Save this scene first?', icon='warning', button=['save', 'continue without saving', 'cancel'], defaultButton='cancel', cancelButton='cancel', dismissString='cancel')
            if confirm == 'cancel':
                return
            if confirm == 'save':
                try:
                    cmds.file(s=1, f=1, type='mayaBinary')
                except RuntimeError:
                    pass

        checkPath = os.path.join(self.M.scenesDir, shot, shotType, '_pipeline', 'checkout.txt')
        initials = ''
        if os.path.exists(checkPath):
            checkFile = open(checkPath, 'r')
            initials = pickle.load(checkFile)
            checkFile.close()
        if initials != '' and initials != self.M.user:
            messageString = '%s shot %s is already checked out by %s. Are you sure you want to edit this scene?' % (shotType.capitalize(), shot, initials.upper())
            confirm = cmds.confirmDialog(title='Shot already checked out!', message=messageString, icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return
        if self.checkedShot != '' and self.checkedShot != shot:
            messageString = 'You already have the shot %s checked out. You will have to release it to continue. OK?' % self.checkedShot
            confirm = cmds.confirmDialog(title='You already have a shot checked out!', message=messageString, icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if confirm == 'no':
                return
            self.releaseShot(False)
        self.checkOutShot(shot, shotType)
        filepath = os.path.join(self.M.scenesDir, shot, shotType, filename)
        if loadRefs == 1:
            cmds.file(filepath, o=1, force=1)
        else:
            cmds.file(filepath, o=1, lrd='none', force=1)
        shot, self.camVersion, self.animVersion, self.lightVersion, owner = self.parseSceneName(filename)
        print 'now editing %s scene %s' % (shotType, filename)
        self.sceneManagerUI()

    def getRenderLayers(self, *args):
        allLayers = cmds.ls(type='renderLayer')
        for index, a in enumerate(allLayers):
            layerSplit = a.split(':')
            if len(layerSplit) > 1:
                allLayers[index] = layerSplit[-1]

        layerSet = list(set(allLayers))
        layerSet.remove('defaultRenderLayer')
        return layerSet

    def reconstruct(self, start = False, end = False, *args):
        windowOff = 1
        scene = cmds.file(q=1, sn=1)
        refsDict = self.getAssets()
        renderLayers = self.getRenderLayers()
        if start == False:
            start = cmds.playbackOptions(q=1, min=1)
        if end == False:
            end = cmds.playbackOptions(q=1, max=1)
        notRefCams = [ f for f in cmds.ls(type='camera') if not cmds.referenceQuery(f, inr=1) ]
        ignoreCams = ['perspShape',
         'topShape',
         'sideShape',
         'frontShape']
        camsToExport = [ f for f in notRefCams if cmds.getAttr(f + '.renderable') == 1 and f not in ignoreCams ]
        self.exportCams(camsToExport, start, end)
        namespaces = []
        newRefsDict = {}
        for rn, filename in refsDict.iteritems():
            namespaces.append(cmds.file(filename, q=1, ns=1))
            newRefsDict[filename] = cmds.file(filename, q=1, ns=1)

        exportPath = self.massAnimExport(namespaces, start, end, 0, windowOff)
        template = self.M.sceneTemplate
        if not os.path.exists(template):
            cmds.file(new=1, f=1)
        else:
            cmds.file(template, o=1, f=1)
        for layer in renderLayers:
            cmds.createRenderLayer(n=layer)

        for filename, namespace in newRefsDict.iteritems():
            newRef = cmds.file(filename, r=1, ns=namespace, shd='renderLayersByName')

        expCams = self.getExportedCameras(self.checkedShot)
        for c in expCams:
            camPath = os.path.join(self.M.scenesDir, self.checkedShot, 'cameras', c)
            self.refCamera('', camPath)

        cmds.playbackOptions(e=1, min=start)
        cmds.playbackOptions(e=1, max=end)
        self.massAnimImport(namespaces, exportPath)
        shot, cam, anim, light, owner = self.parseSceneName(os.path.basename(scene))
        hiCam, hiAnim, hiLight = self.getHighestVersions(shot)
        hiLight = str(int(hiLight) + 1).zfill(3)
        tempFileName = os.path.join(self.M.scenesDir, shot, 'lighting', shot + '_C' + cam + '_A' + anim + '_L' + hiLight + '_' + self.M.user + '.mb')
        cmds.file(rename=tempFileName)
        cmds.file(s=1, f=1)
        notesString = 'Autoconverted from animation scene %s' % scene
        newFile = self.updateScene(cam, anim, hiLight, notesString, False, '.mb', '', 'lighting')
        print 'saved reconstructed file as %s' % newFile
        self.releaseShot()
        self.checkOutShot(shot, 'lighting')
        self.sceneManagerUI()
        return newFile

    def getAssets(self, active = 1, *args):
        refNodes = []
        if active == 1:
            refNodes = [ cmds.file(f, q=1, rfn=1) for f in cmds.file(q=1, r=1) if not cmds.file(f, q=1, dr=1) ]
        else:
            refNodes = [ cmds.file(f, q=1, rfn=1) for f in cmds.file(q=1, r=1) if cmds.file(f, q=1, dr=1) ]
        assetsDict = {}
        for rn in refNodes:
            filename = cmds.referenceQuery(rn, f=1)
            fileSplit = filename.split('/')[-2]
            if fileSplit != 'cameras':
                assetsDict[rn] = filename

        return assetsDict

    def createRef(self, filename, *args):
        finalFile = ''
        if os.path.exists(filename):
            namesp = os.path.splitext(os.path.basename(filename))[0]
            if self.checkedShotType == 'lighting':
                testFile = os.path.splitext(filename)[0] + '_CACHE.mb'
                if os.path.exists(testFile):
                    finalFile = testFile
                else:
                    finalFile = filename
            else:
                finalFile = filename
            newRef = cmds.file(finalFile, r=1, ns=namesp, shd='renderLayersByName')
            newRefRN = cmds.file(newRef, q=1, rfn=1)
            print 'Created reference %s to file %s' % (newRefRN, finalFile)
        else:
            cmds.error('Master file not found! ' + filename)

    def replaceRef(self, refsListCtrl, assetname, replaceUI = '', replaceNS = 0, *args):
        newfile = os.path.join(self.M.assetsDir, assetname, assetname + '.mb')
        refsList = cmds.textScrollList(refsListCtrl, q=1, si=1)
        refNodes = []
        filenames = self.parseRefsList(refsListCtrl)
        for file in filenames:
            ref = cmds.file(file, q=1, rfn=1)
            refNodes.append(ref)

        for refNode in refNodes:
            newRef = cmds.file(newfile, lr=refNode)
            if replaceNS == 1:
                newBaseName = os.path.splitext(os.path.basename(filename))[0]
                newNS = newBaseName
                checkNS = newNS
                suffix = ''
                namespaces = [ cmds.file(f, q=1, namespace=1) for f in cmds.file(q=1, r=1) ]
                if newBaseName in namespaces:
                    newNameRev = newBaseName[::-1]
                    nsIndex = 0
                    for index, char in enumerate(newNameRev):
                        if char in string.digits:
                            nsIndex = index
                        else:
                            break

                    newNameRev = newNameRev[nsIndex:]
                    suffix = '1'
                    newNS = newNameRev[::-1]
                    checkNS = newNS + suffix
                    while checkNS in namespaces:
                        suffix = str(int(suffix) + 1)
                        checkNS = newNS + suffix

                print 'generated new namespace: %s' % checkNS
                cmds.lockNode(refNode, lock=0)
                newRefNode = cmds.rename(refNode, newNS + 'RN' + suffix)
                cmds.lockNode(newRefNode, lock=1)
                cmds.file(newRef, e=1, rfn=newRefNode, namespace=checkNS)
            print 'Replaced reference %s with new file %s' % (refNode, newfile)

        index = cmds.textScrollList(refsListCtrl, q=1, sii=1)
        self.popRefsList(refsListCtrl)
        cmds.textScrollList(refsListCtrl, e=1, sii=index)
        if replaceUI != '':
            cmds.deleteUI(replaceUI)

    def renameRef(self, refsListCtrl, newName, *args):
        filenames = self.parseRefsList(refsListCtrl)
        for filename in filenames:
            oldName = cmds.file(filename, q=1, ns=1)
            try:
                cmds.file(filename, e=1, namespace=newName)
            except RuntimeError:
                cmds.error('that namespace is invalid or in use already. try again.')

            print 'changed namespace %s to %s' % (oldName, newName)

        index = cmds.textScrollList(refsListCtrl, q=1, sii=1)
        self.popRefsList(refsListCtrl)
        cmds.textScrollList(refsListCtrl, e=1, sii=index)

    def unloadRef(self, refsListCtrl, *args):
        filenames = self.parseRefsList(refsListCtrl)
        for file in filenames:
            refNode = cmds.file(file, q=1, rfn=1)
            cmds.file(ur=refNode)

        self.popRefsList(refsListCtrl)

    def reloadRef(self, refsListCtrl, *args):
        filenames = self.parseRefsList(refsListCtrl)
        for file in filenames:
            refNode = cmds.file(file, q=1, rfn=1)
            cmds.file(file, lr=refNode)

        self.popRefsList(refsListCtrl)

    def removeRef(self, refsListCtrl, *args):
        filenames = self.parseRefsList(refsListCtrl)
        for file in filenames:
            refNode = cmds.file(file, q=1, rfn=1)
            namesp = cmds.file(file, q=1, namespace=1)
            cmds.file(file, rr=1)
            cmds.namespace(set=':')
            test = self.removeAnimCurves(namesp)
            if test:
                cmds.namespace(rm=namesp)
            print 'removed reference %s' % refNode

        self.popRefsList(refsListCtrl)

    def removeAnimCurves(self, namesp, *args):
        animCurveTypes = ['animCurveTL',
         'animCurveTA',
         'animCurveTT',
         'animCurveTU',
         'animCurveUL',
         'animCurveUA',
         'animCurveUT',
         'animCurveUU']
        curves = [ f for f in cmds.ls(type=animCurveTypes) if f.split(':')[0] == namesp ]
        if curves:
            for i in curves:
                cmds.delete(i)

        print 'removed animation info under namespace %s' % namesp
        if curves:
            return True
        else:
            return False

    def cleanupRef(self, refNode, refListCtrl, shadingOnly = 0, *args):
        if shadingOnly == 0:
            cmds.file(ur=refNode)
            cmds.file(cr=refNode)
            cmds.file(lr=refNode)
            print 'removed all edits from reference %s' % refNode
        else:
            allEdits = cmds.referenceQuery(refNode, es=1)
            search = 'dagSet'
            dagEdits = [ f for f in allEdits if f.find(search) != -1 ]
            cmds.file(ur=refNode)
            killCount = 0
            for edit in dagEdits:
                try:
                    killMe = edit.split('"')[1]
                    cmds.referenceEdit(killMe, failedEdits=1, successfulEdits=1, removeEdits=1, orn=refNode)
                    killCount += 1
                except IndexError:
                    pass

            cmds.file(lr=refNode)
            print 'nuked %d dagSet edits from reference %s' % (killCount, refNode)

    def sceneManagerUI(self, *args):
        user = self.M.user
        if user == '':
            cmds.error('No user detected. Restart Mustache.')
        winName = 'sceneManagerUI'
        winTitle = '}MUSTACHE{ - SCENE MANAGER'
        if cmds.window(winName, q=1, exists=1):
            cmds.deleteUI(winName)
        window = cmds.window(winName, title=winTitle)
        containerForm = cmds.formLayout()
        changeProjCtrl = cmds.button(l='Change project...', w=110, h=25, c=lambda *x: self.M.setProjectUI(False, True))
        changeProjText = cmds.textField(tx=self.M.project, w=340, en=0)
        changeUserCtrl = cmds.button(l='Change user...', w=110, h=25, c=lambda *x: self.M.setUserUI(False, False, True))
        changeUserText = cmds.textField(tx=self.M.user, w=35, en=0)
        cmds.formLayout(containerForm, e=1, attachForm=[(changeProjCtrl, 'top', 5),
         (changeProjCtrl, 'left', 5),
         (changeProjText, 'top', 8),
         (changeProjText, 'left', 120),
         (changeUserCtrl, 'top', 5),
         (changeUserCtrl, 'left', 485),
         (changeUserText, 'top', 8),
         (changeUserText, 'left', 600)])
        tabs = cmds.tabLayout()
        cmds.formLayout(containerForm, e=1, attachForm=[(tabs, 'top', 40), (tabs, 'left', 5)])
        shotListForm = cmds.formLayout(parent=tabs)
        shotTypeCtrl = cmds.textScrollList(w=130, h=50, ams=0, fn='boldLabelFont', sc=lambda *x: self.popScenesList(shotTypeCtrl, shotListCtrl, sceneListCtrl))
        shotTypeLabel = cmds.text(l='SHOT TYPE', fn='boldLabelFont', ann='Browse through "animation" or "lighting" shots.')
        shotListCtrl = cmds.textScrollList(w=190, h=500, ams=0, fn='boldLabelFont', ann='Select a shot from your project to browse scenes, or to clone this shot.', sc=lambda *x: self.popScenesList(shotTypeCtrl, shotListCtrl, sceneListCtrl))
        shotListLabel = cmds.text(l='SHOTS LIST', fn='boldLabelFont')
        sceneListCtrl = cmds.textScrollList(w=230, h=500, ams=0, ann='Select a scene to view details or edit.', sc=lambda *x: self.selectScene(shotTypeCtrl, shotListCtrl, sceneListCtrl, screenCtrl, modifiedLabel, checkoutAlert, versionNotes))
        sceneListLabel = cmds.text(l='SCENES LIST', fn='boldLabelFont')
        screenCtrl = cmds.image(w=320, h=200)
        modifiedLabel = cmds.text(l='Last modified:')
        checkoutAlert = cmds.text(l='', fn='boldLabelFont')
        versionNotes = cmds.scrollField(w=320, h=250, tx='Version notes: ', ww=1)
        cmds.formLayout(shotListForm, e=1, attachForm=[(shotTypeCtrl, 'top', 25),
         (shotTypeCtrl, 'left', 5),
         (shotListCtrl, 'top', 25),
         (shotListCtrl, 'left', 145),
         (sceneListCtrl, 'top', 25),
         (sceneListCtrl, 'left', 345),
         (shotTypeLabel, 'top', 10),
         (shotTypeLabel, 'left', 5),
         (shotListLabel, 'top', 10),
         (shotListLabel, 'left', 200),
         (sceneListLabel, 'top', 10),
         (sceneListLabel, 'left', 345),
         (screenCtrl, 'top', 25),
         (screenCtrl, 'left', 590),
         (modifiedLabel, 'top', 235),
         (modifiedLabel, 'left', 590),
         (checkoutAlert, 'top', 255),
         (checkoutAlert, 'left', 590),
         (versionNotes, 'top', 275),
         (versionNotes, 'left', 590)])
        versionUpCtrl = cmds.button(l='Save scene', bgc=[0.6, 0.7, 1.0], w=130, h=60, ann='Save a new version of this scene.', c=lambda *x: self.saveSceneUI(shotTypeCtrl, shotListCtrl, sceneListCtrl))
        editSceneCtrl = cmds.button(l='Edit scene', w=130, h=60, bgc=[0.7, 1.0, 0.6], ann='Edit the selected scene.', c=lambda *x: self.editScene(cmds.textScrollList(shotListCtrl, q=1, si=1)[0], cmds.textScrollList(shotTypeCtrl, q=1, si=1)[0], cmds.textScrollList(sceneListCtrl, q=1, si=1)[0], cmds.checkBox(loadRefsCtrl, q=1, v=1)))
        loadRefsCtrl = cmds.checkBox(l='Load references', v=1)
        newShotCtrl = cmds.button(l='New shot', w=130, h=60, ann='Create a new shot for the project.', c=lambda x: self.doNewShot(shotListCtrl))
        cloneShotCtrl = cmds.button(l='Clone shot', w=130, h=60, ann='Duplicate an existing shot, copying all animation and lighting scenes to a new folder.', c=lambda *x: self.doCloneShot(shotListCtrl))
        releaseShotCtrl = cmds.button(l='Release shot', w=130, h=60, ann='Release this shot so others can edit it.', c=lambda x: self.releaseShot(True))
        renameShotCtrl = cmds.button(l='Rename shot', w=130, h=60, ann='Rename selected shot.', c=lambda *x: self.renameShot(shotTypeCtrl, shotListCtrl, sceneListCtrl))
        deleteShotCtrl = cmds.button(l='Delete shot', w=130, h=60, ann='Delete selected shot.', bgc=[1.0, 0.6, 0.7], c=lambda *x: self.deleteShot(shotTypeCtrl, shotListCtrl, sceneListCtrl))
        cmds.formLayout(shotListForm, e=1, attachForm=[(versionUpCtrl, 'top', 100),
         (versionUpCtrl, 'left', 5),
         (editSceneCtrl, 'top', 165),
         (editSceneCtrl, 'left', 5),
         (newShotCtrl, 'top', 265),
         (newShotCtrl, 'left', 5),
         (cloneShotCtrl, 'top', 330),
         (cloneShotCtrl, 'left', 5),
         (releaseShotCtrl, 'top', 395),
         (releaseShotCtrl, 'left', 5),
         (loadRefsCtrl, 'left', 15),
         (loadRefsCtrl, 'top', 235),
         (renameShotCtrl, 'left', 5),
         (renameShotCtrl, 'top', 460),
         (deleteShotCtrl, 'top', 535),
         (deleteShotCtrl, 'left', 5)])
        cmds.textScrollList(shotTypeCtrl, e=1, a=['animation', 'lighting'])
        cmds.textScrollList(shotTypeCtrl, e=1, si='animation')
        self.popShotsList(shotListCtrl, 'animation')
        sceneOpsForm = cmds.formLayout(parent=tabs)
        changeNSCtrl = cmds.button(w=150, h=25, l='Rename', en=0, ann='Change the namespace of the highlighted reference to this text.', c=lambda *x: self.renameRef(refsListCtrl, cmds.textField(namespaceCtrl, q=1, tx=1)))
        changeFileCtrl = cmds.button(w=150, h=25, l='Replace...', en=0, ann='Replace all highlighted references with a new file.', c=lambda *x: self.doReplaceRef(refsListCtrl))
        namespaceCtrl = cmds.textField(w=150)
        namespaceLabel = cmds.text(l='Namespace:')
        filenameCtrl = cmds.textField(w=150, en=0)
        filenameLabel = cmds.text(l='Filename:')
        assetTypeLabel = cmds.text(l='Asset type:')
        assetTypeCtrl = cmds.optionMenu()
        cmds.menuItem(label='Standard')
        cmds.menuItem(label='Cache')
        assetFilterCtrl = cmds.textField(w=121, h=24, aie=1, ec=lambda *x: self.popAssetList(assetListCtrl, cmds.textField(assetFilterCtrl, q=1, tx=1), assetFilterBtn))
        assetFilterBtn = cmds.symbolButton(w=24, h=24, i='filtersOff.png', c=lambda *x: self.popAssetList(assetListCtrl, cmds.textField(assetFilterCtrl, q=1, tx=1), assetFilterBtn))
        assetTypeButton = cmds.button(l='Modify type', w=150, h=25, en=0, ann='Swap highlighted references with either a Standard asset or a Cache asset version (if available).', c=lambda *x: self.swapRefType(refsListCtrl, assetTypeCtrl))
        assetListCtrl = cmds.textScrollList(w=150, h=450, ams=1, fn='boldLabelFont', sc=lambda *x: self.printSelList(assetListCtrl), ann='A list of all assets for the project.')
        assetListLabel = cmds.text(l='ASSETS', fn='boldLabelFont')
        refsListCtrl = cmds.textScrollList(w=200, h=450, ams=1, ann='A list of all assets referenced into your scene.', sc=lambda *x: self.displayRefInfo(refsListCtrl, namespaceCtrl, filenameCtrl, changeNSCtrl, changeFileCtrl, assetTypeCtrl, assetTypeButton))
        refsListLabel = cmds.text(l='SCENE REFERENCES ("*"=unloaded)', fn='boldLabelFont')
        refsFilterCtrl = cmds.textField(w=171, h=24, aie=1, ec=lambda *x: self.popRefsList(refsListCtrl, cmds.textField(refsFilterCtrl, q=1, tx=1), refsFilterBtn))
        refsFilterBtn = cmds.symbolButton(w=24, h=24, i='filtersOff.png', c=lambda *x: self.popRefsList(refsListCtrl, cmds.textField(refsFilterCtrl, q=1, tx=1), refsFilterBtn))
        self.popAssetList(assetListCtrl)
        self.popRefsList(refsListCtrl)
        createCtrl = cmds.button(w=150, h=40, l='Create >>', ann='Select an asset to reference it into your scene.', c=lambda *x: self.doCreateRef(assetListCtrl, refsListCtrl))
        reloadCtrl = cmds.button(w=150, h=40, l='Reload', bgc=[0.6, 0.7, 1.0], ann='Reload an unloaded or outdated reference.', c=lambda x: self.reloadRef(refsListCtrl))
        unloadCtrl = cmds.button(w=150, h=40, l='Unload', ann='Unload a reference.', c=lambda x: self.unloadRef(refsListCtrl))
        cleanupCtrl = cmds.button(w=150, h=40, l='Cleanup', c=lambda *x: self.doCleanupRef(refsListCtrl, cmds.checkBox(cleanupCheckCtrl, q=1, v=1)), ann='Remove edits from selected references. Use "Preserve Animation" to remove only shading edits. Cannot undo.')
        cleanupCheckCtrl = cmds.checkBox(l='Preserve animation', v=1, ann='Attempt to preserve animation while removing edits related to shading and render layers. Cannot undo.')
        removeCtrl = cmds.button(w=200, h=40, l='<< Remove', ann='Remove selected references from this scene. Cannot undo.', c=lambda x: self.doRemoveRef(refsListCtrl))
        duplicateCtrl = cmds.button(w=150, h=40, l='Duplicate', c=lambda x: self.doDuplicateRef(refsListCtrl), ann='Duplicate selected references, including existing reference edits.')
        cmds.formLayout(sceneOpsForm, e=1, attachForm=[(assetListCtrl, 'top', 60),
         (assetListCtrl, 'left', 5),
         (refsListCtrl, 'top', 60),
         (refsListCtrl, 'left', 170),
         (assetListLabel, 'top', 40),
         (assetListLabel, 'left', 5),
         (refsListLabel, 'top', 40),
         (refsListLabel, 'left', 170),
         (namespaceLabel, 'top', 40),
         (namespaceLabel, 'left', 385),
         (namespaceCtrl, 'top', 57),
         (namespaceCtrl, 'left', 385),
         (filenameLabel, 'top', 115),
         (filenameLabel, 'left', 385),
         (filenameCtrl, 'top', 132),
         (filenameCtrl, 'left', 385),
         (changeNSCtrl, 'top', 82),
         (changeNSCtrl, 'left', 385),
         (changeFileCtrl, 'top', 155),
         (changeFileCtrl, 'left', 385),
         (reloadCtrl, 'top', 350),
         (reloadCtrl, 'left', 385),
         (unloadCtrl, 'top', 400),
         (unloadCtrl, 'left', 385),
         (cleanupCtrl, 'top', 450),
         (cleanupCtrl, 'left', 385),
         (cleanupCheckCtrl, 'top', 495),
         (cleanupCheckCtrl, 'left', 395),
         (removeCtrl, 'top', 520),
         (removeCtrl, 'left', 170),
         (createCtrl, 'top', 520),
         (createCtrl, 'left', 5),
         (duplicateCtrl, 'top', 300),
         (duplicateCtrl, 'left', 385),
         (assetTypeLabel, 'left', 385),
         (assetTypeLabel, 'top', 185),
         (assetTypeCtrl, 'left', 385),
         (assetTypeCtrl, 'top', 200),
         (assetTypeButton, 'left', 385),
         (assetTypeButton, 'top', 225),
         (assetFilterBtn, 'top', 5),
         (assetFilterBtn, 'left', 5),
         (assetFilterCtrl, 'top', 5),
         (assetFilterCtrl, 'left', 39),
         (refsFilterBtn, 'top', 5),
         (refsFilterBtn, 'left', 170),
         (refsFilterCtrl, 'top', 5),
         (refsFilterCtrl, 'left', 200)])
        camsLabel = cmds.text(l='CAMERAS', fn='boldLabelFont')
        getCamButton = cmds.button(w=150, h=40, l='Get camera...', c=lambda *x: self.getCameraUI(refCamsList), ann='Reference an exported camera into your scene.')
        exportCamButton = cmds.button(w=150, h=40, l='Export cameras...', c=lambda x: self.exportCameraUI(), ann='Export cameras from your scene.')
        autoUpdateCamButton = cmds.button(w=150, h=40, l='Auto update cameras', bgc=[0.6, 0.7, 1.0], c=lambda x: self.autoUpdateCams(refCamsList), ann='Automatically update all cameras to latest version.')
        refCamsList = cmds.textScrollList(w=160, h=90, ams=0, ann='Lists cameras currently referenced into your scene.')
        replaceCamButton = cmds.button(w=75, h=40, l='Replace...', c=lambda *x: self.replaceCameraUI(cmds.textScrollList(refCamsList, q=1, si=1)[0], refCamsList), ann='Replace selected camera with a different camera.')
        removeCamButton = cmds.button(w=75, h=40, l='Remove', c=lambda x: self.removeCams(refCamsList), ann='Remove selected camera from the scene.')
        loadCamButton = cmds.button(w=75, h=40, l='Reload', c=lambda x: self.reloadCams(refCamsList), ann='Reload selected referenced cameras.')
        unloadCamButton = cmds.button(w=75, h=40, l='Unload', c=lambda x: self.unloadCams(refCamsList), ann='Unload selected referenced cameras.')
        cmds.formLayout(sceneOpsForm, e=1, attachForm=[(camsLabel, 'top', 40),
         (camsLabel, 'left', 570),
         (getCamButton, 'top', 60),
         (getCamButton, 'left', 570),
         (exportCamButton, 'top', 110),
         (exportCamButton, 'left', 570),
         (autoUpdateCamButton, 'top', 160),
         (autoUpdateCamButton, 'left', 570),
         (refCamsList, 'top', 60),
         (refCamsList, 'left', 740),
         (replaceCamButton, 'top', 210),
         (replaceCamButton, 'left', 740),
         (removeCamButton, 'top', 210),
         (removeCamButton, 'left', 825),
         (loadCamButton, 'top', 160),
         (loadCamButton, 'left', 740),
         (unloadCamButton, 'top', 160),
         (unloadCamButton, 'left', 825)])
        animLabel = cmds.text(l='ANIMATION', fn='boldLabelFont')
        miscLabel = cmds.text(l='MISC', fn='boldLabelFont')
        importAnimButton = cmds.button(w=150, h=40, l='Import animation...', c=lambda *x: self.importAnimUI(), ann='Import animation to selected references.')
        exportAnimButton = cmds.button(w=150, h=40, l='Export animation...', c=lambda x: self.doAnimExport(shotTypeCtrl, shotListCtrl, sceneListCtrl), ann='Export animation from selected references.')
        autoRefCtrl = cmds.checkBox(l='Look for missing references (slow)', v=0, ann='Automatically look for missing references in the latest animation export and bring them into this scene before importing animation.')
        autoUpdateAnimButton = cmds.button(w=150, h=40, l='Auto update animation', bgc=[0.6, 0.7, 1.0], c=lambda *x: self.doAutoAnimImport(self.checkedShot, refsListCtrl, cmds.checkBox(autoRefCtrl, q=1, v=1)), ann='Automatically update all animation to latest version.')
        convertBtn = cmds.button(w=150, h=40, l='Convert to lighting scene', bgc=[1.0, 0.6, 0.7], c=lambda x: self.reconstruct(), ann='Reconstruct an existing animation scene into a lighting scene.')
        compareBtn = cmds.button(w=150, h=40, l='Compare references...', c=lambda x: self.doCompareRefs(), ann='Compare references and namespaces in your scene with those of another scene.')
        cmds.formLayout(sceneOpsForm, e=1, attachForm=[(animLabel, 'top', 280),
         (animLabel, 'left', 570),
         (importAnimButton, 'top', 300),
         (importAnimButton, 'left', 570),
         (exportAnimButton, 'top', 350),
         (exportAnimButton, 'left', 570),
         (autoUpdateAnimButton, 'top', 400),
         (autoUpdateAnimButton, 'left', 570),
         (convertBtn, 'top', 520),
         (convertBtn, 'left', 570),
         (miscLabel, 'top', 500),
         (miscLabel, 'left', 570),
         (autoRefCtrl, 'top', 445),
         (autoRefCtrl, 'left', 580),
         (compareBtn, 'top', 520),
         (compareBtn, 'left', 740)])
        cmds.tabLayout(tabs, e=1, tabLabel=[(shotListForm, 'SHOT/SCENE BROWSER'), (sceneOpsForm, 'SCENE CONTROLS')])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=930, h=700)
        self.popCamsList(refCamsList)

    def printSelList(self, ctrl, *args):
        assetList = []
        assetList = cmds.textScrollList(ctrl, q=1, si=1)
        listStr = 'SELECTED: ' + ', '.join(assetList)
        mel.eval('print \n"' + listStr + '"')

    def swapRefType(self, refCtrl, assetTypeCtrl, *args):
        if self.checkedShotType != 'lighting':
            cmds.error('You can only swap asset types in a lighting scene.')
        else:
            filenames = self.parseRefsList(refCtrl)
            assetType = cmds.optionMenu(assetTypeCtrl, q=1, v=1)
            if assetType == 'Standard':
                for file in filenames:
                    if '_CACHE' in file:
                        refNode = cmds.referenceQuery(file, rfn=1)
                        file = file.split('{')[0]
                        replacePath = '_'.join(file.split('_')[:-1]) + '.mb'
                        print 'replacePath: %s' % replacePath
                        cmds.file(replacePath, lr=refNode)

            else:
                for file in filenames:
                    if '_CACHE' not in file:
                        refNode = cmds.referenceQuery(file, rfn=1)
                        file = file.split('{')[0]
                        replacePath = os.path.splitext(file)[0] + '_CACHE.mb'
                        print 'replacePath: %s' % replacePath
                        cmds.file(replacePath, lr=refNode)

            self.popRefsList(refCtrl)

    def displayRefInfo(self, refCtrl, nsCtrl, filenameCtrl, nsButton, fileButton, assetTypeCtrl, assetTypeBtn, *args):
        filenames = self.parseRefsList(refCtrl)
        if len(filenames) > 1:
            cmds.textField(nsCtrl, e=1, en=0, tx='(multiple references selected)')
            cmds.textField(filenameCtrl, e=1, tx='(multiple files selected)')
            cmds.button(nsButton, e=1, en=0)
        else:
            filename = os.path.basename(filenames[0])
            namespace = cmds.file(filenames[0], q=1, ns=1)
            cmds.textField(nsCtrl, e=1, en=1, tx=namespace)
            cmds.textField(filenameCtrl, e=1, tx=filename)
            cmds.button(nsButton, e=1, en=1)
        if '_CACHE' in filenames[-1]:
            cmds.optionMenu(assetTypeCtrl, e=1, v='Cache')
        else:
            cmds.optionMenu(assetTypeCtrl, e=1, v='Standard')
        cmds.button(assetTypeBtn, e=1, en=1)
        if len(filenames) == 0:
            cmds.button(assetTypeBtn, e=1, en=0)
        cmds.button(fileButton, e=1, en=1)

    def popCamsList(self, camsListCtrl, *args):
        refCamFiles = [ f for f in cmds.file(q=1, r=1) if f.split('/')[-2] == 'cameras' ]
        camsList = []
        for file in refCamFiles:
            refNode = cmds.file(file, q=1, rfn=1)
            entry = os.path.basename(file) + ' (' + refNode + ')'
            if cmds.file(file, q=1, dr=1):
                entry = '*' + entry
            camsList.append(entry)

        camsList = natSort.natsorted(camsList)
        cmds.textScrollList(camsListCtrl, e=1, ra=1)
        for i in camsList:
            cmds.textScrollList(camsListCtrl, e=1, a=i)

    def parseCamsList(self, camsListCtrl, *args):
        selList = cmds.textScrollList(camsListCtrl, q=1, si=1)
        camRefsList = []
        try:
            for i in selList:
                camRN = i.split(' ')[-1].strip('()')
                camRefsList.append(camRN)

        except TypeError:
            cmds.error('Try selecting a camera first.')

        return camRefsList

    def popRefsList(self, refsListCtrl, filterType = '', filterBtn = '', *args):
        if filterBtn != '' and cmds.symbolButton(filterBtn, q=1, i=1) == 'filtersOn.png':
            filterType = ''
            cmds.symbolButton(filterBtn, e=1, i='filtersOff.png')
        loadedRefs = self.getAssets(1)
        unloadedRefs = self.getAssets(0)
        cmds.textScrollList(refsListCtrl, e=1, ra=1)
        loadedEntries = []
        unloadedEntries = []
        if filterType != '':
            cmds.symbolButton(filterBtn, e=1, i='filtersOn.png')
        for ref, filename in loadedRefs.iteritems():
            namespace = cmds.file(filename, q=1, ns=1)
            refEntry = namespace + ':  (' + os.path.basename(filename) + ')'
            if filterType != '':
                if filterType in refEntry:
                    loadedEntries.append(refEntry)
            else:
                loadedEntries.append(refEntry)

        for ref, filename in unloadedRefs.iteritems():
            namespace = cmds.file(filename, q=1, ns=1)
            refEntry = '*' + namespace + ':  (' + os.path.basename(filename) + ')'
            if filterType != '':
                if filterType in refEntry:
                    unloadedEntries.append(refEntry)
            else:
                unloadedEntries.append(refEntry)

        loadedEntries = natSort.natsorted(loadedEntries)
        unloadedEntries = natSort.natsorted(unloadedEntries)
        for i in loadedEntries:
            cmds.textScrollList(refsListCtrl, e=1, a=i)

        for i in unloadedEntries:
            cmds.textScrollList(refsListCtrl, e=1, a=i)

    def parseRefsList(self, refsListCtrl, *args):
        filenames = []
        refsList = cmds.textScrollList(refsListCtrl, q=1, si=1)
        if not refsList:
            cmds.error('Select at least one reference to modify.')
            return False
        for ref in refsList:
            filename = ref.strip().split(' ')[-1].strip('()')
            assetName = os.path.splitext(filename.split('{')[0])[0]
            filePath = os.path.join(self.M.assetsDir, assetName, filename)
            if 'CACHE' in assetName.split('_')[-1]:
                print 'parseRefsList detected a _CACHE file'
                assetName = '_'.join(assetName.split('_')[:-1])
                filePath = os.path.join(self.M.assetsDir, assetName, filename)
                print 'interpreting filePath as %s' % filePath
            filenames.append(filePath)

        return filenames

    def popAssetList(self, assetListCtrl, filterName = '', filterBtn = '', *args):
        if filterBtn != '' and cmds.symbolButton(filterBtn, q=1, i=1) == 'filtersOn.png':
            filterName = ''
            cmds.symbolButton(filterBtn, e=1, i='filtersOff.png')
        assetsList = [ f for f in os.listdir(self.M.assetsDir) if f != '_TRASH' and os.path.exists(os.path.join(self.M.assetsDir, f, '_pipeline')) ]
        if filterName != '':
            assetsList = [ f for f in assetsList if filterName in f ]
            cmds.symbolButton(filterBtn, e=1, i='filtersOn.png')
        cmds.textScrollList(assetListCtrl, e=1, ra=1)
        assetsList = natSort.natsorted(assetsList)
        for asset in assetsList:
            cmds.textScrollList(assetListCtrl, e=1, a=asset)

    def isValidShot(self, shot, *args):
        shotDir = os.path.join(self.M.scenesDir, shot)
        if not os.path.exists(shotDir):
            return False
        topdirs = os.listdir(shotDir)
        if 'animation' not in topdirs:
            return False
        if 'lighting' not in topdirs:
            return False
        animDir = os.path.join(shotDir, 'animation')
        print animDir
        lightDir = os.path.join(shotDir, 'lighting')
        animDirSubdirs = os.listdir(animDir)
        lightDirSubdirs = os.listdir(lightDir)
        if '_pipeline' not in animDirSubdirs:
            return False
        if '_scrap' not in animDirSubdirs:
            return False
        if '_pipeline' not in lightDirSubdirs:
            return False
        if '_scrap' not in lightDirSubdirs:
            return False
        return True

    def popShotsList(self, shotListCtrl, *args):
        selIndex = cmds.textScrollList(shotListCtrl, q=1, si=1)
        shotsList = [ f for f in os.listdir(self.M.scenesDir) if os.path.isdir(os.path.join(self.M.scenesDir, f)) == 1 and f != '_TRASH' ]
        cmds.textScrollList(shotListCtrl, e=1, ra=1)
        for shot in natSort.natsorted(shotsList):
            if self.isValidShot(shot):
                cmds.textScrollList(shotListCtrl, e=1, a=shot)

        try:
            if len(selIndex) > 0:
                cmds.textScrollList(shotListCtrl, e=1, si=selIndex[0])
        except:
            pass

    def popScenesList(self, shotTypeCtrl, shotListCtrl, sceneListCtrl, *args):
        shotType = cmds.textScrollList(shotTypeCtrl, q=1, si=1)[0]
        shot = ''
        try:
            shot = cmds.textScrollList(shotListCtrl, q=1, si=1)[0]
        except TypeError:
            shot = ''

        selIndex = cmds.textScrollList(sceneListCtrl, q=1, si=1)
        scenesPath = os.path.join(self.M.scenesDir, shot, shotType)
        scenesList = []
        if os.path.exists(scenesPath):
            scenesList = [ f for f in os.listdir(scenesPath) if os.path.splitext(f)[-1] == '.ma' or os.path.splitext(f)[-1] == '.mb' ]
        cmds.textScrollList(sceneListCtrl, e=1, ra=1)
        for scene in natSort.natsorted(scenesList):
            if self.isValidScene(scene):
                cmds.textScrollList(sceneListCtrl, e=1, a=scene)

        try:
            if len(selIndex) > 0 and selIndex[0] in cmds.textScrollList(sceneListCtrl, q=1, ai=1):
                cmds.textScrollList(sceneListCtrl, e=1, si=selIndex[0])
        except:
            pass

    def selectScene(self, shotTypeCtrl, shotListCtrl, sceneListCtrl, screenCtrl, modifiedCtrl, checkoutAlert, versionNotes, *args):
        shotType = cmds.textScrollList(shotTypeCtrl, q=1, si=1)[0]
        shot = cmds.textScrollList(shotListCtrl, q=1, si=1)[0]
        scene = cmds.textScrollList(sceneListCtrl, q=1, si=1)[0]
        pipelinePath = os.path.join(self.M.scenesDir, shot, shotType, '_pipeline')
        scenePath = os.path.join(self.M.scenesDir, shot, shotType, scene)
        screenPath = os.path.join(pipelinePath, scene) + '.jpg'
        notesPath = os.path.join(pipelinePath, scene) + '.txt'
        if os.path.exists(screenPath):
            cmds.image(screenCtrl, e=1, vis=1, image=screenPath)
        else:
            print 'screenshot not found: %s' % screenPath
            cmds.image(screenCtrl, e=1, vis=0)
        if os.path.exists(notesPath):
            notesLoad = open(notesPath, 'r')
            notesText = pickle.load(notesLoad)
            cmds.scrollField(versionNotes, e=1, tx='Version notes: \n%s' % notesText)
        else:
            cmds.scrollField(versionNotes, e=1, tx='No version notes found')
        checkFile = os.path.join(pipelinePath, 'checkout.txt')
        initials = ''
        if os.path.exists(checkFile):
            loadFile = open(checkFile, 'r')
            initials = pickle.load(loadFile)
            loadFile.close()
        if initials == '':
            cmds.text(checkoutAlert, e=1, l='')
        else:
            labelString = '*** CHECKED OUT BY %s ***' % initials
            cmds.text(checkoutAlert, e=1, l=labelString)
        lastUser = os.path.splitext(scene.split('_')[-1])[0]
        seconds = os.path.getmtime(scenePath)
        lastMod = time.strftime('%Y-%m-%d %H:%M', time.localtime(seconds))
        timestampString = 'Last modified: %s by %s' % (lastMod, lastUser)
        cmds.text(modifiedCtrl, e=1, l=timestampString)

    def increment(self, control, increment, *args):
        num = cmds.textField(control, q=1, tx=1)
        newNum = str(int(num) + increment).zfill(3)
        if int(newNum) < 0:
            newNum = '000'
        cmds.textField(control, e=1, tx=newNum)

    def saveSceneUI(self, shotTypeCtrl = '', shotCtrl = '', scenesCtrl = '', *args):
        windowName = 'saveSceneWindow'
        windowTitle = '}MUSTACHE{ - Save scene...'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        layout = cmds.formLayout()
        topLabelString = 'Updating %s scene for shot %s' % (self.checkedShotType.upper(), self.checkedShot)
        topLabel = cmds.text(l=topLabelString, fn='boldLabelFont')
        camLabel = cmds.text(l='CAMERA')
        animLabel = cmds.text(l='ANIMATION')
        lightLabel = cmds.text(l='LIGHTING')
        if self.lastImportVersion != '':
            if int(self.lastImportVersion) > int(self.animVersion):
                self.animVersion = self.lastImportVersion
        camText = cmds.textField(w=40, tx=self.camVersion)
        animText = cmds.textField(w=40, tx=self.animVersion)
        lightText = cmds.textField(w=40, tx=self.lightVersion)
        cmds.formLayout(layout, e=1, attachForm=[(topLabel, 'top', 5),
         (topLabel, 'left', 5),
         (camLabel, 'top', 30),
         (camLabel, 'left', 5),
         (animLabel, 'top', 30),
         (animLabel, 'left', 75),
         (lightLabel, 'top', 30),
         (lightLabel, 'left', 145),
         (camText, 'left', 5),
         (camText, 'top', 45),
         (animText, 'left', 75),
         (animText, 'top', 45),
         (lightText, 'top', 45),
         (lightText, 'left', 145)])
        camPlus = cmds.button(l='+', w=20, h=20, c=lambda *x: self.increment(camText, 1))
        camMinus = cmds.button(l='-', w=20, h=20, c=lambda *x: self.increment(camText, -1))
        animPlus = cmds.button(l='+', w=20, h=20, c=lambda *x: self.increment(animText, 1))
        animMinus = cmds.button(l='-', w=20, h=20, c=lambda *x: self.increment(animText, -1))
        lightPlus = cmds.button(l='+', w=20, h=20, c=lambda *x: self.increment(lightText, 1))
        lightMinus = cmds.button(l='-', w=20, h=20, c=lambda *x: self.increment(lightText, -1))
        cmds.formLayout(layout, e=1, attachForm=[(camPlus, 'top', 70),
         (camPlus, 'left', 5),
         (camMinus, 'top', 70),
         (camMinus, 'left', 25),
         (animPlus, 'top', 70),
         (animPlus, 'left', 75),
         (animMinus, 'top', 70),
         (animMinus, 'left', 95),
         (lightPlus, 'top', 70),
         (lightPlus, 'left', 145),
         (lightMinus, 'top', 70),
         (lightMinus, 'left', 165)])
        cam, anim, light = self.getHighestVersions(self.checkedShot)
        if self.checkedShotType == 'lighting':
            cmds.textField(lightText, e=1, tx=light)
            self.increment(lightText, 1)
        if self.checkedShotType == 'animation':
            cmds.textField(animText, e=1, tx=anim)
            self.increment(animText, 1)
        notesLabel = cmds.text(l="anything you'd like to say about this version?")
        notesField = cmds.scrollField(w=280, h=100, ww=1)
        saveBtn = cmds.button(l='save', w=100, h=50, bgc=[0.6, 0.7, 1.0], c=lambda *x: self.doSaveScene(cmds.textField(camText, q=1, tx=1), cmds.textField(animText, q=1, tx=1), cmds.textField(lightText, q=1, tx=1), cmds.scrollField(notesField, q=1, tx=1), cmds.checkBox(releaseCheck, q=1, v=1), window, shotTypeCtrl, shotCtrl, scenesCtrl))
        cancelBtn = cmds.button(l='cancel', w=100, h=50, c=lambda x: cmds.deleteUI(window))
        releaseCheck = cmds.checkBox(l='release shot after save?', v=0)
        cmds.formLayout(layout, e=1, attachForm=[(notesLabel, 'top', 100),
         (notesLabel, 'left', 5),
         (notesField, 'top', 115),
         (notesField, 'left', 5),
         (saveBtn, 'top', 260),
         (saveBtn, 'left', 5),
         (cancelBtn, 'top', 260),
         (cancelBtn, 'left', 120),
         (releaseCheck, 'left', 5),
         (releaseCheck, 'top', 235)])
        if self.checkedShotType == 'animation':
            cmds.button(lightPlus, e=1, en=0)
            cmds.button(lightMinus, e=1, en=0)
            cmds.textField(lightText, e=1, en=0)
        cmds.showWindow(window)
        cmds.window(window, e=1, w=300, h=320)

    def renameShot(self, shotTypeCtrl, shotListCtrl, sceneListCtrl, *args):
        shot = ''
        try:
            shot = cmds.textScrollList(shotListCtrl, q=1, si=1)[0]
        except TypeError:
            cmds.error('Please select a shot to rename.')

        confirm = cmds.confirmDialog(t='Rename shot?', ma='left', icon='critical', message='Renaming this shot could cause a currently rendering shot to fail, as well as pissing off others working on this shot. Are you sure you want to rename ' + shot + '?', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
        if confirm == 'no':
            return
        prompt = cmds.promptDialog(t='Rename shot...', ma='left', message='Please enter a new name for ' + shot + ':', button=['ok', 'cancel'], defaultButton='cancel', cancelButton='cancel', dismissString='cancel')
        if prompt == 'cancel':
            return
        name = cmds.promptDialog(q=1, tx=1)
        print 'validating shot name: %s' % name
        rePattern = '^[a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9_]$'
        search = re.findall(rePattern, name)
        if len(search) == 0:
            cmds.error('Invalid shot name: %s' % name)
            return False
        if os.path.exists(os.path.join(self.M.scenesDir, name)):
            cmds.error('A shot with the name ' + name + ' already exists. Aborting.')
        for root, dir, files in os.walk(os.path.join(self.M.scenesDir, shot)):
            for f in files:
                newFile = f.replace(shot, name)
                oldPath = os.path.join(root, f)
                os.rename(oldPath, os.path.join(root, newFile))

        oldPath = os.path.join(self.M.scenesDir, shot)
        newPath = oldPath.replace(shot, name)
        os.rename(oldPath, newPath)
        self.popShotsList(shotListCtrl)
        self.popScenesList(shotTypeCtrl, shotListCtrl, sceneListCtrl)
        cmds.warning('Renamed shot ' + shot + ' to ' + name)

    def doSaveScene(self, cam, anim, light, notes, release, saveUI, shotTypeCtrl = '', shotListCtrl = '', sceneListCtrl = '', *args):
        filename = self.checkedShot + '_C' + cam + '_A' + anim + '_L' + light + '_' + self.M.user + '.mb'
        writePath = os.path.join(self.M.scenesDir, self.checkedShot, self.checkedShotType, filename)
        if os.path.exists(writePath):
            messageString = 'There is already a scene with the name %s. Do you want to overwrite it?' % filename
            overwrite = cmds.confirmDialog(title='File already exists!', message=messageString, icon='warning', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if overwrite == 'no':
                return
        savedFile = self.updateScene(cam, anim, light, notes, release, '.mb', saveUI)
        if shotTypeCtrl != '':
            self.popScenesList(shotTypeCtrl, shotListCtrl, sceneListCtrl)

    def doNewShot(self, shotListCtrl, *args):
        windowName = 'newShotUI'
        windowTitle = 'Create new shot'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, t=windowTitle)
        form = cmds.formLayout()
        labelTxt = cmds.text(l='Enter a name for the new shot (e.g. SH010):')
        shotNameCtrl = cmds.textField(w=130)
        okBtn = cmds.button(l='OK', w=100, h=50, c=lambda *x: self.newShot(cmds.textField(shotNameCtrl, q=1, tx=1), '.mb', True, window, shotListCtrl))
        cancelBtn = cmds.button(l='Cancel', w=100, h=50, c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(labelTxt, 'top', 10),
         (labelTxt, 'left', 10),
         (shotNameCtrl, 'top', 30),
         (shotNameCtrl, 'left', 10),
         (okBtn, 'top', 60),
         (okBtn, 'left', 10),
         (cancelBtn, 'top', 60),
         (cancelBtn, 'left', 120)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=270, h=115)

    def doCloneShot(self, shotListCtrl, *args):
        try:
            selShot = cmds.textScrollList(shotListCtrl, q=1, si=1)[0]
        except TypeError:
            cmds.error('Please select a shot to clone.')

        windowName = 'newShotUI'
        windowTitle = 'Clone existing shot'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, t=windowTitle)
        form = cmds.formLayout()
        labelTxt = cmds.text(l='Enter a name for the new shot (e.g. SH010):')
        cloneMessage = 'CLONING SHOT %s' % selShot
        cloneTxt = cmds.text(l=cloneMessage, fn='boldLabelFont')
        shotNameCtrl = cmds.textField(w=130)
        okBtn = cmds.button(l='OK', w=100, h=50, c=lambda *x: self.cloneShot(cmds.textField(shotNameCtrl, q=1, tx=1), shotListCtrl, window))
        cancelBtn = cmds.button(l='Cancel', w=100, h=50, c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(labelTxt, 'top', 40),
         (labelTxt, 'left', 10),
         (shotNameCtrl, 'top', 60),
         (shotNameCtrl, 'left', 10),
         (okBtn, 'top', 90),
         (okBtn, 'left', 10),
         (cancelBtn, 'top', 90),
         (cancelBtn, 'left', 120),
         (cloneTxt, 'top', 10),
         (cloneTxt, 'left', 10)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=270, h=145)

    def doReplaceRef(self, refsListCtrl, *args):
        windowName = 'replaceRefsWindow'
        windowTitle = 'Replace references'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        assetListCtrl = cmds.textScrollList(w=160, h=400, ams=0, fn='boldLabelFont')
        assetListLabel = cmds.text('Pick a replacement asset...')
        goBtn = cmds.button(w=75, h=35, bgc=[0.6, 0.7, 1.0], l='OK', c=lambda *x: self.replaceRef(refsListCtrl, cmds.textScrollList(assetListCtrl, q=1, si=1)[0], window))
        cancelBtn = cmds.button(w=75, h=35, l='Cancel', c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(assetListLabel, 'top', 5),
         (assetListLabel, 'left', 5),
         (assetListCtrl, 'top', 25),
         (assetListCtrl, 'left', 5),
         (goBtn, 'top', 430),
         (goBtn, 'left', 5),
         (cancelBtn, 'top', 430),
         (cancelBtn, 'left', 90)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=180, h=480)
        assetList = [ f for f in os.listdir(self.M.assetsDir) if os.path.isdir(os.path.join(self.M.assetsDir, f)) ]
        assetListSort = natSort.natsorted(assetList)
        for asset in assetListSort:
            cmds.textScrollList(assetListCtrl, e=1, a=asset)

    def doRemoveRef(self, refsListCtrl, *args):
        sel = 0
        try:
            sel = len(cmds.textScrollList(refsListCtrl, q=1, si=1))
        except TypeError:
            cmds.error('Select one or more references to remove.')

        confirm = ''
        if sel > 1:
            confirm = cmds.confirmDialog(title='Remove references?', icon='warning', message="You can't undo this. Are you sure you want to remove these references?", button=['yes', 'no'], cancelButton='no', defaultButton='no', dismissString='no')
        else:
            confirm = cmds.confirmDialog(title='Remove reference?', icon='warning', message="You can't undo this. Are you sure you want to remove this reference?", button=['yes', 'no'], cancelButton='no', defaultButton='no', dismissString='no')
        if confirm == 'no':
            return
        self.removeRef(refsListCtrl)

    def doCreateRef(self, assetListCtrl, refsListCtrl, *args):
        filesToAdd = cmds.textScrollList(assetListCtrl, q=1, si=1)
        try:
            sel = len(filesToAdd)
        except TypeError:
            cmds.error('You need to select assets to reference!')

        for file in filesToAdd:
            fullPath = os.path.join(self.M.assetsDir, file, file + '.mb')
            self.createRef(fullPath)

        self.popRefsList(refsListCtrl)

    def doCleanupRef(self, refsListCtrl, shadingOnly, *args):
        confirm = cmds.confirmDialog(title='Remove reference edits?', message="You can't undo this. Are you sure you want to clean up these references?", button=['yes', 'no'], cancelButton='no', defaultButton='no', dismissString='no')
        if confirm == 'no':
            return
        files = self.parseRefsList(refsListCtrl)
        for file in files:
            refNode = cmds.file(file, q=1, rfn=1)
            self.cleanupRef(refNode, refsListCtrl, shadingOnly)

    def getCameraUI(self, refCamsList, *args):
        windowName = 'getCameraWindow'
        windowTitle = 'Select camera to reference...'
        if cmds.window(windowName, q=1, exists=1) == True:
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        shotsListCtrl = cmds.textScrollList(w=100, h=150, ams=0, sc=lambda *x: self.getCameraShotSelect(cmds.textScrollList(shotsListCtrl, q=1, si=1)[0], camsListCtrl))
        self.popShotsList(shotsListCtrl)
        cmds.textScrollList(shotsListCtrl, e=1, si=self.checkedShot)
        camsListCtrl = cmds.textScrollList(w=180, h=150, ams=1)
        try:
            self.getCameraShotSelect(cmds.textScrollList(shotsListCtrl, q=1, si=1)[0], camsListCtrl)
        except TypeError:
            pass

        goBtn = cmds.button(w=75, h=40, l='get cameras', bgc=[0.6, 0.7, 1.0], c=lambda *x: self.doGetCamera(shotsListCtrl, camsListCtrl, refCamsList))
        cancelBtn = cmds.button(w=75, h=40, l='done', c=lambda x: cmds.deleteUI(window))
        camsLabel = cmds.text(l='CAMERAS', fn='boldLabelFont')
        shotsLabel = cmds.text(l='SHOTS', fn='boldLabelFont')
        cmds.formLayout(form, e=1, attachForm=[(shotsListCtrl, 'top', 20),
         (shotsListCtrl, 'left', 5),
         (camsListCtrl, 'top', 20),
         (camsListCtrl, 'left', 115),
         (goBtn, 'top', 180),
         (goBtn, 'left', 115),
         (cancelBtn, 'top', 180),
         (cancelBtn, 'left', 210),
         (camsLabel, 'top', 5),
         (camsLabel, 'left', 115),
         (shotsLabel, 'top', 5),
         (shotsLabel, 'left', 5)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=300, h=230)

    def getCameraShotSelect(self, shot, camsListCtrl, *args):
        camsPath = os.path.join(self.M.scenesDir, shot, 'cameras')
        cmds.textScrollList(camsListCtrl, e=1, ra=1)
        if os.path.exists(camsPath):
            camsList = self.getExportedCameras(shot)
            for cam in camsList:
                cmds.textScrollList(camsListCtrl, e=1, a=cam)

    def doGetCamera(self, shotsListCtrl, camsListCtrl, refCamsList, *args):
        camsList = cmds.textScrollList(camsListCtrl, q=1, si=1)
        shot = cmds.textScrollList(shotsListCtrl, q=1, si=1)[0]
        try:
            len(camsList)
        except TypeError:
            cmds.error('You need to select at least one camera to reference.')

        for cam in camsList:
            camPath = os.path.join(self.M.scenesDir, shot, 'cameras', cam)
            self.refCamera('', camPath)

        self.popCamsList(refCamsList)

    def replaceCameraUI(self, oldCam, refCamsList, *args):
        windowName = 'replaceCameraWindow'
        windowTitle = 'Select replacement camera...'
        if cmds.window(windowName, q=1, exists=1) == True:
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        shotsListCtrl = cmds.textScrollList(w=100, h=150, ams=0, sc=lambda *x: self.getCameraShotSelect(cmds.textScrollList(shotsListCtrl, q=1, si=1)[0], camsListCtrl))
        self.popShotsList(shotsListCtrl)
        cmds.textScrollList(shotsListCtrl, e=1, si=self.checkedShot)
        camsListCtrl = cmds.textScrollList(w=180, h=150, ams=0)
        self.getCameraShotSelect(cmds.textScrollList(shotsListCtrl, q=1, si=1)[0], camsListCtrl)
        goBtn = cmds.button(w=75, h=40, l='replace', bgc=[0.6, 0.7, 1.0], c=lambda *x: self.doReplaceCamera(oldCam, shotsListCtrl, camsListCtrl, window, refCamsList))
        cancelBtn = cmds.button(w=75, h=40, l='done', c=lambda x: cmds.deleteUI(window))
        camsLabel = cmds.text(l='CAMERAS', fn='boldLabelFont')
        shotsLabel = cmds.text(l='SHOTS', fn='boldLabelFont')
        cmds.formLayout(form, e=1, attachForm=[(shotsListCtrl, 'top', 20),
         (shotsListCtrl, 'left', 5),
         (camsListCtrl, 'top', 20),
         (camsListCtrl, 'left', 115),
         (goBtn, 'top', 180),
         (goBtn, 'left', 115),
         (cancelBtn, 'top', 180),
         (cancelBtn, 'left', 210),
         (camsLabel, 'top', 5),
         (camsLabel, 'left', 115),
         (shotsLabel, 'top', 5),
         (shotsLabel, 'left', 5)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=300, h=230)

    def doReplaceCamera(self, oldCam, shotsListCtrl, camsListCtrl, replaceUI, refCamsList, *args):
        oldCamRN = oldCam.split(' ')[-1].strip('()')
        shot = cmds.textScrollList(shotsListCtrl, q=1, si=1)[0]
        filename = cmds.textScrollList(camsListCtrl, q=1, si=1)[0]
        newCamPath = os.path.join(self.M.scenesDir, shot, 'cameras', filename)
        self.refCamera(oldCamRN, newCamPath)
        self.popCamsList(refCamsList)
        cmds.deleteUI(replaceUI)

    def exportCameraUI(self, *args):
        windowName = 'exportCamsUI'
        windowTitle = 'Export cameras...'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, t=windowTitle)
        form = cmds.formLayout()
        camsListCtrl = cmds.textScrollList(w=210, h=300, ams=1, ann='Select the cameras you want to export.')
        camsListLabel = cmds.text(l='SCENE CAMERAS', fn='boldLabelFont')
        exportBtn = cmds.button(l='Export', w=100, h=40, bgc=[0.6, 0.7, 1.0], c=lambda *x: self.exportCams(cmds.textScrollList(camsListCtrl, q=1, si=1), float(cmds.textField(startCtrl, q=1, tx=1)), float(cmds.textField(endCtrl, q=1, tx=1)), window), ann='Bake and export selected cameras.')
        cancelBtn = cmds.button(l='Cancel', w=100, h=40, c=lambda x: cmds.deleteUI(window))
        startCtrl = cmds.textField(w=50, tx=str(cmds.playbackOptions(q=1, min=1)))
        endCtrl = cmds.textField(w=50, tx=str(cmds.playbackOptions(q=1, max=1)))
        startLbl = cmds.text(l='Start:', fn='boldLabelFont')
        endLbl = cmds.text(l='End:', fn='boldLabelFont')
        cmds.formLayout(form, e=1, attachForm=[(camsListLabel, 'top', 5),
         (camsListLabel, 'left', 5),
         (camsListCtrl, 'top', 25),
         (camsListCtrl, 'left', 5),
         (exportBtn, 'top', 400),
         (exportBtn, 'left', 5),
         (cancelBtn, 'left', 115),
         (cancelBtn, 'top', 400),
         (startCtrl, 'left', 55),
         (startCtrl, 'top', 350),
         (endCtrl, 'left', 165),
         (endCtrl, 'top', 350),
         (startLbl, 'left', 5),
         (startLbl, 'top', 353),
         (endLbl, 'left', 115),
         (endLbl, 'top', 353)])
        cmds.showWindow(window)
        cmds.window(window, e=1, w=220, h=450)
        dumbCams = ['perspShape',
         'topShape',
         'frontShape',
         'sideShape']
        allCams = [ a for a in cmds.ls(type='camera') if a not in dumbCams ]
        for cam in allCams:
            cmds.textScrollList(camsListCtrl, e=1, a=cam)

    def doAnimExport(self, shotTypeCtrl, shotCtrl, scenesCtrl, *args):
        if cmds.file(q=1, mf=1) == 1:
            confirm = cmds.confirmDialog(title='Unsaved changes!', message='Baking and exporting animation will break your scene. You should save first. Want to open the save dialog?', button=['yes', 'no'], dismissString='no', cancelButton='no', defaultButton='no')
            if confirm == 'no':
                self.exportAnimUI()
            else:
                self.saveSceneUI(shotTypeCtrl, shotCtrl, scenesCtrl)
        else:
            self.exportAnimUI()

    def doAutoAnimImport(self, impShot, refsListCtrl = '', getRefs = 0, *args):
        exports = []
        try:
            exports = [ f for f in os.listdir(os.path.join(cmds.workspace(q=1, fn=1), self.M.animExportFolder)) if os.path.isdir(os.path.join(cmds.workspace(q=1, fn=1), self.M.animExportFolder, f)) ]
        except (TypeError, IndexError):
            cmds.error('No animation is exported for this shot!')

        if len(exports) == 0:
            cmds.error('No animation is exported for this shot!')
        highAnim = '000'
        highFolder = ''
        for folder in exports:
            print 'folder: %s' % folder
            try:
                shot, cam, anim, light, owner = self.parseSceneName(folder)
                if int(anim) > int(highAnim) and shot == impShot:
                    highAnim = anim
                    highFolder = folder
            except:
                continue

        if highFolder == '':
            cmds.error('No animation is exported for this shot!')
        print 'found highest animation version: %s' % highFolder
        if getRefs == 1:
            fileToLoad = ''
            shot, cam, anim, light, owner = self.parseSceneName(highFolder)
            searchPath = os.path.join(self.M.scenesDir, shot, 'animation')
            filename = highFolder + '.mb'
            print 'looking for file: ' + filename
            if filename in os.listdir(searchPath):
                fileToLoad = os.path.join(searchPath, filename)
            else:
                searchPath = os.path.join(self.M.scenesDir, shot, 'lighting')
                if filename in os.listdir(searchPath):
                    fileToLoad = os.path.join(searchPath, filename)
                else:
                    cmds.error('Could not find scene %s in either animation or lighting folders!') % filename
            fileToLoad = fileToLoad.replace('\\', '/')
            subp = subprocess.Popen(os.path.join(self.M.mayaDir, 'mayapy.exe') + ' ' + os.path.join(self.M.scriptsDir, '..', 'python', 'm_analyzeScene.py') + ' ' + fileToLoad, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = subp.communicate()
            output = stdout.split('M_ANALYZESCENE_DUMP')[-1]
            refsDict = pickle.loads(output)
            localNamespaces = [ cmds.file(f, q=1, ns=1) for f in cmds.file(q=1, r=1) ]
            for file, namespace in refsDict.iteritems():
                namespace = namespace.strip('\r')
                if namespace not in localNamespaces:
                    print 'creating missing reference: %s' % namespace
                    cacheFile = os.path.join(self.M.project, self.M.animExportFolder, '_GEOCACHE', highFolder, namespace + '.xml')
                    if os.path.exists(cacheFile):
                        cacheAsset = os.path.splitext(file)[0] + '_CACHE.mb'
                        if os.path.exists(cacheAsset):
                            newRef = cmds.file(cacheAsset, r=1, type='mayaBinary', ns=namespace, shd='renderLayersByName')
                            print 'filename: %s' % cacheAsset
                        else:
                            newRef = cmds.file(file, r=1, type='mayaBinary', ns=namespace, shd='renderLayersByName')
                            print 'filename: %s' % file
                    else:
                        newRef = cmds.file(file, r=1, type='mayaBinary', ns=namespace, shd='renderLayersByName')
                        print 'filename: %s' % file

        self.animVersion = highAnim
        namespList = self.getActiveNamespaces()
        self.massAnimImport(namespList, os.path.join(cmds.workspace(q=1, fn=1), self.M.animExportFolder, highFolder))
        if refsListCtrl != '':
            self.popRefsList(refsListCtrl)

    def copyAnim(self, filename, objs, *args):
        if len(objs) < 1:
            return False
        unk = cmds.ls(type='unknown')
        if len(unk) > 0:
            cmds.error('You have unknown nodes in your scene. Run the cleanup utility before exporting animation.')
        if cmds.objExists('animXferTEMP'):
            cmds.delete('animXferTEMP')
        cmds.createNode('transform', n='animXferTEMP')
        for obj in objs:
            attrs = []
            attrs = cmds.listAttr(obj, k=1)
            startTime = -100000
            endTime = 100000
            try:
                for attr in attrs:
                    numkeys = cmds.keyframe(obj, q=1, at=attr, kc=1)
                    if numkeys > 0:
                        cmds.addAttr('animXferTEMP', at='double', longName=obj.replace(':', '___') + '_ANIMXFER_' + attr)
                        cmds.copyKey(obj, t=(startTime, endTime), at=attr)
                        cmds.pasteKey('animXferTEMP', option='replaceCompletely', at=obj.replace(':', '___') + '_ANIMXFER_' + attr)

            except TypeError:
                print 'Object %s has no attributes?' % obj

        cmds.select('animXferTEMP')
        if filename.split('.')[-1] != '.ma':
            filename = filename + '.ma'
        f = cmds.file(filename, es=1, chn=1, type='mayaAscii', force=1)
        print 'wrote animation to file: %s' % f
        cmds.delete('animXferTEMP')

    def pasteAnim(self, filename, namespace = '', *args):
        try:
            self.removeAnimCurves(namespace)
        except:
            cmds.warning('Error removing anim curves from namespace: ' + namespace)

        errorsList = []
        if cmds.objExists('animXferTEMP'):
            cmds.delete('animXferTEMP')
        try:
            cmds.file(filename, i=1)
            if not cmds.objExists('animXferTEMP'):
                cmds.error('animXferTEMP not found in imported file. aborting.')
        except RuntimeError:
            errString = 'Could not find file %s' % filename
            cmds.warning(errString)
            errorsList.append(errString)
            return errorsList

        attrs = [ a for a in cmds.listAttr('animXferTEMP') if a.find('_ANIMXFER_') != -1 ]
        startTime = -100000
        endTime = 100000
        for a in attrs:
            ns = ''
            obj = ''
            if a.find('___') != -1:
                if namespace != '':
                    ns = namespace
                else:
                    ns = a.split('___')[0]
                obj = a.split('___')[1].split('_ANIMXFER_')[0]
            else:
                obj = a.split('_ANIMXFER_')[0]
            chan = a.split('_ANIMXFER_')[1]
            fullName = ''
            if ns != '':
                fullName = ns + ':' + obj
            else:
                fullName = obj
            numkeys = cmds.keyframe('animXferTEMP', q=1, at=a, t=(startTime, endTime), kc=1)
            if numkeys > 0:
                cmds.copyKey('animXferTEMP', t=(startTime, endTime), at=a)
                try:
                    if cmds.getAttr(fullName + '.' + chan, lock=1) == 1:
                        cmds.setAttr(fullName + '.' + chan, lock=0)
                    cmds.pasteKey(fullName, option='replaceCompletely', at=chan)
                    print 'pasted %d keys to %s.%s' % (numkeys, fullName, chan)
                except:
                    errorString = "Couldn't paste keys to %s.%s" % (fullName, chan)
                    cmds.warning(errorString)
                    errorsList.append(errorString)

        animCurveTypes = ['animCurveTL',
         'animCurveTA',
         'animCurveTT',
         'animCurveTU',
         'animCurveUL',
         'animCurveUA',
         'animCurveUT',
         'animCurveUU']
        tempcurves = [ f for f in cmds.ls(type=animCurveTypes) if 'animXferTEMP' in f ]
        if tempcurves:
            for i in tempcurves:
                cmds.delete(i)

        if len(errorsList) > 0:
            return errorsList
        else:
            return True

    def bakeKeys(self, objs, start, end, windowOff = 1, smartBake = 0, *args):
        print 'baking objects: %s' % objs
        if windowOff == 1:
            mel.eval('setNamedPanelLayout "Single Perspective View"')
            perspPane = cmds.getPanel(vis=1)
            cmds.scriptedPanel('graphEditor1', e=1, rp=perspPane[0])
        cmds.file(rts=1)
        cmds.select(objs)
        start = float(start)
        end = float(end)
        cmds.bakeResults(simulation=1, cp=0, s=0, sb=1.0, t=(start, end))

    def getControls(self, namespace, *args):
        if not cmds.objExists(namespace + ':RIGset') or not cmds.sets(namespace + ':RIGset', q=1):
            allCurves = cmds.ls(type='nurbsCurve')
            controlCurveShapes = [ c for c in allCurves if c.split(':')[0] == namespace and cmds.getAttr(c + '.overrideDisplayType') == 0 ]
            controlCurveXforms = []
            for i in controlCurveShapes:
                try:
                    parent = cmds.listRelatives(i, p=1)[0]
                    if cmds.objectType(parent, isType='transform'):
                        controlCurveXforms.append(parent)
                except:
                    pass

            xFormsNoDupes = list(set(controlCurveXforms))
            return xFormsNoDupes
        else:
            controls = cmds.sets(namespace + ':RIGset', q=1)
            return controls

    def getActiveNamespaces(self, *args):
        refFiles = [ f for f in cmds.file(q=1, r=1) if not cmds.file(f, q=1, dr=1) == 1 ]
        namespaces = []
        for file in refFiles:
            if file.split('/')[-2] != 'cameras':
                ns = cmds.file(file, q=1, ns=1)
                namespaces.append(ns)

        namespaces = natSort.natsorted(namespaces)
        return namespaces

    def massAnimExport(self, namespaces, s, e, windowOff = 1, smartBake = 0, cacheSets = 1, *args):
        allControls = []
        camXForms = []
        for n in namespaces:
            p = self.getControls(n)
            if p:
                allControls.extend(self.getControls(n))

        self.bakeKeys(allControls, s, e, windowOff, smartBake)
        dataPath = os.path.join(cmds.workspace(q=1, fn=1), self.M.animExportFolder, os.path.splitext(cmds.file(q=1, sn=1, shn=1))[0])
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)
        for n in namespaces:
            controls = self.getControls(n)
            if controls:
                self.copyAnim(os.path.join(dataPath, n), controls)

        if cacheSets:
            for n in namespaces:
                testNode = n + ':CACHEset'
                if cmds.objExists(testNode):
                    print 'found CACHEset for namespace %s' % n
                    assetFile = cmds.referenceQuery(testNode, f=1, wcn=1)
                    asset = os.path.splitext(os.path.basename(assetFile))[0]
                    print 'looking for cache master file for asset %s...' % asset
                    if self.getCacheAsset(asset):
                        print ' ...found it.'
                        cacheMe = self.getCacheSet(n, False)
                        thisFile = os.path.splitext(cmds.file(q=1, sn=1, shn=1))[0]
                        cacheDir = os.path.join(cmds.workspace(q=1, fn=1), self.M.animExportFolder, '_ALEMBIC', thisFile)
                        if not os.path.exists(cacheDir):
                            os.makedirs(cacheDir)
                        cmds.select(cacheMe)
                        outPath = os.path.join(cacheDir, n).replace('\\', '/')
                        evalStr = 'AbcExport -j "-root ' + n + ':GEOgrp -uv -ro -wv -fr ' + s + ' ' + e + ' -sl -file ' + outPath + '.abc"'
                        mel.eval(evalStr)

        cmds.warning('Animation data exported to: %s' % dataPath)
        return dataPath

    def massAnimImport(self, namespaces, folder, versionUI = '', geoCaches = 1, *args):
        if versionUI != '':
            cmds.deleteUI(versionUI)
        pasteErrors = []
        folderRoot = folder.split('/')[-1]
        notInteger = re.compile('[^\\d]+')
        sceneSplit = folderRoot.split('_')
        anim = notInteger.sub('', sceneSplit[-3])
        self.lastImportVersion = anim
        for n in namespaces:
            impfile = os.path.join(folder, n) + '.ma'
            errors = self.pasteAnim(impfile, n)
            if errors != True:
                pasteErrors.extend(errors)
            if geoCaches:
                cmds.namespace(set=':')
                cmds.namespace(set=n)
                testObj = cmds.namespaceInfo(ls=1)[0]
                cmds.namespace(set=':')
                origFile = cmds.referenceQuery(testObj, f=1, wcn=1)
                if '_CACHE' in origFile:
                    dataPath = os.path.join(cmds.workspace(q=1, fn=1), self.M.animExportFolder)
                    cachePath = os.path.join(dataPath, '_ALEMBIC', os.path.basename(folder), n + '.abc')
                    cachePath = cachePath.replace('\\', '/')
                    if os.path.exists(cachePath):
                        cacheSet = self.getCacheSet(n, True)
                        if cacheSet:
                            refFile = cmds.referenceQuery(cacheSet[0], f=1, wcn=1)
                            if os.path.basename(refFile).split('_')[-1] == 'CACHE.mb' and os.path.exists(cachePath):
                                print 'found alembic for namespace %s. importing...' % n
                                evalStr = 'AbcImport -ct "' + n + ':GEOgrp" "' + cachePath + '"'
                                try:
                                    mel.eval(evalStr)
                                except:
                                    err = '\nError importing Alembic information for asset: %s under namespace: %s' % (os.path.basename(refFile), n)
                                    pasteErrors.append(err)

                    else:
                        err = "Couldn't find an Alembic file for namespace %s under path %s" % (n, cachePath)
                        pasteErrors.append(err)

        cacheFiles = cmds.ls(type='cacheFile')
        if cacheFiles:
            for i in cacheFiles:
                cmds.setAttr(i + '.multiThread', 1)

        if len(pasteErrors) > 0:
            print '\n-----ANIM IMPORT ERROR LOG-----'
            for e in pasteErrors:
                print e

            cmds.warning('Error importing animation data. See script editor for details.')
        else:
            mel.eval('print "Animation imported successfully!"')
        return folder

    def importAnimUI(self, *args):
        windowName = 'hfImportAnimUI'
        windowTitle = 'ANIM IMPORT'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        assetList = cmds.textScrollList(w=220, h=400, ams=1)
        cacheCtrl = cmds.checkBox(l='import geocaches (when available)', v=1)
        assetLabel = cmds.text(l='select assets to import to:')
        selBtn = cmds.button(l='import selected', w=220, h=50, c=lambda *x: self.animImportVersionUI(cmds.textScrollList(assetList, q=1, si=1), window, cmds.checkBox(cacheCtrl, q=1, v=1)))
        allBtn = cmds.button(l='import ALL', w=220, h=50, c=lambda *x: self.animImportVersionUI(self.getActiveNamespaces(), window, cmds.checkBox(cacheCtrl, q=1, v=1)))
        cancelBtn = cmds.button(l='cancel', w=220, h=50, c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(assetLabel, 'top', 5),
         (assetLabel, 'left', 5),
         (assetList, 'top', 25),
         (assetList, 'left', 5),
         (selBtn, 'top', 475),
         (selBtn, 'left', 5),
         (cancelBtn, 'top', 585),
         (cancelBtn, 'left', 5),
         (allBtn, 'top', 530),
         (allBtn, 'left', 5),
         (cacheCtrl, 'left', 5),
         (cacheCtrl, 'top', 455)])
        nsList = self.getActiveNamespaces()
        for ns in nsList:
            cmds.textScrollList(assetList, e=1, a=ns)

        cmds.showWindow(window)
        cmds.window(window, e=1, w=230, h=645)

    def animImportVersionUI(self, namespaces, importUI, geoCaches = 1, *args):
        cmds.deleteUI(importUI)
        windowName = 'hfImportAnimVersionUI'
        windowTitle = 'ANIM IMPORT VERSION'
        dataPath = os.path.join(cmds.workspace(q=1, fn=1), self.M.animExportFolder)
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        folderListCtrl = cmds.textScrollList(w=400, h=400, ams=0)
        folderFilterLabel = cmds.text(l='filter:')
        folderFilterCtrl = cmds.textField(w=100, tx='', cc=lambda *x: self.filterFolderList(cmds.textField(folderFilterCtrl, q=1, tx=1), folderListCtrl))
        goBtn = cmds.button(l='import', w=100, h=50, c=lambda *x: self.massAnimImport(namespaces, os.path.join(dataPath, cmds.textScrollList(folderListCtrl, q=1, si=1)[0]), window, geoCaches))
        cancelBtn = cmds.button(l='cancel', w=100, h=50, c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(folderFilterLabel, 'top', 5),
         (folderFilterLabel, 'left', 5),
         (folderFilterCtrl, 'top', 3),
         (folderFilterCtrl, 'left', 50),
         (folderListCtrl, 'top', 30),
         (folderListCtrl, 'left', 5),
         (goBtn, 'top', 440),
         (goBtn, 'left', 5),
         (cancelBtn, 'top', 440),
         (cancelBtn, 'left', 120)])
        self.filterFolderList('', folderListCtrl)
        cmds.showWindow(window)
        cmds.window(window, e=1, w=410, h=500)

    def filterFolderList(self, filter, control, *args):
        dataPath = os.path.join(cmds.workspace(q=1, fn=1), self.M.animExportFolder)
        if not os.path.exists(dataPath):
            cmds.error('No animation has been exported for this shot!')
        versionList = [ f for f in os.listdir(dataPath) if os.path.isdir(os.path.join(dataPath, f)) ]
        filteredList = versionList
        if filter != '':
            filteredList = [ f for f in versionList if f.upper().find(filter.upper()) != -1 ]
        cmds.textScrollList(control, e=1, ra=1)
        filteredList = natSort.natsorted(filteredList)
        for f in filteredList:
            cmds.textScrollList(control, e=1, a=f)

    def exportAnimUI(self, *args):
        windowName = 'hfExportAnimUI'
        windowTitle = 'ANIM EXPORT'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        assetList = cmds.textScrollList(w=220, h=400, ams=1)
        assetLabel = cmds.text(l='select assets to export:')
        startLabel = cmds.text(l='start:')
        endLabel = cmds.text(l='end:')
        startCtrl = cmds.textField(w=60, tx=cmds.playbackOptions(q=1, min=1))
        endCtrl = cmds.textField(w=60, tx=cmds.playbackOptions(q=1, max=1))
        cacheCtrl = cmds.checkBox(l='export geocaches (when available)', v=1)
        selBtn = cmds.button(l='export selected', w=220, h=50, c=lambda *x: self.massAnimExport(cmds.textScrollList(assetList, q=1, si=1), cmds.textField(startCtrl, q=1, tx=1), cmds.textField(endCtrl, q=1, tx=1), 1, 0, cmds.checkBox(cacheCtrl, q=1, v=1)))
        allBtn = cmds.button(l='export ALL', w=220, h=50, c=lambda *x: self.massAnimExport(self.getActiveNamespaces(), cmds.textField(startCtrl, q=1, tx=1), cmds.textField(endCtrl, q=1, tx=1), 1, 0, cmds.checkBox(cacheCtrl, q=1, v=1)))
        cancelBtn = cmds.button(l='cancel', w=220, h=50, c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(assetLabel, 'top', 5),
         (assetLabel, 'left', 5),
         (assetList, 'top', 25),
         (assetList, 'left', 5),
         (selBtn, 'top', 495),
         (selBtn, 'left', 5),
         (cancelBtn, 'top', 605),
         (cancelBtn, 'left', 5),
         (allBtn, 'top', 550),
         (allBtn, 'left', 5),
         (startLabel, 'top', 440),
         (startLabel, 'left', 5),
         (endLabel, 'top', 440),
         (endLabel, 'left', 120),
         (startCtrl, 'left', 40),
         (startCtrl, 'top', 438),
         (endCtrl, 'left', 150),
         (endCtrl, 'top', 438),
         (cacheCtrl, 'left', 5),
         (cacheCtrl, 'top', 475)])
        nsList = self.getActiveNamespaces()
        for ns in nsList:
            cmds.textScrollList(assetList, e=1, a=ns)

        cmds.showWindow(window)
        cmds.window(window, e=1, w=230, h=665)

    def doCompareRefs(self, *args):
        filefilter = 'Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)'
        filepath = cmds.fileDialog2(ds=1, dir=self.M.scenesDir, fm=1, fileFilter=filefilter)
        if os.path.exists(filepath[0]):
            self.compareRefs(filepath[0])
        else:
            cmds.warning('File not found, or operation cancelled.')

    def compareRefs(self, scenePath, *args):
        subp = subprocess.Popen(os.path.join(self.M.mayaDir, 'mayapy.exe') + ' ' + os.path.join(self.M.scriptsDir, '..', 'python', 'm_analyzeScene.py') + ' ' + scenePath, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = subp.communicate()
        output = stdout.split('M_ANALYZESCENE_DUMP')[-1]
        refsDict = pickle.loads(output)
        localNamespaces = [ cmds.file(f, q=1, ns=1) for f in cmds.file(q=1, r=1) ]
        localRefs = cmds.file(q=1, r=1)
        missingRefs = {}
        namespaceMismatch = {}
        for file, namespace in refsDict.iteritems():
            namespace = namespace.strip('\r')
            file = file.strip('\r')
            if file not in localRefs:
                missingRefs[file] = namespace
                print 'file %s not found in local references.' % file
            elif namespace not in localNamespaces:
                namespaceMismatch[file] = namespace

        windowName = 'compareRefsUI'
        windowTitle = 'References in ' + os.path.basename(scenePath)
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.formLayout()
        missingRefsList = cmds.textScrollList(w=600, h=300, ams=1)
        mismatchList = cmds.textScrollList(w=600, h=300, ams=1)
        missingRefsLabel = cmds.text(l='MISSING REFERENCES:', font='boldLabelFont')
        mismatchLabel = cmds.text(l='NAMESPACE MISMATCHES:', font='boldLabelFont')
        importBtn = cmds.button(w=150, h=50, l='create refs', c=lambda *x: self.getMissingRefs(cmds.textScrollList(missingRefsList, q=1, si=1), window))
        matchBtn = cmds.button(w=150, h=50, l='match namespaces', c=lambda *x: self.matchNamespaces(cmds.textScrollList(mismatchList, q=1, si=1), window))
        cancelBtn = cmds.button(w=150, h=50, l='cancel', c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(missingRefsList, 'top', 30),
         (missingRefsList, 'left', 5),
         (mismatchList, 'top', 355),
         (mismatchList, 'left', 5),
         (missingRefsLabel, 'top', 5),
         (missingRefsLabel, 'left', 5),
         (mismatchLabel, 'top', 340),
         (mismatchLabel, 'left', 5),
         (importBtn, 'top', 675),
         (importBtn, 'left', 5),
         (matchBtn, 'top', 675),
         (matchBtn, 'left', 165),
         (cancelBtn, 'top', 675),
         (cancelBtn, 'left', 325)])
        for file, namespace in missingRefs.iteritems():
            refString = namespace + ': ' + file
            cmds.textScrollList(missingRefsList, e=1, a=refString)

        for file, namespace in namespaceMismatch.iteritems():
            refString = cmds.file(file, q=1, ns=1) + ' ==> ' + namespace
            cmds.textScrollList(mismatchList, e=1, a=refString)

        cmds.showWindow(window)
        cmds.window(window, e=1, w=610, h=785)

    def getMissingRefs(self, refsList, UI = '', *args):
        try:
            len(refsList)
        except TypeError:
            cmds.error('Select at least one missing reference to create.')

        for item in refsList:
            namespace = item.split(': ')[0]
            filepath = item.split(': ')[1]
            cmds.file(filepath, r=1, ns=namespace)
            print 'Created new reference %s with namespace %s' % (filepath, namespace)

        if UI != '':
            cmds.deleteUI(UI)

    def matchNamespaces(self, nsList, UI = '', *args):
        try:
            len(nsList)
        except TypeError:
            cmds.error('Select at least one namespace to correct.')

        for item in nsList:
            oldNS = item.split(' ==> ')[0]
            newNS = item.split(' ==> ')[1]
            cmds.namespace(set=':')
            cmds.namespace(set=oldNS)
            objs = cmds.namespaceInfo(ls=1)
            cmds.namespace(set=':')
            filename = cmds.referenceQuery(objs[0], f=1)
            try:
                cmds.file(filename, e=1, ns=newNS)
            except RuntimeError:
                warnString = 'Could not rename namespace %s to %s. New namespace is invalid or already exists. Use the cleanup tool to remove unused namespaces.' % (oldNS, newNS)
                cmds.warning(warnString)

        if UI != '':
            cmds.deleteUI(UI)

    def duplicateRef(self, refFile, *args):
        refNode = cmds.file(refFile, q=1, rfn=1)
        allEdits = cmds.referenceQuery(refNode, es=1)
        connEdits = cmds.referenceQuery(refNode, es=1, ec='connectAttr')
        otherEdits = [ f for f in allEdits if f not in connEdits ]
        oldNS = cmds.file(refFile, q=1, ns=1)
        refFilePath = refFile.split('{')[0]
        newRef = cmds.file(refFilePath, r=1, ns=oldNS, shd='renderLayersByName')
        newNS = cmds.file(newRef, q=1, ns=1)
        oldNS = oldNS + ':'
        newNS = newNS + ':'
        for edit in otherEdits:
            newEdit = edit.replace(oldNS, newNS)
            print '\napplying edit: %s' % newEdit
            mel.eval(newEdit)

        for edit in connEdits:
            editSplit = edit.split(' ')
            editRename = editSplit[2].replace(oldNS, newNS)
            newEdit = editSplit[0] + ' ' + editSplit[1] + ' ' + editRename
            print newEdit
            try:
                mel.eval(newEdit)
            except:
                pass

            animCurveTypes = ['animCurveTL',
             'animCurveTA',
             'animCurveTT',
             'animCurveTU',
             'animCurveUL',
             'animCurveUA',
             'animCurveUT',
             'animCurveUU']
            outputNode = editSplit[1].split('.')[0].strip('"')
            if cmds.objectType(outputNode) in animCurveTypes:
                newAnimCurve = cmds.duplicate(outputNode)
                newName = newAnimCurve[0].replace(oldNS, newNS)
                outName = cmds.rename(newAnimCurve[0], newName)
                newConnect = newEdit.replace(outputNode, outName)
                newConnect = newConnect.replace('connectAttr', 'connectAttr -f')
                try:
                    mel.eval(newConnect)
                except:
                    pass

        print 'Duplicated reference %s. New namespace is %s' % (refFile, newNS)
        return newNS

    def doDuplicateRef(self, refsListCtrl, *args):
        refs = self.parseRefsList(refsListCtrl)
        for ref in refs:
            self.duplicateRef(ref)

        self.popRefsList(refsListCtrl)

    def getCacheSet(self, namespace, getObjects = True, *args):
        setName = namespace + ':CACHEset'
        if not cmds.objExists(setName):
            return False
        objs = cmds.sets(setName, q=1)
        objsWithMeshes = []
        meshes = []
        if objs:
            for i in objs:
                newmeshes = []
                shapes = cmds.listRelatives(i, s=1, ni=1)
                if shapes:
                    newmeshes = [ f for f in shapes if cmds.objectType(f) == 'mesh' ]
                if len(newmeshes) > 0:
                    meshes.extend(newmeshes)
                    objsWithMeshes.append(i)

            if len(objsWithMeshes) > 0:
                if getObjects:
                    return objsWithMeshes
                else:
                    return meshes
            else:
                return False
        else:
            return False

    def getCacheAsset(self, asset, *args):
        testFile = os.path.join(self.M.assetsDir, asset, asset + '_CACHE.mb')
        if os.path.exists(testFile):
            return testFile
        else:
            return False