set "ST_MAYA=2015"
set "ST_MAYA_DIR=C:/Program Files/Autodesk/Maya/%ST_MAYA%.0.5"
set "GSBRANCH=//scholar/pipeline/base"
set "LM_LICENSE_FILE=27001@laxlic01"
set "AUTODESK_ADLM_THINCLIENT_ENV=//scholar/apps/Autodesk/adlm/AdlmThinClientCustomEnv.xml"
set "MAYA_STTOOLS=%GSBRANCH%/apps/maya"
set "MAYA_STTOOLS_COMMON=%GSBRANCH%/apps/maya"
set "MAYA_MODULE_PATH=%MAYA_STTOOLS%/modules/%ST_MAYA%"
set "MAYA_PLUG_IN_PATH="""
set "MAYA_PRESET_PATH=%MAYA_STTOOLS%/presets"
set "MAYA_SCRIPT_PATH=%MAYA_STTOOLS%/scripts/mel;%MAYA_STTOOLS%/scripts/python;%MAYA_STTOOLS%/scripts/mel;%MAYA_STTOOLS%/scripts/mel/Utility;%MAYA_STTOOLS%/scripts/Modeling;%MAYA_STTOOLS%/scripts/mel/Rigging;%MAYA_STTOOLS%/scripts/mel/Modeling;%MAYA_STTOOLS%/scripts/mel/Scholar"
set "MAYA_SHELF_PATH=%MAYA_STTOOLS%/shelves/%ST_MAYA%"
set "XBMLANGPATH=%MAYA_STTOOLS%/icons"
set "PYTHONPATH=%GSROOT%/lib/python;%MAYA_STTOOLS%/scripts/python;%GSBRANCH%/gs/python"
set "MAYA_DISABLE_CLIC_IPM=1"
set "MAYA_DISABLE_CIP=1

set "ST_MAYA_REDSHIFT=2.5.13"
set "MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%GSROOT%/bin/external/maya/modules/redshift/%ST_MAYA_REDSHIFT%/win/%ST_MAYA%""
set "MAYA_RENDER_DESC_PATH=%GSROOT%/bin/external/maya/modules/redshift/%ST_MAYA_REDSHIFT%/win/%ST_MAYA%/bin/rendererDesc"

set "ST_MAYA_VRAY=2.40.01"
set "VRAY_AUTH_CLIENT_FILE_PATH=%GSROOT%/bin/external/maya/modules/vrayformaya/%ST_MAYA_VRAY%/win/%ST_MAYA%/conf"
set "MAYA_RENDER_DESC_PATH=%MAYA_RENDER_DESC_PATH%;%GSROOT%/bin/external/maya/modules/vrayformaya/%ST_MAYA_VRAY%/win/%ST_MAYA%/maya_bin/rendererDesc"
set "MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%GSROOT%/bin/external/maya/modules/vrayformaya/%ST_MAYA_VRAY%/win/%ST_MAYA%"

set "MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%GSROOT%/bin/external/maya/modules/bonustools/%ST_MAYA_BT%/win/%ST_MAYA%"

"C:\Program Files\Autodesk\Maya\2015.0.5\bin\maya.exe"