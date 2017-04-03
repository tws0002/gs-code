import os
import sys
import operator
import subprocess
import maya.cmds as cmds
import re
import time
import random
import json
import glob
import shutil
import remote_render

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/pipeline'

import gsstartup
from gsstartup import muster2

MUSTER_POOLS = []
majorver = ''
minorver = ''

exePath = sys.argv[0]
m = re.search('Maya/(.*)/bin', exePath)
if m:
    fullver = m.group(1)
    n = re.search('(\d*)\.(\d*\.\d*)', fullver)
    if n:
        o = re.search('^5\.(\d*)', n.group(2))
        if o:
            majorver = n.group(1)+'.5'
            minorver = o.group(1)
        else:
            majorver = n.group(1)
            minorver = n.group(2)

class Submitter:

    def __init__(self):
        global MUSTER_POOLS

        self.M = ''
        self.imagesFolder = 'images'


        # if not the base branch, the local branch cache prob isn't getting updated so we'll copy it from base branch
        if os.environ['GSBRANCH'].split('/')[-1] != 'base':
            base_mp_cache = os.path.join(os.environ['GSROOT'],'base','gs','python','gsstartup','muster.json')
            local_mp_cache = os.path.join(os.environ['GSBRANCH'],'gs','python','gsstartup','muster.json')
            if os.path.getmtime(base_mp_cache) > time.time() - 60*5:  
                shutil.copy2(base_mp_cache,local_mp_cache)

        # if the mod date is more recent than 5 min ago load it, otherwise query muster
        #try:
        if os.path.getmtime(muster2.MUSTERJSON) > time.time() - 60*5:    
            with open(muster2.MUSTERJSON, 'r') as f:
                muster_json = json.load(f)
                MUSTER_POOLS = muster_json['pools']
        else:
            MUSTER_POOLS = muster2.get_pools()
          
        #except WindowsError:
        #
        #    MUSTER_POOLS = muster2.get_pools()     
        #    print 'init submitter'

    def getCameras(self, *args):
        defaultCams = ['top',
         'side',
         'front',
         'persp']
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

    # used by aspera to get image prefixes
    def getImageOutputPath(self, *args):
        imagePrefix = ''
        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            imagePrefix = cmds.getAttr('vraySettings.fileNamePrefix')
        else:
            imagePrefix = cmds.getAttr('defaultRenderGlobals.imageFilePrefix')
        if not imagePrefix:
            return False
        imagePrefix = '/'.join(imagePrefix.split('/')[:-1])
        # subst <Scene>
        fullPath = cmds.file(q=1, sn=1)
        oldName = os.path.splitext(cmds.file(q=1, sn=1, shn=1))[0]
        fixedName = oldName
        if '_T_' in oldName:
            fixedName = oldName.split('_T_')[0]
        newPrefix1 = imagePrefix.replace('<Scene>', fixedName)

        # if <Layer> is in path, parse the active render layers
        newPrefix2 = newPrefix1.replace('/<Layer>', '')
        # if <Version> is in path
        newPrefix3 = newPrefix2.replace('/<Version>', '')
        # if <Camera> is in path
        newPrefix = newPrefix3.replace('/<Camera>', '')

        projectImgFolder = os.path.join(cmds.workspace(q=1, fn=1), self.imagesFolder, newPrefix)
        normalizedFolder = projectImgFolder.replace('/', '\\')
        return normalizedFolder

    def getUploadFiles(self):
        files = list(remote_render.get_scene_files())
        reffiles = cmds.file(query=True, list=True)
        workspacemel = os.path.join(self.M.project, 'workspace.mel')
        filelist = [workspacemel]
        
        # also make sure to include any pipeline configs
        if 'GSPROJECT' in os.environ:
            proj = os.environ['GSPROJECT']
            config_path = os.path.join('\\\\scholar','projects',proj,'03_production','.pipeline','config')
            filelist.append(config_path)

        for f in files + reffiles:
            if glob.glob(f):
                filelist.append(f)
        files_all = sorted(list(set(filelist)))

        ## Following will detect a sequence of files. Assumes the frame number is right before the extension. ##
        seq_dict = {}
        for f in files_all:
            fname, fext = os.path.splitext(f)
            m = re.sub('(\d+)$','',fname)
            if m:
                try:
                    seq_dict[(m,fext)]+=1
                except KeyError:
                    seq_dict[(m,fext)]=0

        seq_list_final = []
        for d in seq_dict:
            if seq_dict[d]:
                seq_list_final.append(os.path.split(d[0])[0])

        files_final = []
        for l in files_all:
            if any(seq in l for seq in seq_list_final):
                pass
            else:
                files_final.append(l)
        for seq in seq_list_final:
            files_final.append(seq)



        # xgen

        #fullPath = cmds.file(q=1, sn=1)
        #xgenFiles = glob.glob(os.path.splitext(fullPath)[0]+'__*.xgen')
        #for x in xgenFiles:
        #    files_final.append(x)
        #abcFiles = glob.glob(os.path.splitext(fullPath)[0]+'__*.abc')
        #for a in abcFiles:
        #    files_final.append(a)
