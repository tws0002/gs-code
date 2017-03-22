import os
import re
import platform
import subprocess
import json
import time
import getpass
import argparse
try:
    from collections import Counter
except:
    from backport_collections import Counter

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/pipeline'

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

if (os.environ['GSBRANCH'].split('/')[-1]) == 'dev':
    JOB_ENGINE = {
        'ae': '1202',
        'modo': '1204',
        'nuke': '1205',
        'maya': '1206',
        'c4d': '1207',
    }


MUSTERDICT  =   {}
MUSTERJSON  =   os.path.join(os.path.dirname(os.path.realpath(__file__)), 'muster.json')

CONNECT_CMD  =   [MUSTEREXE[platform.system()], '-s', SERVER, '-port', PORT, '-u', USER]

def _build_muster_cmd(flags):
    # Takes a dictionary as an argument #
    reqArgs = ['-e', '-n', '-pool', '-parent']
    if SERVER:
        if os.path.exists(MUSTEREXE[platform.system()]):
            cmd = list(CONNECT_CMD)
            
            try:
                for a in reqArgs:
                    cmd += [a, flags.pop(a)]
            except KeyError:
                print 'Missing required flag: %s' %(a)

            if flags.get('-gpupool'):
                gpupool = flags.pop('-gpupool')
                pools_members = get_pools_members()
                new_pool_string = ','.join(pools_members[gpupool])
                flags['-pool'] = new_pool_string

            for k,v in flags.items():
                if isinstance(v, list):
                    for i in v:
                        if i: cmd += [k,i]
                else:
                    if v: cmd += [k,v]
            
            cmd.append('-b')
            #print cmd
            return cmd
        else:
            print 'Could not locate Muster executable.  Tried to find mrtool in:\n%s'%(CONNECT_CMD)
            exit()
    else:
        print 'Could not locate Muster server.'
        exit()

def submit(flags):
    cmd = _build_muster_cmd(flags)
    cmd = filter(None,cmd)
    output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    m = re.search('ID: (\d+)', output)
    if m:
        return m.group(1)
    else:
        return False

def get_pools():
    cmd = CONNECT_CMD + ['-q', 'p', '-H', '0', '-S', '0', '-pf', 'parent']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout,stderr = proc.communicate()

    pools = stdout.replace('\r','').split('\n')
    for index,item in enumerate(pools):
        pools[index] = item.strip()
    pools = [x for x in sorted(list(set(pools))) if x]

    return pools

def get_pools_members():
    cmd = CONNECT_CMD + ['-q', 'p', '-H', '0', '-pf', 'parent,name']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout,stderr = proc.communicate()

    entries = [x for x in stdout.replace('\r','').split('\n') if x]

    pool_members = {}
    for item in entries:
        itemSplit = item.split('|')
        try:
            pool_members[itemSplit[0].replace('\t','').strip()].append(itemSplit[1].replace('\t','').strip())
        except Exception as error:
            print error
            pool_members[itemSplit[0].replace('\t','').strip()] = [itemSplit[1].replace('\t','').strip()]

    return pool_members

def get_pools_count():
    cmd = CONNECT_CMD + ['-q', 'p', '-H', '0', '-S', '0', '-pf', 'parent']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout,stderr = proc.communicate()

    pools = []
    for p in stdout.replace('\r','').split('\n'):
        if p: pools.append(p.strip())
    pools_count = Counter(pools)
    return pools_count

def get_folders():
    cmd = CONNECT_CMD + ['-q', '-j', '-jf', 'name,id', '-jobparent', '-1', '-H', '0']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout,stderr = proc.communicate()

    entries = [x for x in stdout.replace('\r','').split('\n') if x]

    folders = []
    for item in entries:
        itemSplit = item.split('|')
        for index,x in enumerate(itemSplit):
            itemSplit[index] = x.replace('\t','').strip()
        folders.append(itemSplit[:-1])

    return folders

def get_jobs_active_count(status, engine=''):
    status_dict = {'queued': '1', 'rendering': '2'}
    engine_groups = {'2d': ['nuke', 'ae'], '3d': ['modo', 'maya', 'c4d']}

    if engine in ['2d', '3d']:
        engines = engine_groups[engine]
    else:
        engines = [engine]

    jobs_active = []
    for e in engines:
        try:
            if e:
                cmd = CONNECT_CMD + ['-q', 'j', '-H', '0', '-S', '0', '-jobparent', PRODUCTION_ID, '-jobstatus', status_dict[status], '-jf', 'group', '-jobengine', JOB_ENGINE[e]]
            else:
                cmd = CONNECT_CMD + ['-q', 'j', '-H', '0', '-S', '0', '-jobparent', PRODUCTION_ID, '-jobstatus', status_dict[status], '-jf', 'group']
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout,stderr = proc.communicate()

            for j in stdout.replace('\r','').split('\n'):
                if j: jobs_active.append(j.strip())
        except:
            print 'Is job status "queued" or "rendering"?'
            pass
    jobs_active_count = Counter(jobs_active)
    return jobs_active_count

