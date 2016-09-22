import os
import sys
import socket
import re
import nuke

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/code'
GSTOOLS = os.path.join(GSCODEBASE,'base','apps')
GSBIN = os.path.join(GSCODEBASE,'bin')

#sys.path.append(os.path.join(GSCODEBASE, 'base', 'gs', 'python'))
#sys.path.append(os.path.join(GSCODEBASE, 'lib', 'python'))
import gsstartup
from gsstartup import muster2

hostname = gsstartup.properties['hostname']

NKVERSION = nuke.NUKE_VERSION_STRING
m = re.search('^(.*)v(.*)',NKVERSION)
NKMAJVERSION = m.group(1)
NKMINVERSION = m.group(2)
GSNUKE = os.path.join(GSTOOLS, 'nuke')
GSNUKEPLUGINS = os.path.join(GSBIN, 'external', 'nuke','plugins')

JOPSVERSION = {
        '10.0'  :   '0',
        '9.0'   :   '2.3',
        '8.0'   :   '2.2',
    }
LENSCAREVERSION = {
        '10.0'  :   '1.44',
        '9.0'   :   '1.44',
        '8.0'   :   '1.44',
    }
OFVERSION = {
        '10.0'  :   '1.0.85',
        '9.0'   :   '1.0.8',
        '8.0'   :   '1.0.8',
    }
DFVERSION = {
        '10.0'  :   '1.0',
        '9.0'   :   '1.0',
        '8.0'   :   '1.0',
    }
TWIXVERSION = {
        '10.0'  :   '6.2.2',
        '9.0'   :   '6.2.2',
        '8.0'   :   '6.2.2',
    }
RSMBVERSION = {
        '10.0'  :   '4.2.0',
        '9.0'   :   '4.2.0',
        '8.0'   :   '4.2.0',
    }
NVVERSION = {
        '10.0'  :   '4.0.9',
        '9.0'   :   '4.0.9',
        '8.0'   :   '4.0.9',
    }

CARAVERSION = {
        '10.0'  :   '0',
        '9.0'   :   '1.0b3',
        '8.0'   :   '0',
    }  


def initJOps():
    jopspath = os.path.join(GSNUKEPLUGINS, 'j_ops', JOPSVERSION[NKMAJVERSION],NKMAJVERSION)
    jopspluginpaths = ['','py', 'ndk', 'icons']
    for p in jopspluginpaths:
        path = os.path.join(jopspath, p)
        nuke.pluginAddPath(path)
        sys.path.append(path)

def initOF():
    if 'farm' in hostname.lower():
        build = 'farm'
    else:
        build = 'workstation'
    ofpath = os.path.join(GSNUKEPLUGINS, 'opticalflares', OFVERSION[NKMAJVERSION], NKMAJVERSION, build)

    if build == 'workstation':
        os.environ['OPTICAL_FLARES_LICENSE_PATH'] = os.path.join(ofpath, 'licenses', hostname)

    os.environ['OPTICAL_FLARES_PATH'] = ofpath
    nuke.pluginAddPath(ofpath)
    sys.path.append(ofpath)

def initLenscare():
    lcpath = os.path.join(GSNUKEPLUGINS, 'lenscare', LENSCAREVERSION[NKMAJVERSION], NKMAJVERSION)
    nuke.pluginAddPath(lcpath)

def initDF():
    dfpath = os.path.join(GSNUKEPLUGINS, 'deflicker', DFVERSION[NKMAJVERSION], NKMAJVERSION)
    nuke.pluginAddPath(dfpath)

def initTwixtor():
    twixpath = os.path.join(GSNUKEPLUGINS, 'twixtor', TWIXVERSION[NKMAJVERSION], NKMAJVERSION)
    nuke.pluginAddPath(twixpath)

def initRSMB():
    rsmbpath = os.path.join(GSNUKEPLUGINS, 'rsmb', RSMBVERSION[NKMAJVERSION], NKMAJVERSION)
    nuke.pluginAddPath(rsmbpath)

def initNV():
    nvpath = os.path.join(GSNUKEPLUGINS, 'neatvideo', NVVERSION[NKMAJVERSION], NKMAJVERSION)
    nuke.pluginAddPath(nvpath)

def initCara():
    carapath = os.path.join(GSNUKEPLUGINS, 'caravr', CARAVERSION[NKMAJVERSION], NKMAJVERSION)
    nuke.pluginAddPath(carapath)

def initGSEnv():
    pluginpaths = [
            'gizmos',
            'icons',
            'plug-ins',
            os.path.join('scripts', 'python'),
        ]
    for p in pluginpaths:
        nuke.pluginAddPath(os.path.join(GSNUKE, p))

def init():
    print "Loading Gentleman Scholar Nuke preferences..."
    initGSEnv()
    initJOps()
    initOF()
    initLenscare()
    initDF()
    initTwixtor()
    initRSMB()
    initNV()

init()