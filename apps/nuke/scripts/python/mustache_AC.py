# nuke/mustache beauty auto-comp
#
# purpose: automatically build vray (possibly mental ray) comps in nuke out of a given multichannel EXR or set of EXR sequences.
# given a multichannel sequence or a list of single-channel sequences, create a set of read and shuffle nodes and merge them together.
# multichannel exrs need to have each channel shuffled out, and also added together (merge all channels)
# single-channel images just need to be added together. might be useful to shuffle out to channels first in order to create an identical flow.
#
# vray comp: lightSelect# + lightSelect# + GI + reflection + refraction + specular + selfIllumination + sss + caustics
#
#
# User defines up to three sequences: a beauty sequence, technical sequence and matte sequence.

import nuke
import nukescripts
import os,random,re

nuke.mustache_AC_xpos = 0
nuke.mustache_AC_ypos = 0

class mustache_AC(nukescripts.PythonPanel):

    def __init__(self):
        nukescripts.PythonPanel.__init__(self,'}MUSTACHE{ Auto-Comp Builder', 'mustache.AutoComp')

        # make knobs
        self.autoCompTab = nuke.Tab_Knob('Auto-Comp Multi')
        self.nameStr = nuke.String_Knob('nameStr','Comp name:')
        self.nameStr.setValue('Comp 1')
        self.backdropColor = nuke.ColorChip_Knob('backdropColor')
        self.beautyStr = nuke.String_Knob('beautyStr','Beauty sequence:')
        self.getBeauty = nuke.PyScript_Knob('getBeauty','Get Beauty')
        self.techStr = nuke.String_Knob('techStr','Tech sequence:')
        self.getTech = nuke.PyScript_Knob('getTech','Get Tech')
        self.matteStr = nuke.String_Knob('matteStr','Matte sequence:')
        self.getMatte = nuke.PyScript_Knob('getMatte','Get Matte')
        self.ok = nuke.PyScript_Knob('doAutoComp','Create comp')

        # attach to panel
        self.addKnob(self.autoCompTab)
        self.addKnob(self.nameStr)
        self.addKnob(self.backdropColor)
        self.backdropColor.setValue(0x999999FF)
        self.addKnob(self.beautyStr)
        self.addKnob(self.getBeauty)
        self.addKnob(self.matteStr)
        self.addKnob(self.getMatte)
        self.addKnob(self.techStr)
        self.addKnob(self.getTech)
        self.addKnob(self.ok)
        self.ok.setFlag(nuke.STARTLINE)
        
        # make knobs for single-channel grouper
        self.grouperTab = nuke.Tab_Knob('Footage Grouper')
        self.sequenceStr = nuke.String_Knob('sequenceStr','Root sequence:')
        self.getSequence = nuke.PyScript_Knob('getSequence','Get Sequence')
        self.makeGroup = nuke.PyScript_Knob('doGroup','Group passes')
        
        # attach to panel
        self.addKnob(self.grouperTab)
        self.addKnob(self.sequenceStr)
        self.addKnob(self.getSequence)
        self.addKnob(self.makeGroup)
        self.makeGroup.setFlag(nuke.STARTLINE)

    # knob changin'

    def knobChanged(self, knob):
        if knob in (self.getBeauty, self.getTech, self.getMatte):
            if knob == self.getBeauty:
                setStr = nuke.getClipname('Get beauty sequence...')
                self.beautyStr.setValue(setStr)
            elif knob == self.getTech:
                setStr = nuke.getClipname('Get tech sequence...')
                self.techStr.setValue(setStr)
            elif knob == self.getMatte:
                setStr = nuke.getClipname('Get matte sequence...')
                self.matteStr.setValue(setStr)
        elif knob == self.ok:
            # try to run this thing
            errors = []
            # if this is a sequence and we want to check for a valid file path, we need to remove the sequence information from the end of the string.
            if not os.path.exists(os.path.dirname(self.beautyStr.value())):
                errors.append('Beauty sequence path is invalid')
            if not os.path.exists(os.path.dirname(self.techStr.value())):
                errors.append('Tech sequence path is invalid')
            if not os.path.exists(os.path.dirname(self.matteStr.value())):
                errors.append('Matte sequence path is invalid')
            if errors:
                if os.path.exists(self.beautyStr.value()):
                    # warn but we can comp anyways
                    askStr = '}MUSTACHE{ detected the following errors: \n%s\n\nBuild comp anyways?' % ('\n'.join(errors))
                    if nuke.ask(askStr):
                        autoComp(self.beautyStr.value(),self.techStr.value(),self.matteStr.value(),self.nameStr.value(),self.backdropColor.value())
                else:
                    messStr = '}MUSTACHE{ detected the following errors: \n%s\n\nCan\'t build an auto-comp without a beauty sequence!' % ('\n'.join(errors))
                    nuke.message(messStr)
            else:
                autoComp(self.beautyStr.value(),self.techStr.value(),self.matteStr.value(),self.nameStr.value(),self.backdropColor.value())
            # print self.beautyStr.value(),self.techStr.value(),self.matteStr.value(),self.nameStr.value()
        elif knob == self.getSequence:
            setStr = nuke.getClipname('Get pass sequence...',None,None,False)
            self.sequenceStr.setValue(setStr)
        elif knob == self.makeGroup:
            # run the grouping function thing
            createPassGroup(self.sequenceStr.value())

            
