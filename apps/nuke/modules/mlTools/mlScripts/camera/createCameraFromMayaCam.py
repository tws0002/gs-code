import nuke

def main():
    cam = nuke.getFilename('select Maya File', '*.ma')

    camFile=cam.split('/')[-1].split('.')[0]


    fileObject=open(cam,"r")
    contents=fileObject.read()
    fileObject.close()

    attrConvert={   "translateX":"translate:0",
                    "translateY":"translate:1",
                    "translateZ":"translate:2",
                    "rotateX":"rotate:0",
                    "rotateY":"rotate:1",
                    "rotateZ":"rotate:2",
                    "horizontalFilmAperture":"haperture:0",
                    "verticalFilmAperture":"vaperture:0",
                    "focalLength":"focal:0"}

    cameraData={"translateX":[],
                "translateY":[],
                "translateZ":[],
                "rotateX":[],
                "rotateY":[],
                "rotateZ":[],
                "horizontalFilmAperture":[],
                "verticalFilmAperture":[],
                "focalLength":[]}

    currentAttr=''
    chunkStart=0
    chunk=''
    fl=0
    hap=0
    vap=0

    for line in contents.split('\n'):
        if 'createNode' in line:
            for attr in cameraData.keys():
                if attr in line:
                    currentAttr=attr
        if "ktv[" in line:
            chunkStart=1
        if chunkStart:
            lineFiltered=line.strip("\t;")
            chunk+=lineFiltered
        if chunkStart and ";" in line:
            if currentAttr in cameraData.keys():
                keys= chunk.split("]\"  ")[1]
                keys=keys.split(" ")  
                for i,k in enumerate(keys):
                    if i%2==0:
                        cameraData[currentAttr].append(k+":"+keys[i+1])    
            chunk=''
            chunkStart=0
            currentAttr=''

        #find camera shape non-keyframed
        if 'setAttr \".cap\"' in line:
            capData=line.split('\"double2\"')[-1]
            capData=capData.split(" ")
            hap=float(capData[1])*25.4
            vap=float(capData[2])*25.4
        if 'setAttr \".fl\"' in line:
            focalData=line.split('\".fl\"')[-1].strip(";")
            fl=float(focalData)







    print fl,vap,hap
    nukeCam=nuke.nodes.Camera2()
    nukeCam['rot_order'].setValue('XYZ')
    nukeCam.setName('shotCam')
    nukeCam['label'].setValue(camFile)
    for attr in cameraData.keys():
        keyData=cameraData[attr]
        #print attr,keyData
        attr=attrConvert[attr]#add correct channel name and index
        idx=attr.split(":")[1]
        attr=attr.split(":")[0]
        if attr:
            nukeCam[attr].setAnimated()
        for i in range(len(keyData)):
            frm,val=keyData[i].split(":")
            if 'aperture' in attr:
                val=float(val)*25.4#inch to mm conversion
            nukeCam[attr].setValueAt(float(val),float(frm),int(idx))

    if not cameraData['focalLength']:
        nukeCam['focal'].setValue(fl)
    if not cameraData['horizontalFilmAperture']:
        nukeCam['haperture'].setValue(hap)
    if not cameraData['verticalFilmAperture']:
        nukeCam['vaperture'].setValue(vap)


#setAttr ".cap" -type "double2" 1.41732 0.94488 ;
#setAttr ".fl" 75;