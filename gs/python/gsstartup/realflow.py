import os
import subprocess
import sys
import argparse
import shutil
import ctypes

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/code'
GSTOOLS = os.path.join(GSCODEBASE,'tools')
GSBIN = os.path.join(GSCODEBASE,'bin')

LIC = '5055@laxlic01'
MAJV = '2015'
MINV = '0.0.0144'
LOC = 'local'
EXE = 'gui'
ADDARGS = []

ROOT_APP_PATH = {'local':'C:/Program Files', 'network':'//scholar/apps'}
APP_EXE = {'gui':'RealFlow.exe', 'cli':'RealFlowNode.exe'}

def set_env(env,abs=False):
    for k,v in env.items():
        if isinstance(v, list):
            for e in v:
            #v = v.replace('\\', '/')
                try:
                    os.environ[k] = '%s;%s' %( os.environ[k], e )
                except KeyError:
                    os.environ[k] = e

                if k == 'PYTHONPATH':
                    sys.path.append( e )
        else:
            print 'Error adding environment variable "%s = %s", set_env takes list as variable.' %(k,v)

def install():
    netAppPath = '%s/NextLimit/Realflow/%s.%s' %(ROOT_APP_PATH['network'], MAJV, MINV)
    locAppPath = '%s/NextLimit/Realflow/%s.%s' %(ROOT_APP_PATH['local'], MAJV, MINV)

    if os.path.exists(netAppPath):
        if not os.path.exists(locAppPath):
            appsize = 0
            for item in os.walk(netAppPath):
                for f in item[2]:
                    try:
                        appsize = appsize + os.path.getsize(os.path.join(item[0], f))
                    except:
                        print("error with file:  " + os.path.join(item[0], f))

            freebytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p('C:\\'), None, None, ctypes.pointer(freebytes))
            
            if float(appsize) < freebytes:            
                print "Installing Realflow %s.%s from the network. Please wait..." %(MAJV, MINV)
                shutil.copytree(netAppPath, locAppPath)
                print "Done!"
            else:
                print "Not enough disk space! Alert your administrator or run with --network flag."
                return 1
        else:
            print "%s already exists on your computer!" %(locAppPath)
            return 1
    else:
        print "%s does not exist on the app server!" %(netAppPath)
        return 1

def start(appPath):
    print "Launching Realflow %s.%s from %s..." %(MAJV, MINV, LOC)
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESTDHANDLES

    cmd = [appPath] + ADDARGS

    if args.renderargs:
        rendercmds = build_render_cmd(args.renderargs)
        cmd += rendercmds
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=os.environ.copy(), startupinfo=si)
        for line in p.stdout:
            print line.replace('\n', '')
    else:
        if FILE: cmd.append(FILE)

        p = subprocess.Popen(cmd, env=os.environ.copy(), startupinfo=si)
        p.communicate()

def build_render_cmd(args):
    p = argparse.ArgumentParser(description='Render command handler')
    p.add_argument('-startframe')
    p.add_argument('-endframe')
    p.add_argument('-filename')
    r = p.parse_args(args[0].split())

    flags = {}
    flags['-range']     = '%s %s' %(r.startframe, r.endframe)

    commands = []
    for k,v in flags.items():
        commands += [k,v]
    commands.append(r.filename)

    return commands

def main():
    print "Using %s as repository..." %(GSCODEBASE)
    
    print "Setting up environment..."
    envVars = {
        'nextlimit_LICENSE'                     :   [LIC],
        'RF_STARTUP_PYTHON_SCRIPT_FILE_PATH'    :   [os.path.join(GSTOOLS, 'realflow', 'scripts', 'startup.py')],
        'RF_%s_PATH' %(MAJV)                    :   [os.path.join(ROOT_APP_PATH[LOC], 'NextLimit', 'Realflow', '%s.%s' %(MAJV, MINV))],
    }
    set_env(envVars)

    appPath = '%s/NextLimit/Realflow/%s.%s/%s' %(ROOT_APP_PATH[LOC], MAJV, MINV, APP_EXE[EXE])
    if os.path.exists(appPath):
        start(appPath)
    else:
        print "%s does not exist. Installing app locally. \nPlease wait..." %(appPath)
        install()
        start(appPath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GS Realflow launcher.')
    parser.add_argument('file', nargs='?', help='File to open.')
    parser.add_argument('-a', '--add', dest='args', help='Additional arguments to pass to the executable.')
    parser.add_argument('-R', '--render', dest='renderargs', nargs='*', help='Specify to use render executable.')
    parser.add_argument('-i', '--install', action='store_true', help='Install local copy of app. Requires that app exist on the network.')
    parser.add_argument('-n', '--network', action='store_true', help='Specify to use network installed application.')
    parser.add_argument('-V', '--major', dest='MAJV', help='Specify the major version to run. (default: %s' %(MAJV))
    parser.add_argument('-v', '--minor', dest='MINV', help='Specify the minor version to run. (default: %s' %(MINV))
    args = parser.parse_args()
    
    if args.MAJV: MAJV = args.MAJV
    if args.MINV: MINV = args.MINV
    if args.renderargs:
        EXE = 'cli'
    if args.network: LOC = 'network'
    if args.args: ADDARGS += args.args
    FILE = ''
    if args.file: FILE = args.file

    if not args.install:
        main()
    else:
        install()