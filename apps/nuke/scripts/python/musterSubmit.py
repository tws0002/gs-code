import os
import sys
import subprocess
import re 
import time
import json

import nuke
import nukescripts

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/pipeline'

sys.path.append(os.path.join(GSCODEBASE, 'general', 'scripts', 'python'))
import gsstartup
from gsstartup import muster

MUSTER_POOLS = []
m = re.search('^(.*)v(.*)',nuke.NUKE_VERSION_STRING)
majorver = m.group(1)
minorver = m.group(2)



try:
    PROJ_NAME = os.environ['GSPROJECT']
except KeyError:
    PROJ_NAME = ""

def nuke_ui():       
    allWriteNodes = [node for node in nuke.allNodes() if node.Class() == 'Write' or node.Class() == 'DeepWrite']
    
    panel = nuke.Panel( 'GS Render Submit' )
    panel.addSingleLineInput( 'Project', PROJ_NAME)
    panel.addSingleLineInput( 'Job Name', os.path.splitext(os.path.split(nuke.value('root.name'))[1])[0] )
    if gsstartup.properties['location'] == 'NYC':
        panel.addBooleanCheckBox( 'Use LA Render Farm', 0 )
    panel.addSingleLineInput( 'Frame Range', '%s-%s' %(nuke.knob('first_frame'),nuke.knob('last_frame')) )
    panel.addSingleLineInput( 'Packet Size', 5 )
    panel.addSingleLineInput( 'Priority (1-100)', 50 )
    for n in allWriteNodes:
        k = panel.addBooleanCheckBox( n.name(), n.isSelected() )
    panel.setWidth(300)
    panel.addButton('Cancel')
    panel.addButton('Submit')
    result = panel.show()
    
    selected_write_nodes = [n for n in allWriteNodes if panel.value(n.name())]
    selected_write_nodes_string = ','.join([n.name() for n in selected_write_nodes])

    if result and check_saved()==1 and check_write_selected(selected_write_nodes_string)==1:
        newfile = save_render_file()
        framerange = [int(value) for value in re.sub('[^0-9]',',',panel.value('Frame Range')).split(',')]
        
        musterflags = {}
        musterflags['-add']     = '--major %s  --job %s -X \"%s\"' %(nuke.NUKE_VERSION_STRING,panel.value('Project'), selected_write_nodes_string)
        musterflags['-e']       = '1105'
        musterflags['-n']       = panel.value('Job Name')
        musterflags['-parent']  = '33409'
        musterflags['-group']    = gsstartup.get_project_from_path(newfile)
        try:
            if panel.value('Use LA Render Farm') or gsstartup.properties['location'] == 'LAX':
                musterflags['-pool']    = 'NUKE'
            else:
                musterflags['-pool']    = 'WKSTN-NY'
        except:
            musterflags['-pool']    = 'NUKE'
        musterflags['-sf']      = str(framerange[0])
        musterflags['-ef']      = str(framerange[1])
        musterflags['-bf']      = len(framerange) > 2 and str(framerange[2]) or '1'
        musterflags['-pr']      = panel.value('Priority (1-100)')
        musterflags['-f']       = newfile
                
        for n in selected_write_nodes:
            if n.knob('file_type').value() in ['mov']:
                musterflags['-pk'] = '999999'
                break
            else:   
                musterflags['-pk'] = panel.value('Packet Size')

        if gsstartup.properties['location'] == 'NYC' and musterflags['-pool'] != 'WKSTN-NY':
            newfileup = newfile.replace("\\", "/").replace(" ", "\ ").replace("//","/")
            newfiledest = os.path.split(newfileup)[0].replace("\\", "/").replace(" ", "\ ").replace("//","/")
            ascpupcmd = 'ascpgs render@nycbossman:%s %s;' %(newfileup, newfiledest)
            
            ascpupflags = {}
            ascpupflags['-e']       = '43'
            ascpupflags['-n']       = '%s Asset Upload' %(panel.value('Job Name'))
            ascpupflags['-parent']  = '33409'
            ascpupflags['-group']    = gsstartup.get_project_from_path(newfile)
            ascpupflags['-pool']    = 'ASPERA'
            
            for r in get_read_nodes():
                #src = re.sub('%\d+d','*', r).replace("\\", "/").replace(" ", "\ ").replace("//","/")
                src = os.path.split(r)[0].replace("\\", "/").replace(" ", "\ ").replace("//","/")
                dest = os.path.split(src)[0].replace("\\", "/").replace(" ", "\ ").replace("//","/")
                ascpupcmd = ascpupcmd + 'ascpgs render@nycbossman:%s %s;' %(src, dest)

            for w in selected_write_nodes:
                f = w.knob('file').value()
                dest = os.path.split(f)[0].replace("\\", "/").replace(" ", "\ ").replace("//","/")
                ascpupcmd = ascpupcmd + 'mkdir -p %s;' %(dest)

            ascpupflags['-add'] = '-c \"%s\"' %(ascpupcmd)
            ascpupsubmit = muster.submit(ascpupflags)

            if ascpupsubmit:
                musterflags['-wait'] = ascpupsubmit
                rendersubmit = muster.submit(musterflags)
                if rendersubmit:
                    ascpdownflags = {}
                    ascpdownflags['-e']         = '43'
                    ascpdownflags['-n']         = '%s Render Download' %(panel.value('Job Name'))
                    ascpdownflags['-parent']    = '33409'
                    ascpdownflags['-group']      = gsstartup.get_project_from_path(newfile)
                    ascpdownflags['-pool']      = 'ASPERA'
                    ascpdownflags['-wait']      = rendersubmit
                    
                    ascpdowncmd = ''
                    for w in selected_write_nodes:
                        f = w.knob('file').value()
                        src = re.sub('%\d+d','*',f).replace("\\", "/").replace(" ", "\ ").replace("//","/")
                        dest = os.path.split(f)[0].replace("\\", "/").replace(" ", "\ ").replace("//","/")
                        #ascpdowncmd = ascpdowncmd + 'ascp -p -d -v -k 1 --remove-after-transfer -i ~/.ssh/id_rsa -l 1G %s render@nycbossman:%s;' %(src, dest)
                        ascpdowncmd = ascpdowncmd + 'ascpgs %s render@nycbossman:%s;' %(src, dest)
                    ascpdownflags['-add'] = '-c \"%s\"' %(ascpdowncmd)
                    ascpdownsubmit = muster.submit(ascpdownflags)

                    if ascpdownsubmit:
                        nuke.message('Jobs successfully submitted to Muster!')
                    else:
                        print 'There was an error submitting download job to Muster'
                else:
                    print 'There was an error submitting render job to Muster.'
            else:
                print 'There was an error submitting upload job to Muster.'
        else:
            rendersubmit = muster.submit(musterflags)
            if rendersubmit:
                nuke.message('Job ID#%s successfully submitted to Muster!' %(rendersubmit))
            else:
                print 'There was an error submitting render job to Muster.'
    else:
        print 'Cancelled Muster Render'


