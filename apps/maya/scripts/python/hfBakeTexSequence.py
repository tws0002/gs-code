# mental ray texture sequence bake
#
# create a textureBakeSet, set options (resolution, bleeding, etc)
# put objects in set
# set mentalrayGlobals options
    # textureBakeSet1.overrideUvSet
    # textureBakeSet1.uvSetName
    # textureBakeSet1.xResolution, yResolution
    # textureBakeSet1.bitsPerChannel (1 = 8, 2 = 16, 4 = 32)
    # textureBakeSet1.fillTextureSeams
# run convertLightmap('shadingGroup','objectXform'), files render to /project/renderData/mentalray/lightMap, function returns image path
# copy image path to predetermined directory, add sequence suffix

# faaaaarts

import maya.cmds as cmds
import shutil
import os

def bakeSetup(objects,xres=512,yres=512,prefix='baked',format=1,bits=1,fillseams=1.0,overrideuv=0,set='map1',samples=1,*args):
    # create a textureBakeSet, set options, add objects.
    newSet = cmds.createNode('textureBakeSet',n='hf_autoTextureBakeSet')
    attrs = ['xres','yres','format','bits','fillseams','samples','overrideuv']
    cmds.setAttr(newSet+'.xres',xres)
    cmds.setAttr(newSet+'.yres',yres)
    cmds.setAttr(newSet+'.format',format)
    cmds.setAttr(newSet+'.bits',bits)
    cmds.setAttr(newSet+'.fillseams',fillseams)
    cmds.setAttr(newSet+'.overrideuv',overrideuv)
    cmds.setAttr(newSet+'.samples',samples)
    cmds.setAttr(newSet+'.prefix',prefix,type='string')
    if overrideuv == 1:
        cmds.setAttr(newSet+'.set',set,type='string')
    # add objects.
    # add object shape nodes. first build a list of usable shape nodes to add to the set.
    shapesList = []
    for i in objects:
        shapes = cmds.listRelatives(i,s=1,ni=1)
        if shapes:
            shapesList.extend(shapes)
    cmds.sets(shapesList,e=1,fe=newSet)
    return objects,newSet

def runBake(objects,fileDest,bakeSet,rename=False,start=False,end=False,*args):
    # for each object, run the bake in sequence.
    for i in objects:
        # get shading engine from object
        objShape = cmds.listRelatives(i,s=1,ni=1)[0]
        se = cmds.listConnections(objShape,type='shadingEngine')[0]
        if start == False: start = cmds.playbackOptions(q=1,min=1)
        if end == False: end = cmds.playbackOptions(q=1,max=1)
        for x in range(start,(end+1)):
            print 'Baking texture for object %s at frame %d' % (i,x)
            cmds.currentTime(x)
            outFile = cmds.convertLightmap(se,i,bo=bakeSet)[0]
            # outFile returns the file name, without a path or extension, as a list.
            lightmapsDir = os.path.join(cmds.workspace(q=1,fn=1),'renderData','mentalray','lightMap')
            writeFileBase = [f for f in os.listdir(lightmapsDir) if outFile in f]
            # hopefully that will get the right file, this is ghetto as fuck
            outFullPath = os.path.join(lightmapsDir,writeFileBase[0])
            # now copy this to some real folder
            if not os.path.exists(fileDest): os.makedirs(fileDest)
            outName = os.path.splitext(writeFileBase[0])[0]
            if rename:
                outName = rename
            newFileBase = outName+'.'+str(x).zfill(4)+os.path.splitext(writeFileBase[0])[-1]
            copyTo = os.path.join(fileDest,newFileBase)
            shutil.move(outFullPath,copyTo)

