import os
import sys
import socket
import re
import nuke

import gsstartup
from gsstartup import muster2

def load_gizmos():
    var = os.environ.get('ST_NUKE_GIZMOS')
    gizmos = []
    if var != None:
        gizmos = var.split(';')
    for g in gizmos:
        gizmopath = os.path.expandvars(g)
        nuke.pluginAddPath(gizmopath)
        for path, dirs, files in os.walk(gizmopath):
            try:
                path = path.replace("\\","/")
                nuke.pluginAddPath(path)
            except:
                print ("Could not load plugin path {0}".format(path))

def init():
    print "Loading Gentleman Scholar Nuke preferences..."
    load_gizmos()

init()