__author__ = 'adamb'

HAS_PYWIN = False
HAS_PYAD = False

import os, sys, shutil, errno
from settings import *

# Load Pywin, if its available load pyad package
try:
    from win32com.client import Dispatch
    from win32com.shell import shell
    import win32api
    HAS_PYWIN = True
    try:
        from pyad import aduser
        HAS_PYAD = True
    except ImportError:
        print("Missing pyad package. Disabling AD services")

except ImportError:
    print("Missing pywin package. Disabling pywin services")



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
def updatePipelineFavorites():
    if HAS_PYWIN:
        # remove any gs pipelie favs
        # add new pipeline faves
        root = '//scholar/projects/{0}'.format(os.environ['GSPROJECT'])
        createUserFavorite(root)

def createUserFavorite(path):
    if HAS_PYWIN:
        os_path = os.path.normpath(path)
        link_name = '{0}.lnk'.format(os.path.basename(os_path))
        fav_links = '{0}\{1}'.format(os.path.expandvars('%USERPROFILE%\Links'),link_name)
        print ('createShortcut(path={0},target={1},wd={2})'.format(fav_links,os_path,os_path))
        createShortcut(path=fav_links,target=path,wd=path)
 
def createShortcut(path, target='', wd='', icon=''):  
    if HAS_PYWIN:
        wind_path = os.path.normpath(path)  
        wind_target = os.path.normpath(target)  
        wind_wd = os.path.normpath(wd)
        wind_icon = os.path.normpath(icon)

        user = str(os.environ['USERNAME'])
        shell = Dispatch('WScript.Shell', userName=user)
        shortcut = shell.CreateShortCut(str(wind_path))

        shortcut.Targetpath = wind_target
        shortcut.WorkingDirectory = wind_wd
        if icon == '':
            pass
        else:
            shortcut.IconLocation = wind_icon
        shortcut.save()

def isAdmin():
    result = False
    try:
        result = shell.IsUserAnAdmin()
    except:
        print ("Unable determine privilege (pywin), please ask a systems admin for help")
    return result


def loadActiveUser():
    user = ''
    if (HAS_PYAD):
        try:
            ad_dn = win32api.GetUserNameEx(win32api.NameFullyQualifiedDN)
            user = aduser.ADUser.from_dn(ad_dn)
        except:
            print ("Unable to connect to AD server, please ask a systems admin for help")
    return user

#def isAdmin():
#    result = False
#    try:
#        user = loadActiveUser():
#        user = aduser.ADUser.from_cn("myuser")
#        # search user groups for Admins
#        ad_groups = user.get_attributes('memberOf')
#        if ad_groups.search("CN=Domain Admins"):
#            result = True
#    except:
#        print ("Unable to connect to AD server, please ask a systems admin for help")
#    return result

def get_initials(fullname):
    initials = ''
    if HAS_PYWIN:
        xs = (fullname)
        name_list = xs.split()

        for name in name_list:  # go through each name
          initials += name[0].upper()  # append the initial

    return initials