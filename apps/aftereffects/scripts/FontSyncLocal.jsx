var M_JOBNAME = null;
var M_TITLE = "GS Font Sync Utility"
var M_FONTINSTALLERLOC = "\\\\scholar\\code\\general\\scripts\\batch\\installFont.vbs";

function syncFonts(){
    if (M_JOBNAME){
        fontFolder = "\\\\scholar\\projects\\"+M_JOBNAME+"\\03_production\\04_elements\\03_fonts";
    } else {
        fontFolder = "\\\\scholar\\assets\\Fonts\\_fontinstaller";
    }
    cmd ='cscript '+M_FONTINSTALLERLOC+' '+fontFolder;
	var cmdOutput = system.callSystem(cmd);
	alert(cmdOutput,M_TITLE);
    return;    
}

function main(mainOBJ){
    if (app.project.file != null){
        M_PROJECTFILE = app.project.file.fsName;
        m = /(\\\\scholar\\projects\\)(.*?)\\/i.exec(app.project.file.fsName);
        if ( m ){ M_JOBNAME = m[2] };
    }else{
        alert("Please save or load a project",M_TITLE);
        return false;
    }
    if (system.osName == "MacOS") {
        alert("Mac OS X detected. This script only works on Windows.",M_TITLE)
        return false
    }
    
    syncFonts();
}

main(this)