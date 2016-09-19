import os
import sys
import re
import socket
import glob
import shutil

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except:
    GSCODEBASE = '//scholar/code'
GSTOOLS = os.path.join(GSCODEBASE,'tools')
GSBIN = os.path.join(GSCODEBASE,'bin')

C4DVERSION = 'R17'

OCTVERSION = {
        'R17'   :   '2.24.2',
    }

QCMDSVERSION = {
        'R17'   :   '0.21',
}

STIPVERSION = {
        'R17'   :   '1.0',
}

# Takes a dictionary as an argument
def appendEnv(env,abs=False):
    for k,v in env.items():
        #v = v.replace('\\', '/')
        try:
            for i in v:
                os.environ[k] = '%s;%s' %( os.environ[k], i )
        except KeyError:
            for i in v:
                os.environ[k] = i

        if k == 'PYTHONPATH':
            for i in v:
                sys.path.append( i )

def initBrowserlib():
    try:
        BL_MAIN = os.path.join(GSTOOLS, 'cinema4d', 'browserlib', C4DVERSION)
        env_vars = {
                'C4D_BROWSERLIBS'   :   [BL_MAIN],
            }
        appendEnv(env_vars)
    except KeyError:
        pass

def initOct():
    try:
        OCT_MAIN = os.path.join(GSTOOLS, 'cinema4d', 'plug-ins', C4DVERSION, 'c4doctane', OCTVERSION[C4DVERSION])
        env_vars = {
                'C4D_PLUGINS_DIR'   :   [OCT_MAIN],
             }
        appendEnv(env_vars)
    except KeyError:
        pass

def initQcmds():
    try:
        QCMDS_MAIN = os.path.join(GSTOOLS, 'cinema4d', 'plug-ins', C4DVERSION, 'QCmds', QCMDSVERSION[C4DVERSION])
        env_vars = {
                'C4D_PLUGINS_DIR'   :   [QCMDS_MAIN],
             }
        appendEnv(env_vars)
    except KeyError:
        pass

def initGSplugs():
    GSSCRIPTS = os.path.join(GSTOOLS, 'cinema4d', 'scripts', 'python')
    gsplugins = glob.glob(os.path.join(GSSCRIPTS, '*'))
    user_plugin_folders = glob.glob(os.path.join(os.getenv('APPDATA'), 'MAXON', '%s*' %(C4DVERSION), 'plugins'))
    for folder in user_plugin_folders:
        for gsplugin in gsplugins:
            shutil.copy(gsplugin, folder)


def init():
    initBrowserlib()
    initGSplugs()
    if 'farm' not in socket.gethostname().lower():
        initOct()
        initQcmds()

init()