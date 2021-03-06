set "ST_C4D=R18"
set "GSBRANCH=//scholar/pipeline/base"
set "GSROOT=//scholar/pipeline/"
set "C4D_PLUGINS_DIR='%C4D_PLUGINS_DIR%;%GSROOT%/base/apps/cinema4d/scripts/python"
set "C4D_BROWSERLIBS='%C4D_BROWSERLIBS%;%GSROOT%/bin/external/cinema4d/browserlib/%ST_C4D%"

set "ST_C4D_REDSHIFT=2.5.13"
set "REDSHIFT_COREDATAPATH=%GSROOT%/bin/external/cinema4d/plugins/redshift/%ST_C4D_REDSHIFT%/%ST_C4D%/core"
set "REDSHIFT_LOCALDATAPATH=%GSROOT%/bin/external/cinema4d/plugins/redshift/%ST_C4D_REDSHIFT%/%ST_C4D%/core"
set "REDSHIFT_PLUG_IN_PATH=%GSROOT%/bin/external/cinema4d/plugins/redshift/%ST_C4D_REDSHIFT%/%ST_C4D%"
set "C4D_PLUGINS_DIR=%C4D_PLUGINS_DIR%;%GSROOT%/bin/external/cinema4d/plugins/redshift/%ST_C4D_REDSHIFT%/%ST_C4D%"
set "PATH=%PATH%;%REDSHIFT_COREDATAPATH%/bin"

set "ST_C4D_OCTANE=3.05.3"
set "C4D_PLUGINS_DIR=%"C4D_PLUGINS_DIR%;%GSROOT%/bin/external/cinema4d/plugins/c4doctane/%ST_C4D_OCTANE%/%ST_C4D%"
set "ST_C4D_XPART=3.5.0391"
set "C4D_PLUGINS_DIR=%"C4D_PLUGINS_DIR%;%GSROOT%/bin/external/cinema4d/plugins/x-particles/%ST_C4D_XPART%/%ST_C4D%"
set "ST_QCMDS=0.21"
set "C4D_PLUGINS_DIR=%"C4D_PLUGINS_DIR%;%GSROOT%/bin/external/cinema4d/plugins/qcmds/%ST_QCMDS%/%ST_C4D%"

C:\"Program Files"\Maxon\Cinema4D\R18.039\"CINEMA 4D.exe"