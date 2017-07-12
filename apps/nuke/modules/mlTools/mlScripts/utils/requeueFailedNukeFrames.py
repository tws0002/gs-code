import getpass,platform
import subprocess,os,nuke

def main():
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
	        if USER in jd and '(W)' in jd:
	            failJobs.append(jd)

	failedChunks={}
	for job in failJobs:
	    parts=job.split('|')
	    jobId=parts[0]
	    name=parts[1]
	    user=parts[2]
	    status=parts[3]
	    cmd = CONNECT_CMD + ['-q', 'h', '-H', '0', '-S', '1','-job',jobId,'-hf','id,status']
	    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	    stdout,stderr = proc.communicate()
	    chunkData=stdout.split('\r\n')
	    for ch in chunkData:
	        if '(W)' in ch:
	            if not jobId in failedChunks.keys():
	                failedChunks[jobId]=[]
	            failedChunks[jobId].append(ch.split('|')[0])

	for job in failedChunks.keys():
	    for id in failedChunks[job]:
	        print job,id 
	        cmd = CONNECT_CMD + ['-chunkrq', job,id]
	        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	message=""
	for k in failedChunks:
		message+=jobId+":"+",".join(failedChunks[jobId])+'\n'
	nuke.message(message)