import maya.cmds as cmds
import pickle

def copyAll(*args):
    obj=cmds.ls(sl=1)[0]
    copyDict = {}
    attrs = cmds.listAttr(obj,m=True,w=True,v=True,se=True,sa=True)
    for a in attrs:
        try:
            copyDict[a] = cmds.getAttr(obj+'.'+a)
        except RuntimeError:
            # this is probably a compound attribute with mixed type elements, and getAttr doesn't work with these
            pass
    f = open("C:\copyAll.txt",'w')
    pickle.dump(copyDict,f)
    f.close()


def pasteAll(debugMe=0,*args):
    sel = cmds.ls(sl=True)
    f = open("C:\copyAll.txt",'r')
    copyDict = pickle.load(f)
    f.close()
    for obj in sel:
        exceptList = []
        for chan, val in copyDict.iteritems():
            try:    
                cmds.setAttr(obj+'.'+chan, val)
            except RuntimeError:
                # may be a list, redundant because we are using the m flag for listAttr
                if type(val) != type(list()):
                    exceptList.append(chan)
    exceptList = list(set(exceptList))
    if debugMe != 0: print "didn't sync channels: %s" % (exceptList)
