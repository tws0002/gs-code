set GSBRANCH=//scholar/pipeline/base
set RLM_LICENSE=4101@laxlic01
set NUKE_PATH=%GSBRANCH%/apps/nuke/startup
set NUKE_DISK_CACHE=C:\Temp\Nuke_Cache
set NUKE_TEMP_DIR=C:\Temp\Nuke
set PYTHONPATH=%PYTHONPATH%;%GSBRANCH%/apps/nuke/scripts/python;%GSBRANCH%/gs/python
if not exist "C:\Temp\Nuke_Cache" mkdir C:\Temp\Nuke_Cache
if not exist "C:\Temp\Nuke" mkdir C:\Temp\Nuke
C:\"Program Files"\Foundry\Nuke\10.0v5\Nuke10.0.exe --nukex
