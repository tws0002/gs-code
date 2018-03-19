import os
import sys
import socket
import time
import datetime
import re

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/pipeline'

import gsstartup
from gsstartup import muster2

CARBON_SERVER = '10.10.204.71'
CARBON_PORT = 2003
TIMESTAMP = int(time.time())

def send_msg(message):
    try:
        sock = socket.socket()
        sock.connect((CARBON_SERVER, CARBON_PORT))
        sock.sendall(message)
        sock.close()
    except:
        print "Error connecting to %s" %CARBON_SERVER
        exit()

def main():
    try:
        jobid = os.environ.get('MUSTER_JOB_ID')
        chunkid = os.environ.get('MUSTER_CHUNK_ID')
        frame_start = float(os.environ.get('MUSTER_START_FRAME'))
        frame_end = float(os.environ.get('MUSTER_END_FRAME'))
        frame_total = frame_end - frame_start + 1
        muster_engine = os.environ.get('MUSTER_ENGINE')

        project = muster2.get_project_from_jobid(jobid)
        user = muster2.get_user_from_jobid(jobid)
        if user == '': user = 'unknown'
        a = muster2.get_chunk_start_time(jobid, chunkid)
        time_start = int(time.mktime(time.strptime(muster2.get_chunk_start_time(jobid, chunkid), '%m/%d/%Y %H:%M:%S')))
        time_now = TIMESTAMP
        time_total = time_now - time_start

        job_name = muster2.get_name_from_jobid(jobid).replace(' ','_')
        job_name = re.sub('[^0-9a-zA-Z_-]+', '', job_name)
        searches = ['^(.*)_C\d+_A\d+_L\d+.*', '^(.*)_v\d+.*', '(.*)_\d+$']
        name = job_name
        for s in searches:
            if name == job_name:
                m = re.search(s, job_name)
                if m: name = m.group(1)
            else:
                break

        grafana_frame_number_offset = int((datetime.datetime(2000,1,1) - datetime.datetime(1970,1,1)).total_seconds())

        if muster_engine in ['1002', '1005']:
            job_type = '2d'
        elif muster_engine in ['1004', '1006', '1007']:
            job_type = '3d'
        else:
            job_type = 'general'

        for i in range(int(frame_start), int(frame_end+1)):
            send_msg('renderstats.projects.{}.{}.{}.{}.{} {} {}\n'.format(project, job_type, user, name, jobid, time_total/frame_total, grafana_frame_number_offset+i*3600))
    except KeyError as err:
        print 'Environment variable not found. Is this initiated by a Muster chunk action? Error: {}'.format(err)

if __name__ == '__main__':
    main()