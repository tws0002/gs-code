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
MAJV = '901'
MINV = 'SP2'
LOC = 'local'
EXE = 'gui'
ADDARGS = []

GSMODO = os.path.join(GSTOOLS, 'modo')
GSRESOURCES = os.path.join(GSMODO, 'resources')

ROOT_APP_PATH = { 'local' : 'C:/Program Files', 'network' : '//scholar/apps' }
APP_EXE = { 'gui' : 'modo.exe', 'cli' : 'modo_cl.exe' }

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

def initEnv():
    userFolder = os.path.join( GSRESOURCES, MAJV )
    userConfigs = os.path.join( userFolder, 'configs' )
    userScripts = os.path.join( userFolder, 'scripts' )
    userPlugins = os.path.join( userFolder, 'plugins' )
    userProfile = os.environ['USERPROFILE']
    userLocalConfigs = os.path.join( userProfile, 'AppData', 'Roaming', 'Luxology', 'Configs' )
    userLocalConfigFile = os.path.join( userLocalConfigs, 'gs_env.cfg' )

    cfg = "<?xml version='1.0' encoding='UTF-8'?><configuration><import>%s</import><import>%s</import><import>%s</import><import>%s</import></configuration>" %(userFolder, userConfigs, userScripts, userPlugins)
    if os.path.exists(userLocalConfigs):
        with open(userLocalConfigFile, 'w') as f:
            f.write(cfg)
    else:
        os.makedirs(userLocalConfigs)
        with open(userLocalConfigFile, 'w') as f:
            f.write(cfg)        

def install():
    if MAJV == '10.0':
        netAppPath = '%s/Foundry/Modo/%sv%s' %(ROOT_APP_PATH['network'], MAJV, MINV)
        locAppPath = '%s/Foundry/Modo/%sv%s' %(ROOT_APP_PATH['local'], MAJV, MINV)
    else:
        netAppPath = '%s/Foundry/Modo/%s_%s' %(ROOT_APP_PATH['network'], MAJV, MINV)
        locAppPath = '%s/Foundry/Modo/%s_%s' %(ROOT_APP_PATH['local'], MAJV, MINV)

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
                print "Installing Modo %s_%s from the network. Please wait..." %(MAJV, MINV)
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
    if MAJV == '10.0':
        fullVersion = '%sv%s' %(MAJV, MINV)
    else:
        fullVersion = '%s_%s' %(MAJV, MINV)

    print "Launching Modo %s from %s..." %(fullVersion, LOC)
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESTDHANDLES

    cmd = [appPath] + ADDARGS

    if args.renderargs:
        rendercmds = build_render_cmd(args.renderargs)
        p = subprocess.Popen( cmd, stdin=subprocess.PIPE, env=os.environ.copy(), startupinfo=si )
        for i in rendercmds:
            p.stdin.write(i)
        p.communicate()
    else:
        if FILE: cmd.append(FILE)
        
        p = subprocess.Popen( cmd, env=os.environ.copy(), startupinfo=si )
        p.communicate()

def build_render_cmd(args):
    p = argparse.ArgumentParser(description='Render command handler')
    p.add_argument('-rendergroup', nargs='?', default='')
    p.add_argument('-outputpath')
    p.add_argument('-startframe')
    p.add_argument('-endframe')
    p.add_argument('-step')
    p.add_argument('-filename')
    p.add_argument('-format')
    r = p.parse_args(args[0].split())

    commands = []
    commands.append( 'log.toConsole true\n' )
    commands.append( 'log.toConsoleRolling true\n' )
    commands.append( 'scene.open "%s"\n' %(r.filename) )
    commands.append( 'select.itemType polyRender\n' )
    commands.append( 'item.channel first %s\n' %(r.startframe) )
    commands.append( 'item.channel last %s\n' %(r.endframe) )
    commands.append( 'item.channel step %s\n' %(r.step) )
    if not r.rendergroup:
        commands.append( '!render.animation "%s" %s {*}\n' %(r.outputpath, r.format) )
    else:
        commands.append( '!render.animation "%s" %s {*} group:%s\n' %(r.outputpath, r.format, r.rendergroup) )
    commands.append( 'app.quit\n' )
    
    return commands

def main():
    print "Using %s as repository..." %(GSCODEBASE)
    
    print "Setting up environment..."
    envVars = {
        #'NEXUS_LICENSE'    :   [''],
        #'NEXUS_USER'   :   [''],
        #'NEXUS_PREFS'  :   [''],
        #'NEXUS_TEMP'   :   [''],
        'RLM_LICENSE'   :   ['%s' %(LIC)],
        'NEXUS_ASSET'   :   ['%s/%s/content/Assets' %(GSRESOURCES, MAJV)],
        'NEXUS_CONTENT' :   ['%s/%s/content' %(GSRESOURCES, MAJV)],
    }
    set_env(envVars)
    initEnv()

    if MAJV == '10.0':
        fullVersion = '%sv%s' %(MAJV, MINV)
    else:
        fullVersion = '%s_%s' %(MAJV, MINV)
    
    appPath = '%s/Foundry/Modo/%s/%s' %(ROOT_APP_PATH[LOC], fullVersion, APP_EXE[EXE])
    if os.path.exists(appPath):
        start(appPath)
    else:
        print "%s does not exist. Installing app locally. \nPlease wait..." %(appPath)
        install()
        start(appPath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GS Modo launcher.')
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