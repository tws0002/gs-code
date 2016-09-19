# Philippe HUBERDEAU (philpma@free.fr)
#
# Python script to create windows Batch file to launch Nuke renders by command line. It's less memory consuming
# Plus some options like :
# render "frame by frame" which allows to flush properly the memory for each frame. Some comps (same thing with Eyeon Fusion) tends to increase rendering time all along the process.
# "skip existing frame" for deleted bug frames or deleted modified frames to avoid complicated frameranges.

# These scripts are inspired from Tim BOWMAN's "bgNukes" and Jep HILL's "skip existing renders" scripts .
#

# From Python
import os, sys, shutil, string
import subprocess
# From Nuke
import nuke, nukescripts

if __name__ == "__main__":
    if len ( sys.argv ) != 5:
      print 'Usage: NUKE renderWskipExistingFrame.py <nuke_script> <write name> <frame number> <views>'
      sys.exit(-1)
    comp = sys.argv[1]
    write = sys.argv[2]
    framenum = sys.argv[3]
    views = sys.argv[4]
    nuke.scriptOpen( comp )
    filepath = nuke.toNode(write)['file'].value()
    padding = int(filepath.split("%0")[1][0])
    for i in range(padding-len(framenum)):
        framenum = "0" + framenum
    for view in views.split(","):
        image = (filepath.replace("%04d", framenum)).replace("%V", view).replace("%v", view)
        tmpImage = image + ".tmp"
        if not (os.path.exists(image) or os.path.exists(tmpImage)):
            print image + " doesn't exist so rendering this frame.........................................................."
            nuke.execute( write, int(framenum), int(framenum), 1, [view])
        else:
            print "\n"
            print image + " : already exists ... skipping..."

