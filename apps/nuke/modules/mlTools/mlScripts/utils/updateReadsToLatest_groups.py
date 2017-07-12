import nuke
import re,os



def getAllNodes(topLevel):
    '''
    recursively return all nodes starting at topLevel. Default topLevel is nuke.root()
    '''
    allNodes = nuke.allNodes( group=topLevel )
    for n in allNodes:
        allNodes = allNodes+getAllNodes( n )
    return allNodes

def allReads():
    found=[]
    for n in getAllNodes(nuke.root()):
        if n.Class()=='Read':
            found.append(n)
    return found

def main():
    allRead= allReads()
    found=[]
    for n in allRead:
        if n.Class()=='Read':
            currentPath=n['file'].value()
            newPath=findLatest(currentPath)
            if newPath:
                n['file'].setValue(newPath)
                found.append(n['file'].value())
    if found:
        nuke.message("updated Reads:\n"+"\n".join(found))

def findLatest(origPath):
    if origPath:
        regex = re.compile("L[0-9]{2,9}")
        vers=regex.findall(origPath)
        if vers:
            origDir=origPath.split('/')[11]
            for i in range(1,10)[::-1]:
                path=origPath
                up=int(i)
                for ver in vers:
                    numsOnly=ver[1:]
                    pad=len(numsOnly)
                    val=int(numsOnly)
                    newVer='L'+str((val+up)).zfill(pad)
                    path=path.replace(ver,newVer)
                parDir='/'.join(path.split('/')[0:11])
                if os.path.exists(parDir):
                    for dir in os.listdir(parDir):
                        if newVer in dir:
                            print origDir,dir
                            path=origPath.replace(origDir,dir)
                            return path

def findLatest2(origPath):
    regex = re.compile("v[0-9]{2,9}")
    vers=regex.findall(origPath)
    for i in range(1,10)[::-1]:
        path=origPath
        up=int(i)
        for ver in vers:
            numsOnly=ver[1:]
            pad=len(numsOnly)
            val=int(numsOnly)
            newVer='v'+str((val+up)).zfill(pad)
            path=path.replace(ver,newVer)
        dirPath='/'.join(path.split('/')[:-1])
        if os.path.exists(dirPath):
            return path
            


