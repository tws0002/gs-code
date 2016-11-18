# userSetup.py

import os
import sys
import re
import maya.cmds as cmds
import mustache

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except:
    GSCODEBASE = '//scholar/code'
GSTOOLS = os.path.join(GSCODEBASE,'tools')
GSBIN = os.path.join(GSCODEBASE,'bin')

MVERSION = re.search( '(\d\d\d\d)', cmds.about(version=True) ).group(0)

VRAYVERSION = {
        '2016'  :   '3.30.01',
        '2015'  :   '3.30.01',
        '2013'  :   '2.30.01',
    }

MTOAVERSION = {
        '2015'  :   '1.1.0.4-core.4.2.0.5-win64',
        '2013'  :   '1.1.0.4-core.4.2.0.5-win64',
    }

PHXVERSION = {
        '2016'  :   '2.20.00.26357',
        '2015'  :   '2.20.00.25392',
        '2013'  :   '2.00.00',
    }

RFVERSION = {
        '2016'  :   '2015.0.0.2',
        '2015'  :   '2014.0.1',
    }
MRVERSION = {
        '2015'  :   '3.12.1.18',
    }
FFXVERSION = {
        '2016'  :   '1.9.1',
        '2015'  :   '1.9.1',
    }
FUMEVERSION = {
        '2016'  :   '4.0.0',
        '2015'  :   '4.0.0',
    }
PIOVERSION = {
        '2016'  :   '0.9.6',
        '2015'  :   '0.9.6',
        '2013'  :   '0.9.6',
    }
UINVERSION = {
        '2016'  :   '1.2',
        '2015'  :   '1.2',
        '2013'  :   '1.2',
    }
BTVERSION = {
        '2016'  :   '16.0.4',
        '2015'  :   '1.0',
    }
KRAKVERSION = {
        '2016'  :   '2.4.3.59396',
        '2015'  :   '2.4.3.59396',
}

# Takes a dictionary as an argument
def appendEnv(env,overwrite=False):
    for k,v in env.items():
        #v = v.replace('\\', '/')
        try:
            if overwrite:
                for i in v:
                    os.environ[k] = i                
            else:
                for i in v:
                    os.environ[k] = '%s;%s' %( os.environ[k], i )
        except KeyError:
            for i in v:
                os.environ[k] = i

        if k == 'PYTHONPATH':
            for i in v:
                sys.path.append( i )

def initLogo():


    asciiart = os.path.join(GSCODEBASE,'tools','studio', 'python','launcher','res', 'gs2.txt')
    txt_opn = open(asciiart)
    print txt_opn.read()



def initVray():
    try:
        VRAY_MAIN = os.path.join(GSBIN, 'vray', 'vrayformaya', VRAYVERSION[MVERSION], 'win', MVERSION)
        env_vars = {
                'PATH'                                      :   [ os.path.join( VRAY_MAIN, 'maya_bin' ) ],
                'MAYA_PLUG_IN_PATH'                         :   [ os.path.join( VRAY_MAIN, 'plug-ins' ) ],
                'MAYA_SCRIPT_PATH'                          :   [ os.path.join( VRAY_MAIN, 'scripts' ) ],
                'XBMLANGPATH'                               :   [ os.path.join( VRAY_MAIN, 'icons' ) ],
                'MAYA_RENDER_DESC_PATH'                     :   [ os.path.join( VRAY_MAIN, 'maya_bin/rendererDesc' ) ],
                'PYTHONPATH'                                :   [ os.path.join( VRAY_MAIN, 'scripts' ) ],
                'XGEN_CONFIG_PATH'                          :   [ os.path.join( VRAY_MAIN, '/plug-ins/xgen/presets') ],
                'VRAY_FOR_MAYA%s_PLUGINS_x64' %(MVERSION)   :   [ os.path.join( VRAY_MAIN, 'vrayplugins' ) ],
                'VRAY_PLUGINS_x64'                          :   [ os.path.join( VRAY_MAIN, 'vrayplugins' ) ],
                'VRAY_TOOLS_MAYA%s_x64' %(MVERSION)         :   [ os.path.join( VRAY_MAIN, 'bin' ) ],
                'VRAY_FOR_MAYA_SHADERS'                     :   [ os.path.join( VRAY_MAIN, 'shaders' ) ],
            }
        env_vars_ow = {
                'VRAY_FOR_MAYA%s_MAIN_x64' %(MVERSION)      :   [ VRAY_MAIN ],
                'VRAY_AUTH_CLIENT_FILE_PATH'                :   [ os.path.join( VRAY_MAIN, 'conf' ) ],
            }
        appendEnv(env_vars)
        appendEnv(env_vars_ow, overwrite=True)
    except KeyError:
        #print "v-ray not a supported GS network plug-in for maya %s" %( MVERSION )
        pass        