def CLrender(nodes=[]):
    """
    Creates command-line Nuke batch file with different control parameters (frame by frame, skip existing frame, Stereo)
    """
    
    if nuke.root().knob('name').value() == '':
        nuke.message('This script is not named. Please save it and try again.')
        return
    nodelist = ''
    if nodes != []:
        nodelist = ','.join([n.name() for n in nodes if n.Class() == "Write"])
    else:
        Writes = nuke.allNodes("Write")
        if len(Writes)==1:
            nodelist = Writes[0].name()
    if nodelist == "":
        nuke.message("Please select Write node(s) !")
        return
    
    class CLrenderDialog(nukescripts.PythonPanel):
        def __init__(self):
            nukescripts.PythonPanel.__init__(self, 'Create rendering command line batch file(s) -- (philhub 2011)')
            self.setMinimumSize(600, 300)
            self.nodesKnob = nuke.String_Knob('nodesExec', 'Node(s) to execute:', nodelist)
            self.addKnob(self.nodesKnob)
            self.startKnob = nuke.Int_Knob('startFrame', 'Start frame :')
            self.addKnob(self.startKnob)
            self.endKnob = nuke.Int_Knob('endFrame', ' End frame :')
            self.addKnob(self.endKnob)
            self.endKnob.clearFlag(nuke.STARTLINE)
            self.spaceKnob = nuke.Text_Knob('space', '')
            self.addKnob(self.spaceKnob)
            self.spaceKnob.setFlag(nuke.STARTLINE)
            
            self.limitKnob = nuke.Boolean_Knob('limit', 'Limit Memory to (Go)')
            self.addKnob(self.limitKnob)
            self.limitKnob.setFlag(nuke.STARTLINE)
            self.memKnob = nuke.Int_Knob('mem', '')
            self.addKnob(self.memKnob)
            self.memKnob.clearFlag(nuke.STARTLINE)
            # self.unitKnob = nuke.Text_Knob('unit', 'Go')
            # self.addKnob(self.unitKnob)
            # self.unitKnob.clearFlag(nuke.STARTLINE)
            
            self.limitcpuKnob = nuke.Boolean_Knob('limitcpu', 'Limit Cores to')
            self.addKnob(self.limitcpuKnob)
            self.limitcpuKnob.clearFlag(nuke.STARTLINE)
            self.cpuKnob = nuke.Int_Knob('cpu', '')
            self.addKnob(self.cpuKnob)
            self.cpuKnob.clearFlag(nuke.STARTLINE)
            
            self.spaceKnob2 = nuke.Text_Knob('space2', '')
            self.addKnob(self.spaceKnob2)
            self.spaceKnob2.setFlag(nuke.STARTLINE)
            
            self.threadsKnob = nuke.Int_Knob('threads', 'Number of BAT files :')
            self.addKnob(self.threadsKnob)
            self.threadsKnob.setFlag(nuke.STARTLINE)
            self.threadWhyKnob = nuke.Text_Knob('threadWhy', '(to distrib on multiple cores/boxes)')
            self.addKnob(self.threadWhyKnob)
            self.threadWhyKnob.clearFlag(nuke.STARTLINE)
            self.fbfKnob = nuke.Boolean_Knob('fbf', 'Frame by Frame ?  (to avoid some insanes increasing render time)')
            self.addKnob(self.fbfKnob)
            self.fbfKnob.setFlag(nuke.STARTLINE)
            self.skipKnob = nuke.Boolean_Knob('skip', 'Skip existing Frames ?')
            self.addKnob(self.skipKnob)
            self.skipKnob.setFlag(nuke.STARTLINE)
            self.stereoKnob = nuke.Boolean_Knob('stereo', 'Stereo ?')
            self.addKnob(self.stereoKnob)
            self.stereoKnob.setFlag(nuke.STARTLINE)
            self.backupKnob = nuke.Boolean_Knob('backup', "Create a comp's backup ? (and renders from it)")
            self.addKnob(self.backupKnob)
            self.openFolderKnob = nuke.Boolean_Knob('openFolder', "open folder ?")
            self.addKnob(self.openFolderKnob)
	    self.openFolderKnob.setFlag(nuke.STARTLINE)
            self.spaceKnob2 = nuke.Text_Knob('space', '')
            self.addKnob(self.spaceKnob2)
            self.spaceKnob2.setFlag(nuke.STARTLINE)
            self.backupKnob.setFlag(nuke.STARTLINE)
            self.okButton = nuke.Script_Knob( "OK" )
            self.addKnob( self.okButton )
            self.okButton.setFlag(nuke.STARTLINE)
            self.cancelButton = nuke.Script_Knob( "Cancel" )
            self.addKnob( self.cancelButton )
            self.infosKnob = nuke.PyScript_Knob('infos', "infos")
            self.infosKnob.setCommand('''import webbrowser
webbrowser.open("http://www.nukepedia.com/python/render/cmdlinerender/")''')
            self.addKnob(self.infosKnob)

    p = CLrenderDialog()
    
    p.startKnob.setValue(int(nuke.knob("first_frame")))
    p.endKnob.setValue(int(nuke.knob("last_frame")))
    p.memKnob.setValue(8)
    p.cpuKnob.setValue(2)
    p.threadsKnob.setValue(1)
    p.fbfKnob.setValue(1)
    p.skipKnob.setValue(0)
    p.stereoKnob.setValue(0)
    p.backupKnob.setValue(1)
    p.openFolderKnob.setValue(1)
    
    result = p.showModalDialog()
    
    if not result: return
    nuke.scriptSave('')
    start = p.startKnob.value()
    end = p.endKnob.value()
    threads = p.threadsKnob.value()
    mem = p.memKnob.value()
    cpu = p.cpuKnob.value()
    fbf = p.fbfKnob.value()
    skip = p.skipKnob.value()
    stereo = p.stereoKnob.value()
    if threads < 1: 
        return
    flags = "-x "
    if stereo:
        views = ','.join(nuke.views())
    else:
        views =  nuke.views()[0]
    flags += " -view " + views
    
    if nodelist != '':
        flags += " -X " + nodelist
        if p.limitKnob.value():
            flags +=   " -c " + str(mem) + "G"
        if p.limitcpuKnob.value():
            flags +=   " -m " + str(cpu)
    comp_dirpath = nuke.value("root.name")
    exe = '"'+nuke.env['ExecutablePath']+'"'        # for BAT file, " avoid error with names with spaces
    
    if p.backupKnob.value():
        bkp_dirpath = os.path.dirname(comp_dirpath) + '/backup_from_CLrender/'
        if not os.path.exists(bkp_dirpath):
            os.makedirs(bkp_dirpath)
        bkp_filepath = bkp_dirpath + os.path.basename(comp_dirpath)
        shutil.copy(comp_dirpath, bkp_filepath)
        comp_dirpath = '"' + bkp_filepath + '"'   # for BAT file, " avoid error with names with spaces
    else:
        comp_dirpath = '"' + comp_dirpath + '"'   # for BAT file, " avoid error with names with spaces
        
    for thread in range(threads):
    
        bat_name = nuke.value("root.name").replace('.nk', '_' + nodelist.replace(",","-") + "_x"+ str(threads)  + "x"  + str(start+ thread) + "-" + str(end)+ '.bat')
        if fbf and not(skip):
            cmd = r"FOR /l %%I IN (" + ",".join([str(start + thread), str(threads), str(end)]) + r") DO (" + " ".join([exe, flags, r"-F %%I-%%I", comp_dirpath]) + ")"
            bat_name = bat_name.replace('.bat', '_FrameByFrame.bat')
        elif skip:
            cmd = r"FOR /l %%I IN (" + ",".join([str(start + thread), str(threads), str(end)]) + r") DO (" + " ".join([exe, "-t", os.path.realpath( __file__ ), comp_dirpath, nodelist, "%%I", views]) + ")"
            bat_name = bat_name.replace('.bat', '_SkipExisting.bat')
        else:
            cmd = " ".join([exe, flags, '-F', '"' + str(start+ thread) + "-" + str(end) + 'x' + str(threads) + '"', comp_dirpath ])

        if stereo:
            bat_name = bat_name.replace('.bat', '_STEREO.bat')

        print "command : " + cmd
        print  "saved to : " + bat_name

        try:
            file = open(bat_name, 'w')
            #file.write("mode con cols=500 lines=500")
            file.write("\nCOLOR 4f\n")
            file.write("\n")
            file.write(cmd)
            file.write("\n\nCOLOR 2f\n")
            file.write("pause")
        finally:
            file.close()
    if p.openFolderKnob.value():
        openCompFolder()
            
def openCompFolder():
    path = nuke.tcl("return [file dirname [value root.name]]")
    cmd = "explorer " + (path.replace("//","/")).replace("/","\\")
    os.system(cmd)

'''
menubar = nuke.menu('Nuke')
m =  menubar.addMenu('Nukepedia')
m.addCommand('CL Render', 'CmdLineRender.CLrender(nuke.selectedNodes())')
'''