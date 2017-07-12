import getpass,platform
import subprocess,os,nuke

def main():
    n=nuke.selectedNode()
    path=n['file'].value()
    renderDir=path.split('/')[11]
    parentDir="/".join(path.split('/')[:-1])
    if '_T_' in renderDir:
        renderDir=renderDir.split('_T_')[0]
    print renderDir

    frames=[]
    for f in os.listdir(parentDir):
        if os.path.isfile(parentDir+'/'+f) and not f.endswith('lock'):
            frames.append(f)
    frames.sort()
    missing=[]
    for i,fr in enumerate(frames):
        if i>0:
            thisFrmNumber=fr.split('.')[-2]
            prevFrmNumber=frames[i-1].split('.')[-2]
            if int(thisFrmNumber)-1!=int(prevFrmNumber):
                missing.append(str(int(thisFrmNumber)-1))

    if renderDir and missing:            
        nuke.message('renderDir:'+renderDir+"\nmissing: "+",".join(missing))

        USER        =   getpass.getuser()
        SERVER      =   "dispatch.studio.gentscholar.com"
        PORT        =   "8681"
        MUSTEREXE   =   { 
                        'Windows'   :   "C:/Program Files/Virtual Vertex/Muster 7/Mrtool.exe",
                        'Linux'     :   "/usr/local/muster7/mrtool",
                        }
        PRODUCTION_ID = '33409'
        JOB_ENGINE = {
                'ae': '1102',
                'modo': '1104',
                'nuke': '1105',
                'maya': '1106',
                'c4d': '1107',
            }
        MUSTERDICT  =   {}
        MUSTERJSON  =   os.path.join(os.path.dirname(os.path.realpath(__file__)), 'muster.json')

        CONNECT_CMD  =   [MUSTEREXE[platform.system()], '-s', SERVER, '-port', PORT, '-u', USER]
        cmd = CONNECT_CMD + ['-q', 'j', '-H', '0', '-S', '1','-jf', 'id,name,submitter,status']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        jobData=stdout.split('\r\n')
        failJobs=[]
        for jd in jobData:
            if jd:
                if renderDir in jd:
                    failJobs.append(jd)

        failedChunks={}
        for job in failJobs:
            parts=job.split('|')
            jobId=parts[0]
            name=parts[1]
            user=parts[2]
            status=parts[3]
            cmd = CONNECT_CMD + ['-q', 'h', '-H', '0', '-S', '1','-job',jobId,'-hf','id,status,sf']
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout,stderr = proc.communicate()
            chunkData=stdout.split('\r\n')
            for ch in chunkData:
                chParts=ch.split('|')

                if len(chParts)>1:
                    print chParts
                    id=chParts[0]
                    status=chParts[1]
                    frame=chParts[2]
                    if frame in missing:
                        if not jobId in failedChunks.keys():
                            failedChunks[jobId]=[]
                        failedChunks[jobId].append(frame)

        for job in failedChunks.keys():
            for id in failedChunks[job]:
                print job,id 
                cmd = CONNECT_CMD + ['-chunkrq', job,id]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        message=""
        for k in failedChunks:
            message+=jobId+":"+",".join(failedChunks[jobId])+'\n'
        nuke.message(message)