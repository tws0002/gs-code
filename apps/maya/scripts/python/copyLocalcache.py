import os
import sys
import shutil
import filecmp

from pymel import core as pm

localPath = "C:/Temp"

print "Creating local copy of Alembic cache"
abcnodes = pm.general.ls(type='AlembicNode')
for n in abcnodes:
    netfile = n.getAttr('abc_File')
    filename = os.path.split(netfile)[1]
    localfile = os.path.join(localPath,filename)
    
    if os.path.exists(localfile) and filecmp.cmp(localfile, netfile):
        print "Local copy already exists: ", filename
    elif os.path.exists(localfile) and not filecmp.cmp(localfile, netfile):
        print "Local copy exists, but is different from scene's cache. Making local copy: ", filename
        shutil.copyfile(netfile, localfile)
        print "Done!"
    else:
        print "Making local copy: ", filename
        shutil.copyfile(netfile, localfile)
        print "Done!"

#print pm.general.listNodeTypes('AlembicNode')
#alembicnode = pm.general.selected()[0]
#print pm.general.nodeType(alembicnode)
#print alembicnode.setAttr('abc_File', 'C:\Temp\alembic_test_cache\Store_Page_cutout_MASTER.abc')