import os
import sys
import socket
import re
import nuke

import gsstartup
from gsstartup import muster2

def check_temp_dir():
    temp_dir = ''
    try:
        temp_dir = os.environ['NUKE_DISK_CACHE']
    except KeyError:
        print 'NUKE_DISK_CACHE variable not set. Skipping folder creation.'
    
    if temp_dir:
        try:
            os.makedirs(temp_dir)
        except OSError:
            if not os.path.isdir(temp_dir):
                raise

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
    check_temp_dir()

init()