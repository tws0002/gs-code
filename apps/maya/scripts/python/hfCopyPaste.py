# hfCopyPaste.py v1.1 by Henry Foster (henry@toadstorm.com), 05/02/2011
#
# this script copies channels from one selected object and pastes them to any number
# of other objects. select an object's channels in the channel box and run copyChan()
# to copy to the clipboard. select a number of other objects and run pasteChan() to paste
# the channels from the clipboard.
#
# the clipboard for this script resides in a local file on the computer. this way channels can be pasted
# between instances of maya and are persistent even after maya is closed.


import pickle
import platform
import maya.cmds as cmds
import maya.mel as mel
import os
def copyChan():
    try:
        obj = cmds.ls(sl=1)[0]
    except IndexError:
        cmds.error('try selecting something.')
    xformChan = cmds.channelBox('mainChannelBox',q=1,sma=1)
    shapeChan = cmds.channelBox('mainChannelBox',q=1,ssa=1)
    # inputChan = cmds.channelBox('mainChannelBox',q=1,sha=1)
    objShape = cmds.channelBox('mainChannelBox',q=1,sol=1)
    bigPickle = []
    xDict = {}
    sDict = {}
    # iDict = {}
    if xformChan != None:
        for a in xformChan:
            xDict[a] = cmds.getAttr(str(obj)+'.'+str(a))
    if shapeChan != None:
        for a in shapeChan:
            sDict[a] = cmds.getAttr(str(objShape[0])+'.'+str(a))
    # now we have two dictionaries of transform channels and shape channels. let's write these somewhere
    # so that we can paste between instances of maya.
    if platform.system() == 'Windows' or platform.system() == 'Microsoft':
        if not os.path.exists('C:/hfCP'):
            os.makedirs('C:\hfCP')
        cppath = 'c:\hfCP\hfCopyPaste.txt'
    else:
        cppath = '/Users/Shared/hfCopyPaste.txt'
    clearfile = open(cppath, 'w')
    # close file immediately to clear it.
    clearfile.close()
    writefile = open(cppath, 'w')
    bigPickle.append(xDict)
    bigPickle.append(sDict)
    pickle.dump(bigPickle,writefile)
    writefile.close()
    print(xDict)
    print(sDict)
    mel.eval('print("Values copied to clipboard.")')

def pasteChan():
    objs = cmds.ls(sl=1)
    if len(objs) < 1:
        cmds.error('you should probably select something to paste to.')
    # load the dicts back from the file and get ready to apply channels
    if platform.system() == 'Windows' or platform.system() == 'Microsoft':
        cppath = 'C:\hfCP\hfCopyPaste.txt'
    else:
        cppath = '/Users/Shared/hfCopyPaste.txt'
    pastefile = open(cppath, 'r')
    # index 0 is xform channels. index 1 is shape channels.
    channels = pickle.load(pastefile)
    # print(channels)
    xDict = dict(channels[0])
    sDict = dict(channels[1])
    print(xDict)
    print(sDict)
    # now assign each channel to every object in objs.
    for chan, value in xDict.iteritems():
        for obj in objs:
            try:
                cmds.setAttr(obj+'.'+chan, value)
            except:
                pass
    # pasting shape values will be trickier. typically we are only selecting xforms.
    # we'll have to get any associated shapes with each obj in objs and paste channels to them if possible.
    # since we don't know exactly what we're pasting to or what we copied from, we should just try to paste to everything,
    # the selected objects and their shapes.
    allShapes = []
    allShapes.extend(objs)
    for obj in objs:
        shapes = cmds.listRelatives(obj,s=1)
        if shapes != None:
            allShapes.extend(shapes)
    for chan, value in sDict.iteritems():
        for shape in allShapes:
            try:
                cmds.setAttr(shape+'.'+chan, value)
            except:
                pass
    print 'Channels pasted to %d objects' % len(objs)
