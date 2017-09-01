import nuke
attrConvert={   "translateX":"translate:0",
                "translateY":"translate:1",
                "translateZ":"translate:2",
                "rotateX":"rotate:0",
                "rotateY":"rotate:1",
                "rotateZ":"rotate:2",
                "scaleX":"scaling:0",
                "scaleY":"scaling:1",
                "scaleZ":"scaling:2",
                "horizontalFilmAperture":"haperture:0",
                "verticalFilmAperture":"vaperture:0",
                "focalLength":"focal:0"}

transformAttrs=["translateX",
            "translateY",
            "translateZ",
            "rotateX",
            "rotateY",
            "rotateZ",
            "scaleX",
            "scaleY",
            "scaleZ",
            "horizontalFilmAperture",
            "verticalFilmAperture",
            "focalLength"]

def main():
    cam = nuke.getFilename('select Maya File', '*.ma')
    #cam='E:/Desktop/trash/testAnim.ma'
    fileObject=open(cam,"r")
    contents=fileObject.read()
    fileObject.close()

    sceneData={}
    currentObj=''
    currentAttr=''
    chunkStart=0
    chunk=''
    for line in contents.split('\n'):
        if 'createNode' in line:
            cmd,typ,fl,name=line.split(" ")[:4]
            name=name.strip("\";")
            nameparts=name.split("_")
            if len(nameparts)>1:
                obj="_".join(nameparts[:-1])
                attr=nameparts[-1]
                if attr in transformAttrs:
                    currentObj=obj
                    currentAttr=attr
        if "ktv[" in line and currentAttr:
            chunkStart=1
        if chunkStart:
            lineFiltered=line.strip("\t;")
            chunk+=lineFiltered
        if chunkStart and ";" in line:
            if not currentObj in sceneData.keys():
                sceneData[currentObj]={}
            if not currentAttr in sceneData[currentObj].keys():
                sceneData[currentObj][currentAttr]=[]
            keys= chunk.split("]\"  ")[1]
            keys=keys.split(" ")  
            for i,k in enumerate(keys):
                if i%2==0:
                    sceneData[currentObj][currentAttr].append(k+":"+keys[i+1])    
            chunk=''
            chunkStart=0
            currentAttr=''

    transforms=sceneData.keys()
    transforms.sort()
    p = nuke.Panel('import transforms',scrollable=True)
    p.addEnumerationPulldown('transform1',' '.join(transforms))
    p.addEnumerationPulldown('transform2',' '.join(transforms))
    p.addEnumerationPulldown('transform3',' '.join(transforms))
    p.addEnumerationPulldown('transform4',' '.join(transforms))
    p.addEnumerationPulldown('transform5',' '.join(transforms))
    ret = p.show()

    if ret:
        createTransform(p.value('transform1'),sceneData)
        createTransform(p.value('transform2'),sceneData)
        createTransform(p.value('transform3'),sceneData)
        createTransform(p.value('transform4'),sceneData)
        createTransform(p.value('transform5'),sceneData)

    '''
    p = nuke.Panel('import transforms',scrollable=True)
    for k in sceneData.keys():
        p.addBooleanCheckBox(k, False)
    ret = p.show()
    if ret:
        for k in sceneData.keys():
            if p.value(k):
                print k
                createTransform(k,sceneData)
    '''

def createTransform(object,sceneData):
    axis=nuke.nodes.Axis2()
    axis.setName(object)
    axis['rot_order'].setValue('XYZ')
    for attr in sceneData[object].keys():
        keyData=sceneData[object][attr]
        #print attr,keyData
        attr=attrConvert[attr]#add correct channel name and index
        idx=attr.split(":")[1]
        attr=attr.split(":")[0]
        axis[attr].setAnimated()
        for i in range(len(keyData)):
            frm,val=keyData[i].split(":")
            if 'aperture' in attr:
                val=float(val)*25.4#inch to mm conversion
            axis[attr].setValueAt(float(val),float(frm),int(idx))
