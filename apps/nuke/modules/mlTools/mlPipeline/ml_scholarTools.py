import nuke,mlTools,nukescripts
import os,re,sys

lightingAovs=[  "DiffuseTint",
                "Diffuse Lighting",
                "Global Illumination Raw",
                "Global Illumination",
                "Reflections",
                "Refractions",
                "Specular Lighting",
                "Sub Surface Scatter Raw",
                "Sub Surface Scatter",
                "Total Diffuse Lighting Raw"]


outImagesPath='01_MAYA/images/'
__NODES_FOR_VERSION = ( "Read",
                        "Write",
                        "Precomp",
                        "DeepRead",
                        "DeepWrite",
                      )
assetGizmos=os.path.dirname(os.path.dirname(mlTools.__file__))+'/assetGizmos'
assetGizmos=assetGizmos.replace('\\','/')


def version_get(string, prefix, suffix = None):
    """Extract version information from filenames used by DD (and Weta, apparently)
    These are _v# or /v# or .v# where v is a prefix string, in our case
    we use "v" for render version and "c" for camera track version.
    See the version.py and camera.py plugins for usage."""

    if string is None:
        raise ValueError, "Empty version string - no match"

    regex = "[/_.]"+prefix+"\d+"
    matches = re.findall(regex, string, re.IGNORECASE)
    if not len(matches):
        msg = "No \"_"+prefix+"#\" found in \""+string+"\""
        raise ValueError, msg
    return (matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group())

def version_set(string, prefix, oldintval, newintval):
    regex = "[/_.]"+prefix+"\d+"
    matches = re.findall(regex, string, re.IGNORECASE)
    if not len(matches):
        return ""

    # Filter to retain only version strings with matching numbers
    matches = filter(lambda s: int(s[2:]) == oldintval, matches)
    print matches
    # Replace all version strings with matching numbers
    for match in matches:
        # use expression instead of expr so 0 prefix does not make octal
        fmt = "%%(#)0%dd" % (len(match) - 2)
        newfullvalue = match[0] + prefix + str(fmt % {"#": newintval})
        string = re.sub(match, newfullvalue, string)
    #print string
    return string

def version_set2(string, prefix, oldintval, newintval):
    thisDir=os.path.dirname(string)
    thisDirName=thisDir.split('/')[-1]
    parDir=os.path.dirname(thisDir)

    newVer='L'+str(newintval).zfill(3)
    foundDir=''

    for dir in os.listdir(parDir):
        if newVer in dir:
            foundDir=dir
            return string.replace(thisDirName,foundDir)
    if not foundDir:
        return version_set(string,prefix,oldintval,newintval)


def version_up():
    """All new version_up that uses the version_get/set functions.
    This script takes the render version up one in selected iread/writes."""

    n = nuke.selectedNodes()
    for i in n:
        _class = i.Class()
        # check to make sure this is a read or write op
        if _class in ('Read'):
            fileKnob = i['file']
            proxyKnob = i.knob('proxy')
            try:
                (prefix, v) = version_get(fileKnob.value(), 'L')
                v = int(v)
                fileKnob.setValue(version_set2(fileKnob.value(), prefix, v, v + 1))
            except ValueError:
                (prefix, v) = version_get(fileKnob.value(), 'v')
                v = int(v)
                fileKnob.setValue(version_set2(fileKnob.value(), prefix, v, v + 1))
            nuke.root().setModified(True)

def version_down():
    """All new version_down that uses the version_get/set functions.
    This script takes the render version up one in selected iread/writes."""

    n = nuke.selectedNodes()
    for i in n:
        _class = i.Class()
        # check to make sure this is a read or write op
        if _class in ('Read'):
            fileKnob = i['file']
            proxyKnob = i.knob('proxy')
            try:
                (prefix, v) = version_get(fileKnob.value(), 'L')
                v = int(v)
                fileKnob.setValue(version_set2(fileKnob.value(), prefix, v, v - 1))
            except ValueError:
                (prefix, v) = version_get(fileKnob.value(), 'v')
                v = int(v)
                fileKnob.setValue(version_set2(fileKnob.value(), prefix, v, v - 1))
            nuke.root().setModified(True)

def matchAovs():
    node=nuke.thisNode()
    filenames=''
    token='Beauty'
    for i in range(node.inputs()):
        if i==1:
            token='Utility'
        path=node.input(i)['file'].value()
        first=node.input(i)['first'].value()
        last=node.input(i)['last'].value()
        err=node.input(i)['on_error'].value()
        renderString=path.split(outImagesPath)[-1].split('/')[0]
        filepath=path.split('/')[-1]
        filenames+=filepath.split('.')[0]+'\n'
        parent='/'.join(path.split('/')[:-1])#scholar
        dirs=os.listdir(parent)
        #attempt to remove any lighting aovs that are misplaced in Utils to avoid incorrect renders
        if i==1:
            for la in lightingAovs:
                if la in dirs:
                    dirs.remove(la)
        with node:
            nuke.selectAll()
            nuke.invertSelection()
            for n in nuke.allNodes('Read'):
                if n.name() in dirs:
                    print n.name()
                    n['file'].setValue(parent+'/'+n.name()+'/'+filepath.replace(token,token+"."+n.name()))
                    n['first'].setValue(first)
                    n['last'].setValue(last)
                    n['on_error'].setValue(err)
        #node['label'].setValue('[lindex [split [lindex [split [value input0.file] /] end] .] 0]\n[lindex [split [lindex [split [value input1.file] /] end] .] 0]')
        nodeName="_".join(filepath.split('_')[:-3])+"_REBUILD"
        #try:
        #    node['name'].setValue(nodeName)
        #except:
        #    continue