def get_jobs_active_nodes_count():
    cmd = CONNECT_CMD + ['-q', 'c', '-H', '0', '-S', '0', '-cf', 'jobid']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout,stderr = proc.communicate()

    active_jobs = []
    for j in stdout.replace('\r','').split('\n'):
        if j and j.strip()!='-1': active_jobs.append(j.strip())
    active_jobs_id_count = Counter(active_jobs)
    active_jobs_name_count = {}
    for i in active_jobs_id_count:
        active_jobs_name_count[get_project_from_jobid(i)] = active_jobs_id_count[i]
    return active_jobs_name_count

def get_nodes_status_count(type='any'):
    cmd = CONNECT_CMD + ['-q', 'c', '-H', '0', '-cf', 'name,status']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout,stderr = proc.communicate()

    entries = [x for x in stdout.replace('\r','').split('\n') if x]

    nodes = {}
    for item in entries:
        itemSplit = item.split('|')
        for index,x in enumerate(itemSplit):
            itemSplit[index] = x.replace('\t','').strip()
        nodes[itemSplit[:-1][0]] = itemSplit[:-1][1]

    nodes_count = {'idle': 0, 'logged': 0, 'in progress': 0, 'paused': 0, 'offline': 0}
    if type == 'any':
        for i in nodes:
            try:
                nodes_count[nodes[i].lower()]+=1
            except KeyError:
                pass
    if type == 'workstation':
        for i in nodes:
            if 'gent' in i.lower():
                try:
                    nodes_count[nodes[i].lower()]+=1
                except KeyError:
                    pass
    if type == 'farm':
        for i in nodes:
            if 'farm' in i.lower():
                try:
                    nodes_count[nodes[i].lower()]+=1
                except KeyError:
                    pass
    return nodes_count

def get_project_from_jobid(jobid):
    if jobid:
        cmd = CONNECT_CMD + ['-q', 'j', '-H', '0', '-S', '0', '-job', jobid, '-jf', 'group']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        project = stdout.replace('\r','').split('\n')[1].strip()
        return project
    else:
        print 'Job ID must be specified'
def get_name_from_jobid(jobid):
    if jobid:
        cmd = CONNECT_CMD + ['-q', 'j', '-H', '0', '-S', '0', '-job', jobid, '-jf', 'name']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        job_name = stdout.replace('\r','').split('\n')[1].strip()
        return job_name
    else:
        print 'Job ID must be specified'

def get_user_from_jobid(jobid):
    if jobid:
        cmd = CONNECT_CMD + ['-q', 'j', '-H', '0', '-S', '0', '-job', jobid, '-jf', 'submitter']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        user = stdout.replace('\r','').split('\n')[1].strip()
        return user
    else:
        print 'Job ID must be specified'

def get_chunk_completion_time(jobid, chunkid):
    if jobid and chunkid:
        cmd = CONNECT_CMD + ['-q', 'h', '-H', '0', '-S', '0', '-job', jobid, '-chunk', chunkid, '-hf', 'elapsed']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        comp_time = stdout.replace('\r','').split('\n')[1].strip()
        m = re.search('^(\d+) days, (\d+) hours, (\d+) mins, (\d+) secs', comp_time)
        if m:
            days, hours, mins, secs = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            total_secs = 24*60*60*days + 60*60*hours + 60*mins + secs
        else:
            total_secs = 0
        return total_secs
    else:
        print 'Job ID and chunk ID must be specified'

def get_chunk_start_time(jobid, chunkid):
    if jobid and chunkid:
        cmd = CONNECT_CMD + ['-q', 'h', '-H', '0', '-S', '0', '-job', jobid, '-chunk', chunkid, '-hf', 'st']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        start_time = stdout.replace('\r','').split('\n')[1].strip()
        return start_time
    else:
        print 'Job ID and chunk ID must be specified'

def main():
    parser = argparse.ArgumentParser(description='GS Maya launcher.')
    parser.add_argument('-j', '--jsoncmd', dest='jsoncmd', help='If specified, will take a dictionary of Muster flags to be submitted.')
    args = parser.parse_args()

    if args.jsoncmd:
        jsoncmd = args.jsoncmd
        output = submit(json.loads(jsoncmd))
    else:
        MUSTERDICT['pools'] = get_pools()
        with open(MUSTERJSON, 'w') as f:
            json.dump(MUSTERDICT, f)

if __name__ == '__main__':
    main()