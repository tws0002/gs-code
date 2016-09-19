@echo off

if not defined GSCODEBASE (
	set GSCODEBASE=//scholar/code
)
set GSTOOLS=%GSCODEBASE%\tools)
set GSBIN=%GSCODEBASE%\bin)

echo "Using %GSCODEBASE% as repository."
echo "Setting up Maya 2013 environment..."

set GSMAYA=%GSTOOLS%/maya
set GSMAYASCRIPT=%GSMAYA%/scripts
set GSMAYAMEL=%GSMAYASCRIPT%/mel

set PYTHONPATH=%GSMAYASCRIPT%;%GSMAYASCRIPT%/python;c:/Program Files/Autodesk/Maya2013/Python/Lib/site-packages
set MAYA_SHELF_PATH=%GSMAYA%/shelves/2013
set MAYA_SCRIPT_PATH=%GSMAYAMEL%;%GSMAYAMEL%/Modeling;%GSMAYAMEL%/Rigging;%GSMAYAMEL%/Scholar;%GSMAYAMEL%/Utility
set XBMLANGPATH=%GSMAYA%/icons
set MAYA_PRESET_PATH=%GSMAYA%/presets
set MAYA_PLUG_IN_PATH=%GSMAYA%/plug-ins/2013
set TEXTURES=//scholar/assets/3d/GLOBAL_TEXTURES
set LM_LICENSE_FILE=@scholar-lic01;@scholar-lic02
set RLM_LICENSE=4101@scholar-lic01


:: If -GSRENDER flag is specified, will launch Render.exe instead of maya.exe ::
if "%1"=="-GSRENDER" (
	goto launchmayarender
) else (
	goto launchmaya
)

:launchmayarender
:: Take parameters after -GSRENDER ::
SHIFT
set params=%1
:loop
SHIFT
if "%1" == "" goto endlaunchmayarender
set params=%params% %1
goto loop
:endlaunchmayarender
echo "Starting Maya 2013 Render."
if exist "C:\Program Files\Autodesk\Maya2013\bin\Render.exe" (
	"C:\Program Files\Autodesk\Maya2013\bin\Render.exe" %params%
) else (
	echo "Maya 2013 not installed on this computer"
	pause
)
goto end

:launchmaya
echo "Starting Maya 2013."
if exist "C:\Program Files\Autodesk\Maya2013\bin\maya.exe" (
	start "" "C:\Program Files\Autodesk\Maya2013\bin\maya.exe" %*
) else (
	echo "Maya 2013 not installed on this computer"
	pause
)
goto end

:end
exit