def initMtoa():
    try:
        MTOA_MAIN = os.path.join(GSBIN, 'arnold', 'mtoa', MTOAVERSION[MVERSION], 'win', MVERSION)

        env_vars = {
                'PATH'                      :   [ os.path.join( MTOA_MAIN, 'bin') ],
                'MAYA_PLUG_IN_PATH'         :   [ os.path.join( MTOA_MAIN, 'plug-ins' ) ],
                'MAYA_SCRIPT_PATH'          :   [ os.path.join( MTOA_MAIN, 'scripts' ) ],
                'XBMLANGPATH'               :   [ os.path.join( MTOA_MAIN, 'icons' ) ],
                'MAYA_RENDER_DESC_PATH'     :   [ MTOA_MAIN ],
                'PYTHONPATH'                :   [ os.path.join( MTOA_MAIN, 'scripts' ) ],
                'MTOA_PATH'                 :   [ MTOA_MAIN ],
                'ARNOLD_PLUGIN_PATH'        :   [ os.path.join( MTOA_MAIN, 'shaders' ),
                                                    os.path.join( MTOA_MAIN, 'procedurals' )
                                                ],
                'MTOA_EXTENSIONS_PATH'      :   [ os.path.join( MTOA_MAIN, 'extensions') ],
            }
        appendEnv(env_vars)
    except KeyError:
        #print "mtoa not a supported GS network plug-in for maya %s" %( MVERSION )
        pass    

def initPhx():
    try:
        PHX_MAIN = os.path.join( GSBIN, 'maya', 'modules', MVERSION, 'phoenixfd', PHXVERSION[MVERSION] )
        env_vars = {
                'MAYA_PLUG_IN_PATH'                         :   [ os.path.join( PHX_MAIN, 'plug-ins' ) ],
                'MAYA_SCRIPT_PATH'                          :   [ os.path.join( PHX_MAIN, 'scripts' ),
                                                                    os.path.join ( PHX_MAIN, 'samples/scripts' )
                                                                ],
                'XBMLANGPATH'                               :   [ os.path.join( PHX_MAIN, 'icons' ) ],
                'VRAY_FOR_MAYA%s_PLUGINS_x64' %(MVERSION)   :   [ os.path.join( PHX_MAIN, 'vrayplugins' ) ],
                'PHX_FOR_MAYA%s_MAIN_x64' %(MVERSION)       :   [ PHX_MAIN ],
                'PATH'                                      :   [ os.path.join( PHX_MAIN, 'maya_bin') ],
            }
        appendEnv(env_vars)
    except KeyError:
        #print "phoenixfd not a supported GS network plug-in for maya %s" %( MVERSION )
        pass

