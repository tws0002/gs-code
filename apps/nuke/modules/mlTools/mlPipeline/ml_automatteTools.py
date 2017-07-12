from __future__ import with_statement
import nuke
import os,re,sys
import nukescripts

exprTemplate="(M0.red==ID?M1.red:0)+(M0.green==ID?M1.green:0)+(M0.blue==ID?M1.blue:0)+(M0.alpha==ID?M1.alpha:0)"

def makeExpression(IDList,type):
    layer1=type
    layer2=type[:-1]+"1"
    exprString=""
    for id in IDList:
        exprString+=exprTemplate.replace("M0",layer1).replace("M1",layer2).replace("ID",id)+" + "
    exprString=exprString[:-2]
    return exprString

def update():
    node=nuke.thisNode()
    if node.Class()=='ml_automatte':#prevent Root interaction
        IdList=node['IDList']
        IDMultiList=node['IDMultiList']
        currentIDList=IdList.value().split(",")
        IdList.setValue(array2List(currentIDList,','))
        IDMultiList.setValue(array2List(currentIDList,'\n'))
        matteList=node['matteList']
        matteMultiList=node['matteMultiList']
        node.begin()
        matteChan=nuke.toNode("insertData").knob("in").value()#object or material
        exprNode=nuke.toNode("matteExpr")
        exprNode['expr0'].setValue(makeExpression(currentIDList,matteChan))
        if currentIDList[0]=='':#if reset
            exprNode['expr0'].setValue('0')
        node.end()

        ns=node['namespace'].value()
        foundMattes=[]
        for id in currentIDList:
            if id:
                if node['matteType'].value()=="object":
                    key='exr/obj'+id.zfill(7)
                if node['matteType'].value()=="material":
                    key='exr/mat'+id.zfill(7)
                if node['matteType'].value()=="asset":
                    key='exr/ast'+id.zfill(7)
                if key in node.metadata().keys():
                    foundMatte=node.metadata()[key]
                    foundMattes.append(filterNS(foundMatte,ns))
        matteList.setValue(array2List(foundMattes,','))  
        matteMultiList.setValue(array2List(foundMattes,'\n'))

def filterNS(matteString,ns):
    node=nuke.thisNode()
    if ns:
        return matteString
    else:
        m=matteString.split(':')
        if len(m)>0:
            return m[-1]
        else:
            return matteString

def addMatte():
    node=nuke.thisNode()
    if node.input(0):
        sample=nuke.thisKnob()
        IdList=node['IDList']
        IDMultiList=node['IDMultiList']
        currentIDList=IdList.value().split(",")
        currentVal=str(int(sample.value()[0]))
        if not currentVal in currentIDList and currentVal != '0':
            currentIDList.extend([currentVal])
            IdList.setValue(array2List(currentIDList,','))
            IDMultiList.setValue(array2List(currentIDList,'\n'))
        update()

def subtractMatte():
    node=nuke.thisNode()
    if node.input(0):
        sample=nuke.thisKnob()
        IdList=node['IDList']
        IDMultiList=node['IDMultiList']
        currentIDList=IdList.value().split(",")
        currentVal=str(int(sample.value()[0]))
        if currentVal in currentIDList:
            currentIDList.remove(currentVal)
            IdList.setValue(array2List(currentIDList,','))
            IDMultiList.setValue(array2List(currentIDList,'\n'))
        update()


def searchIDs():
    node=nuke.thisNode()
    IdList=node['IDList']
    IDMultiList=node['IDMultiList']
    searchString=node['search']
    foundIDs=[]
    for k in node.metadata().keys():
        searchText=searchString.value()
        if searchText in str(node.metadata()[k]):
            #print id
            id=str(int(k.split('/')[-1].strip("objmat")))
            foundIDs.append(id)
    currentIDList=IdList.value().split(",")
    for foundID in foundIDs:
        if not foundID in currentIDList:
            currentIDList.extend([foundID])
    IdList.setValue(array2List(currentIDList,','))
    IDMultiList.setValue(array2List(currentIDList,'\n'))
    update()

def clear():
    node=nuke.thisNode()
    node['IDList'].setValue('')
    node['matteList'].setValue('')
    node['IDMultiList'].setValue('')
    node['matteMultiList'].setValue('')
    update()

def changeMatteType():
    node=nuke.thisNode()
    mType=node['matteType']
    clear()
    node.begin()
    exprNode=nuke.toNode("insertData")   
    if mType.value()=="object":
        exprNode['in'].setValue("objectMatte00")
    if mType.value()=="material":
        exprNode['in'].setValue("materialMatte00")
    if mType.value()=="asset":
        exprNode['in'].setValue("assetMatte00")
    node.end()
    update()

def exportMatte():
    node=nuke.thisNode()
    mattes= node['matteList'].value().replace(":","_").replace("|","_").split(',')
    with node:
        exprNode=nuke.toNode("matteExpr")
        express=exprNode['expr0'].value()
    expr=nuke.nodes.Expression()
    expr['expr0'].setValue(express)
    expr['channel0'].setValue('rgba')
    expr.setInput(0,node)
    expr.setName('_'.join(mattes))


def array2List(array,delim):
    list=''
    if array:
        if len(array)<2:
            list=array[0]
        else:
            while '' in array:
                array.remove('')
            list=str(delim).join(array)
    return list