def createPassGroup(rootSequence,debug=True,*args):
    # given a root sequence (assuming all passes share the same prefix as the root sequence), assemble all passes with the same prefix into a group and add the channels together.
    # also add knobs onto the group instance to allow fast updating of all footage layers inside.
    passDir = os.path.dirname(rootSequence)
    rootPrefix = '.'.join(os.path.splitext(os.path.basename(rootSequence))[0].split('.')[:-1])
    # create Read for root sequence (rgba).
    rootRead = nuke.nodes.Read()
    rootRead['file'].fromUserText(rootSequence)
    readNodes = []
    readNodes.append(rootRead)
    if debug:
        print 'passes dir: %s' % (passDir)
        print 'root prefix: %s' % (rootPrefix)
    # rootPrefix returns the base name of the primary framebuffer render, without passes. doesn't include sequence numbers.
    # get all files that contain rootPrefix, then pack them into sequences.
    passes = []
    allFiles = [f for f in os.listdir(passDir) if rootPrefix in f]
    # parse the pass name for each of these files. if it doesn't already exist in passes, add it.
    separator = '.'
    for f in allFiles:
        # turntable_V5Aspire_C000_A000_L008_BG_masterLayer.reflect.0065.exr
        passName = f.split(rootPrefix)[-1].lstrip('._ ')
        # reflect.0065.exr, or in some cases reflect_0065.exr...
        regex = re.compile('[\._-]{1}\d+\.')
        match = regex.findall(passName)
        if debug:
            print 'matching %s...' % (passName)
            print match
        if match:
            passName = passName.split(match[0])[0]
            separator = match[0][0]
            if passName not in passes:
                passes.append(passName)
    if debug:
        print '\npasses found:'
        print '\n'.join(passes)
    # for each entry in passes, create a sequence string to load. use passDir and rootPrefix, then tack on the passName, frame number and file extension.
    # the frame range and file extension can be gathered from the rootSequence, since they should all be identical.
    # the rootSequence itself is considered "RGBA."
    # first, need to establish a suffix (separator, frame number in printf syntax (%04d), .ext)
    fileExt = os.path.splitext(rootSequence)[-1].split(' ')[0] # the split is to get rid of the (0-##) at the end of the sequence after the file extension
    frameNumRegex = re.compile('[\._-]%\d{1,2}[dD]')
    search = frameNumRegex.findall(rootRead['file'].getValue())
    rootSuffix = fileExt
    if len(search) > 0:
        # there is an extension here. search returns a list of matches, so just use the first index as your suffix, plus the file extension.
        rootSuffix = search[0]+fileExt
    # sequence string = os.path.join(passDir,rootPrefix)+separator+passes[n]+rootSuffix
    # start with rootRead. this is our RGBA channel. for every other pass, create a Read node, shuffle RGBA to the appropriate channel (p), and merge it (+) to the flow without altering RGBA.
    for p in passes:
        newSeqStr = os.path.join(passDir,rootPrefix)+separator+p+rootSuffix
        newSeqStr = newSeqStr.replace('\\','/')
        newRead = nuke.nodes.Read()
        newRead['file'].fromUserText(newSeqStr)
    

            

