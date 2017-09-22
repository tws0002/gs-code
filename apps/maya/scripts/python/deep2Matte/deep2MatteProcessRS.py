#!/usr/bin/python
import sys
import os
import time
import threading
import random
import json
#sys.path.append(os.path.dirname(__file__)+"/OpenImageIO")
#sys.path.append(os.path.dirname(__file__))
sys.path.append('//scholar/pipeline/lib/python')
from OpenImageIO import OpenImageIO as oiio

nameTuple= ("objectMatte00.R",
            "objectMatte00.G",
            "objectMatte00.B",
            "objectMatte00.A",
            "objectMatte01.R",
            "objectMatte01.G",
            "objectMatte01.B",
            "objectMatte01.A",
            "materialMatte00.R",
            "materialMatte00.G",
            "materialMatte00.B",
            "materialMatte00.A",
            "materialMatte01.R",
            "materialMatte01.G",
            "materialMatte01.B",
            "materialMatte01.A",
            "assetMatte00.R",
            "assetMatte00.G",
            "assetMatte00.B",
            "assetMatte00.A",
            "assetMatte01.R",
            "assetMatte01.G",
            "assetMatte01.B",
            "assetMatte01.A")

class ProgressBar(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.event = threading.Event()

    def run(self):
        event = self.event
        while not event.is_set():
            sys.stdout.write(".")
            sys.stdout.flush()
            event.wait(1)
 
    def stop(self):
        self.event.set()

def createAssetData(deepFileSpec):
    #create assetData IDs and asset namespaces
    assetDict={0.0:0.0}
    namespaceDict={}
    for i in range(len(deepFileSpec.extra_attribs)) :
        if 'obj' in deepFileSpec.extra_attribs[i].name:
            objId=int(str(deepFileSpec.extra_attribs[i].name.lstrip("obj0")))
            objName=deepFileSpec.extra_attribs[i].value
            hasNamespace=objName.split(":")
            ns=''
            if len(hasNamespace):
                ns=hasNamespace[0]
                nsHsh= abs(hash(ns)) % (10 ** 7)
            else:
                nsHsh= abs(hash('NONE')) % (10 ** 7)
            assetDict[objId]=nsHsh
            if not nsHsh in namespaceDict.keys():
                namespaceDict[nsHsh]=ns
    return assetDict,namespaceDict

def genRand(value):
	randomVal=0
	if value:
		random.seed(value)
		randomVal=random.random()
	return randomVal

def convertSceneData(sceneData):
    objData={}
    for mat in sceneData['material']:
        for id in sceneData['material'][mat]:
            id=str(id)
            if not id in objData.keys():
                objData[id]=[0,0,0,0]
            objData[id][0]=str(mat)
            objData[id][1]=abs(hash(mat))%(10**7)
    for ast in sceneData['asset']:
        for id in sceneData['asset'][ast]:
            id=str(id)
            if not id in objData.keys():
                objData[id]=[0,0,0,0]
            objData[id][2]=str(ast)
            objData[id][3]=abs(hash(ast))%(10**7)
    return objData


def consolidateIdSamplesPerPixel(deepData,pixel,idIndex,alphaIndex):
    idList=[]
    alphaList=[]
    samples=deepData.samples(pixel)
    for s in range(samples)[::-1]:
        alpha= deepData.deep_value(pixel,alphaIndex,s)
        id= deepData.deep_value_uint(pixel,idIndex,s)
        #print id,alpha
        found=0
        for t in range(len(idList)):
            priorAlpha=alphaList[t]
            if id==idList[t]:
                found=1
                alphaList[t]=priorAlpha*(1.0-alpha)+alpha
            else:
                alphaList[t]=priorAlpha*(1-alpha)
        if not found:
            idList.append(float(id))
            alphaList.append(alpha)
    #extend array to fill all channels
    while(len(idList)<4):
        idList.append(0.0)
        alphaList.append(0.0)
    return idList,alphaList

def processDeepAE(infile,outfile):
    startTime = time.time()

    outdir=os.path.dirname(outfile)
    outfilename=os.path.basename(outfile).replace('Matte','CONTEXTLAYER')
    outfile=os.path.join(outdir,outfilename)
    print outfile

    #get deepFile input
    deepFile=str(infile)

    deepBuf=oiio.ImageInput.open(deepFile)
    #get channel index
    alphaChannelName='A'
    obIdChannelName='objectId'
    matIdChannelName='multimatteID'
    #obIdChannelName='other.objectId'
    #matIdChannelName='other.multimatteID'
    deepFileSpec=deepBuf.spec()
    print deepFileSpec.channelnames
    print deepFileSpec.channelformats


    alphaIndex=deepFileSpec.channelnames.index(alphaChannelName)
    objIdIndex=deepFileSpec.channelnames.index(obIdChannelName)
    matIdIndex=deepFileSpec.channelnames.index(matIdChannelName)
    print objIdIndex,matIdIndex,alphaIndex
    #create channelBuffers
    outputSpec=oiio.ImageSpec(deepFileSpec.width, deepFileSpec.height, 4, oiio.UINT16)
    objBufA=oiio.ImageBuf(outputSpec)
    objBufB=oiio.ImageBuf(outputSpec)
    matBufA=oiio.ImageBuf(outputSpec)
    matBufB=oiio.ImageBuf(outputSpec)
    astBufA=oiio.ImageBuf(outputSpec)
    astBufB=oiio.ImageBuf(outputSpec)

    print 'Converting...'
    progress_bar = ProgressBar()
    progress_bar.start()

    #getAssetData
    assetDict,namespaceDict=createAssetData(deepFileSpec)

    deepData=deepBuf.read_native_deep_scanlines(0,deepFileSpec.height,100,0,len(deepFileSpec.channelnames)-1)

    #iterate over pixels
    for pixel in range(0,deepData.pixels):#deepData.pixels
        #get list of sorted samples
        #print pixel
        x=pixel%deepFileSpec.width
        y=int(pixel/deepFileSpec.width)
        objIdList,objAlphaList=consolidateIdSamplesPerPixel(deepData,pixel,objIdIndex,alphaIndex)
        matIdList,matAlphaList=consolidateIdSamplesPerPixel(deepData,pixel,matIdIndex,alphaIndex)
        objBufA.setpixel(x,y,tuple([genRand(objIdList[0]),genRand(objIdList[1]),genRand(objIdList[2]),genRand(objIdList[3])]))
        objBufB.setpixel(x,y,tuple([objAlphaList[0],objAlphaList[1],objAlphaList[2],objAlphaList[3]]))
        matBufA.setpixel(x,y,tuple([genRand(matIdList[0]),genRand(matIdList[1]),genRand(matIdList[2]),genRand(matIdList[3])]))
        matBufB.setpixel(x,y,tuple([matAlphaList[0],matAlphaList[1],matAlphaList[2],matAlphaList[3]]))
        try:
            astBufA.setpixel(x,y,tuple([genRand(assetDict[objIdList[0]]),genRand(assetDict[objIdList[1]]),genRand(assetDict[objIdList[2]]),genRand(assetDict[objIdList[3]])]))
        except:
            pass
        astBufB.setpixel(x,y,tuple([objAlphaList[0],objAlphaList[1],objAlphaList[2],objAlphaList[3]]))

    #write out buffers as 16bit pngs

    outdir=os.path.dirname(outfile)
    outfilename=os.path.basename(outfile).replace('Matte','CONTEXTLAYER')
    outfile=os.path.join(outdir,outfilename)
    print outfile


    objBufA.write(str(outfile).replace('CONTEXTLAYER','ObjectMatte00').replace('.exr','.png'))
    objBufB.write(str(outfile).replace('CONTEXTLAYER','ObjectMatte01').replace('.exr','.png'))
    matBufA.write(str(outfile).replace('CONTEXTLAYER','MaterialMatte00').replace('.exr','.png'))
    matBufB.write(str(outfile).replace('CONTEXTLAYER','MaterialMatte01').replace('.exr','.png'))
    astBufA.write(str(outfile).replace('CONTEXTLAYER','AssetMatte00').replace('.exr','.png'))
    astBufB.write(str(outfile).replace('CONTEXTLAYER','AssetMatte01').replace('.exr','.png'))

    progress_bar.stop()
    progress_bar.join()

    outInfo= 'duration: '+ str(time.time()-startTime)+ ' seconds.'
    return outInfo

def processDeep(infile,outfile,sceneDataPath):
    startTime = time.time()

    #get exported sceneData
    objData={}
    sceneData={}
    try:
        with open(sceneDataPath,'r') as fp:
            sceneData = json.load(fp)
        objData=convertSceneData(sceneData)
    except:
        pass

    print 'in: ',infile
    print 'out: ',outfile
    #get deepFile input
    deepFile=str(infile)

    #deepFileBuf=oiio.ImageBuf(deepFile)
    print oiio

    deepBuf=oiio.ImageInput.open(deepFile)
    #get channel index
    alphaChannelName='A'
    obIdChannelName='ID.R'
    deepFileSpec=deepBuf.spec()
    print 'deepExrChannels: ',deepFileSpec.channelnames

    alphaIndex=deepFileSpec.channelnames.index(alphaChannelName)
    objIdIndex=deepFileSpec.channelnames.index(obIdChannelName)
    print 'ID: ',objIdIndex
    print 'A: ',alphaIndex
    #create channelBuffers
    outputSpec=oiio.ImageSpec(deepFileSpec.width, deepFileSpec.height, 24, oiio.FLOAT)
    outputSpec.channelnames=tuple(nameTuple)
    outBuf=oiio.ImageBuf(outputSpec)



    print 'Converting...'
    progress_bar = ProgressBar()
    progress_bar.start()


    deepData=deepBuf.read_native_deep_scanlines(0,deepFileSpec.height,100,0,len(deepFileSpec.channelnames))


    allObjIds=[]
    allMatIds=[]
    allAstIds=[]
    #iterate over pixels
    for pixel in range(0,deepData.pixels):#deepData.pixels
        #get list of sorted samples
        x=pixel%deepFileSpec.width
        y=int(pixel/deepFileSpec.width)
        objIdList,objAlphaList=consolidateIdSamplesPerPixel(deepData,pixel,objIdIndex,alphaIndex)
        for id in objIdList:
            id=str(int(id))
            if not id in objData.keys():
                objData[id]=[0,0,0,0]
        
        outBuf.setpixel(x,y,tuple([objIdList[0],objIdList[1],objIdList[2],objIdList[3],#objectMatte00
                                objAlphaList[0],objAlphaList[1],objAlphaList[2],objAlphaList[3],#objectMatte01
                                objData[str(int(objIdList[0]))][1],#materialMatte00
                                objData[str(int(objIdList[1]))][1],
                                objData[str(int(objIdList[2]))][1],
                                objData[str(int(objIdList[3]))][1],
                                objAlphaList[0],objAlphaList[1],objAlphaList[2],objAlphaList[3],#materialMatte01
                                objData[str(int(objIdList[0]))][3],#assetMatte00
                                objData[str(int(objIdList[1]))][3],
                                objData[str(int(objIdList[2]))][3],
                                objData[str(int(objIdList[3]))][3],
                                objAlphaList[0],objAlphaList[1],objAlphaList[2],objAlphaList[3]]))#assetMatte01

    progress_bar.stop()
    progress_bar.join()
    '''
    #filter used IDs, remove unused IDs from metadata
    allObjIds.extend(objIdList)
    allMatIds.extend(matIdList)

    allObjIds=set(allObjIds)
    allMatIds=set(allMatIds)
    allAstIds=set(allAstIds)

    #filter visible Ids in metadata
    for i in range(len(deepFileSpec.extra_attribs)):
        idName=deepFileSpec.extra_attribs[i].name
        if 'obj' in idName or 'mat' in idName:
            idString=deepFileSpec.extra_attribs[i].value
            idInt=int(idName[3:])
            if idInt in allObjIds or idInt in allMatIds:
                outbuffer.specmod().attribute(idName,idString)
    '''

    #add metadata
    for asset in sceneData['asset'].keys():
        outBuf.specmod().attribute('ast'+str(abs(hash(asset))%(10**7)).zfill(7),str(asset))
    for material in sceneData['material'].keys():
        outBuf.specmod().attribute('mat'+str(abs(hash(material))%(10**7)).zfill(7),str(material))
    for obj in sceneData['object'].keys():
        outBuf.specmod().attribute('obj'+str(obj).zfill(7),str(sceneData['object'][obj]))


    outBuf.write(str(outfile).replace('\\','/'))

    outInfo= 'duration: '+ str(time.time()-startTime)+ ' seconds.'
    return outInfo
