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

LIC = '4101@laxlic01'
MAJV = '9.0'
MINV = '7'
LOC = 'local'
EXE = 'gui'
ADDARGS = []

GSNUKE = os.path.join(GSTOOLS, 'nuke')
if os.path.exists('E:'):
    NUKECACHE = 'E:/Temp/Nuke_Cache'
else:
    NUKECACHE = 'C:/Temp/Nuke_Cache'

ROOT_APP_PATH = {'local':'C:/Program Files', 'network':'//scholar/apps'}
APP_EXE = {'gui':'nuke%s.exe' %(MAJV), 'cli':'nuke%s.exe' %(MAJV) }

def set_env(env,abs=False):
    for k,v in env.items():
        if isinstance(v, list):
            for e in v:
            #v = v.replace('\\', '/')
                try:
                    os.environ[k] = '%s;%s' %(os.environ[k], e)
                except KeyError:
                    os.environ[k] = e

                if k == 'PYTHONPATH':
                    sys.path.append( e )
        else:
            print 'Error adding environment variable "%s = %s", set_env takes list as variable.' %(k,v)

def install():
    netAppPath = '%s/Foundry/Nuke/%sv%s' %(ROOT_APP_PATH['network'], MAJV, MINV)
    locAppPath = '%s/Foundry/Nuke/%sv%s' %(ROOT_APP_PATH['local'], MAJV, MINV)

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
                print "Installing Nuke %sv%s from the network. Please wait..." %(MAJV, MINV)
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
    print "Launching Nuke %sv%s from %s..." %(MAJV, MINV, LOC)
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESTDHANDLES

    cmd = [appPath] + ADDARGS

    if args.renderargs:
        rendercmds = build_render_cmd(args.renderargs)
        cmd += rendercmds

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=os.environ.copy())
        for line in p.stdout:
            print line.strip()
    else:
        if FILE: cmd.append(FILE)

        p = subprocess.Popen(cmd, env=os.environ.copy())
        p.communicate()

def build_render_cmd(args):
    p = argparse.ArgumentParser(description='Render command handler')
    p.add_argument('-startframe')
    p.add_argument('-endframe')
    p.add_argument('-step')
    p.add_argument('-writenodes')
    p.add_argument('-filename')
    r = p.parse_args(args[0].split())

    flags = {}
    flags['-V']     = ''
    flags['-F']     = '%s-%sx%s' %(r.startframe, r.endframe, r.step)
    flags['-X']     = r.writenodes
    flags['-x']     = r.filename

    commands = []
    for k,v in flags.items():
        commands += [k,v]
    
    return commands

def main():
    print "Using %s as repository..." %(GSCODEBASE)
    
    print "Setting up environment..."
    envVars = {
        'PYTHONPATH'        :   [os.path.join(GSCODEBASE,'general','scripts','python'),
                                os.path.join(GSCODEBASE,'lib','python')],
        'RLM_LICENSE'       :   ['%s' %(LIC)],
        'NUKE_PATH'         :   ['%s/startup' %(GSNUKE)],
        'NUKE_DISK_CACHE'   :   [NUKECACHE],
        'NUKE_TEMP_DIR'     :   [NUKECACHE],
    }
    set_env(envVars)

    APP_EXE = {'gui':'nuke%s.exe' %(MAJV), 'cli':'nuke%s.exe' %(MAJV) }
    appPath = '%s/Foundry/Nuke/%sv%s/%s' %(ROOT_APP_PATH[LOC], MAJV, MINV, APP_EXE[EXE])
    if os.path.exists(appPath):
        start(appPath)
    else:
        print "%s does not exist. Installing app locally. \nPlease wait..." %(appPath)
        install()
        start(appPath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GS Nuke launcher.')
    parser.add_argument('file', nargs='?', help='File to open.')
    parser.add_argument('-p', '--package', nargs=1, choices=['nukex', 'nukeassist', 'studio'], help='Choose Nuke package (options are nukex, nukeassist, studio).')
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
    if args.package:
        ADDARGS += ['--%s' %(args.package[0])]
    if args.args: ADDARGS += args.args
    FILE = ''
    if args.file: FILE = args.file

    if not args.install:
        main()
    else:
        install()