def get_read_nodes():
    all_read_nodes = [node for node in nuke.allNodes() if node.Class() == 'Read']
    all_read_nodes_files = []
    for n in all_read_nodes:
        if n.dependent() or n.dependencies():
            knob = n.knob('file')
            file = knob.value()
            if file: all_read_nodes_files.append(file)
        else:
            continue
    return all_read_nodes_files

def check_saved():
    if nuke.root().name() == 'Root':
        r = nuke.ask("Script must be saved to continue.\nSave now?")
        if r:
            nuke.scriptSaveAs()
            save_render_file()
            return 1
        else:
            return 0
    elif nuke.root().modified():
        r = nuke.ask("There are unchanged changes to the script.\nSave now?")
        if r:
            save_render_file()
            return 1
        else:
            return 0
    else:
        return 1

def save_render_file():
    cur_script = nuke.root().name()

    tstamp = str(int(time.time()))
    cur_file = nuke.root().name()
    fdir,fname = os.path.split(cur_file)
    fnamebase, ext = os.path.splitext(fname)

    newdir = '%s/_musterfiles' %fdir

    if not os.path.exists(newdir):
        os.makedirs(newdir)

    newname = '%s/%s_%s%s' %(newdir,fnamebase,tstamp,ext)

    nuke.scriptSaveAs(newname, 1)
    nuke.scriptSaveAs(cur_script, 1)
    return newname

def check_write_selected(selected_write_nodes):
    if selected_write_nodes:
        return 1
    else:
        nuke.message("No write nodes selected.")
        return 2

def main():
    global MUSTER_POOLS

    try:
        if os.path.getmtime(muster.MUSTERJSON) > time.time() - 60*5:    
            with open(muster.MUSTERJSON, 'r') as f:
                muster_json = json.load(f)
                MUSTER_POOLS = muster_json['pools']
        else:
            MUSTER_POOLS = muster.get_pools()
    except WindowsError:
        MUSTER_POOLS = muster.get_pools()

    nuke_ui()

if __name__ == '__main__':
    main()