#

        return list(set(files_final))

    def get_gs_musterId(self,package):
        mId = 1100
        if package == 'maya':
            mId += 6

        # if running dev branch, increment the mId by 1000
        branch = os.environ['GSBRANCH'].split('/')[-1]
        if branch == 'dev':
            mId += 100
        print ('Detected Branch:{0} Using muster template id:{1}'.format(branch,mId))
        return mId



    def getDownloadFiles(self):
        files = self.getImageOutputPath()
        return files.replace('\\','/')

    def musterSubmitJob(self, file, name, project, pool, priority, depend, start, end, step, packet, x, y, flags, notes, emails = 0, framecheck = 0, minsize = '0', framePadding = '4', suffix = '', layers = '', exr2tiff = False, rsGpus = 0, *args):
        nameNoStamp = name
        mtid = self.get_gs_musterId('maya');
        if '_T_' in name:
            nameNoStamp = '_T_'.join(name.split('_T_')[:-1]) + suffix

        musterflags = {}
        if majorver and minorver:
            musterflags['-add']             = '--package maya --major %s --minor %s --render -x %s -y %s' %(majorver, minorver, x, y)
        else:
            musterflags['-add']             = '--render maya -x %s -y %s' %(x, y)

        musterflags['-e']               = str(mtid)
        musterflags['-n']               = nameNoStamp
        musterflags['-parent']          = '33409'
        musterflags['-group']           = self.M.projectName
        musterflags['-proj']            = project
        musterflags['-pool']            = pool
        musterflags['-sf']              = str(start)
        musterflags['-ef']              = str(end)
        musterflags['-bf']              = str(step)
        musterflags['-pr']              = str(priority)
        musterflags['-pk']              = str(packet)
        musterflags['-f']               = file
        musterflags['-ecerrtype']       = '1'
        musterflags['-logerrtype']      = '1'
        if depend: musterflags['-wait'] = depend
        if notes: musterflags['-info']  = notes
            
        if gsstartup.properties['location'] == 'NYC' and pool != 'WKSTN-NY':
            ascpupsubmit=''
            upfile = file.replace(" ", "\ ").replace("//","/")
            ascpupcmd = 'ascpgs render@nycbossman:%s %s;' %(upfile, os.path.split(upfile)[0])
            uploadfiles = self.getUploadFiles()
            chunks = [uploadfiles[x:x+10] for x in range(0, len(uploadfiles), 10)]
            i=1
            for chunk in chunks:
                ascpupflags = {}
                ascpupflags['-e']       = '43'
                ascpupflags['-n']       = '%s Asset Upload %s of %s' %(nameNoStamp, i, len(chunks))
                ascpupflags['-parent']  = '33409'
                ascpupflags['-group']    = self.M.projectName
                ascpupflags['-pool']    = 'ASPERA'                
                ascpupcmd = ''
                if ascpupsubmit:
                    ascpupflags['-wait'] = ascpupsubmit
                for r in chunk:
                    f = r.replace("\\","/").replace(" ", "\ ").replace("//","/")
                    src = re.sub('%\d+d','*',f)
                    dest = os.path.split(src)[0]
                    ascpupcmd = ascpupcmd + 'ascpgs render@nycbossman:%s %s;' %(src, dest)
                ascpupflags['-add'] = '-c \"%s\"' %(ascpupcmd)
                ascpupsubmit = muster2.submit(ascpupflags)
                i+=1

            if ascpupsubmit:
                musterflags['-wait'] = ascpupsubmit
                if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'redshift':
                    if rsGpus == 1:
                        rsGpuString = ['{0}', '{1}', '{2}', '{3}']
                        i=0
                        for g in rsGpuString:
                            rsmusterflags = musterflags.copy()
                            rsmusterflags['-n'] = '%s - GPU%s' %(nameNoStamp, g)
                            rsmusterflags['-sf'] = str(int(start)+i)
                            rsmusterflags['-bf'] = str(len(rsGpuString))
                            rsmusterflags['-gpupool'] = 'GPU-'+str(i)
                            rsmusterflags['-add'] = musterflags['-add'] + ' -r redshift -gpu %s' %g
                            rendersubmit = muster2.submit(rsmusterflags)
                            i+=1
                    if rsGpus == 2:
                        rsGpuString = ['{0,1}', '{2,3}']
                        i=0
                        for g in rsGpuString:
                            rsmusterflags = musterflags.copy()
                            rsmusterflags['-n'] = '%s - GPU%s' %(nameNoStamp, g)
                            rsmusterflags['-sf'] = str(int(start)+i)
                            rsmusterflags['-bf'] = str(len(rsGpuString))
                            rsmusterflags['-gpupool'] = 'GPU-'+str(i)
                            rsmusterflags['-add'] = musterflags['-add'] + ' -r redshift -gpu %s' %g
                            rendersubmit = muster2.submit(rsmusterflags)
                            i+=1
                    if rsGpus == 4:
                        rendersubmit = muster2.submit(musterflags)
                else:
                    rendersubmit = muster2.submit(musterflags)
                if rendersubmit:
                    ascpdownflags = {}
                    ascpdownflags['-e']         = '43'
                    ascpdownflags['-n']         = '%s Render Download' %(nameNoStamp)
                    ascpdownflags['-parent']    = '33409'
                    ascpdownflags['-group']      = self.M.projectName
                    ascpdownflags['-pool']      = 'ASPERA'
                    ascpdownflags['-wait']      = rendersubmit
                    
                    ascpdowncmd = ''
                    f = self.getDownloadFiles().replace(" ", "\ ").replace("//","/")
                    src = "%s/*" %(f)
                    dest = f
                    ascpdowncmd = ascpdowncmd + 'ascpgs %s render@nycbossman:%s;' %(src, dest)
                    ascpdownflags['-add'] = '-c \"%s\"' %(ascpdowncmd)
                    ascpdownsubmit = muster2.submit(ascpdownflags)

                    if ascpdownsubmit:
                        print 'Jobs successfully submitted to Muster!'
                    else:
                        print 'There was an error submitting download job to Muster'
                else:
                    print 'There was an error submitting render job to Muster.'
            else:
                print 'There was an error submitting upload job to Muster.'
        else:
            if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'redshift':
                if rsGpus == 1:
                    rsGpuString = ['{0}', '{1}', '{2}', '{3}']
                    i=0
                    for g in rsGpuString:
                        rsmusterflags = musterflags.copy()
                        rsmusterflags['-n'] = '%s - GPU%s' %(nameNoStamp, g)
                        rsmusterflags['-sf'] = str(int(start)+i)
                        rsmusterflags['-bf'] = str(len(rsGpuString))
                        rsmusterflags['-gpupool'] = 'GPU-'+str(i)
                        rsmusterflags['-add'] = musterflags['-add'] + ' -r redshift -gpu %s' %g
                        rendersubmit = muster2.submit(rsmusterflags)
                        i+=1
                if rsGpus == 2:
                    rsGpuString = ['{0,1}', '{2,3}']
                    i=0
                    for g in rsGpuString:
                        rsmusterflags = musterflags.copy()
                        rsmusterflags['-n'] = '%s - GPU%s' %(nameNoStamp, g)
                        rsmusterflags['-sf'] = str(int(start)+i)
                        rsmusterflags['-bf'] = str(len(rsGpuString))
                        rsmusterflags['-gpupool'] = 'GPU-'+str(i)
                        rsmusterflags['-add'] = musterflags['-add'] + ' -r redshift -gpu %s' %g
                        rendersubmit = muster2.submit(rsmusterflags)
                        i+=1
                if rsGpus == 4:
                    rendersubmit = muster2.submit(musterflags)
            else:
                print musterflags
                rendersubmit = muster2.submit(musterflags)
            if rendersubmit:
                print 'Job ID#%s successfully submitted to Muster!' %(rendersubmit)
            else:
                print 'There was an error submitting render job to Muster.'
                return False

        newID = rendersubmit

        if framecheck or emails:
            vrayFormats = ['',
             'png',
             'jpg',
             'vrimg',
             'hdr',
             'exr',
             'exr',
             'tga',
             'bmp',
             'sgi',
             'tif']
            mayaFormats = {'6': 'als',
             '11': 'cin',
             '35': 'dds',
             '9': 'eps',
             '0': 'gif',
             '8': 'jpg',
             '7': 'iff',
             '10': 'iff',
             '31': 'psd',
             '36': 'psd',
             '32': 'png',
             '12': 'yuv',
             '2': 'rla',
             '5': 'sgi',
             '13': 'sgi',
             '1': 'pic',
             '19': 'tga',
             '3': 'tif',
             '4': 'tif',
             '20': 'bmp',
             '63': 'xpm',
             '51': 'exr'}

            # imgExt = ''
            # if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            #     imgExt = cmds.getAttr('vraySettings.imageFormatStr')
            #     if imgExt == 'exr (multichannel)':
            #         imgExt = 'exr'
            # else:
            #     imgCode = cmds.getAttr('defaultRenderGlobals.imageFormat')
            #     imgExt = mayaFormats[str(imgCode)]
            # emailsArg = 'none'
            # if emails:
            #     emailsFix = [ f.strip() for f in emails.split(',') if '@' in f ]
            #     emailsArg = ','.join(emailsFix)
            #     print 'EMAILS LIST: %s' % emailsArg
            # imgPath = self.getImageOutputPath()
            # if not notes:
            #     notes = 'none'
            # elif notes == '':
            #     notes = 'none'
            # notesFormat = notes.replace(' ', '___')
            # if not notes:
            #     notes = '___'
            # name = '_T_'.join(name.split('_T_')[:-1]) + suffix
            # nameFormat = name.replace(' ', '___')
            # if imgPath:
            #     imgPathFormat = imgPath.replace(' ', '___')
            # supportID = str(int(newID) + 1)
            # renderLayers = ','.join(layers)

            # checkFlags = {}
            # checkFlags['-e'] = '43'
            # checkFlags['-n'] = '%s_check' %(name)
            # checkFlags['-pool'] = pool
            # checkFlags['-parent'] = '33409'
            # checkFlags['-group'] = self.M.projectName
            # checkFlags['-proj'] = project
            # checkFlags['-pr'] = '100'
            # checkFlags['-wait'] = newID
            # checkFlags['-si'] = '1'
            # checkFlags['-max'] = '1'
            # checkFlags['-sf'] = '1'
            # checkFlags['-ef'] = '1'
            # checkFlags['-bf'] = '1'
            # checkFlags['-pk'] = '1'
            # addflags = [
            #             '"%s"' %(os.path.join(self.M.mayaDir, 'mayapy.exe')), 
            #             '"%s"' %(os.path.join(self.M.scriptsDir, '..', 'python', 'm_submitCheck.py')),
            #             '0', emailsArg, nameFormat, notesFormat, newID, supportID, imgPath,
            #             imgExt, framePadding, minsize, renderLayers
            #             ]
            # checkFlags['-add'] = ' '.join(addflags)

            # print 'Sending frame check job to Muster'
            # checkJob = muster2.submit(checkFlags)
            # if checkJob:
            #     print checkJob
            # else:
            #     cmds.warning('Error submitting support job to Muster')
            #     return False

            if exr2tiff:
                exr2tiffFlags = {}
                exr2tiffFlags['-e'] = '993'
                exr2tiffFlags['-f'] = imgPath
                exr2tiffFlags['-n'] = '%s_EXR2TIFF' %(name)
                exr2tiffFlags['-pool'] = 'NUKE'
                exr2tiffFlags['-parent'] = '33409'
                exr2tiffFlags['-group'] = self.M.projectName
                exr2tiffFlags['-proj'] = project
                exr2tiffFlags['-pr'] = '100'
                exr2tiffFlags['-wait'] = newID
                exr2tiffFlags['-sf'] = '1'
                exr2tiffFlags['-ef'] = '1'
                exr2tiffFlags['-bf'] = '1'
                exr2tiffFlags['-pk'] = '1'

                exr2tiffJob = muster2.submit(exr2tiffFlags)
                if exr2tiffJob:
                    print exr2tiffJob
                else:
                    cmds.warning('Error submitting exr2tiff job to Muster')
                    return False
        return newID

    def save_render_file(self, sceneSuffix = '', frameSuffix = '', *args):
        shot = self.M.SM.checkedShot
        fullPath = cmds.file(q=1, sn=1)
        oldName = os.path.splitext(cmds.file(q=1, sn=1, shn=1))[0]
        fixedName = oldName
        if '_T_' in oldName:
            fixedName = oldName.split('_T_')[0]
        renderScenesDir = os.path.join(self.M.scenesDir, shot, 'mustache_renderScenes')
        if not os.path.exists(renderScenesDir):
            os.makedirs(renderScenesDir)
        imagePrefix = ''
        sceneName = cmds.file(q=1, sn=1, shn=1)

        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            imagePrefix = cmds.getAttr('vraySettings.fileNamePrefix')
            newPrefix = imagePrefix.replace('<Scene>', fixedName + sceneSuffix)
            if newPrefix[-1] == '.':
                newPrefix = newPrefix[:-1] + frameSuffix + '.'
            else:
                newPrefix = newPrefix + frameSuffix
            cmds.setAttr('vraySettings.fileNamePrefix', newPrefix, type='string')
        else:
            imagePrefix = cmds.getAttr('defaultRenderGlobals.imageFilePrefix')
            newPrefix = imagePrefix.replace('<Scene>', fixedName + sceneSuffix)
            if newPrefix[-1] == '.':
                newPrefix = newPrefix[:-1] + frameSuffix + '.'
            else:
                newPrefix = newPrefix + frameSuffix
            try:
                cmds.setAttr('defaultRenderGlobals.imageFilePrefix', newPrefix, type='string')
            except:
                pass
        
        #if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'redshift':
        #    cmds.setAttr('redshiftOptions.exrForceMultilayer', True)
        
        timestamp = str(int(time.time()))
        cmds.file(rename=os.path.join(renderScenesDir, fixedName + '_T_' + timestamp + '.mb'))
        new_file = cmds.file(s=1, f=1)
        cmds.file(rts=1)

        # restore image prefix without <scene> substitution
        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            cmds.setAttr('vraySettings.fileNamePrefix', imagePrefix, type='string')
        else:
            cmds.setAttr('defaultRenderGlobals.imageFilePrefix', imagePrefix, type='string')

        if cmds.pluginInfo('xgenToolkit.mll', q=1, l=1):
            xgenFiles = glob.glob(os.path.splitext(fullPath)[0]+'__*.xgen')
            abcFiles = glob.glob(os.path.splitext(fullPath)[0]+'__*.abc')
            for x in xgenFiles:
                search = '(%s)(.+\.xgen)$' %(oldName)
                m = re.search(search, x)
                if m:
                    shutil.copy2(x, os.path.join(renderScenesDir, fixedName+'_T_'+timestamp+m.group(2)))
                    shutil.copy2(x, os.path.join(renderScenesDir))
            for a in abcFiles:
                search = '(%s)(.+\.abc)$' %(oldName)
                m = re.search(search, a)
                if m:
                    shutil.copy2(a, os.path.join(renderScenesDir, fixedName+'_T_'+timestamp+m.group(2)))
                    shutil.copy2(a, os.path.join(renderScenesDir))

        return new_file

    def setRenderPrefix(self, imagePrefix, *args):

        if 'GS_MAYA_REND_PREFIX' in os.environ:
            imagePrefix = os.environ['GS_MAYA_REND_PREFIX']
            result = imagePrefix.replace("<gs_shot>",self.M.SM.checkedShot)
        else:
            result = self.M.SM.checkedShot + '/<Scene>/<Scene>_<Layer>'

        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            #if cmds.getAttr('vraySettings.imageFormatStr') == 'exr (multichannel)':
                #imagePrefix = imagePrefix + '.'
            cmds.setAttr('vraySettings.fileNamePrefix', result, type='string')
        else:
            try:
                cmds.setAttr('defaultRenderGlobals.imageFilePrefix', result, type='string')
            except:
                pass

    def getRenderPrefix(self, *args):
        imagePrefix = ''

        #imagePrefix = '/'.join(imagePrefix.split('/')[:-1])
        if 'GS_MAYA_REND_PREFIX' in os.environ:
            imagePrefix = os.environ['GS_MAYA_REND_PREFIX']
            result = imagePrefix.replace("<gs_shot>",self.M.SM.checkedShot)
        else:
            if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
                result = cmds.getAttr('vraySettings.fileNamePrefix')
            else:
                result = cmds.getAttr('defaultRenderGlobals.imageFilePrefix')
        return result

    def vray_prepassSetup(self, beautyLayer, *args):
        sceneName = cmds.file(q=1, sn=1)
        if '_T_' in sceneName:
            sceneName = '_T_'.join(sceneName.split('_T_')[:-1]) + '.mb'
        IRPath = os.path.join(self.M.projectsBase, self.M.project, 'renderData', 'IRMAP', self.M.SM.checkedShot, os.path.basename(sceneName))
        if not os.path.exists(IRPath):
            os.makedirs(IRPath)
        IRFile = os.path.join(IRPath, os.path.splitext(cmds.file(q=1, sn=1, shn=1))[0] + '.vrmap')
        cmds.setAttr('vraySettings.imap_mode', 6)
        cmds.setAttr('vraySettings.imap_autoSaveFile', IRFile, type='string')
        rlayers = cmds.ls(type='renderLayer')
        enabledLayers = []
        for layer in rlayers:
            if cmds.getAttr(layer + '.renderable') == 1:
                enabledLayers.append(layer)
            cmds.setAttr(layer + '.renderable', 0)

        cmds.setAttr(beautyLayer + '.renderable', 1)
        cmds.file(rename=os.path.splitext(sceneName)[0] + '_PREPASS.mb')
        prepassScene = cmds.file(s=1, f=1)
        cmds.setAttr('vraySettings.imap_mode', 7)
        cmds.setAttr('vraySettings.imap_fileName', IRFile, type='string')
        cmds.file(rename=sceneName)
        cmds.setAttr(beautyLayer + '.renderable', 0)
        for layer in enabledLayers:
            cmds.setAttr(layer + '.renderable', 1)

        return prepassScene

    def sceneRenderPrep(self, renderCam, layers, imgPlanes = 0, imageType = 'exr', framePadding = 4, memLimit = '5000', displaceLimit = '4', *args):
        vrayFormats = ['png',
         'jpg',
         'vrimg',
         'hdr',
         'exr',
         'exr (multichannel)',
         'tga',
         'bmp',
         'sgi',
         'tif']
        mayaFormats = {'8': 'jpg',
         '7': 'iff',
         '10': 'iff (16)',
         '31': 'psd',
         '36': 'psd (layers)',
         '32': 'png',
         '19': 'tga',
         '3': 'tif',
         '4': 'tif16',
         '13': 'sgi',
         '51': 'exr'}
        if imgPlanes == 0:
            ip = cmds.ls(type='imagePlane')
            for i in ip:
                cmds.setAttr(i + '.displayMode', 0)

        cams = cmds.ls(type='camera')
        for cam in cams:
            cmds.setAttr(cam + '.renderable', 0)

        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            cmds.setAttr('vraySettings.batchCamera', renderCam, type='string')
            cmds.setAttr('vraySettings.sys_low_thread_priority', 0)
            cmds.setAttr('vraySettings.stamp_on', 0)
            cmds.setAttr('vraySettings.imageFormatStr', imageType, type='string')
            cmds.setAttr('vraySettings.sys_rayc_dynMemLimit', int(memLimit))
            cmds.setAttr('vraySettings.ddisplac_maxSubdivs', int(displaceLimit))
            cmds.setAttr('vraySettings.imgOpt_exr_compression', 3)
        else:
            revDict = dict([ (v, k) for k, v in mayaFormats.iteritems() ])
            match = int(revDict[imageType])
            cmds.setAttr('defaultRenderGlobals.imageFormat', match)
        cmds.setAttr(renderCam + '.renderable', 1)
        allLayers = cmds.ls(type='renderLayer')
        for l in allLayers:
            cmds.setAttr(l + '.renderable', 0)

        for l in layers:
            print l
            cmds.setAttr(l + '.renderable', 1)

        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            cmds.setAttr('vraySettings.fileNamePadding', int(framePadding))
        else:
            cmds.setAttr('defaultRenderGlobals.extensionPadding', int(framePadding))

        return True

    def parseRenderSuffix(self, sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, framePreviewCtrl, imageTypeCtrl, *args):
        imgString = ''
        extension = cmds.optionMenu(imageTypeCtrl, q=1, v=1)
        scene = os.path.splitext(cmds.file(q=1, sn=1, shn=1))[0]
        ssuff = cmds.textField(sceneSuffixCtrl, q=1, tx=1)
        fsuff = cmds.textField(frameSuffixCtrl, q=1, tx=1)
        imageDir = self.M.imagesDir
        padding = int(cmds.textField(paddingCtrl, q=1, tx=1))
        paddingStr = ''
        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            prf = str(cmds.getAttr('vraySettings.fileNamePrefix'))
            imgString = prf.strip('.')
        else:
            imgString = cmds.getAttr('defaultRenderGlobals.imageFilePrefix')
        if not imgString:
            imgString = '<NULL>'
        for x in range(0, padding):
            paddingStr = paddingStr + '#'

        # commented out because we only want to parse <scene> when saving temp renderscene
        #imgString = imageDir + imgString.replace('<Scene>', scene + ssuff) + fsuff + '.' + paddingStr + '.' + extension
        imgString = imageDir + imgString + fsuff + '.' + paddingStr + '.' + extension
        cmds.text(framePreviewCtrl, e=1, l=imgString)
        

    def parseImagePrefix(self, imagePrefixCtrl, sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, framePreviewCtrl, imageTypeCtrl, *args):
        imagePrefix = cmds.textField(imagePrefixCtrl, q=1, tx=1)
        self.setRenderPrefix(imagePrefix)
        self.parseRenderSuffix(sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, framePreviewCtrl, imageTypeCtrl, *args)


    def userSubmit(self, pool, priority, start, end, step, packet, x, y, flags, notes, emails, framecheck, minsize, renderCam, imgPlanes, suffix, endSuffix, renderLayers, prepassBeautyLayer = '', depend = 0, framePadding = 4, imageType = 'exr', memLimit = '5000', displaceLimit = '4', exr2tiff = False, rsGpus = 0, *args):
        origFile = cmds.file(q=1, sn=1)
        self.sceneRenderPrep(renderCam, renderLayers, imgPlanes, imageType, framePadding, memLimit, displaceLimit)
        prepassID = '0'
        if prepassBeautyLayer:
            self.save_render_file(suffix, endSuffix)
            IRFile = self.vray_prepassSetup(prepassBeautyLayer)
            irStart = str(int(start) - int(cmds.getAttr('vraySettings.imap_interpFrames')))
            irEnd = str(int(end) + int(cmds.getAttr('vraySettings.imap_interpFrames')))
            irName = os.path.basename(IRFile)
            prepassID = self.musterSubmitJob(IRFile, irName, self.M.project, pool, priority, depend, irStart, irEnd, step, packet, x, y, flags, notes + ' PREPASS', '', 0, '0', str(framePadding), suffix)
            if not prepassID:
                cmds.error('Error submitting prepass!')
        finalScene = self.save_render_file(suffix, endSuffix)
        finalScene = self.musterSubmitJob(finalScene, cmds.file(q=1, sn=1, shn=1), self.M.project, pool, priority, prepassID, start, end, step, packet, x, y, flags, notes, emails, framecheck, str(minsize), str(framePadding), suffix, renderLayers, exr2tiff, rsGpus)
        if finalScene == False:
            cmds.confirmDialog(title='Error submitting render!', message='Muster has found an ERROR. Check the script editor.', button="Please Resubmit")
        else:
            cmds.confirmDialog(title='Submission successful.', message='Successfully submitted Job#%s to Muster.' %(finalScene), button='OK')
        cmds.file(rename=origFile)
        cmds.file(rts=1)

    def submitUI(self, *args):
        if not self.M.SM.checkedShot:
            cmds.error('You need to have a valid scene open and checked out in order to render.')
        windowName = 'mustache_submitUI'
        windowTitle = '}MUSTACHE{ - SUBMIT RENDER'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle, w=600, h=900)
        wrapperForm = cmds.formLayout(parent=window)
        mayaGlobalSettings = cmds.formLayout(parent=wrapperForm)
        lm1 = 5
        lm2 = 100
        lm3 = 290
        lm4 = 365
        lm5 = 620
        tm1 = 5
        tm2 = 30
        tm3 = 85
        tm4 = 160
        tm5 = 260
        lineHeight = 22
        smallInputWidth = 60
        largeInputWidth = 500
        mayaLabel = cmds.text(l='MAYA GLOBAL SETTINGS', fn='boldLabelFont', parent=mayaGlobalSettings)
        sceneLabel = cmds.text(l='Scene name:', parent=mayaGlobalSettings)
        projectLabel = cmds.text(l='Project name:', parent=mayaGlobalSettings)
        startLabel = cmds.text(l='Start frame:', parent=mayaGlobalSettings)
        endLabel = cmds.text(l='End frame:', parent=mayaGlobalSettings)
        stepLabel = cmds.text(l='Framestep:', ann='Render every nth frame. Leave at 1 to render every frame.', parent=mayaGlobalSettings)
        sizeXLabel = cmds.text(l='Size X:', ann='Pixel dimensions of output image.', parent=mayaGlobalSettings)
        sizeYLabel = cmds.text(l='Size Y:', ann='Pixel dimensions of output image.', parent=mayaGlobalSettings)
        paddingLabel = cmds.text(l='Padding:', ann='Number of leading zeroes used to pad the frame number. Default is 4.', parent=mayaGlobalSettings)
        sceneSuffixLabel = cmds.text(l='Scene suffix:', ann='Filename text added after each instance of the scene name for each rendered frame.', parent=mayaGlobalSettings)
        frameSuffixLabel = cmds.text(l='Frame suffix:', ann='Filename text added just before the frame number of each rendered frame.', parent=mayaGlobalSettings)
        renderPrefixLabel = cmds.text(l='Image Prefix', ann='Image Naming Pattern (from Render Globals).', parent=mayaGlobalSettings)
        frameExampleLabel = cmds.text(l='Image files will be named:', fn='obliqueLabelFont', parent=mayaGlobalSettings)
        frameExample = cmds.text(l='', fn='smallPlainLabelFont', parent=mayaGlobalSettings)
        engineString = 'render engine is ' + cmds.getAttr('defaultRenderGlobals.currentRenderer').upper()
        renderEngineLabel = cmds.text(l=engineString, fn='boldLabelFont', parent=mayaGlobalSettings)
        mustacheCtrl = cmds.image(w=150, h=150)
        sceneCtrl = cmds.textField(tx=cmds.file(q=1, sn=1), en=0, w=largeInputWidth, parent=mayaGlobalSettings)
        projectCtrl = cmds.textField(tx=cmds.workspace(q=1, fn=1), en=0, w=largeInputWidth, parent=mayaGlobalSettings)
        startCtrl = cmds.textField(tx=str(int(cmds.getAttr('defaultRenderGlobals.startFrame'))), w=smallInputWidth, parent=mayaGlobalSettings)
        endCtrl = cmds.textField(tx=str(int(cmds.getAttr('defaultRenderGlobals.endFrame'))), w=smallInputWidth, parent=mayaGlobalSettings)
        stepCtrl = cmds.textField(tx=str(int(cmds.getAttr('defaultRenderGlobals.byFrameStep'))), w=smallInputWidth, parent=mayaGlobalSettings)
        sizeXCtrl = cmds.textField(tx=cmds.getAttr('defaultResolution.width'), w=smallInputWidth, parent=mayaGlobalSettings)
        sizeYCtrl = cmds.textField(tx=cmds.getAttr('defaultResolution.height'), w=smallInputWidth, parent=mayaGlobalSettings)
        paddingCtrl = cmds.textField(tx=cmds.getAttr('defaultRenderGlobals.extensionPadding'), w=smallInputWidth, parent=mayaGlobalSettings, cc=lambda *x: self.parseRenderSuffix(sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, frameExample, imageTypeCtrl))
        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            cmds.textField(paddingCtrl, e=1, tx=cmds.getAttr('vraySettings.fileNamePadding'))
        sceneSuffixCtrl = cmds.textField(tx='', w=150, parent=mayaGlobalSettings, cc=lambda *x: self.parseRenderSuffix(sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, frameExample, imageTypeCtrl))
        frameSuffixCtrl = cmds.textField(tx='', w=150, parent=mayaGlobalSettings, cc=lambda *x: self.parseRenderSuffix(sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, frameExample, imageTypeCtrl))
        renderPrefixCtrl = cmds.textField(tx=self.getRenderPrefix(), w=largeInputWidth, parent=mayaGlobalSettings, cc=lambda *x: self.parseImagePrefix(renderPrefixCtrl,sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, frameExample, imageTypeCtrl))
        cmds.formLayout(mayaGlobalSettings, e=1, attachForm=[(mayaLabel, 'top', tm1),
         (mayaLabel, 'left', lm1),
         (sceneLabel, 'top', tm2),
         (sceneLabel, 'left', lm1),
         (projectLabel, 'top', tm2 + lineHeight),
         (projectLabel, 'left', lm1),
         (startLabel, 'top', tm3),
         (startLabel, 'left', lm1),
         (endLabel, 'top', tm3 + lineHeight),
         (endLabel, 'left', lm1),
         (stepLabel, 'top', tm3 + lineHeight * 2),
         (stepLabel, 'left', lm1),
         (sizeXLabel, 'top', tm3),
         (sizeXLabel, 'left', lm3),
         (sizeYLabel, 'top', tm3 + lineHeight),
         (sizeYLabel, 'left', lm3),
         (paddingLabel, 'top', tm3 + lineHeight * 2),
         (paddingLabel, 'left', lm3),
         (sceneSuffixLabel, 'top', tm4),
         (sceneSuffixLabel, 'left', lm1),
         (frameSuffixLabel, 'top', tm4 + lineHeight),
         (frameSuffixLabel, 'left', lm1),
         (renderPrefixLabel, 'top', tm4 + lineHeight*2),
         (renderPrefixLabel, 'left', lm1),
         (frameExampleLabel, 'top', tm4 + lineHeight * 3),
         (frameExampleLabel, 'left', lm1)])
        cmds.formLayout(mayaGlobalSettings, e=1, attachForm=[(sceneCtrl, 'top', tm2),
         (sceneCtrl, 'left', lm2),
         (projectCtrl, 'top', tm2 + lineHeight),
         (projectCtrl, 'left', lm2),
         (startCtrl, 'top', tm3),
         (startCtrl, 'left', lm2),
         (endCtrl, 'top', tm3 + lineHeight),
         (endCtrl, 'left', lm2),
         (stepCtrl, 'top', tm3 + lineHeight * 2),
         (stepCtrl, 'left', lm2),
         (sizeXCtrl, 'top', tm3),
         (sizeXCtrl, 'left', lm4),
         (sizeYCtrl, 'top', tm3 + lineHeight),
         (sizeYCtrl, 'left', lm4),
         (paddingCtrl, 'top', tm3 + lineHeight * 2),
         (paddingCtrl, 'left', lm4),
         (sceneSuffixCtrl, 'top', tm4),
         (sceneSuffixCtrl, 'left', lm2),
         (frameSuffixCtrl, 'top', tm4 + lineHeight),
         (frameSuffixCtrl, 'left', lm2),
         (renderPrefixCtrl, 'top', tm4 + lineHeight*2),
         (renderPrefixCtrl, 'left', lm2),
         (frameExample, 'top', tm4 + lineHeight * 3+10),
         (frameExample, 'left', lm1),
         (mustacheCtrl, 'left', lm5),
         (mustacheCtrl, 'top', tm2),
         (renderEngineLabel, 'top', tm2 + 160),
         (renderEngineLabel, 'left', lm5)])
        layersScroll = cmds.scrollLayout(w=250, h=150, parent=mayaGlobalSettings, ann='Render layers you want to render for this scene.')
        layersLabel = cmds.text(l='Render layers:', parent=mayaGlobalSettings)
        renderLayerControls = []
        rlayers = sorted(cmds.ls(type='renderLayer'))
        rlayersFiltered = list(set([ f for f in rlayers if ':' not in f ]))
        for i in rlayersFiltered:
            layerCtrl = cmds.checkBox(l=i, v=cmds.getAttr(i + '.renderable'), parent=layersScroll)
            renderLayerControls.append(layerCtrl)

        cameraCtrl = cmds.optionMenu(l='Render camera:', parent=mayaGlobalSettings, ann='The camera you want to render this scene with.', bgc=[1.0, 0.6, 0.7], cc=lambda *x: self.setImportantCtrl(cameraCtrl, cameraCtrl, poolCtrl, prepassCtrl, prepassLayerCtrl, submitBtn))
        defaultCams = ['topShape',
         'perspShape',
         'sideShape',
         'frontShape']
        cams = [ f for f in cmds.ls(type='camera') if f not in defaultCams ]
        for i in cams:
            cmds.menuItem(label=i)

        imagePlanesCtrl = cmds.checkBox(l='Render image planes', v=0, parent=mayaGlobalSettings, ann="Turn this option on if you want to render image planes, which you don't.")
        exr2tiffCtrl = cmds.checkBox(l='Post-convert EXR to TIFF', v=0, parent=mayaGlobalSettings, ann='Convert multichannel EXRs to TIFFs after rendering is completed.')
        vrayFormats = ['png',
         'jpg',
         'vrimg',
         'hdr',
         'exr',
         'exr (multichannel)',
         'tga',
         'bmp',
         'sgi',
         'tif']
        mayaFormats = {'8': 'jpg',
         '7': 'iff',
         '10': 'iff (16)',
         '31': 'psd',
         '36': 'psd (layers)',
         '32': 'png',
         '19': 'tga',
         '3': 'tif',
         '4': 'tif16',
         '13': 'sgi',
         '51': 'exr'}
        imageTypeCtrl = cmds.optionMenu(l='Image format:   ', parent=mayaGlobalSettings, ann='The file type you want to render. Some file formats are not supported by Mustache because they are stupid.', cc=lambda *x: self.parseRenderSuffix(sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, frameExample, imageTypeCtrl))
        formatIndex = 1
        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            for i in sorted(vrayFormats):
                cmds.menuItem(l=i)
                if i == cmds.getAttr('vraySettings.imageFormatStr'):
                    formatIndex = cmds.optionMenu(imageTypeCtrl, q=1, ni=1)

        else:
            for index, i in sorted(mayaFormats.iteritems(), key=operator.itemgetter(1)):
                cmds.menuItem(l=i)
                if index == str(cmds.getAttr('defaultRenderGlobals.imageFormat')):
                    formatIndex = cmds.optionMenu(imageTypeCtrl, q=1, ni=1)

        cmds.optionMenu(imageTypeCtrl, e=1, sl=formatIndex)
        cmds.formLayout(mayaGlobalSettings, e=1, attachForm=[(layersLabel, 'top', tm5),
         (layersLabel, 'left', lm1),
         (layersScroll, 'top', tm5 + lineHeight),
         (layersScroll, 'left', lm1),
         (cameraCtrl, 'top', tm5),
         (cameraCtrl, 'left', lm3),
         (imageTypeCtrl, 'top', tm5 + lineHeight),
         (imageTypeCtrl, 'left', lm3),
         (imagePlanesCtrl, 'top', tm5 + lineHeight * 2),
         (imagePlanesCtrl, 'left', lm3),
         (exr2tiffCtrl, 'top', tm5 + lineHeight * 3),
         (exr2tiffCtrl, 'left', lm3)])
        #####################################
        vraySettingsLayout = cmds.formLayout(parent=wrapperForm)
        cmds.formLayout(wrapperForm, e=1, attachForm=[(vraySettingsLayout, 'top', 450)])
        vraySettingsLabel = cmds.text(l='VRAY SPECIFIC SETTINGS', fn='boldLabelFont', parent=vraySettingsLayout)
        prepassCtrl = cmds.checkBox(l='Create irradiance map prepass', v=0, en=0, parent=vraySettingsLayout, cc=lambda *x: self.enablePrepassCtrl(prepassCtrl, prepassLayerCtrl, submitBtn), ann='If using irradiance map as primary GI method, create an automatic prepass to smooth out blotchiness. THIS IS SLOW.')
        prepassLayerCtrl = cmds.optionMenu(l='Prepass layer:  ', en=0, parent=vraySettingsLayout, ebg=0, bgc=[0.4, 0.4, 0.4], ann='If creating a prepass, choose the layer you are prepassing from. Typically your "beauty" layer.', cc=lambda *x: self.setImportantCtrl(prepassLayerCtrl, cameraCtrl, poolCtrl, prepassCtrl, prepassLayerCtrl, submitBtn))
        cmds.menuItem(l='')
        for i in rlayersFiltered:
            cmds.menuItem(l=i)

        memLimitLabel = cmds.text(l='Memory limit:', parent=vraySettingsLayout, ann='Memory limit for scene render. Minimum should be 5000 to prevent frequent memory flushing.')
        memLimitLabel2 = cmds.text(l='kb', parent=vraySettingsLayout)
        displaceLimitLabel = cmds.text(l='Displace limit:', parent=vraySettingsLayout, ann='Maximum number of subdivisions per triangle allowed when tessellating displaced or subdivision surfaces.')
        memLimit = 5000
        dispLimit = 4
        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            memLimit = cmds.getAttr('vraySettings.sys_rayc_dynMemLimit')
            dispLimit = cmds.getAttr('vraySettings.ddisplac_maxSubdivs')
        if int(memLimit) < 5000:
            memLimit = 5000
        memLimitCtrl = cmds.textField(tx=memLimit, w=smallInputWidth, parent=vraySettingsLayout, en=0)
        if int(dispLimit) > 4:
            dispLimit = 4
        displaceLimitCtrl = cmds.textField(tx=dispLimit, w=smallInputWidth, parent=vraySettingsLayout, en=0)
        if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
            cmds.checkBox(prepassCtrl, e=1, en=1)
            cmds.textField(memLimitCtrl, e=1, en=1)
            cmds.textField(displaceLimitCtrl, e=1, en=1)
        tm3 = 55
        cmds.formLayout(vraySettingsLayout, e=1, attachForm=[(vraySettingsLabel, 'top', tm1),
         (vraySettingsLabel, 'left', lm1),
         (prepassCtrl, 'top', tm2),
         (prepassCtrl, 'left', lm1),
         (prepassLayerCtrl, 'top', tm2),
         (prepassLayerCtrl, 'left', lm3),
         (memLimitLabel, 'top', tm3),
         (memLimitLabel, 'left', lm1),
         (memLimitLabel2, 'top', tm3),
         (memLimitLabel2, 'left', lm2 + 65),
         (displaceLimitLabel, 'top', tm3 + lineHeight),
         (displaceLimitLabel, 'left', lm1),
         (memLimitCtrl, 'top', tm3),
         (memLimitCtrl, 'left', lm2),
         (displaceLimitCtrl, 'top', tm3 + lineHeight),
         (displaceLimitCtrl, 'left', lm2)])
        #####################################
        rsSettingsLayout = cmds.formLayout(parent=wrapperForm)
        cmds.formLayout(wrapperForm, e=1, attachForm=[(rsSettingsLayout, 'top', 570)])
        rsSettingsLabel = cmds.text(l='REDSHIFT SPECIFIC SETTINGS', fn='boldLabelFont', parent=rsSettingsLayout)
        rsGpuLabel = cmds.text(l='GPUs per Frame:', parent=rsSettingsLayout)
        rsGpuRadioColCtrl = cmds.radioCollection(parent=rsSettingsLayout)
        rs1GpuCtrl = cmds.radioButton(l='1 GPU', en=0, cl=rsGpuRadioColCtrl, sl=1, ann='Use 1 GPU per frame. (Recommended)')
        rs2GpuCtrl = cmds.radioButton(l='2 GPUs', en=0, cl=rsGpuRadioColCtrl, ann='Use 2 GPUs per frame.')
        rs4GpuCtrl = cmds.radioButton(l='4 GPUs', en=0, cl=rsGpuRadioColCtrl, ann='Use 4 GPUs per frame.')
        #if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'redshift':
        #    cmds.radioButton(rs1GpuCtrl, e=1, en=1)
        #    cmds.radioButton(rs2GpuCtrl, e=1, en=1)
        #    cmds.radioButton(rs4GpuCtrl, e=1, en=1)
        gpuButtonSpacing = 60
        cmds.formLayout(rsSettingsLayout, e=1, attachForm=[(rsSettingsLabel, 'top', tm1),
         (rsSettingsLabel, 'left', lm1),
         (rsGpuLabel, 'top', tm2),
         (rsGpuLabel, 'left', lm1),
         (rs1GpuCtrl, 'top', tm2),
         (rs1GpuCtrl, 'left', lm2),
         (rs2GpuCtrl, 'top', tm2),
         (rs2GpuCtrl, 'left', lm2 + gpuButtonSpacing),
         (rs4GpuCtrl, 'top', tm2),
         (rs4GpuCtrl, 'left', lm2 + gpuButtonSpacing * 2)])
        rsButtonDict = {cmds.radioButton(rs1GpuCtrl, q=1, fpn=1).split('|')[-1]: 1, cmds.radioButton(rs2GpuCtrl, q=1, fpn=1).split('|')[-1]: 2, cmds.radioButton(rs4GpuCtrl, q=1, fpn=1).split('|')[-1]: 4}
        #####################################
        musterSettingsLayout = cmds.formLayout(parent=wrapperForm)
        cmds.formLayout(wrapperForm, e=1, attachForm=[(musterSettingsLayout, 'top', 640)])
        musterSettingsLabel = cmds.text(l='MUSTER SETTINGS', fn='boldLabelFont', parent=musterSettingsLayout)
        priorityLabel = cmds.text(l='Priority:', parent=musterSettingsLayout, ann='Priority of the job. 100 is highest. Folder priority will determine the overall priority against other projects.')
        packetLabel = cmds.text(l='Packet size:', parent=musterSettingsLayout, ann="Number of frames to submit at a time. The more memory-intensive the scene, the smaller the size you should use. If you're not sure, use 1.")
        minSizeLabel = cmds.text(l='Min size:', parent=musterSettingsLayout, ann='The smallest image size (in KB) that you expect to render. Anything smaller will be considered a bad frame and requeued.')
        notesLabel = cmds.text(l='Notes:', parent=musterSettingsLayout, ann='Scene notes. These will appear in the "notes" column in Muster, and be sent to anyone on the email list.')
        emailsLabel = cmds.text(l='Email notify:', parent=musterSettingsLayout, ann='}MUSTACHE{ will notify via email anyone in this list. Separate email addresses with commas.')
        priorityCtrl = cmds.textField(w=smallInputWidth, tx='50')
        packetCtrl = cmds.textField(w=smallInputWidth, tx='1')
        minSizeCtrl = cmds.textField(w=smallInputWidth, tx='2')
        notesCtrl = cmds.textField(w=largeInputWidth)
        emailsCtrl = cmds.textField(w=largeInputWidth)
