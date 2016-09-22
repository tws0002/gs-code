__author__ = 'adamb'

import os, sys, shutil, errno
from settings import *
#from win32com.client import Dispatch


def driveToUNC(p, switchToFwdSlash=False):
    """
    @param p: path
    @param switchToFwdSlash: RV requires forward slashes in rvlink:// when in browser mode
                             (if you want to keep the link readible)
    """
    for share, letter in DRIVE_MAP.iteritems():
        if letter in p:
            p = p.replace(letter, ('//'+SERVER+'/'+SHARES[share]))
            if switchToFwdSlash:
                p = p.replace('\\', '/')
            return p
    return p

def win_shell_safe (filepath):
    # make the filepath safe for sending to start shell command
    # this means any dir names with spaces need to be quotemarked
    # and all slashes are backslashes
    newpath = filepath.replace('/','\\')
    resultpath = ''
    split = newpath.split("\\")

    if newpath.startswith('\\\\'):
        resultpath = "\\"

    for i in range(len(split)):
        if i < len(split)-1:
            if len(split[i].split(' ')) > 1:
                split[i] = ('"'+split[i]+'"')

    for i in range(len(split)):
        if i == 0:
            resultpath += split[i]
        else:
            resultpath +=  '\\' + split[i]

    return resultpath



def copyDirTree(src,dest):
    try:
        shutil.copytree(src, dest)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        #else: raise
#def updatePipelineFavorites():
#    # remove any gs pipelie favs
#    # add new pipeline faves
#    root = '//scholar/projects/{0}'.format(os.environ['GSPROJECT'])
#    createUserFavorite(root)
#
#def createUserFavorite(path):
#    link_name = '{0}.lnk'.format(os.path.basename(path))
#    fav_links = '{0}\{1}'.format(os.path.expandvars('%USERPROFILE%\Links'),link_name)
#    print (fav_links)
#    createShortcut(path=fav_links,target=path,wd=path)
# 
#def createShortcut(path, target='', wd='', icon=''):    
#    user = str(os.environ['USERNAME'])
#    shell = Dispatch('WScript.Shell', userName=user)
#    shortcut = shell.CreateShortCut(str(path))
#    print(dir (shortcut))
#    shortcut.Targetpath = target
#    shortcut.WorkingDirectory = wd
#    if icon == '':
#        pass
#    else:
#        shortcut.IconLocation = icon
#    shortcut.save()#