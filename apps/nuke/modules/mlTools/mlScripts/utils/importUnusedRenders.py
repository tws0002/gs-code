import nuke
import re,os

def main():
    allFiles= allFilesAllGroups("Read")
    shotPublishes=getShotPublishes()
    
    for sP in shotPublishes:
        if not sP in allFiles:
            if 'deep' in sP or 'DEEP' in sP:
                n=nuke.nodes.DeepRead()
            else:
                n=nuke.nodes.Read()
            n['file'].setValue(sP)
            n['first'].setValue(int(nuke.root()['first_frame'].value()))
            n['last'].setValue(int(nuke.root()['last_frame'].value()))
            n['name'].setValue(sP.split('/')[-1].split('_beauty_v')[0])

def getShotPublishes():
    import tank
    import shotgun_api3 as shotgun
    
    shotPublishes={}
    maxVersions=[]
    #returns tank context based on what shot is open in nuke, untitled file wont work.
    SHOT=tank.platform.current_engine().context.entity

    # Get handle to Asset Manager tank application
    assetmgr = tank.platform.current_engine().apps["psy-multi-assetmanager"]
    # Grab updated publish data from shotgun
    publish_directory = assetmgr.publish_directory.find_publish_entity(SHOT)

    #this will iterate over all publishes for a shot, printing aovs within metadata per publish
    for publish in list(publish_directory.find_publish_type('image/render').all_publishes):
        renderLayer=publish.component_name
        if not renderLayer in shotPublishes.keys():
            shotPublishes[renderLayer]=[]
        publishPath=publish.path.replace("%04d","####").replace("\\","/")
        shotPublishes[renderLayer].append(publishPath)

    for renderLayer in shotPublishes.keys():
        maxVersions.append(max(shotPublishes[renderLayer]))
    return maxVersions
    
def findLatest(origPath):
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
            
            
def allFilesAllGroups(NodeClass):
    filepaths=[]
    for n in nuke.allNodes(NodeClass):
        filepath=n['file'].value().replace("%04d","####")
        filepaths.append(filepath)
    for grp in nuke.allNodes('Group'):
        with grp:
            for n in nuke.allNodes(NodeClass):
                filepath=n['file'].value().replace("%04d","####")
                filepaths.append(filepath)
    return filepaths