def getAssetGizmos(node):
    thisAssetGizmos=[]
    with node:
        for n in nuke.allNodes():
            try:
                path=n.filename()
                if 'assetGizmos' in path:
                    thisAssetGizmos.append(n.Class())
            except:
                pass
    thisAssetGizmos.sort()
    return thisAssetGizmos


def showMattes():
    node=nuke.thisNode()
    aList='Mattes:\n'
    mattes=[]
    for ch in node.channels():
        chan=ch.split('.')[0]
        if chan.startswith('m_'):
            if not chan in mattes:
                mattes.append(chan)
    for matte in mattes:
        aList+=matte+'\n'
    eList='Existing:\n'
    node['assetList'].setValue(aList)
    for assetGizmo in getAssetGizmos(node):
        eList+=assetGizmo+'\n'
    node['existList'].setValue(eList)
        
def matchReformat():
    n=nuke.thisNode()
    k=nuke.thisKnob()
    val=nuke.toNode(n.name())[k.name()].value()
    for reformat in nuke.allNodes('Reformat'):
        reformat[k.name()].setValue(val)


def gatherMattes():
    node=nuke.thisNode()
    parent=nuke.thisParent()
    utilRead= parent.input(1)
    utilPath= utilRead['file'].value()
    utilDir=os.path.dirname(utilPath)
    utilContents= os.listdir(utilDir)
    mattes=[]
    for util in utilContents:
        if util.startswith("m_"):
            mattes.append(util)
    print mattes
    with node:
        inputNode=nuke.toNode('Input1')
        outputNode=nuke.toNode('Output1')
        #remove existing Nodes
        for r in nuke.allNodes('Read'):
            nuke.delete(r)
        for c in nuke.allNodes('Copy'):
            nuke.delete(c)
        prior=inputNode
        for matte in mattes:
            #create Read, set knobs
            r=nuke.nodes.Read()
            utilFile=utilPath.split('/')[-1]
            filepath=utilDir+'/'+matte+'/'+utilFile.replace('Utility','Utility.'+matte)
            r['file'].setValue(filepath)
            r['first'].setValue(utilRead['first'].value())
            r['last'].setValue(utilRead['last'].value())
            r['on_error'].setValue(utilRead['on_error'].value())
            r.setName(matte)
            #create copy node, set inputs
            copy=nuke.nodes.Copy()
            copy.setInput(0,prior) 
            copy.setInput(1,r)
            copy.setName('copy_'+matte)
            nuke.tcl('add_layer { '+matte+' '+matte+'.red '+matte+'.green '+matte+'.blue}')
            copy['from0'].setValue('rgba.red')
            copy['from1'].setValue('rgba.green')
            copy['from2'].setValue('rgba.blue')
            copy['to0'].setValue(matte+'.red')
            copy['to1'].setValue(matte+'.green')
            copy['to2'].setValue(matte+'.blue')
            prior=copy
        outputNode.setInput(0,prior)

def setWriteOutput():
    n=nuke.thisNode()
    ext=n['file_type'].value()
    regex = re.compile("v[0-9]{2,9}")
    thisPath= nuke.root().name()
    vers=regex.findall(thisPath)[0]
    thisShotPath=thisPath.split("/work")[0]
    thisShotName=thisShotPath.split('/')[-1]
    filename=thisShotName+"_"+n.name()+"_"+vers+".%04d."+ext
    outPath=thisShotPath+"/render/"+n.name()+"/"+vers+"/"+filename
    n['file'].setValue(outPath)

def getMatteChannel():
    node=nuke.thisNode()
    found=''
    with node:
        x,y=node['queryPosition'].value()
        for ch in node.channels():
            if ch.startswith('m_') and not 'alpha' in ch and not 'all' in ch:
                result= node.sample(ch,x,y)
                if result:
                    found=ch
                    break
        if found:
            expr=nuke.toNode('matteExpr')
            expr['expr0'].setValue(ch)
    node['label'].setValue(found)