def alignNodes(nodes,axis,value,debug=0,*args):
    # align center of each node to the given axis.
    # first, to force the measurement of each node, run autoplaceSnap
    for i in nodes:
        # get current position
        x = i.xpos()
        y = i.ypos()
        nuke.autoplaceSnap(i)
        i['xpos'].setValue(x)
        i['ypos'].setValue(y)
        if axis=='x':
            if debug:
                print 'aligning node %s to value %s=%d, node dimension is %d' % (i.name(),axis,value,i.screenWidth())
            i['xpos'].setValue(int(value-(i.screenWidth()/2)))
            # i.setXpos(int(value-(i.screenWidth()/2)))
        else:
            if debug:
                print 'aligning node %s to value %s=%d, node dimension is %d' % (i.name(),axis,value,i.screenHeight())
            i['ypos'].setValue(int(value-(i.screenHeight()/2)))
            # i.setYpos(int(value-(i.screenHeight()/2)))


def autoComp(beauty, tech, matte, comp_name, backdropColor, Xpos=-1, Ypos=-1, xMargin=120, yMargin=80, *args):
    # make giant-ass comp
    # first make the reads. add all non-RGBA layers together through merge nodes.
    # beauty read, shuffle and dot
    if Xpos==-1:
        Xpos = nuke.mustache_AC_xpos
    if Ypos==-1:
        Ypos = nuke.mustache_AC_ypos
    shufLabel = '[knob in]'
    beautyNode = nuke.nodes.Read(xpos=Xpos,ypos=Ypos)
    beautyNode['file'].fromUserText(beauty)
    # print('DEBUG: creating beautyNode at location %d, %d') % (Xpos, Ypos)
    beautyDot = nuke.nodes.Dot(inputs=[beautyNode])
    # tech read and merge
    techNode = nuke.nodes.Read(ypos=Ypos+yMargin)
    techNode['file'].fromUserText(tech)
    techMerge = nuke.nodes.Merge2(inputs=[beautyDot,techNode],operation='plus',also_merge='all',A='none')
    # matte read and merge
    matteNode = nuke.nodes.Read(ypos=Ypos+(yMargin*2))
    matteNode['file'].fromUserText(matte)
    matteMerge = nuke.nodes.Merge2(inputs=[techMerge,matteNode],operation='plus',also_merge='all',A='none')
    # quick contact sheet
    contactSheet = nuke.nodes.LayerContactSheet(inputs=[matteNode],postage_stamp=True,label='MATTE REFERENCE',ypos=Ypos+(yMargin*3),showLayerNames=1)
    # okay, now we start with the shuffles. there are specific channels we're looking for, with specific rules.
    # beauty comps should include some or all of the following:
    # lighting, gi, reflect, refract, selfIllum, specular, sss, lightSelect#, shadow, rawShadow
    # passes to ADD: lighting (or lightSelect), gi, reflect, refract, sss, specular, selfIllum
    # passes to add OPTIONALLY: shadow (default merge to zero)
    # passes to MULTIPLY: rawShadow (after inversion)
    # if an AO pass is present we'll multiply that against the GI if there is a GI pass.
    beautyChans = list(set([f.split('.')[0] for f in beautyNode.channels()]))
    techChans = list(set([f.split('.')[0] for f in techNode.channels()]))
    matteChans = list(set([f.split('.')[0] for f in matteNode.channels()]))
    defaultBeautyChans = ['GI','reflect','refract','selfIllum','specular','SSS','shadow','rawShadow','caustics']
    # nodePairs is a list of tuples joining each shuffle node with its accompanying merge/switch. this is for alignment later.
    nodePairs = []
    # first split out lightSelect elements.
    lightSelects = [f for f in beautyChans if 'lightselect' in f]
    if lightSelects:
        # shuffle these out first, then connect them to a final switch (input 1. input 0 will be the lighting pass)
        for i in range(0,len(lightSelects)):
            if i==0:
                shuf = nuke.nodes.Shuffle(inputs=[matteMerge],label=shufLabel)
                shuf['in'].setValue(lightSelects[i])
                dot = nuke.nodes.Dot(inputs=[shuf])
                nodePairs.append((shuf,dot))
            else:
                shuf = nuke.nodes.Shuffle(inputs=[nodePairs[-1][0]],label=shufLabel)
                shuf['in'].setValue(lightSelects[i])
                merge = nuke.nodes.Merge2(inputs=[nodePairs[-1][-1],shuf],operation='plus')
                nodePairs.append((shuf,merge))
        # now bring in the lighting pass and make a switch
        if 'lighting' in beautyChans:
            lighting = nuke.nodes.Shuffle(inputs=[shuf],label=shufLabel)
            lighting['in'].setValue('lighting')
            switch = nuke.nodes.Switch(inputs=[nodePairs[-1][-1],lighting],label='SEPARATE_LIGHTS',which=1)
            nodePairs.append((lighting,switch))
    else:
        # if there are no lightSelects, check for a lighting pass and just add a dot
        if 'lighting' in beautyChans:
            lighting = nuke.nodes.Shuffle(inputs=[matteMerge],label=shufLabel)
            lighting['in'].setValue('lighting')
            dot = nuke.nodes.Dot(inputs=[lighting])
            nodePairs.append((lighting,dot))
    beautyChansLeft = [f for f in beautyChans if f not in lightSelects]
    # iterate through the rest of the channels in order. if the channel doesn't meet an existing case, save it for later.
    knownLayersPresent = sorted([f for f in beautyChansLeft if f in defaultBeautyChans],key=str.lower)
    for i in range(0,len(knownLayersPresent)):
        prevNodes = nodePairs[-1]
        if knownLayersPresent[i] == 'GI':
            # look for an AO to multiply against
            AOchan = [f for f in techChans if 'VRayDirt' in f]
            if AOchan:
                # shuffle this in first, then multiply against GI
                AO = nuke.nodes.Shuffle(inputs=[prevNodes[0]],label=shufLabel)
                AO['in'].setValue(AOchan[0])
                GI = nuke.nodes.Shuffle(inputs=[AO],label=shufLabel)
                GI['in'].setValue('GI')
                mult = nuke.nodes.Merge2(inputs=[GI,AO],operation='multiply',mix=0)
                merge = nuke.nodes.Merge2(inputs=[prevNodes[-1],mult],operation='plus')
                nodePairs.append((AO,))
                nodePairs.append((GI,mult,merge))
            else:
                # just merge this shit in
                GI = nuke.nodes.Shuffle(inputs=[prevNodes[0]],label=shufLabel)
                GI['in'].setValue('GI')
                merge = nuke.nodes.Merge2(inputs=[prevNodes[-1],GI])
                nodePairs.append((GI,merge))
        elif knownLayersPresent[i] == 'rawShadow':
            # invert and then multiply
            rawShadow = nuke.nodes.Shuffle(inputs=[prevNodes[0]],label=shufLabel)
            rawShadow['in'].setValue('rawShadow')
            invert = nuke.nodes.Invert(inputs=[rawShadow])
            merge = nuke.nodes.Merge2(inputs=[prevNodes[-1],invert],operation='multiply',mix=0)
            nodePairs.append((rawShadow,invert,merge))
        elif knownLayersPresent[i] == 'shadow':
            # default merge mix to 0
            shadow = nuke.nodes.Shuffle(inputs=[prevNodes[0]],label=shufLabel)
            shadow['in'].setValue('shadow')
            merge = nuke.nodes.Merge2(inputs=[prevNodes[-1],shadow],operation='plus',mix=0)
            nodePairs.append((shadow,merge))
        else:
            layer = nuke.nodes.Shuffle(inputs=[prevNodes[0]],label=shufLabel)
            layer['in'].setValue(knownLayersPresent[i])
            merge = nuke.nodes.Merge2(inputs=[prevNodes[-1],layer],operation='plus')
            nodePairs.append((layer,merge))
    # now for unknown layers
    unknownLayers = [f for f in beautyChansLeft if f not in defaultBeautyChans and f!='lighting' and f!='rgba']
    for i in range(0,len(unknownLayers)):
        prevNodes = nodePairs[-1]
        # we don't know what this is. shuffle it out, but don't merge with anything.
        layer = nuke.nodes.Shuffle(inputs=[prevNodes[0]],label=shufLabel)
        layer['in'].setValue(unknownLayers[i])
        nodePairs.append((layer,))
    # each channel should be shuffled out by now. the last step is to shuffle the original alpha back into the comp. this is our output.
    # this should be connected to the last merge node we created, whatever that is.
    # sort backwards through nodePairs and find the first listing that has at least two values.
    nodePairsRev = sorted(nodePairs,reverse=True)
    nodePairIndex = 0
    for x in range(0,len(nodePairsRev)):
        if len(nodePairsRev[x]) > 1:
            # this one is good
            nodePairIndex = x
            break
    #fixAlpha = nuke.nodes.Shuffle(inputs=[nodePairsRev[nodePairIndex][-1]],label='fix alpha')
    #fixAlpha['in'].setValue('origRGBA')
    #fixAlpha['out'].setValue('alpha')
    #fixAlpha['red'].setValue('alpha')
    fixAlpha = nuke.nodes.Copy(inputs=[nodePairsRev[nodePairIndex][-1],beautyDot],label='fix alpha',from0='rgba.alpha',to0='rgba.alpha')
    nodePairs.append((fixAlpha,))
    out = nuke.nodes.NoOp(inputs=[fixAlpha],label='OUTPUT')
    out['tile_color'].setValue(294519039)
    nodePairs.append((out,))
    # now to align everything.
    # for each entry in nodePairs, there will be 1-3 entries in the tuple.
    col1 = []
    col2 = []
    col3 = []
    for x in range(0,len(nodePairs)):
        col1.append(nodePairs[x][0])
        if len(nodePairs[x]) == 3:
            col2.append(nodePairs[x][1])
            col3.append(nodePairs[x][2])
        elif len(nodePairs[x]) == 2:
            col3.append(nodePairs[x][1])
        # now do vertical alignment.
        alignNodes(nodePairs[x],'y',Ypos+(yMargin*(x+3)))
    # cycle through cols and do horizontal alignment.
    col1.extend([beautyDot,techMerge,matteMerge])
    alignNodes(col1,'x',Xpos+(xMargin*2),1)
    alignNodes(col2,'x',Xpos+(xMargin*3),1)
    alignNodes(col3,'x',Xpos+(xMargin*6),1)
    alignNodes([fixAlpha],'x',Xpos+(xMargin*6),1)
    alignNodes([out],'y',Ypos+(yMargin*(len(nodePairs)+1)))
    alignNodes([out],'x',Xpos+(xMargin*7),1)
    alignNodes([beautyNode,techNode,matteNode,contactSheet],'x',Xpos,1)
    alignNodes([beautyNode,beautyDot],'y',Ypos,1)
    alignNodes([techNode,techMerge],'y',Ypos+yMargin,1)
    alignNodes([matteNode,matteMerge],'y',Ypos+(yMargin*2),1)
    # contact sheet goes to the wrong place for some inexplicable reason, fuck you nuke
    contactSheet.setYpos(matteNode.ypos()+yMargin)
    # create a backdrop behind the whole table
    back = nuke.nodes.BackdropNode(xpos=Xpos-80,ypos=Ypos-120,bdwidth=(xMargin*8)+60,bdheight=yMargin*(len(nodePairs)+3)+60,label=comp_name,note_font_size=36,note_font='bold')
    back['tile_color'].setValue(backdropColor)
    nodesList = [beautyDot,techMerge,matteMerge,beautyNode,techNode,matteNode,contactSheet,back]
    for pair in nodePairs:
        for i in pair:
            nodesList.append(i)
    for node in nuke.selectedNodes():
        node.setSelected(False)
    for node in nodesList:
        node.setSelected(True)
    backX = back.xpos()+back['bdwidth'].getValue()/2
    backY = back.ypos()+back['bdheight'].getValue()/2
    nuke.zoom(0.5,[backX,backY])
    nuke.mustache_AC_xpos = nuke.mustache_AC_xpos+back['bdwidth'].getValue()+20
    # nuke.mustache_AC_ypos = nuke.mustache_AC_ypos+100
    # print('\nActual location: %d, %d') % (beautyNode.xpos(), beautyNode.ypos())