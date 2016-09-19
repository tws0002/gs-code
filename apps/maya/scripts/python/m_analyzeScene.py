# m_analyzeScene v0.01 by henry foster (henry@toadstorm.com), 7/22/2011
#
# used with argument 'inputFile'
# opens the file in maya standalone and returns a dictionary of all referenced files with their namespaces.
# refsDict[filename] = namespace

import sys
import maya.standalone
import maya.cmds as cmds
import subprocess
import pickle

# open inputFile, list all loaded references, and return a dictionary where dict[filename] = namespace.

inputFile = sys.argv[1]
sys.stdout.write('Initializing Maya Python interpreter.')
maya.standalone.initialize(name='python')
sys.stdout.write('Opening file for analysis: '+inputFile)
cmds.file(inputFile,o=1)
# look for active (non-deferred) references. don't include cameras.
refs = [cmds.file(f,q=1,rfn=1) for f in cmds.file(q=1,r=1) if not cmds.file(f,q=1,dr=1)]
refsDict = {}
sys.stdout.write('Opened file: '+cmds.file(q=1,sn=1))
for ref in refs:
    filename = cmds.referenceQuery(ref,f=1)
    namespace = cmds.file(filename,q=1,ns=1)
    if filename.split('/')[-2] != 'cameras':
        refsDict[filename]=namespace
# now use subprocess to return this thing.
sys.stdout.write('M_ANALYZESCENE_DUMP')
sys.stdout.write(pickle.dumps(refsDict))
