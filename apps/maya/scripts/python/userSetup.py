# userSetup.py

import os, sys
import maya.cmds as cmds
import maya.mel as mel
import mustache
import time
import gs_menu

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
            print ('Plugin Not Found: {0}'.format(plugin))
            raise



    #os.environ['MAYA_PLUG_IN_PATH'] = tmp 
    #os.environ['MAYA_SCRIPT_PATH'] = tmp2

def gs_autoload(local_only=False):
    #gs_load_deferred_modules()


    plugs = os.environ.get('GS_MAYA_AUTOLOAD')
    # temporarily remove network paths from mayas search paths, this speeds up load time dramatically
    temp_var_dict = {}
    #temp_sys_path = list(sys.path)
    var_to_check=['MAYA_PLUG_IN_PATH','MAYA_SCRIPT_PATH','MAYA_SHELF_PATH','XBMLANGPATH','MAYA_PRESET_PATH','MAYA_RENDER_DESC_PATH','MAYA_PLUG_IN_RESOURCE_PATH','MAYA_MODULE_PATH','PYTHONPATH','PATH']
    if local_only == True:
        for var in var_to_check:
            if var in os.environ:
                temp_var_dict[var] = os.environ[var]
                new_paths = ''
                for p in os.environ[var].split(';'):
                    if p[:2] == '//' or p[:2] == '\\\\':
                        pass
                    else:
                        if new_paths == '':
                            new_paths = p
                        else:
                            new_paths += ';{0}'.format(p)
                os.environ[var] = new_paths

                #print ("Temporarily Removing Network Paths on {0}".format(var))
                #print ("{0}={1}".format(var,new_paths))
        #sys.path = []
        #for sp in temp_sys_path:
        #    if sp[:2] == '\\\\' or sp[:2] == '//':
        #        pass
        #    else:
        #        sys.path.append(sp)

    plugins = []
    failed_plugins = []
    if plugs != None:
        plugins = plugs.split(';')

    progress = 0
    cmds.progressWindow(title='GS Init Local Plugins', progress=progress, status='Loading Plugins: 0%')

    for p in plugins:
        cmds.progressWindow( edit=True, progress=progress, status=('Loading {0}: '.format(p) + `progress` + '%' ) )
        try:
            gs_pluginLoad(p)
        except:
            print ("Could not load plugin {0}, Checking Network on second pass".format(p))
            failed_plugins.append(p) 
        progress += int(100.0 / float(len(plugins)))
        
    if len(failed_plugins) == 0:
        cmds.progressWindow(endProgress=1)

    if local_only == True:
        for var in var_to_check:
            if var in temp_var_dict:
                os.environ[var] = temp_var_dict[var]
    # this causes dramatic slowdown in maya shutdown procedure
    #sys.path = list(temp_sys_path)
    #sys.path = []
    #for sp in temp_sys_path:
    #    sys.path.append(sp)

    if len(failed_plugins) > 0:
        progress = int(100.0 / float(len(failed_plugins)))
        cmds.progressWindow(edit=True, title='GS Init Network Plugins', progress=progress, status='Loading {0}: 0%'.format(failed_plugins[0]))

        for p in failed_plugins:
            print ("Trying to load network plugin {0}".format(p))
            cmds.progressWindow( edit=True, progress=progress, status=('Loading {0}: '.format(p) + `progress` + '%' ) )
            try:
                gs_pluginLoad(p)
            except:
                print ("Could not load plugin {0}".format(p))
            progress += int(100.0 / float(len(failed_plugins)))
        cmds.progressWindow(endProgress=1)
    

def gs_set_renderlayer_mode():

    mode = 'legacy'
    if 'GS_MAYA_LAYERMODE' in os.environ:
        mode = os.environ['GS_MAYA_LAYERMODE']

    if mode == 'rendersetup':
        cmds.optionVar(iv=('renderSetupEnable', 1))
    else:
        cmds.optionVar(iv=('renderSetupEnable', 0))

def gs_load_deferred_modules():
    print ("Setting deferred Modules")
    if 'GS_MAYA_MODULE_PATH' in os.environ:
        if 'MAYA_MODULE_PATH' in os.environ:
            os.environ['MAYA_MODULE_PATH'] += ';{0}'.format(os.environ['GS_MAYA_MODULE_PATH'])
        else:
            os.environ['MAYA_MODULE_PATH'] = os.environ['GS_MAYA_MODULE_PATH']
    if 'GS_MAYA_SHELF_PATH' in os.environ:
        if 'MAYA_SHELF_PATH' in os.environ:
            os.environ['MAYA_SHELF_PATH'] += ';{0}'.format(os.environ['GS_MAYA_SHELF_PATH'])
        else:
            os.environ['MAYA_SHELF_PATH'] = os.environ['GS_MAYA_SHELF_PATH']

def force_legacy_render_layers():
    cmds.optionVar(iv=('renderSetupEnable', 0))

def init():
    #initLogo()
<<<<<<< HEAD
    force_legacy_render_layers()
    gs_autoload()
=======
    gs_set_renderlayer_mode()
    cmds.evalDeferred("gs_autoload(local_only=True)")
>>>>>>> refs/remotes/origin/master
    gs_restore_pwd()
    cmds.evalDeferred("initMustache()")
    cmds.evalDeferred("import gs_menu;gs_menu.init_gs_menu()")
    gs_set_renderlayer_mode()


if __name__ == '__main__':
    init()