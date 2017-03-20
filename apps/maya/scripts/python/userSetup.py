# userSetup.py

import os
import maya.cmds as cmds
import mustache
import time

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except:
    GSCODEBASE = '//scholar/code'

def initLogo():
    asciiart = os.path.join(GSCODEBASE,'base','gs', 'python','launcher','res', 'gs2.txt')
    txt_opn = open(asciiart)
    print txt_opn.read()

def initMustache():
    start_time = time.time()
    mustache.init()
    autoInitMustacheProject()
    elapsed_time = time.time() - start_time
    print("// GS: Mustache loaded in {0} sec".format(elapsed_time))

def autoInitMustacheProject():
    
    if mustache.M != None:
        if 'GSINITIALS' in os.environ:
            mustache.M.user = os.environ['GSINITIALS']
        if 'GSPROJECT' in os.environ:
            mustache.M.projectName =  os.environ['GSPROJECT']
            mustache.M.project = '/'.join(['//scholar/projects', mustache.M.projectName, '03_production','01_cg','01_MAYA'])
            mustache.M.assetsDir = '/'.join([mustache.M.project, mustache.M.assetsBase])
            mustache.M.scenesDir = '/'.join([mustache.M.project, mustache.M.shotsBase])
            mustache.M.sceneTemplate = os.path.join(mustache.M.project, 'scenes', 'TEMPLATE.mb')
    else:
        print ("Mustache non Initialized yet. Cannot run Auto Init in userSetup.py")
    

def gs_restore_pwd():
    m_install = ''
    try:
        m_install = os.environ['ST_MAYA_DIR']
        os.chdir(m_install)
        cmds.evalDeferred("import os;os.chdir('{0}')".format(m_install), lowestPriority=False)
    except:
        os.chdir(m_install)
        cmds.evalDeferred("import os;os.chdir('C:\Windows\System32')", lowestPriority=False)

def gs_pluginLoad(plugin=''):
    start_time = time.time()
    if plugin != '':
        try:
            cmds.loadPlugin(plugin)
            elapsed_time = time.time() - start_time
            print("// GS: '{0}' loaded in {1} sec".format(plugin,elapsed_time))
        except:
            print ('Plugin invalid: {0}'.format(plugin))


def gs_autoload():
    var = os.environ.get('GS_MAYA_AUTOLOAD')
    plugins = []
    if var != None:
        plugins = var.split(';')
    for p in plugins:
        try:
            cmds.evalDeferred("gs_pluginLoad('{0}')".format(p), lowestPriority=False)
        except:
            print ("Could not load plugin {0}".format(p))


def init():
    #initLogo()
    gs_autoload()
    gs_restore_pwd()
    cmds.evalDeferred("initMustache()", lowestPriority=True)
if __name__ == '__main__':
    init()