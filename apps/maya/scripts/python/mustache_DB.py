import os
import maya.mel as mel
import maya.cmds as cmds
import shutil
from xml.etree import ElementTree as ET
import xml.dom.minidom
from xml.parsers.expat import ExpatError
import subprocess
import pickle
import re
import natSort
import string

class MustacheDB:

    def __init__(self, *args):
        self.categories = ['Miscellaneous',
         'Abstract',
         'Logos',
         'Furnishings',
         'Architecture',
         'Vehicles',
         'Characters',
         'Collections',
         'Electronics',
         'Sports & Hobbies',
         'Weapons & Armor',
         'Industrial',
         'Aircraft',
         'Plants',
         'Animals',
         'Food',
         'Science',
         'Containers',
         'Watercraft',
         'Spacecraft']
        print 'init asset library'

    def initDB(self):
        if not os.path.exists(self.M.assetsDatabase):
            df = open(self.M.assetsDatabase, 'w')
            df.write('<assets></assets>')
            df.close()
        if not os.path.exists(self.M.assetsBlacklist):
            df = open(self.M.assetsBlacklist, 'w')
            df.write('<blacklist></blacklist>')
            df.close()

    def backupDB(self, *args):
        shutil.copy(self.M.assetsDatabase, self.M.assetsDatabase + '.BAK')
        shutil.copy(self.M.assetsBlacklist, self.M.assetsBlacklist + '.BAK')

    def scanMayaFiles(self, root, ext = ['.ma', '.mb', '.obj']):
        mayaFiles = []
        for root, dirs, files in os.walk(root):
            for file in files:
                print 'analyzing %s' % os.path.join(root, file)
                if os.path.splitext(file)[-1] in ext:
                    mayaFiles.append(os.path.join(root, file).replace('\\', '/'))

        return natSort.natsorted(mayaFiles)

    def getUniqueName(self, name, folder):
        files = os.listdir(folder)
        for k, v in enumerate(files):
            files[k] = v.lower()

        i = 0
        suff = ''
        iterName = name.lower()
        regex = re.compile('^(.)*_[0-9]{3}$')
        while iterName in files:
            i = i + 1
            suff = '_' + str(i).zfill(3)
            search = regex.search(iterName)
            if search:
                iterName = '_'.join(iterName.split('_')[:-1]) + suff
            else:
                iterName = iterName + suff

        return iterName

    def waitForAccess(self, i = 5, *args):
        try:
            dbfile = ET.parse(self.M.assetsDatabase)
            blackfile = ET.parse(self.M.assetsBlacklist)
            return True
        except ExpatError:
            if i > 0:
                cmds.warning('Database is being modified by another user. Waiting...')
                cmds.pause(sec=1)
                access = self.waitForAccess(i - 1)
            else:
                cmds.error('Could not access database. The XML files are possibly corrupt. Check error log for bad tags.')

    def processFiles(self, folder, category = 'UNCATEGORIZED', tags = ''):
        self.initDB()
        if not os.path.exists(folder):
            cmds.error('Directory does not exist.')
        mayaFiles = self.scanMayaFiles(folder)
        okFiles = []
        blacklist = []
        progbar = mel.eval('$temp = $gMainProgressBar')
        progStr = 'initializing...'
        if len(mayaFiles) < 1:
            cmds.error('No Maya files found in ' + folder)
        cmds.progressBar(progbar, e=1, bp=1, ii=1, status=progStr, max=len(mayaFiles), pr=0)
        for index, f in enumerate(mayaFiles):
            if cmds.progressBar(progbar, q=1, ic=1):
                cmds.progressBar(progbar, e=1, ep=1)
                cmds.error('Cancelled operation.')
            progStr = 'processing file %d of %d... (%s)' % (index + 1, len(mayaFiles), f)
            cmds.progressBar(progbar, e=1, status=progStr, step=1)
            ok = True
            assetName = os.path.splitext(os.path.basename(f))[0]
            access = self.waitForAccess()
            blackDB = ET.parse(self.M.assetsBlacklist)
            blackroot = blackDB.getroot()
            blacklisted = [ asset.get('path') for asset in blackroot.findall('asset') if asset.get('path') == f ]
            if not blacklisted:
                access = self.waitForAccess()
                fileDB = ET.parse(self.M.assetsDatabase)
                fileroot = fileDB.getroot()
                dupes = [ asset.get('path') for asset in fileroot.findall('asset') if os.path.splitext(os.path.basename(asset.get('path')).lower())[0] == os.path.splitext(os.path.basename(f).lower())[0] ]
                if dupes:
                    for d in dupes:
                        if os.path.getsize(d) == os.path.getsize(f):
                            ok = False

                    if ok:
                        assetName = self.getUniqueName(assetName, self.M.assetsLib)
                        print 'renaming asset to %s' % assetName
                if ok:
                    pFile = open(os.path.join(os.environ['USERPROFILE'], 'mustacheDB_out'), 'w')
                    print 'Creating preview for file %s' % f
                    pickle.dump(f, pFile, pickle.HIGHEST_PROTOCOL)
                    pFile.close()
                    startup = subprocess.STARTUPINFO()
                    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subp = subprocess.Popen(os.path.join(self.M.mayaDir, 'mayapy.exe') + ' ' + os.path.join(self.M.scriptsDir, '..', 'python', 'm_processLibraryFiles.py'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startup)
                    stdout, stderr = subp.communicate()
                    logfile = open(os.path.join(os.environ['USERPROFILE'], 'mustacheDB_logfile.txt'), 'w')
                    logstr = 'stdout: \n' + stdout + '\n\nstderr: \n' + stderr + '\n------END LOG------'
                    logfile.write(logstr)
                    logfile.close()
                    exitcode = subp.returncode
                    if str(exitcode) != '0':
                        print 'ERROR: File %s is broken and added to blacklist.' % f
                        blacklist.append(f)
                        access = self.waitForAccess()
                        elem = ET.SubElement(blackroot, 'asset', path=f)
                        blackDB.write(self.M.assetsBlacklist)
                    else:
                        returnFile = open(os.path.join(os.environ['USERPROFILE'], 'mustacheDB_in'), 'r')
                        inData = pickle.load(returnFile)
                        returnFile.close()
                        print '\n File %s processed successfully.' % f
                        filename = inData[0]
                        screen = inData[1]
                        texstring = inData[2]
                        outfile = inData[3]
                        if not os.path.exists(screen):
                            blacklist.append(f)
                            access = self.waitForAccess()
                            elem = ET.SubElement(blackroot, 'asset', path=f)
                            blackDB.write(self.M.assetsBlacklist)
                            print '\n Just kidding! File %s is broken and added to blacklist.' % f
                        else:
                            textures = texstring.split(',')
                            ext = '.mb'
                            if not os.path.exists(os.path.join(self.M.assetsLib, assetName)):
                                os.makedirs(os.path.join(self.M.assetsLib, assetName))
                            print 'copying new asset file: %s' % os.path.join(self.M.assetsLib, assetName, assetName + ext)
                            shutil.copyfile(outfile, os.path.join(self.M.assetsLib, assetName, assetName + ext))
                            print 'copying new screenshot: %s' % os.path.join(self.M.assetsLib, assetName, assetName + '.jpg')
                            shutil.copyfile(screen, os.path.join(self.M.assetsLib, assetName, assetName + '.jpg'))
                            if len(textures) > 0:
                                if not os.path.exists(os.path.join(self.M.assetsLib, assetName, 'tex')):
                                    os.makedirs(os.path.join(self.M.assetsLib, assetName, 'tex'))
                                for tex in textures:
                                    if not os.path.exists(tex):
                                        end = False
                                        sourceImages = filename
                                        iterations = 20
                                        while end == False and iterations > 0:
                                            try:
                                                if sourceImages == os.path.dirname(sourceImages):
                                                    sourceImages = False
                                                    end = True
                                                    break
                                                dirname = os.path.dirname(sourceImages)
                                                dirslist = os.listdir(dirname)
                                                if 'sourceimages' in dirslist:
                                                    sourceImages = os.path.join(dirname, 'sourceimages')
                                                    end = True
                                                elif dirname == '//':
                                                    sourceImages = False
                                                    end = True
                                                else:
                                                    sourceImages = dirname
                                                    iterations = iterations - 1
                                            except:
                                                sourceImages = False
                                                end = True

                                        if sourceImages:
                                            for root, dirs, files in os.walk(sourceImages):
                                                for testfile in files:
                                                    if os.path.basename(testfile) == os.path.basename(tex):
                                                        tex = os.path.join(root, testfile)

                                        else:
                                            for root, dirs, files in os.walk(os.path.dirname(f)):
                                                for testfile in files:
                                                    if os.path.basename(testfile) == os.path.basename(tex):
                                                        tex = os.path.join(root, testfile)

                                    if os.path.exists(tex):
                                        print 'copying texture file: %s' % tex
                                        shutil.copyfile(tex, os.path.join(self.M.assetsLib, assetName, 'tex', os.path.basename(tex)))

                            access = self.waitForAccess()
                            fileDB = ET.parse(self.M.assetsDatabase)
                            fileroot = fileDB.getroot()
                            ET.SubElement(fileroot, 'asset', category=category, name=assetName, path=os.path.join(self.M.assetsLib, assetName, assetName + ext).replace('\\', '/'), screen=os.path.join(self.M.assetsLib, assetName, assetName + '.jpg').replace('\\', '/'), tags=tags)
                            fileDB.write(self.M.assetsDatabase)
                            print 'Added new asset to database: %s' % assetName
                            okFiles.append(os.path.join(self.M.assetsLib, assetName, assetName + ext).replace('\\', '/'))
                else:
                    print 'duplicate file found: %s' % f
            else:
                print 'blacklisted file found: %s' % f

        cmds.progressBar(progbar, e=1, ep=1)
        access = self.waitForAccess()
        dbfile = xml.dom.minidom.parse(self.M.assetsDatabase)
        prettydb = dbfile.toprettyxml()
        lines = []
        for line in prettydb.split('\n'):
            if line.strip() != '':
                lines.append(line)

        writefile = file(self.M.assetsDatabase, 'w')
        writefile.write('\n'.join(lines))
        writefile.close()
        access = self.waitForAccess()
        blfile = xml.dom.minidom.parse(self.M.assetsBlacklist)
        prettybl = blfile.toprettyxml()
        lines = []
        for line in prettybl.split('\n'):
            if line.strip() != '':
                lines.append(line)

        writebl = file(self.M.assetsBlacklist, 'w')
        writebl.write('\n'.join(lines))
        writebl.close()
        print '\n...done! %d files added to MustacheDB.' % len(okFiles)
        if len(blacklist) > 0:
            print '%d files added to blacklist.' % len(blacklist)
        self.backupDB()
        return (okFiles, blacklist)

    def libraryUI(self, *args):
        self.initDB()
        user = self.M.user
        if user == '':
            cmds.error('No user detected. Restart Mustache.')
        windowName = 'mustache_DBUI'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title='}MUSTACHE{ - Asset Library')
        form = cmds.formLayout()
        tm1 = 40
        tm2 = 60
        tm3 = 273
        tm4 = 293
        tm5 = 328
        tm6 = 370
        tm7 = 440
        lm0 = 10
        lm1 = 150
        lm2 = 200
        lm3 = 310
        lm4 = 520
        lm5 = 620
        changeProjCtrl = cmds.button(l='Change project...', w=110, h=25, c=lambda *x: self.M.setProjectUI(False, False))
        changeProjText = cmds.textField(tx=self.M.project, w=340, en=0)
        changeUserCtrl = cmds.button(l='Change user...', w=110, h=25, c=lambda *x: self.M.setUserUI(False, False, False))
        changeUserText = cmds.textField(tx=self.M.user, w=35, en=0)
        cmds.formLayout(form, e=1, attachForm=[(changeProjCtrl, 'top', 5),
         (changeProjCtrl, 'left', 5),
         (changeProjText, 'top', 8),
         (changeProjText, 'left', 120),
         (changeUserCtrl, 'top', 5),
         (changeUserCtrl, 'left', 485),
         (changeUserText, 'top', 8),
         (changeUserText, 'left', 600)])
        catsL = cmds.text(l='Categories', fn='boldLabelFont')
        azL = cmds.text(l='A-Z', fn='boldLabelFont')
        tagsL = cmds.text(l='Tags', fn='boldLabelFont')
        assetsL = cmds.text(l='Assets', fn='boldLabelFont')
        infoL = cmds.text(l='Info (click image to enlarge)', fn='boldLabelFont')
        cmds.formLayout(form, e=1, attachForm=[(catsL, 'top', tm1),
         (catsL, 'left', lm0),
         (azL, 'top', tm1),
         (azL, 'left', lm1),
         (tagsL, 'top', tm1),
         (tagsL, 'left', lm2),
         (assetsL, 'top', tm1),
         (assetsL, 'left', lm3),
         (infoL, 'top', tm1),
         (infoL, 'left', lm4)])
        self.catsLabel = cmds.text(l='CATEGORIES:', fn='boldLabelFont', al='left')
        self.assetsCount = cmds.text(l='')
        self.assetsCountLabel = cmds.text(l='TOTAL ASSETS:', fn='boldLabelFont')
        self.catsText = cmds.textField(tx='', w=260, ed=0)
        self.tagsLabel = cmds.text(l='TAGS:', fn='boldLabelFont', al='left')
        self.tagsText = cmds.scrollField(tx='', w=260, h=60, fn='smallPlainLabelFont', ed=0, ww=1)
        self.sizeLabel = cmds.text(l='SIZE:', fn='boldLabelFont')
        self.sizeText = cmds.text(l='(no file selected)')
        self.pathLabel = cmds.text(l='PATH:', fn='boldLabelFont')
        self.pathText = cmds.textField(tx='', w=260, ed=0, fn='smallPlainLabelFont')
        cmds.formLayout(form, e=1, attachForm=[(self.sizeLabel, 'top', tm3),
         (self.sizeLabel, 'left', lm4),
         (self.sizeText, 'top', tm3),
         (self.sizeText, 'left', lm5),
         (self.catsLabel, 'top', tm4),
         (self.catsLabel, 'left', lm4),
         (self.catsText, 'top', tm4),
         (self.catsText, 'left', lm5),
         (self.tagsLabel, 'top', tm6),
         (self.tagsLabel, 'left', lm4),
         (self.tagsText, 'top', tm6),
         (self.tagsText, 'left', lm5),
         (self.pathLabel, 'top', tm5),
         (self.pathLabel, 'left', lm4),
         (self.pathText, 'top', tm5),
         (self.pathText, 'left', lm5),
         (self.assetsCountLabel, 'top', tm7),
         (self.assetsCountLabel, 'left', lm4),
         (self.assetsCount, 'top', tm7),
         (self.assetsCount, 'left', lm5)])
        self.alphaList = cmds.textScrollList(w=40, h=400, ams=1, fn='boldLabelFont', sc=lambda *x: self.popLibrary())
        self.catsList = cmds.textScrollList(w=130, h=400, ams=1, fn='boldLabelFont', sc=lambda *x: self.changeCategory())
        self.tagsList = cmds.textScrollList(w=100, h=400, ams=1, sc=lambda *x: self.popLibrary())
        self.assetList = cmds.textScrollList(w=200, h=400, ams=1, fn='fixedWidthFont', sc=lambda *x: self.showAssetInfo())
        self.screenCtrl = cmds.symbolButton(w=360, h=203, i=self.M.defaultImage, c=lambda *x: self.zoomIn(cmds.symbolButton(self.screenCtrl, q=1, i=1)))
        self.assetFilterCtrl = cmds.textField(tx='', w=130, cc=lambda *x: self.popLibrary(self.assetFilterCtrl))
        cmds.formLayout(form, e=1, attachForm=[(self.alphaList, 'top', tm2),
         (self.alphaList, 'left', lm1),
         (self.tagsList, 'top', tm2),
         (self.tagsList, 'left', lm2),
         (self.assetList, 'top', tm2),
         (self.assetList, 'left', lm3),
         (self.screenCtrl, 'top', tm2),
         (self.screenCtrl, 'left', lm4),
         (self.catsList, 'top', tm2),
         (self.catsList, 'left', lm0),
         (self.assetFilterCtrl, 'top', tm1 - 3),
         (self.assetFilterCtrl, 'left', lm3 + 60)])
        bw = 120
        bh = 75
        margin = 125
        buttonForm = cmds.formLayout(parent=form, w=880)
        searchBtn = cmds.button(w=bw, h=bh, l='Search folder', bgc=[0.6, 0.7, 1.0], parent=buttonForm, c=lambda *x: self.searchFolderUI())
        assetBtn = cmds.button(w=bw, h=bh, l='Send to project', bgc=[0.6, 1.0, 0.7], parent=buttonForm, c=lambda *x: self.sendToProject())
        importBtn = cmds.button(w=bw, h=bh, l='Import to scene', parent=buttonForm, c=lambda *x: self.importAsset())
        openBtn = cmds.button(w=bw, h=bh, l='Open file', parent=buttonForm, c=lambda *x: self.openAsset(self.assetList))
        renameBtn = cmds.button(w=bw, h=bh, l='Rename asset', parent=buttonForm, c=lambda *x: self.renameAsset(self.assetList))
        editInfoBtn = cmds.button(w=bw, h=bh, l='Edit info', parent=buttonForm, c=lambda *x: self.editInfoUI())
        deleteBtn = cmds.button(w=bw, h=bh, l='Delete', bgc=[1.0, 0.6, 0.7], parent=buttonForm, c=lambda *x: self.deleteAssets(cmds.textScrollList(self.assetList, q=1, si=1)))
        cmds.formLayout(buttonForm, e=1, attachForm=[(searchBtn, 'left', 0),
         (assetBtn, 'left', margin),
         (importBtn, 'left', margin * 2),
         (openBtn, 'left', margin * 3),
         (renameBtn, 'left', margin * 4),
         (editInfoBtn, 'left', margin * 5),
         (deleteBtn, 'left', margin * 6)])
        cmds.formLayout(form, e=1, attachForm=[(buttonForm, 'left', lm0), (buttonForm, 'top', 470)])
        cmds.showWindow(window)
        self.popAlphaList()
        self.popTagsList()
        self.popCatsList()
        self.popLibrary()
        cmds.window(window, e=1, w=900, h=550)

    def popAlphaList(self, *args):
        letters = ['<all>']
        letters.extend(list(string.ascii_uppercase))
        cmds.textScrollList(self.alphaList, e=1, ra=1)
        for i in letters:
            cmds.textScrollList(self.alphaList, e=1, a=i)

    def popCatsList(self, *args):
        cats = natSort.natsorted(self.categories)
        cats.insert(0, '<all>')
        cats.insert(1, 'UNCATEGORIZED')
        cmds.textScrollList(self.catsList, e=1, ra=1)
        for i in cats:
            cmds.textScrollList(self.catsList, e=1, a=i)

    def changeCategory(self, *args):
        self.popTagsList()
        self.popLibrary()

    def popTagsList(self, *args):
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        categories = cmds.textScrollList(self.catsList, q=1, si=1)
        getTags = []
        if categories and '<all>' not in categories:
            getTags = [ f.get('tags') for f in dbroot.findall('asset') if set(categories) & set(f.get('category').split(',')) ]
        else:
            getTags = [ f.get('tags') for f in dbroot.findall('asset') ]
        tags = []
        for i in getTags:
            if ',' in i:
                tag = list(set(i.split(',')))
                tags.extend(tag)
            elif i != '':
                tags.append(i)

        seltags = cmds.textScrollList(self.tagsList, q=1, si=1)
        cmds.textScrollList(self.tagsList, e=1, ra=1)
        tags = natSort.natsorted(list(set(tags)))
        tags.insert(0, '<all>')
        for tag in tags:
            cmds.textScrollList(self.tagsList, e=1, a=tag)

        if seltags:
            cmds.textScrollList(self.tagsList, e=1, si=seltags)

    def popLibrary(self, filterCtrl = '', *args):
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        assets = []
        for f in dbroot.findall('asset'):
            asset = {}
            asset['name'] = f.get('name')
            asset['tags'] = f.get('tags')
            asset['category'] = f.get('category')
            assets.append(asset)

        cmds.text(self.assetsCount, e=1, l=len(assets))
        letters = cmds.textScrollList(self.alphaList, q=1, si=1)
        if letters and '<all>' not in letters:
            assets = [ f for f in assets if f['name'][0].upper() in letters ]
        cats = cmds.textScrollList(self.catsList, q=1, si=1)
        if cats and '<all>' not in cats:
            assets = [ f for f in assets if set(f['category'].split(',')) & set(cats) ]
        tags = cmds.textScrollList(self.tagsList, q=1, si=1)
        if tags and '<all>' not in tags:
            assets = [ f for f in assets if set(f['tags'].split(',')) & set(tags) ]
        selasset = cmds.textScrollList(self.assetList, q=1, si=1)
        cmds.textScrollList(self.assetList, e=1, ra=1)
        sortedList = []
        for i in assets:
            sortedList.append(i['name'])

        sortedList = sorted(sortedList, key=str.lower)
        if filterCtrl != '':
            filth = cmds.textField(filterCtrl, q=1, tx=1)
            if not filth or filth != '':
                sortedList = [ f for f in sortedList if filth in f ]
        for i in sortedList:
            cmds.textScrollList(self.assetList, e=1, a=i)

        if selasset:
            cmds.textScrollList(self.assetList, e=1, si=selasset)
            self.showAssetInfo()

    def getInfo(self, asset, *args):
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        match = [ f for f in dbroot.findall('asset') if f.get('name') == asset ]
        try:
            screen = match[0].get('screen')
            tags = sorted(match[0].get('tags').split(','), key=str.lower)
            category = sorted(match[0].get('category').split(','), key=str.lower)
            path = match[0].get('path')
            size = os.path.getsize(path)
            return (path,
             screen,
             category,
             tags,
             size)
        except WindowsError as IndexError:
            remove = cmds.confirmDialog(ma='left', title='Missing asset', icn='warning', message='The asset ' + asset + ' may have been improperly removed or modified. Remove entry from database?', button=['yes', 'no'], defaultButton='no', cancelButton='no', dismissString='no')
            if remove == 'yes':
                dbroot.remove(match[0])
                dbfile.write(self.M.assetsDatabase)
                cmds.textScrollList(self.assetList, e=1, da=1)
            else:
                cmds.error('Error loading file info.')
            self.popLibrary()

    def zoomIn(self, image, *args):
        windowName = 'libraryZoomWindow'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title='}MUSTACHE{ - Asset Library Magnifier')
        layout = cmds.formLayout()
        imgCtrl = cmds.image(w=720, h=405, i=image)
        cmds.showWindow(window)
        cmds.window(windowName, e=1, w=720, h=405)

    def showAssetInfo(self, *args):
        asset = cmds.textScrollList(self.assetList, q=1, si=1)
        try:
            path, screen, category, tags, size = self.getInfo(asset[-1])
            if not screen or not os.path.exists(screen):
                cmds.symbolButton(self.screenCtrl, e=1, i=self.M.defaultImage)
            else:
                cmds.symbolButton(self.screenCtrl, e=1, i=screen)
            sizeFixed = '%.2f MB on disk' % (float(size) / 1048576.0)
            cmds.text(self.sizeText, e=1, l=sizeFixed)
            cmds.textField(self.catsText, e=1, tx=', '.join(category))
            cmds.scrollField(self.tagsText, e=1, tx=', '.join(tags))
            cmds.textField(self.pathText, e=1, tx=path)
        except TypeError:
            pass

    def searchFolderUI(self, *args):
        window = 'mustacheDB_searchWindow'
        if cmds.window(window, q=1, exists=1):
            cmds.deleteUI(window)
        cmds.window(window, t='Search for assets')
        form = cmds.formLayout()
        tm0 = 10
        tm1 = 30
        tm2 = 70
        tm3 = 90
        tm4 = 190
        tm45 = 290
        tm5 = 360
        tm6 = 430
        tm7 = 500
        tm8 = 570
        lm0 = 10
        lm1 = 150
        lm2 = 290
        catsL = cmds.text(l='Apply categories:', fn='boldLabelFont')
        tagsL = cmds.text(l='Apply tags:', fn='boldLabelFont')
        newTagsL = cmds.text(l='Separate new tags with commas:')
        searchL = cmds.text(l='Search folder:', fn='boldLabelFont')
        cmds.formLayout(form, e=1, attachForm=[(searchL, 'top', tm0),
         (searchL, 'left', lm0),
         (catsL, 'top', tm2),
         (catsL, 'left', lm0),
         (tagsL, 'top', tm2),
         (tagsL, 'left', lm1),
         (newTagsL, 'top', tm2),
         (newTagsL, 'left', lm2)])
        folderBtn = cmds.button(w=40, h=26, l='>>', c=lambda *x: cmds.textField(folderText, e=1, tx=cmds.fileDialog2(ds=2, okc='Choose', cap='Choose a folder to scan for Maya files...', dir=self.M.assetsLib, fm=3)[0]))
        folderText = cmds.textField(w=400, h=26)
        catsList = cmds.textScrollList(w=130, h=400, ams=1, fn='boldLabelFont')
        tagsList = cmds.textScrollList(w=130, h=540, ams=1)
        newTagBtn = cmds.button(w=200, h=60, l='Add new tags', c=lambda *x: self.addNewTags(tagsList, newTagWindow))
        newTagWindow = cmds.scrollField(w=200, h=90, ww=1)
        processBtn = cmds.button(w=200, h=60, l='Process folder', bgc=[0.6, 0.7, 1.0], c=lambda *x: self.doProcessFiles(cmds.textField(folderText, q=1, tx=1), cmds.textScrollList(catsList, q=1, si=1), cmds.textScrollList(tagsList, q=1, si=1), window))
        cancelBtn = cmds.button(w=200, h=60, l='Cancel', c=lambda *x: cmds.deleteUI(window))
        blacklistBtn = cmds.button(w=200, h=60, l='View blacklist', c=lambda *x: self.viewBlacklist())
        processProjectBtn = cmds.button(w=200, h=60, l='Process current project', bgc=[1.0, 0.6, 0.7], c=lambda *x: self.doProcessProject(cmds.textScrollList(catsList, q=1, si=1), cmds.textScrollList(tagsList, q=1, si=1), window))
        processFileBtn = cmds.button(w=200, h=60, l='Process current file', c=lambda *x: self.doProcessFile(cmds.textScrollList(catsList, q=1, si=1), cmds.textScrollList(tagsList, q=1, si=1), window))
        cmds.formLayout(form, e=1, attachForm=[(catsList, 'top', tm3),
         (catsList, 'left', lm0),
         (tagsList, 'top', tm3),
         (tagsList, 'left', lm1),
         (folderBtn, 'top', tm1),
         (folderBtn, 'left', lm0),
         (folderText, 'top', tm1),
         (folderText, 'left', lm0 + 45),
         (newTagBtn, 'top', tm4),
         (newTagBtn, 'left', lm2),
         (processBtn, 'top', tm5),
         (processBtn, 'left', lm2),
         (cancelBtn, 'top', tm8),
         (cancelBtn, 'left', lm2),
         (newTagWindow, 'top', tm3),
         (newTagWindow, 'left', lm2),
         (blacklistBtn, 'top', tm45),
         (blacklistBtn, 'left', lm2),
         (processProjectBtn, 'top', tm6),
         (processProjectBtn, 'left', lm2),
         (processFileBtn, 'top', tm7),
         (processFileBtn, 'left', lm2)])
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        tags = [ f.get('tags') for f in dbroot.findall('asset') ]
        tagsSorted = []
        for i in tags:
            each = i.split(',')
            for j in each:
                if j.strip() != '':
                    tagsSorted.append(j)

        tagsSorted = sorted(list(set(tagsSorted)), key=str.lower)
        tagsSorted.insert(0, '<None>')
        for i in tagsSorted:
            cmds.textScrollList(tagsList, e=1, a=i)

        cmds.textScrollList(catsList, e=1, a='UNCATEGORIZED')
        for i in sorted(self.categories, key=str.lower):
            cmds.textScrollList(catsList, e=1, a=i)

        cmds.textScrollList(catsList, e=1, si='UNCATEGORIZED')
        cmds.showWindow(window)
        cmds.window(window, e=1, w=500, h=650)

    def doProcessProject(self, cats, tags, window, *args):
        if not tags or '<None>' in tags:
            tags = []
        else:
            for i, v in enumerate(tags):
                tags[i] = v.strip()

        assetList = [ f for f in os.listdir(self.M.assetsDir) if os.path.isdir(os.path.join(self.M.assetsDir, f)) and f != '_TRASH' and os.path.exists(os.path.join(self.M.assetsDir, f, '_pipeline')) ]
        tempdir = os.path.join(self.M.assetsDir, 'DB_TEMP')
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)
        for i in assetList:
            assetPath = os.path.join(self.M.assetsDir, i, i + '.mb')
            if os.path.exists(assetPath):
                shutil.copy(assetPath, os.path.join(tempdir, os.path.basename(assetPath)))

        self.processFiles(tempdir, ','.join(cats), ','.join(tags))
        cmds.deleteUI(window)
        shutil.rmtree(tempdir)
        self.libraryUI()

    def doProcessFiles(self, folder, cats, tags, window, *args):
        if not tags or '<None>' in tags:
            tags = []
        else:
            for i, v in enumerate(tags):
                tags[i] = v.strip()

        self.processFiles(folder, ','.join(cats), ','.join(tags))
        cmds.deleteUI(window)
        self.libraryUI()

    def doProcessFile(self, cats, tags, window, *args):
        if not tags or '<None>' in tags:
            tags = []
        else:
            for i, v in enumerate(tags):
                tags[i] = v.strip()

        tempdir = os.path.join(os.path.dirname(cmds.file(q=1, sn=1)), 'DB_TEMP')
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)
        prompt = cmds.promptDialog(t='Enter a name for this asset...', ma='left', message='Enter a new name for this scene.', button=['ok', 'cancel'], defaultButton='ok', cancelButton='cancel', dismissString='cancel')
        if prompt == 'cancel':
            return
        name = cmds.promptDialog(q=1, tx=1)
        newfilename = name + os.path.splitext(cmds.file(q=1, sn=1, shn=1))[-1]
        shutil.copy(cmds.file(q=1, sn=1), os.path.join(tempdir, newfilename))
        self.processFiles(tempdir, ','.join(cats), ','.join(tags))
        cmds.deleteUI(window)
        shutil.rmtree(tempdir)
        self.libraryUI()

    def addNewTags(self, tagsCtrl, newTagsCtrl, *args):
        newTags = cmds.scrollField(newTagsCtrl, q=1, tx=1).split(',')
        for i, v in enumerate(newTags):
            newTags[i] = v.strip()

        oldTags = cmds.textScrollList(tagsCtrl, q=1, si=1)
        allTags = cmds.textScrollList(tagsCtrl, q=1, ai=1)
        sameTags = []
        if not oldTags or '<None>' in oldTags:
            oldTags = []
        if '<None>' in oldTags:
            oldTags.remove('<None>')
        for tag in newTags:
            if tag not in oldTags and tag != '' and tag not in allTags:
                cmds.textScrollList(tagsCtrl, e=1, ap=[2, tag])
            elif tag in allTags:
                sameTags.append(tag)

        oldTags.extend(newTags)
        oldTags.extend(sameTags)
        oldTags = list(set(oldTags))
        cmds.textScrollList(tagsCtrl, e=1, da=1)
        cmds.textScrollList(tagsCtrl, e=1, si=oldTags)
        cmds.scrollField(newTagsCtrl, e=1, tx='')

    def editInfoUI(self, *args):
        selAssets = cmds.textScrollList(self.assetList, q=1, si=1)
        if not selAssets:
            cmds.error('Select assets you want to edit first.')
        windowName = 'mustacheDB_editInfoUI'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, t='}MUSTACHE{ - Edit Asset Info')
        form = cmds.formLayout()
        lm0 = 10
        lm1 = 220
        lm2 = 360
        lm3 = 470
        tm0 = 10
        tm1 = 30
        tm2 = 130
        tm3 = 300
        tm4 = 230
        tm5 = 370
        editAssetLabel = cmds.text(l='Editing assets:', fn='boldLabelFont')
        editCatsLabel = cmds.text(l='Assign categories:', fn='boldLabelFont')
        editTagsLabel = cmds.text(l='Assign tags:', fn='boldLabelFont')
        editAssetList = cmds.scrollField(w=200, h=300, fn='fixedWidthFont', editable=0)
        refreshAssetsBtn = cmds.button(l='Reload selection', w=200, h=60, c=lambda *x: self.editInfoUI())
        editCatsList = cmds.textScrollList(w=130, h=400, ams=1, fn='boldLabelFont')
        editTagsList = cmds.textScrollList(w=100, h=400, ams=1)
        newTagsLabel = cmds.text(l='Separate new tags with commas:')
        newTagsBtn = cmds.button(l='Add new tags', w=200, h=60, c=lambda *x: self.addNewTags(editTagsList, newTagsText))
        newTagsText = cmds.scrollField(w=200, h=90, ww=1)
        screenBtn = cmds.button(l='Retake screenshot', w=200, h=60, c=lambda *x: self.retakeScreenshot(cmds.textScrollList(self.assetList, q=1, si=1)))
        applyBtn = cmds.button(l='Apply new info', w=200, h=60, bgc=[0.6, 0.7, 1.0], c=lambda *x: self.editInfo(cmds.textScrollList(self.assetList, q=1, si=1), cmds.textScrollList(editCatsList, q=1, si=1), cmds.textScrollList(editTagsList, q=1, si=1), window))
        cancelBtn = cmds.button(l='Close', w=200, h=60, c=lambda *x: cmds.deleteUI(window))
        cmds.formLayout(form, e=1, attachForm=[(editAssetLabel, 'top', tm0),
         (editAssetLabel, 'left', lm0),
         (editCatsLabel, 'top', tm0),
         (editCatsLabel, 'left', lm1),
         (editTagsLabel, 'top', tm0),
         (editTagsLabel, 'left', lm2),
         (editAssetList, 'top', tm1),
         (editAssetList, 'left', lm0),
         (editCatsList, 'top', tm1),
         (editCatsList, 'left', lm1),
         (editTagsList, 'top', tm1),
         (editTagsList, 'left', lm2),
         (refreshAssetsBtn, 'top', tm5),
         (refreshAssetsBtn, 'left', lm0),
         (newTagsLabel, 'top', tm0),
         (newTagsLabel, 'left', lm3),
         (newTagsBtn, 'top', tm2),
         (newTagsBtn, 'left', lm3),
         (newTagsText, 'top', tm1),
         (newTagsText, 'left', lm3),
         (applyBtn, 'top', tm3),
         (applyBtn, 'left', lm3),
         (cancelBtn, 'top', tm5),
         (cancelBtn, 'left', lm3),
         (screenBtn, 'top', tm4),
         (screenBtn, 'left', lm3)])
        cmds.scrollField(editAssetList, e=1, tx='\n'.join(selAssets))
        cmds.textScrollList(editCatsList, e=1, a='UNCATEGORIZED')
        for i in sorted(self.categories, key=str.lower):
            cmds.textScrollList(editCatsList, e=1, a=i)

        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        cats = [ f.get('category') for f in dbroot.findall('asset') if f.get('name') in selAssets ]
        selCats = []
        if cats:
            for i in cats:
                catsSplit = i.split(',')
                for each in catsSplit:
                    selCats.append(each)

            selCats = list(set(selCats))
        cmds.textScrollList(editCatsList, e=1, si=selCats)
        allTags = [ f.get('tags') for f in dbroot.findall('asset') ]
        allTagsSorted = []
        for i in allTags:
            tagsSplit = i.split(',')
            for j in tagsSplit:
                if j.strip() != '' and j.strip() != '<None>':
                    allTagsSorted.append(j)

        allTagsSorted = sorted(list(set(allTagsSorted)), key=str.lower)
        allTagsSorted.insert(0, '<None>')
        for i in allTagsSorted:
            cmds.textScrollList(editTagsList, e=1, a=i)

        selTags = [ f.get('tags') for f in dbroot.findall('asset') if f.get('name') in selAssets ]
        selTagsSorted = []
        for i in selTags:
            tagsSplit = i.split(',')
            for j in tagsSplit:
                if j.strip() != '':
                    selTagsSorted.append(j)

        selTagsSorted = list(set(selTagsSorted))
        if len(selTagsSorted) > 0:
            cmds.textScrollList(editTagsList, e=1, si=selTagsSorted)
        else:
            cmds.textScrollList(editTagsList, e=1, si='<None>')
        cmds.showWindow(window)
        cmds.window(window, e=1, w=700, h=450)

    def editInfo(self, assets, cats, tags, window = '', *args):
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        tagsFix = []
        for i in tags:
            if i.strip() != '' and i.strip() != '<None>':
                tagsFix.append(i)

        dbroot = dbfile.getroot()
        for i in assets:
            print 'making changes to asset %s' % i
            getAsset = [ f for f in dbroot.findall('asset') if f.get('name') == i ]
            if not getAsset:
                cmds.error("Couldn't find database entry for asset " + i)
            editAsset = getAsset[0]
            editAsset.attrib['category'] = ','.join(cats)
            editAsset.attrib['tags'] = ','.join(tagsFix)

        dbfile.write(self.M.assetsDatabase)
        if window != '':
            cmds.deleteUI(window)
        self.backupDB()
        self.popTagsList()
        self.popLibrary()

    def renameAsset(self, assetList, *args):
        asset = cmds.textScrollList(assetList, q=1, si=1)
        if not asset or len(asset) > 1:
            cmds.error('Select exactly one asset to rename.')
        promptStr = 'New name for asset %s' % asset[0]
        prompt = cmds.promptDialog(t=promptStr, ma='left', message='Please enter a new name for asset ' + asset[0] + ':', button=['ok', 'cancel'], defaultButton='ok', cancelButton='cancel', dismissString='cancel')
        if prompt == 'cancel':
            return
        newName = cmds.promptDialog(q=1, tx=1)
        rePattern = '^[a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9_]$'
        search = re.findall(rePattern, newName)
        if len(search) == 0:
            cmds.error('Invalid asset name: %s' % newName)
            return False
        assets = [ f.lower() for f in os.listdir(self.M.assetsLib) ]
        if newName.lower() in assets:
            newName = self.getUniqueName(newName, self.M.assetsLib)
            cmds.warning('Another asset with that name already exists. Renaming to ' + newName)
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        getAsset = [ f for f in dbroot.findall('asset') if f.get('name') == asset[0] ]
        editAsset = getAsset[0]
        path = editAsset.attrib['path']
        screen = editAsset.attrib['screen']
        newpath = path.replace(asset[0], newName)
        newscreen = screen.replace(asset[0], newName)
        texfolder = os.path.join(os.path.dirname(path), 'tex')
        newtexfolder = os.path.join(os.path.dirname(newpath), 'tex')
        print 'newpath: %s' % newpath
        if not os.path.exists(os.path.dirname(newpath)):
            os.makedirs(os.path.dirname(newpath))
        shutil.copy(path, newpath)
        shutil.copy(screen, newscreen)
        shutil.copytree(texfolder, newtexfolder)
        access = self.waitForAccess()
        editAsset.attrib['path'] = newpath
        editAsset.attrib['screen'] = newscreen
        editAsset.attrib['name'] = newName
        dbfile.write(self.M.assetsDatabase)
        shutil.rmtree(os.path.dirname(path))
        self.popLibrary()
        cmds.textScrollList(self.assetList, e=1, si=newName)
        ind = cmds.textScrollList(self.assetList, q=1, sii=1)[0]
        cmds.textScrollList(self.assetList, e=1, shi=ind)
        cmds.textField(self.assetFilterCtrl, e=1, tx='')
        self.backupDB()
        print 'Renamed asset %s to %s!' % (asset[0], newName)

    def deleteAssets(self, assets, *args):
        if not assets:
            cmds.error('No assets selected for deletion.')
        warnString = 'Are you sure you want to DELETE assets ' + ', '.join(assets) + '?'
        confirm = cmds.confirmDialog(t='DELETE assets from library?', message=warnString, icn='critical', button=['yes', 'no'], defaultButton='yes', cancelButton='no', dismissString='no')
        if confirm == 'no':
            return
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        trashFolder = os.path.join(self.M.assetsLib, '_TRASH')
        if not os.path.exists(trashFolder):
            os.makedirs(trashFolder)
        deleteList = []
        for a in assets:
            match = [ f for f in dbroot.findall('asset') if f.get('name') == a ]
            deleteMe = match[0]
            path = os.path.dirname(deleteMe.attrib['path'])
            try:
                shutil.move(path, os.path.join(trashFolder, a))
            except:
                pass

        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        match = [ f for f in dbroot.findall('asset') if f.get('name') in assets ]
        for m in match:
            dbroot.remove(m)

        dbfile.write(self.M.assetsDatabase)
        cmds.textScrollList(self.assetList, e=1, da=1)
        self.popLibrary()

    def openAsset(self, assetListCtrl, *args):
        assetList = cmds.textScrollList(assetListCtrl, q=1, si=1)
        if not assetList or len(assetList) > 1:
            cmds.error('Select exactly one asset to open.')
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        path = [ f.get('path') for f in dbroot.findall('asset') if f.get('name') == assetList[0] ][0]
        if cmds.file(q=1, mf=1) == 1:
            confirm = cmds.confirmDialog(title='Unsaved changes', message='Your scene has been modified. Save this scene first?', icon='warning', button=['save', 'continue without saving', 'cancel'], defaultButton='cancel', cancelButton='cancel', dismissString='cancel')
            if confirm == 'cancel':
                return
            if confirm == 'save':
                try:
                    cmds.file(s=1, f=1, type='mayaBinary')
                except RuntimeError:
                    pass

        cmds.file(path, o=1, f=1)

    def openBlacklistAsset(self, assetListCtrl, *args):
        assetList = cmds.textScrollList(assetListCtrl, q=1, si=1)
        if not assetList or len(assetList) > 1:
            cmds.error('Select exactly one asset to open.')
        path = assetList[0]
        if cmds.file(q=1, mf=1) == 1:
            confirm = cmds.confirmDialog(title='Unsaved changes', message='Your scene has been modified. Save this scene first?', icon='warning', button=['save', 'continue without saving', 'cancel'], defaultButton='cancel', cancelButton='cancel', dismissString='cancel')
            if confirm == 'cancel':
                return
            if confirm == 'save':
                try:
                    cmds.file(s=1, f=1, type='mayaBinary')
                except RuntimeError:
                    pass

        cmds.file(path, o=1, f=1)

    def importAsset(self, *args):
        assetList = cmds.textScrollList(self.assetList, q=1, si=1)
        if not assetList:
            cmds.error('Select one or more assets to import.')
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        paths = [ f.get('path') for f in dbroot.findall('asset') if f.get('name') in assetList ]
        cmds.namespace(set=':')
        for p in paths:
            namesp = os.path.splitext(os.path.basename(p))[0]
            cmds.file(p, i=1, ra=1, ns=namesp)
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

        print 'Imported library asset %s into current scene.' % p

    def sendToProject(self, *args):
        assetList = cmds.textScrollList(self.assetList, q=1, si=1)
        if not assetList:
            cmds.error('Select one or more assets to add to the project.')
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        matches = [ f for f in dbroot.findall('asset') if f.get('name') in assetList ]
        for match in matches:
            name = match.attrib['name']
            print 'Adding %s to project...' % name
            path = match.attrib['path']
            texpath = os.path.join(os.path.dirname(path), 'tex')
            if name in os.listdir(self.M.assetsDir):
                name = self.getUniqueName(name, self.M.assetsLib)
            if ' ' in name:
                name = name.replace(' ', '_')
            if not os.path.exists(os.path.join(self.M.assetsDir, name)):
                os.makedirs(os.path.join(self.M.assetsDir, name, '_pipeline'))
                os.makedirs(os.path.join(self.M.assetsDir, name, '_scrap'))
                os.makedirs(os.path.join(self.M.assetsDir, name, '_versions'))
            ext = os.path.splitext(path)[-1]
            basename = name
            newPath = os.path.join(self.M.assetsDir, name, '_versions', basename + '_v001_' + self.M.user + ext)
            shutil.copyfile(path, newPath)
            if not os.path.exists(os.path.join(self.M.project, 'sourceimages', basename)):
                shutil.copytree(texpath, os.path.join(self.M.project, 'sourceimages', basename))
            subp = subprocess.Popen(os.path.join(self.M.mayaDir, 'mayapy.exe') + ' ' + os.path.join(self.M.scriptsDir, '..', 'python', 'm_libraryAssetToProject.py') + ' ' + newPath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = subp.communicate()
            if stderr:
                cmds.warning(stderr)
            print 'Added new asset %s to project.' % name

    def viewBlacklist(self, *args):
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsBlacklist)
        dbroot = dbfile.getroot()
        blacklist = [ f.get('path') for f in dbroot.findall('asset') ]
        windowName = 'mustacheDB_blacklistUI'
        windowTitle = '}MUSTACHE{ - Blacklist Viewer'
        if cmds.window(windowName, q=1, exists=1):
            cmds.deleteUI(windowName)
        window = cmds.window(windowName, title=windowTitle)
        form = cmds.columnLayout(adj=1, rs=10)
        blacklistCtrl = cmds.textScrollList(w=600, h=300, ams=1, parent=form)
        openBtn = cmds.button(w=600, h=60, l='Open file (WARNING! May crash Maya!)', c=lambda *x: self.openBlacklistAsset(blacklistCtrl), parent=form)
        deleteBtn = cmds.button(w=600, h=60, l='Remove from blacklist', c=lambda *x: self.removeFromBlacklist(blacklistCtrl), parent=form)
        self.popBlacklist(blacklistCtrl)
        cmds.showWindow(window)
        cmds.window(window, e=1, w=610, h=450)

    def popBlacklist(self, ctrl, *args):
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsBlacklist)
        dbroot = dbfile.getroot()
        blacklist = [ f.get('path') for f in dbroot.findall('asset') ]
        cmds.textScrollList(ctrl, e=1, ra=1)
        for f in sorted(blacklist, key=str.lower):
            cmds.textScrollList(ctrl, e=1, a=f)

    def removeFromBlacklist(self, blacklistCtrl, *args):
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsBlacklist)
        dbroot = dbfile.getroot()
        toRemove = cmds.textScrollList(blacklistCtrl, q=1, si=1)
        if not toRemove:
            cmds.error('Select one or more assets to remove from the blacklist.')
        for i in toRemove:
            match = [ f for f in dbroot.findall('asset') if f.get('path') == i ]
            dbroot.remove(match[0])

        access = self.waitForAccess()
        dbfile.write(self.M.assetsBlacklist)
        self.popBlacklist(blacklistCtrl)

    def retakeScreenshot(self, assetList, *args):
        if not assetList:
            cmds.error("You're an idiot.")
        access = self.waitForAccess()
        dbfile = ET.parse(self.M.assetsDatabase)
        dbroot = dbfile.getroot()
        assets = [ f for f in dbroot.findall('asset') if f.get('name') in assetList ]
        progbar = mel.eval('$temp = $gMainProgressBar')
        progStr = 'initializing...'
        cmds.progressBar(progbar, e=1, bp=1, ii=1, status=progStr, max=len(assets), pr=0)
        for index, i in enumerate(assets):
            if cmds.progressBar(progbar, q=1, ic=1):
                cmds.progressBar(progbar, e=1, ep=1)
                cmds.error('Cancelled operation.')
            f = i.attrib['path']
            progStr = 'processing file %d of %d... (%s)' % (index + 1, len(assets), f)
            cmds.progressBar(progbar, e=1, status=progStr, step=1)
            pFile = open(os.path.join(os.environ['USERPROFILE'], 'mustacheDB_out'), 'w')
            print 'Creating preview for file %s' % f
            pickle.dump(f, pFile, pickle.HIGHEST_PROTOCOL)
            pFile.close()
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subp = subprocess.Popen(os.path.join(self.M.mayaDir, 'mayapy.exe') + ' ' + os.path.join(self.M.scriptsDir, '..', 'python', 'm_processLibraryFiles.py'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startup)
            stdout, stderr = subp.communicate()
            exitcode = subp.returncode
            if str(exitcode) != '0':
                print "ERROR: Couldn't process file %s." % f
            else:
                returnFile = open(os.path.join(os.environ['USERPROFILE'], 'mustacheDB_in'), 'r')
                inData = pickle.load(returnFile)
                returnFile.close()
                print '\n File %s processed successfully.' % f
                filename = inData[0]
                screen = inData[1]
                texstring = inData[2]
                outfile = inData[3]
            newscreenpath = i.attrib['screen']
            shutil.copy(screen, newscreenpath)

        cmds.progressBar(progbar, e=1, ep=1)
        print '...done!'