def initMr():
    try:
        MR_MAIN = os.path.join( GSBIN, 'mentalray', 'mayatomr', MRVERSION[MVERSION], 'win', MVERSION)
        MR_MAYA_PRESET_PATH = MR_MAIN+'/presets'
        MR_MAYA_ATTR_PATH = MR_MAYA_PRESET_PATH+'/attrPresets'
        MR_SCRIPTS = MR_MAIN+'/scripts'
        MR_SHADERS = MR_MAIN+'/shaders'

        env_vars = {
                'MAYA_PLUG_IN_PATH'             :   [ os.path.join( MR_MAIN, 'plug-ins' ) ],
                'MAYA_PLUG_IN_RESOURCE_PATH'    :   [ os.path.join( MR_MAIN, 'resources' ) ],
                'MAYA_PRESET_PATH'              :   [ MR_MAYA_PRESET_PATH,
                                                        os.path.join( MR_MAYA_ATTR_PATH, 'maya_bifrost_liquid' ),
                                                        os.path.join( MR_MAYA_ATTR_PATH, 'mia_material' ),
                                                        os.path.join( MR_MAYA_ATTR_PATH, 'mia_material_x' ),
                                                        os.path.join( MR_MAYA_ATTR_PATH, 'mia_material_x_passes' ),
                                                    ],
                'MAYA_RENDER_DESC_PATH'         :   [ os.path.join( MR_MAIN, 'rendererDesc' ) ],
                'MAYA_SCRIPT_PATH'              :   [ MR_SCRIPTS,
                                                        os.path.join( MR_SCRIPTS, 'AETemplates' ),
                                                        os.path.join( MR_SCRIPTS, 'mentalray' ),
                                                        os.path.join( MR_SCRIPTS, 'unsupported' ),
                                                    ],
                'MENTALRAY_BIN_LOCATION'        :   [ os.path.join( MR_MAIN, 'bin' ) ],
                'MENTALRAY_INCLUDE_LOCATION'    :   [ os.path.join( MR_SHADERS, 'include' ) ],
                'MENTALRAY_LOCATION'            :   [ MR_MAIN ],
                'MENTALRAY_SHADERS_LOCATION'    :   [ MR_SHADERS ],
                'MI_CUSTOM_SHADER_PATH'         :   [ os.path.join( MR_MAIN, 'shaders' ) ],
                'PATH'                          :   [ os.path.join( MR_MAIN, 'bin' ) ],
                'PYTHONPATH'                    :   [ MR_SCRIPTS,
                                                        os.path.join( MR_SCRIPTS, 'AETemplates' ),
                                                        os.path.join( MR_SCRIPTS, 'mentalray' ),
                                                        os.path.join( MR_SCRIPTS, 'unsupported' ),
                                                    ],
                'XBMLANGPATH'                   :   [ os.path.join( MR_MAIN, 'icons') ],
            }

        appendEnv(env_vars)
    except KeyError:
        pass

def initRealflow():
    try:
        RF_MAIN = os.path.join( GSBIN, 'plugins', 'maya', 'realflow', RFVERSION[MVERSION], 'win', MVERSION)
        m = re.search('^(\d*)\.\d*\.', RFVERSION[MVERSION])
        RFCONVER = m.group(1)
        env_vars = {
            'PATH'                                      :   [ os.path.join( RF_MAIN, 'bin' ) ],
            'RFCONNECT%s_ROOT' %(RFCONVER)              :   [ os.path.join( RF_MAIN, 'bin' ) ],
            'MAYA_PLUG_IN_PATH'                         :   [ os.path.join( RF_MAIN, 'plug-ins' ) ],
            'MAYA_SCRIPT_PATH'                          :   [ os.path.join( RF_MAIN, 'scripts' ) ],
            'VRAY_FOR_MAYA%s_PLUGINS_x64' %(MVERSION)   :   [ os.path.join( RF_MAIN, 'vrayplugins' ) ],
            'XBMLANGPATH'                               :   [ os.path.join( RF_MAIN, 'icons' ) ],
        }
        appendEnv(env_vars)
    except KeyError:
        pass

def initFractureFX():
    try:
        FFX_MAIN = os.path.join( GSBIN, 'plugins', 'maya', 'fracturefx', FFXVERSION[MVERSION], 'win', MVERSION)
        env_vars = {
            'MAYA_PLUG_IN_PATH' :   [ os.path.join( FFX_MAIN, 'plug-ins' ) ],
            'MAYA_SCRIPT_PATH'  :   [ os.path.join( FFX_MAIN, 'scripts' ) ],
            'FX_LCN_FILE'       :   [ os.path.join( FFX_MAIN, 'config', 'fxlcn') ],
        }
        appendEnv(env_vars)
    except KeyError:
        pass

def initFumeFX():
    try:
        FUME_MAIN = os.path.join( GSBIN, 'plugins', 'maya', 'fumefx', FUMEVERSION[MVERSION], 'win', MVERSION)
        env_vars = {
            'MAYA_PLUG_IN_PATH'                         :   [ os.path.join( FUME_MAIN, 'plug-ins' ) ],
            'PATH'                                      :   [ os.path.join( FUME_MAIN, 'bin' ) ],
            'MAYA_SCRIPT_PATH'                          :   [ os.path.join( FUME_MAIN, 'scripts' ) ],
            'XBMLANGPATH'                               :   [ os.path.join( FUME_MAIN, 'icons' ) ],
            'VRAY_FOR_MAYA_SHADERS'                     :   [ os.path.join( FUME_MAIN, 'shaders', 'vray' ) ],
            'VRAY_FOR_MAYA%s_PLUGINS_x64' %(MVERSION)   :   [ os.path.join( FUME_MAIN, 'vrayplugins' ) ],
        }
        appendEnv(env_vars)
    except KeyError:
        pass

