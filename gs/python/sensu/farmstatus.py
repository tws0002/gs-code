import os
import sys
import socket
import time

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/code'
GSTOOLS = os.path.join(GSCODEBASE,'tools')
GSBIN = os.path.join(GSCODEBASE,'bin')

sys.path.append(os.path.join(GSTOOLS, 'general','scripts','python'))

import gs
from gs import muster

CARBON_SERVER = '10.10.204.71'
CARBON_PORT = 2003
TIMESTAMP = int(time.time())

def send_msg(message):
    sock = socket.socket()
    sock.connect((CARBON_SERVER, CARBON_PORT))
    sock.sendall(message)
    sock.close()

def pools():
    pools_count = muster.get_pools_count()
    for p in pools_count:
        print 'renderstats.status.pools.%s %s %d' %(p, pools_count[p], TIMESTAMP)

def jobsactive():
    for kind in ['2d', '3d']:
        for status in ['queued', 'rendering']:
            jobs_active = muster.get_jobs_active_count(status, kind)
            for j in jobs_active:
                print 'renderstats.status.jobsactive.%s.%s_%s %s %d' %(j, kind, status, jobs_active[j], TIMESTAMP)

def nodesactive():
    jobs_active_nodes = muster.get_jobs_active_nodes_count()
    for n in jobs_active_nodes:
        print 'renderstats.status.nodesactive.%s %s %d' %(n, jobs_active_nodes[n], TIMESTAMP)

def nodes():
    for kind in ['farm', 'workstation']:
        nodes_status = muster.get_nodes_status_count(kind)
        for n in nodes_status:
            print 'renderstats.status.nodes.%s.%s %s %d' %(kind, n.replace(" ", ""), nodes_status[n], TIMESTAMP)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            arg = sys.argv[i]
            if arg == 'pools':
                pools()
            elif arg == 'jobsactive':
                jobsactive()
            elif arg == 'nodesactive':
                nodesactive()
            elif arg == 'nodes':
                nodes()
    else:
        pools()
        jobsactive()
        nodesactive()
        nodes()

    print 'renderstats.status.heartbeat 0 %d\n' %(TIMESTAMP)