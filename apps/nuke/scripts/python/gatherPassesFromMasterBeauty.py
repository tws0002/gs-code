from __future__ import with_statement
import nuke
import os

'''
import sys

sys.path.append("W:/pvsz_12034/assets/tools/lavoy/nukeTools")

import gatherPassesFromMasterBeauty
reload(gatherPassesFromMasterBeauty)
'''


def getChannelsfromRead(node):
    chanDict={}
    for ch in node.channels():
        chName=ch.split('.')[0]
        chColor=ch.split('.')[-1]
        if not chName in chanDict:
            chanDict[chName]=[]
        chanDict[chName].append(chColor)    
    return chanDict

def findRendersFromDirectory(dir):
    seqs=[]
    for path, dirs, files in os.walk(dir):
        fList= nuke.getFileNameList(path,True)
        for item in fList:
            item=item.replace('exrsl','')
            if 'exr' in item:
                foundPath=path+'/'+item
                seqs.append(foundPath.replace('\\','/'))
                
    if len(seqs)<2:
        if nuke.ask('No other passes found in selected Read directory, search in parent directory instead?'):
            dir=os.path.dirname(dir)
            seqs=[]
            for path, dirs, files in os.walk(dir):
                fList= nuke.getFileNameList(path,True)
                for item in fList:
                    item=item.replace('exrsl','')
                    if 'exr' in item:
                        foundPath=path+'/'+item
                        seqs.append(foundPath.replace('\\','/'))
                        
    commonPath=os.path.commonprefix(seqs)
    print commonPath
    #get commonName
    names=[]
    for each in seqs:
        names.append(each.split(' ')[0].split('/')[-1].split('.')[0])

    commonName=os.path.commonprefix(names)
    print commonName
    uniquePaths=[]
    uniqueNames=[]
    for seq in seqs:
        uniquePath=seq.replace(commonPath,"").split(" ")[0]
        if not uniquePath in uniquePaths:
            uniquePaths.append(uniquePath)
            uniqueNames.append("".join(uniquePath.split("/")[-1].replace(commonName,"").split(".")[:-2]))#passName.####.exr
        
        
    return uniquePaths,uniqueNames,commonPath,commonName

#create readGroup
def createReadGroup(node,grp):
    knobs=['file','cacheLocal','format','proxy','proxy_format','first','before','last','after','frame_mode','frame','origfirst','origlast','on_error','reload','colorspace','premultiplied','raw','auto_alpha','offset_negative_display_window']
    for k in knobs:
        l = nuke.Link_Knob(k)
        l.makeLink(node.name(), k)
        grp.addKnob( l )
        if not node.knobs()[k].getFlag(nuke.STARTLINE):
            l.clearFlag(nuke.STARTLINE)

def main():
    #get other passes from selected Read
    n=nuke.selectedNode()
    grp=nuke.collapseToGroup(n)
    myGroup=nuke.toNode(grp.name())
    n= nuke.allNodes('Read',group=myGroup)[0]
    n['name'].setValue("HeroRead")

    f=n['file'].value()
    dir=os.path.dirname(f)
    seqData=findRendersFromDirectory(dir)
    uniquePaths,uniqueNames,commonPath,commonName=seqData

    #return message of number of sequences found
    nuke.message(str(len(uniqueNames)) +' sequences found:'+"\n"+"\n".join(uniqueNames))

    nodes=[]
    priorShuffle=''
    with grp:
        for p,each in enumerate(uniqueNames):
            if not each=="":
                #create read node, set expressions
                r=nuke.nodes.Read()
                r['file'].setValue(commonPath+uniquePaths[p])
                r['first'].setExpression("HeroRead.first")
                r['last'].setExpression("HeroRead.last")
                r['name'].setValue(each)
        
                #create shuffleCopy and setup
                sh=nuke.nodes.ShuffleCopy()
                sh.setInput(1,r)
                if not priorShuffle:
                    sh.setInput(0,n)
                if priorShuffle:
                    sh.setInput(0,priorShuffle)
                sh['in'].setValue('rgba')
                sh['in2'].setValue('none')
                nuke.tcl('add_layer { '+each+' '+each+'.red '+each+'.green '+each+'.blue '+each+'.alpha}')
                sh['out'].setValue('none')
                sh['out2'].setValue(each)
                #sh['red'].setValue('red')
                #sh['green'].setValue('green')
                #sh['blue'].setValue('blue')
                #sh['alpha'].setValue('alpha')
                sh['black'].setValue('red')    
                sh['white'].setValue('green')    
                sh['red2'].setValue('blue') 
                sh['green2'].setValue('alpha')    
                sh['label'].setValue('[value out2]')

                #add to array
                priorShuffle=sh
                nodes.append(r)
        nuke.toNode('Output1').setInput(0,sh)
        
    createReadGroup(n,grp)
    grp['postage_stamp'].setValue(1)  
    grp.knobs()['User'].setLabel("MultiChannelRead")
    grp['label'].setValue("[lrange [split [value file] / ] [expr [llength [split [value file] / ]]-3] [expr [llength [split [value file] / ]]-3] ]")
    
    pyButton = nuke.PyScript_Knob('updateVersion', "updatePassesToBeautyVersion", "gatherPassesFromMasterBeauty.updatedPassesVersion()")
    pyButton.setFlag(nuke.STARTLINE) 
    grp.addKnob(pyButton)


def updatedPassesVersion():
    import re
    pattern = re.compile('v[0-9]{2,6}')
    result = pattern.findall(nuke.thisNode()['file'].value())
    with nuke.thisNode():
        for read in nuke.allNodes("Read"):
            path=read['file'].value()
            foundVersions=pattern.findall(path)
            for f in foundVersions:
                path=path.replace(f,result[0])
            print "updated:",path
            read['file'].setValue(path)
    