def initKrakatoa():
    try:
        KRAK_MAIN = os.path.join( GSBIN, 'plugins', 'maya', 'krakatoa', KRAKVERSION[MVERSION], 'win', MVERSION)
        env_vars = {
            'MAYA_PLUG_IN_PATH'         :   [ os.path.join( KRAK_MAIN, 'plug-ins' ) ],
            'MAYA_SCRIPT_PATH'          :   [ os.path.join( KRAK_MAIN, 'scripts', 'mel' ) ],
            'PYTHONPATH'                :   [ os.path.join( KRAK_MAIN, 'scripts', 'python' ) ],
            'XBMLANGPATH'               :   [ os.path.join( KRAK_MAIN, 'icons' ) ],
            'MAYA_RENDER_DESC_PATH'     :   [ os.path.join( KRAK_MAIN, 'rendererDesc' ) ],
        }
        appendEnv(env_vars)
    except KeyError:
        pass

def initPartio():
    try:
        PIO_MAIN = os.path.join( GSBIN, 'plugins', 'maya', 'partio', PIOVERSION[MVERSION], 'win', MVERSION)
        env_vars = {
            'MAYA_PLUG_IN_PATH' :   [ os.path.join( PIO_MAIN, 'plug-ins' ) ],
            'PATH'              :   [ os.path.join( PIO_MAIN, 'bin' ) ],
            'MAYA_SCRIPT_PATH'  :   [ os.path.join( PIO_MAIN, 'scripts', 'mel' ) ],
            'PYTHONPATH'        :   [ os.path.join( PIO_MAIN, 'scripts', 'python' ) ],
            'XBMLANGPATH'       :   [ os.path.join( PIO_MAIN, 'icons' ) ],
        }
        appendEnv(env_vars)
    except KeyError:
        pass

def initUninstancer():
    try:
        UIN_MAIN = os.path.join( GSBIN, 'plugins', 'maya', 'uninstancer', UINVERSION[MVERSION], 'win', MVERSION)
        env_vars = {
            'MAYA_PLUG_IN_PATH' :   [ os.path.join( UIN_MAIN, 'plug-ins' ) ],
            'MAYA_SCRIPT_PATH'  :   [ os.path.join( UIN_MAIN, 'scripts', 'mel' ) ],
            'PYTHONPATH'        :   [ os.path.join( UIN_MAIN, 'scripts', 'python' ) ],
        }
        appendEnv(env_vars)
    except KeyError:
        pass

def initBonusTools():
    try:
        BT_MAIN = os.path.join( GSBIN, 'plugins', 'maya', 'bonustools', BTVERSION[MVERSION], 'win', MVERSION)
        env_vars = {
            'MAYA_PLUG_IN_PATH' :   [ os.path.join( BT_MAIN, 'plug-ins' ) ],
            'MAYA_SCRIPT_PATH'  :   [ os.path.join( BT_MAIN, 'scripts', 'mel' ) ],
            'PYTHONPATH'        :   [ os.path.join( BT_MAIN, 'scripts', 'python' ) ],
            'XBMLANGPATH'       :   [ os.path.join( BT_MAIN, 'icons' ) ],
        }
        appendEnv(env_vars)
    except KeyError:
        pass

def initMustache():
    mustache.init()

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
    #cmds.evalDeferred("import os;os.chdir('C:\Windows\System32')")
    os.chdir('C:\Windows\System32')

def gs_autoload():
    var = os.environ.get('GS_MAYA_AUTOLOAD')
    plugins = []
    if var != None:
        plugins = var.split(';')
    for p in plugins:
        try:
            cmds.loadPlugin(p)
        except:
            print ("Could not load plugin {0}".format(p))

def init():
    #initLogo()
    #initPhx()
    ##initVray()
    ##initMtoa()
    ##initMr()
    #initFumeFX()
    #initRealflow()
    #initFractureFX()
    #initKrakatoa()
    #initPartio()
    #initUninstancer()
    #initBonusTools()
    initMustache()
    autoInitMustacheProject()

    gs_autoload()
    gs_restore_pwd()
if __name__ == '__main__':
    init()