def hfBakeTexSequence(*args):
    # UI for this shit
    # select objects then click BAKE
    # options fields: resolution, shape prefix, rename string (single object only), output path, edge bleed, format, bit depth, uv override, uv set, samples
    windowName = 'hfBakeTexSequenceUI'
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    window = cmds.window(windowName,t='Bake Texture Sequence')
    form = cmds.formLayout()
    lm0 = 10
    lm1 = 180
    lm2 = 540
    padding = 25
    tm0 = 10
    tm1 = 120
    # define labels
    prefixLabel = cmds.text(l='Shape prefix:')
    renameLabel = cmds.text(l='Rename sequence (single obj):')
    outputLabel = cmds.text(l='Output path:')
    resLabel = cmds.text(l='Resolution:')
    formatLabel = cmds.text(l='Image format:')
    depthLabel = cmds.text(l='Bit depth:')
    bleedLabel = cmds.text(l='Edge bleed (pixels):')
    samplesLabel = cmds.text(l='Samples:')
    uvSetLabel = cmds.text(l='UV set (blank for default):')
    # attach labels
    cmds.formLayout(form,e=1,attachForm=[(prefixLabel,'top',tm0),(prefixLabel,'left',lm0),(renameLabel,'top',tm0+padding),(renameLabel,'left',lm0),
                                         (outputLabel,'top',tm0+(padding*2)),(outputLabel,'left',lm0),(formatLabel,'top',tm1+padding),(formatLabel,'left',lm0),
                                         (depthLabel,'top',tm1+(padding*2)),(depthLabel,'left',lm0),(uvSetLabel,'top',tm1+(padding*5)),(uvSetLabel,'left',lm0),
                                         (resLabel,'top',tm1),(resLabel,'left',lm0),(bleedLabel,'top',tm1+(padding*3)),(bleedLabel,'left',lm0),
                                         (samplesLabel,'top',tm1+(padding*4)),(samplesLabel,'left',lm0)])
    # define controls
    wideField = 350
    shortField = 60
    prefixCtrl = cmds.textField(w=wideField,tx='baked')
    renameCtrl = cmds.textField(w=wideField)
    defaultOutFolder = os.path.join(cmds.workspace(q=1,fn=1),'images','bakeTextureSequence').replace('/','\\')
    outputCtrl = cmds.textField(w=wideField,tx=defaultOutFolder)
    resCtrl = cmds.intSliderGrp(field=1,min=256,max=4096,s=256,v=1024,cw2=(55,295))
    formatCtrl = cmds.optionMenu(w=shortField)
    formats = ['TIF','IFF','JPG','RGB','RLA','TGA','BMP','HDR']
    for i in formats:
        cmds.menuItem(label=i)
    depthCtrl = cmds.optionMenu(w=shortField)
    depths = ['8 bits','16 bits','32 bits'] # bit depth control is only available for TIFF format
    for i in depths:
        cmds.menuItem(label=i)
    bleedCtrl = cmds.floatSliderGrp(field=1,min=0.0,max=10.0,s=1,v=1.0,cw2=(45,290))
    samplesCtrl = cmds.intSliderGrp(field=1,min=0,max=4,s=1,v=1,cw2=(55,295))
    uvSetCtrl = cmds.textField(w=wideField)
    outputPathBtn = cmds.button(w=30,h=20,l='...',c=lambda *x: setOutputPath(outputCtrl))
    # attach controls
    cmds.formLayout(form,e=1,attachForm=[(prefixCtrl,'top',tm0),(prefixCtrl,'left',lm1),(renameCtrl,'top',tm0+padding),(renameCtrl,'left',lm1),
                                         (outputCtrl,'top',tm0+(padding*2)),(outputCtrl,'left',lm1),(resCtrl,'top',tm1),(resCtrl,'left',lm1),
                                         (formatCtrl,'top',tm1+padding),(formatCtrl,'left',lm1),(depthCtrl,'top',tm1+(padding*2)),(depthCtrl,'left',lm1),
                                         (bleedCtrl,'top',tm1+(padding*3)),(bleedCtrl,'left',lm1),(samplesCtrl,'top',tm1+(padding*4)),(samplesCtrl,'left',lm1),
                                         (uvSetCtrl,'top',tm1+(padding*5)),(uvSetCtrl,'left',lm1),(outputPathBtn,'top',tm0+(padding*2)),(outputPathBtn,'left',lm2)])

    # big ol buttons
    bakeBtn = cmds.button(l='Bake sequence',w=150,h=55,bgc=[0.6,0.7,1.0],c=lambda *x: getBakeVars(cmds.textField(prefixCtrl,q=1,tx=1),cmds.textField(renameCtrl,q=1,tx=1),cmds.textField(outputCtrl,q=1,tx=1),cmds.intSliderGrp(resCtrl,q=1,v=1),cmds.optionMenu(formatCtrl,q=1,sl=1),cmds.optionMenu(depthCtrl,q=1,sl=1),cmds.floatSliderGrp(bleedCtrl,q=1,v=1),cmds.intSliderGrp(samplesCtrl,q=1,v=1),cmds.textField(uvSetCtrl,q=1,tx=1)))
    closeBtn = cmds.button(l='Cancel',w=150,h=55,c=lambda x: cmds.deleteUI(window))
    cmds.formLayout(form,e=1,attachForm=[(bakeBtn,'top',300),(bakeBtn,'left',10),(closeBtn,'top',300),(closeBtn,'left',180)])
    cmds.showWindow(window)
    cmds.window(window,e=1,w=600,h=375)

def getBakeVars(prefix,rename,outPath,res,format,bits,bleed,samples,uvset,*args):
    # gather variables and run bake.
    # bakeSetup(objects,xres=512,yres=512,prefix='baked',format=1,bits=1,fillseams=1.0,overrideuv=0,set='map1',samples=1,*args)
    # runBake(objects,fileDest,rename=False,start=False,end=False,*args)
    sel = cmds.ls(sl=1)
    objects = []
    bakeset = ''
    if not sel:
        cmds.error('you need to select something dumbass')
    if uvset != '':
        objects, bakeset = bakeSetup(sel,int(res),int(res),prefix,format,bits,float(bleed),1,uvset,int(samples))
    else:
        objects, bakeset = bakeSetup(sel,int(res),int(res),prefix,format,bits,float(bleed),0,'map1',int(samples))
    # now runBake
    outPathFixed = outPath.replace('\\','/')
    if rename != '':
        runBake(objects,outPathFixed,bakeset,rename)
    else:
        runBake(objects,outPathFixed,bakeset)
    cmds.delete(bakeset)

def setOutputPath(outputCtrl,*args):
    # set the output path and update the control.
    currentPath = cmds.textField(outputCtrl,q=1,tx=1).replace('/','\\')
    newPath = cmds.fileDialog2(ds=2,cap='Choose an output folder for the texture sequence...',dir=currentPath,fm=3)
    print newPath
    if newPath:
        cmds.textField(outputCtrl,e=1,tx=newPath[0])