#        for f in musterFolders:
#            cmds.menuItem(l=f[0])
        poolCtrl = cmds.optionMenu(l='Muster pool:     ', parent=musterSettingsLayout, bgc=[1.0, 0.6, 0.7], cc=lambda *x: self.setImportantCtrl(poolCtrl, cameraCtrl, poolCtrl, prepassCtrl, prepassLayerCtrl, submitBtn), ann="The pool of computers dedicated to rendering your job. If you don't know which one to use, ask a supervisor.")
        pools = list(MUSTER_POOLS)
        for p in pools:
            cmds.menuItem(l=p)
        #####################################
        submitBtn = cmds.button(l='Submit render', w=150, h=60, bgc=[1.0, 0.6, 0.7], en=0, parent=musterSettingsLayout,
            c=lambda *x: self.userSubmit( pool = cmds.optionMenu(poolCtrl, q=1, v=1),
                priority = cmds.textField(priorityCtrl, q=1, tx=1),
                start = cmds.textField(startCtrl, q=1, tx=1),
                end = cmds.textField(endCtrl, q=1, tx=1),
                step = cmds.textField(stepCtrl, q=1, tx=1),
                packet = cmds.textField(packetCtrl, q=1, tx=1),
                x = cmds.textField(sizeXCtrl, q=1, tx=1),
                y = cmds.textField(sizeYCtrl, q=1, tx=1),
                flags = '',
                notes = cmds.textField(notesCtrl, q=1, tx=1),
                emails = cmds.textField(emailsCtrl, q=1, tx=1),
                framecheck = 1,
                minsize = cmds.textField(minSizeCtrl, q=1, tx=1),
                renderCam = cmds.optionMenu(cameraCtrl, q=1, v=1),
                imgPlanes = cmds.checkBox(imagePlanesCtrl, q=1, v=1),
                suffix = cmds.textField(sceneSuffixCtrl, q=1, tx=1),
                endSuffix = cmds.textField(frameSuffixCtrl, q=1, tx=1),
                renderLayers = self.getEnabledRenderLayers(renderLayerControls),
                prepassBeautyLayer = cmds.optionMenu(prepassLayerCtrl, q=1, v=1),
                depend = '0',
                framePadding = cmds.textField(paddingCtrl, q=1, tx=1),
                imageType = cmds.optionMenu(imageTypeCtrl, q=1, v=1),
                memLimit = cmds.textField(memLimitCtrl, q=1, tx=1),
                displaceLimit = cmds.textField(displaceLimitCtrl, q=1, tx=1),
                exr2tiff = cmds.checkBox(exr2tiffCtrl, q=1, v=1),
                rsGpus = rsButtonDict[cmds.radioCollection(rsGpuRadioColCtrl, q=1, sl=1)]
                )
            )
        resetBtn = cmds.button(l='Reset to default', w=150, h=60, parent=musterSettingsLayout, c=lambda x: self.submitUI())
        closeBtn = cmds.button(l='Close window', w=150, h=60, parent=musterSettingsLayout, c=lambda x: cmds.deleteUI(window))
        cmds.formLayout(musterSettingsLayout, e=1, attachForm=[(musterSettingsLabel, 'top', tm1),
         (musterSettingsLabel, 'left', lm1),
         (priorityLabel, 'top', tm2),
         (priorityLabel, 'left', lm1),
         (packetLabel, 'top', tm2 + lineHeight),
         (packetLabel, 'left', lm1),
         (minSizeLabel, 'top', tm2 + lineHeight * 2),
         (minSizeLabel, 'left', lm1),
         (notesLabel, 'top', tm2 + lineHeight * 4),
         (notesLabel, 'left', lm1),
         (emailsLabel, 'top', tm2 + lineHeight * 6),
         (emailsLabel, 'left', lm1),
         (priorityCtrl, 'top', tm2),
         (priorityCtrl, 'left', lm2),
         (packetCtrl, 'top', tm2 + lineHeight),
         (packetCtrl, 'left', lm2),
         (minSizeCtrl, 'top', tm2 + lineHeight * 2),
         (minSizeCtrl, 'left', lm2),
         (notesCtrl, 'top', tm2 + lineHeight * 4),
         (notesCtrl, 'left', lm2),
         (emailsCtrl, 'top', tm2 + lineHeight * 6),
         (emailsCtrl, 'left', lm2),
         (poolCtrl, 'top', tm2 + lineHeight),
         (poolCtrl, 'left', lm3),
#         (folderCtrl, 'top', tm2 + lineHeight * 2),
#         (folderCtrl, 'left', lm3),
         (submitBtn, 'top', tm2),
         (submitBtn, 'left', lm5),
         (resetBtn, 'top', tm2 + lineHeight * 3),
         (resetBtn, 'left', lm5),
         (closeBtn, 'top', tm2 + lineHeight * 6),
         (closeBtn, 'left', lm5)])
        self.parseRenderSuffix(sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, frameExample, imageTypeCtrl)
        self.parseImagePrefix(renderPrefixCtrl,sceneSuffixCtrl, frameSuffixCtrl, paddingCtrl, frameExample, imageTypeCtrl)
        mustacheDir = '//scholar/code/maya/icons/mustaches'
        if os.path.exists(mustacheDir):
            mustaches = [ f for f in os.listdir(mustacheDir) if os.path.splitext(f)[-1] == '.jpg' ]
            rand = random.randint(0, len(mustaches) - 1)
            img = os.path.join(mustacheDir, mustaches[rand])
            cmds.image(mustacheCtrl, e=1, i=img)
        cmds.showWindow(window)
        cmds.window(window, e=1, w=800, h=800)

    def setImportantCtrl(self, ctrl, camCtrl, poolCtrl, prepassCtrl, prepassLayerCtrl, submitBtn, *args):
        cmds.optionMenu(ctrl, e=1, bgc=[0.6, 1.0, 0.7])
        a = cmds.optionMenu(camCtrl, q=1, bgc=1)[1]
        c = cmds.optionMenu(poolCtrl, q=1, bgc=1)[1]
        e = 1.0
        if cmds.checkBox(prepassCtrl, q=1, v=1) == 1:
            e = cmds.optionMenu(prepassLayerCtrl, q=1, bgc=1)[1]
        if a == 1.0 and c == 1.0 and e == 1.0:
            cmds.button(submitBtn, e=1, en=1, bgc=[0.6, 1.0, 0.7])
        else:
            cmds.button(submitBtn, e=1, en=0, bgc=[1.0, 0.6, 0.7])

    def enablePrepassCtrl(self, prepassCtrl, prepassLayerCtrl, submitBtn, *args):
        prepass = cmds.checkBox(prepassCtrl, q=1, v=1)
        if prepass:
            cmds.optionMenu(prepassLayerCtrl, e=1, en=1, bgc=[1.0, 0.6, 0.7])
        else:
            cmds.optionMenu(prepassLayerCtrl, e=1, en=0, bgc=[0.4, 0.4, 0.4])
            cmds.optionMenu(prepassLayerCtrl, e=1, sl=1)

    def getEnabledRenderLayers(self, renderLayerControls, *args):
        enabledLayers = []
        for i in renderLayerControls:
            if cmds.checkBox(i, q=1, v=1):
                enabledLayers.append(cmds.checkBox(i, q=1, l=1))

        return enabledLayers
