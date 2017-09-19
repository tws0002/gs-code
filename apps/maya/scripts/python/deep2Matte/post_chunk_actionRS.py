import sys
import os
import re
import subprocess

sys.path.append('//scholar/pipeline/dev/apps/maya/scripts/python')
from deep2Matte import deep2MatteProcessRS

start=sys.argv[1]
end= sys.argv[2]
outpath= sys.argv[3]
sceneDataPath= sys.argv[4]
print 'start: ',start
print 'end: ',end
print 'outpath: ',outpath
print 'sceneDataPath: ',sceneDataPath

def convertFrame(fr,outpath,datapath):
    for root, dirs, files in os.walk(outpath):
        for name in files:
            regex = re.compile(".[0-9]{4}.")
            framepad=regex.findall(name)[-1]
            if framepad:
                filename=name.split(framepad)[0]
                if fr in framepad and 'Matte' in filename and name.endswith('exr'):
                    filepath=os.path.join(root, name)
                    outpath=os.path.join(root, name.replace('Matte','Automatte'))
                    print 'converting:',filepath
                    result=deep2MatteProcessRS.processDeep(filepath,outpath,datapath)
                    print result


if not start == end:
    #iterate thru chunk frames
    for fr in range(int(start),int(end)):
        fr=str(fr).zfill(4)
        convertFrame(fr,outpath,sceneDataPath)
else:
    fr=str(start).zfill(4)
    convertFrame(fr,outpath,sceneDataPath)