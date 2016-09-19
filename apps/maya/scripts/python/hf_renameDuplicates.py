# hf_renameDuplicates v0.2 by henry foster (henry@toadstorm.com)

import maya.cmds as cmds

def renameDuplicates(padding=3):
    # get all xforms. if an xform name contains a '|', it's appearing more than once and we'll have to rename it.
    badXforms = [f for f in cmds.ls() if '|' in f]
    badXformsUnlock = [f for f in badXforms if cmds.lockNode(f,q=1,lock=1)[0] == False]
    count = 0
    # we need to somehow sort this list by the number of '|' appearing in each name. this way we can edit names from the bottom of the hierarchy up,
    # and not worry about losing child objects from the list.
    countDict = {}
    for f in badXformsUnlock:
        countDict[f] = f.count('|')
    # now sort the dictionary by value, in reverse, and start renaming.
    for key,value in sorted(countDict.iteritems(),reverse=True, key=lambda (key,value): (value,key)):
        # okay, now we can start actually renaming objects in order.
        n = 1
        # print '\ndebug: renaming object %s' % (key)
        newObj = cmds.rename(key,key.split('|')[-1]+'_'+str(n).zfill(padding))
        while newObj.count('|') > 0:
            # INFINITE LOOP PROBLEM: if the transform and the shape are named the same, this will go on forever.
            # we need to write some kind of exception to prevent this from happening.
            n += 1
            basename = newObj.split('|')[-1]
            newName = '_'.join(basename.split('_')[0:-1])+'_'+str(n).zfill(padding)
            newObj = cmds.rename(newObj,newName)
        print 'renamed %s to %s' % (key,newObj)
        count = count+1
    if count < 1:
        return 'No duplicate names found.'
    else:
        return 'Found and renamed '+str(count)+' objects with duplicate names. Check script editor for details.'