def replaceShuffle():
    node=nuke.thisNode()
    expr=''
    node.begin()
    expr=nuke.toNode('matteExpr')['expr0'].value()
    node.end()
    parent=nuke.thisParent()
    print parent
    dep=node.dependencies()
    nodeIn=node.input(0)
    nodePos=[node.xpos(),node.ypos()]
    matteString=expr
    if matteString:
        matte,channel=matteString.split(".")
        if parent:
            with parent:
                sh=nuke.nodes.Shuffle()
                sh['in'].setValue(matte)
                sh['red'].setValue(channel)
                sh['green'].setValue(channel)
                sh['blue'].setValue(channel)
                sh['alpha'].setValue(channel)
                sh.setXYpos(nodePos[0],nodePos[1])
                sh['label'].setValue('[value in]')
                sh.setInput(0,nodeIn)
                nuke.delete(node)
        else:
            sh=nuke.nodes.Shuffle()
            sh['in'].setValue(matte)
            sh['red'].setValue(channel)
            sh['green'].setValue(channel)
            sh['blue'].setValue(channel)
            sh['alpha'].setValue(channel)
            sh.setXYpos(nodePos[0],nodePos[1])
            sh['label'].setValue('[value in]')
            sh.setInput(0,nodeIn)
            nuke.delete(node)
def getMatteAssets(node):
    mattes=[]
    for ch in node.channels():
        matteName=ch.split('.')[0]
        if matteName.startswith('m_'):
            if not matteName in mattes:
                mattes.append(matteName)
    return mattes

def addAssetGizmos(*args):
    nuke.selectAll() 
    nuke.invertSelection() 
    node=nuke.thisNode()
    addedGizmos=[]
    matteAssets=getMatteAssets(node)

    with node:
        for n in nuke.allNodes('NoOp'):
            if n.name().endswith("_OUT"):
                aov=n.name().split("_OUT")[0]
                gizmos= findAssetGizmos(aov,matteAssets)
                lastNode=n.dependencies()[0]
                addedGizmos.extend(gizmos)
                for g in gizmos:
                    lastNode.setSelected(True)
                    giz=nuke.createNode(g,inpanel=False)
                    nuke.selectAll() 
                    nuke.invertSelection() 
                    giz.setInput(0,lastNode)
                    giz.setXYpos(lastNode.xpos(),lastNode.ypos()+30)
                    giz['tile_color'].setValue(16711935) 
                    lastNode=giz
                n.setInput(0,lastNode)
    if len(addedGizmos):
        nuke.message('ADDING ASSETS:\n'+"\n".join(addedGizmos))
        #show data
    thisNode=nuke.toNode(node.name())
    with thisNode:
        showMattes()

def clearAssetGizmos():
    node=nuke.thisNode()
    with node:
        for n in nuke.allNodes():
            try:
                path=n.filename()
                if 'assetGizmos' in path:
                    nuke.delete(n)
            except:
                pass
    thisNode=nuke.toNode(node.name())
    with thisNode:
        showMattes()               
            
def forceAddAssetGizmos():
    nuke.selectAll() 
    nuke.invertSelection() 
    node=nuke.thisNode()
    addedGizmos=[]
    matteAssets=getAssetListSelection()

    with node:
        for n in nuke.allNodes('NoOp'):
            if n.name().endswith("_OUT"):
                aov=n.name().split("_OUT")[0]
                gizmos= findAssetGizmos(aov,matteAssets)
                lastNode=n.dependencies()[0]
                addedGizmos.extend(gizmos)
                for g in gizmos:
                    lastNode.setSelected(True)
                    giz=nuke.createNode(g,inpanel=False)
                    nuke.selectAll() 
                    nuke.invertSelection() 
                    giz.setInput(0,lastNode)
                    giz.setXYpos(lastNode.xpos(),lastNode.ypos()+30)
                    giz['tile_color'].setValue(16711935) 
                    lastNode=giz
                n.setInput(0,lastNode)
    if len(addedGizmos):
        nuke.message('ADDING ASSETS:\n'+"\n".join(addedGizmos))
        #show data
    thisNode=nuke.toNode(node.name())
    with thisNode:
        showMattes()


def getAssetListSelection():
    selectedAssets=[]
    class TestPanel(nukescripts.PythonPanel):
        def __init__(self):
            super(TestPanel,self).__init__('select assetGizmos to import' )

            #list of assets
            assets=os.listdir(assetGizmos)
            assets.sort()
            for asset in assets:
                b=nuke.Boolean_Knob(asset)
                b.setFlag(nuke.STARTLINE)
                self.addKnob(b) 
            self._makeOkCancelButton()  
    p = TestPanel()
    result=p.showModalDialog()

    if result:
        for k in p.knobs():
            if p.knobs()[k].Class()=='Boolean_Knob':
                if p.knobs()[k].value():
                    selectedAssets.append(k)
    return selectedAssets
        
def findAssetGizmos(aov,assetMetadata):
    foundGizmos=[]
    missingGizmos=[]
    assets=[]
    assetDirs=os.listdir(assetGizmos)
    foundAssets=[]
    for asset in assetMetadata:
        for assetDir in assetDirs:
            if assetDir in asset:
                if not assetDir in foundAssets:
                    foundAssets.append(assetDir)
                
    for asset in foundAssets:
        if asset+"_"+aov+".gizmo" in os.listdir(assetGizmos+'/'+asset):
            foundGizmos.append(asset+"_"+aov)
    for fg in foundGizmos:
        if len(nuke.allNodes(fg))==0:
            missingGizmos.append(fg)
    
    #print 'foundAssets',foundAssets
    #print 'foundgizmos',foundGizmos
    #print 'missingGizmos',missingGizmos
    return missingGizmos