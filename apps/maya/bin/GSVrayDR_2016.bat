@echo off

if not defined GSCODEBASE (
	set GSCODEBASE=\\scholar\pipeline
)
set GSTOOLS=%GSCODEBASE%\tools)
set GSBIN=%GSCODEBASE%\bin

echo Using %GSCODEBASE% as repository.

if not "%2"=="" (
	set MAYAVER=%1
	set VRAYVER=%2
	goto startvraydr
) else (
	echo This script requires two arguments: Maya version and V-ray version (i.e. GSVrayDR.bat 2013 2.30.01)
	goto end
)

:startvraydr
echo Setting up environment...
set VRAY_MAIN=%GSBIN%\external\maya\modules\vrayformaya\%VRAYVER%\win\%MAYAVER%
set PATH=%PATH%;%VRAY_MAIN%\maya_bin
set MAYA_PLUG_IN_PATH=%VRAY_MAIN%
set MAYA_SCRIPT_PATH=%VRAY_MAIN%\scripts
set XBMLANGPATH=%VRAY_MAIN%\icons
set MAYA_RENDER_DESC_PATH=%VRAY_MAIN%\maya_bin\rendererDesc
set PYTHONPATH=%PYTHONPATH%;%VRAY_MAIN%\scripts
set XGEN_CONFIG_PATH=%VRAY_MAIN%\plug-ins\xgen\presets
set VRAY_FOR_MAYA%MAYAVER%_MAIN_x64=%VRAY_MAIN%
set VRAY_FOR_MAYA%MAYAVER%_PLUGINS_x64=%VRAY_MAIN%\Vrayplugins
set VRAY_AUTH_CLIENT_FILE_PATH=%VRAY_MAIN%\conf
set VRAY_PLUGINS_x64=%VRAY_MAIN%\vrayplugins
set VRAY_TOOLS_MAYA%MAYAVER%_x64=%VRAY_MAIN%\bin
set LM_LICENSE_FILE=@scholar-lic01;@scholar-lic02
set RLM_LICENSE=4101@scholar-lic01

echo Running \\scholar\pipeline\bin\external\maya\modules\vrayformaya\%VRAYVER%\win\%MAYAVER%\bin\vray.exe...
\\scholar\pipeline\bin\external\maya\modules\vrayformaya\%VRAYVER%\win\%MAYAVER%\bin\vray.exe -server -portNumber=20207

:end
exit