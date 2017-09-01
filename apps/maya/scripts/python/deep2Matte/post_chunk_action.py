import sys
import os
import re
import subprocess

sys.path.append('//scholar/pipeline/dev/apps/maya/scripts/python')
from deep2Matte import deep2MatteProcess

start=sys.argv[1]
end= sys.argv[2]
outpath= sys.argv[3]
print start,end,outpath

def convertFrame(frame,outpath):
    for root, dirs, files in os.walk(outpath):
        for name in files:
            regex = re.compile(".[0-9]{4}.")
            framepad=regex.findall(name)[-1]
            if framepad:
                filename=name.split(framepad)[0]
                if fr in framepad and 'DeepMatte' in filename and name.endswith('exr'):
                    filepath=os.path.join(root, name)
                    outpath=os.path.join(root, name.replace('DeepMatte','Matte'))
                    print 'converting:',filepath
                    result=deep2MatteProcess.processDeep(filepath,outpath)
                    print result


if not start == end:
    #iterate thru chunk frames
    for fr in range(int(start),int(end)):
        fr=str(fr).zfill(4)
        convertFrame(fr,outpath)
else:
    fr=str(start).zfill(4)
    convertFrame(fr,outpath)