import os
import sys
import subprocess
import time
import c4d
from c4d import gui, plugins, bitmaps, documents

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/code'
GSTOOLS = os.path.join(GSCODEBASE,'tools')
GSBIN = os.path.join(GSCODEBASE,'bin')

sys.path.append(os.path.join(GSTOOLS, 'general', 'scripts', 'python'))
import gs
from gs import muster

MUSTER_POOLS = []
PLUGIN_ID = 1000000 # Test ID

SEL_POOL_ID = 10001
JOB_NAME_ID = 10002
FRAME_START_ID = 10003
FRAME_END_ID = 10004
PACKET_SZ_ID = 10005
PRIORITY_ID = 10006
SUBMIT_BUTTON = 20001

class SubmitDialog(gui.GeDialog):
    def CreateLayout(self): #main dialog
        self.SetTitle('GS Muster Submitter')

        self.GroupBegin(id=1000, flags=c4d.BFH_SCALEFIT, cols=2)

        self.AddStaticText(id=1001, flags=c4d.BFH_LEFT, name='Pools')
        self.AddComboBox(SEL_POOL_ID, c4d.BFH_SCALEFIT, 100, 0)
        for i in range(len(MUSTER_POOLS)):
            child_id = 100100 + i
            self.AddChild(id=SEL_POOL_ID, subid=child_id, child=MUSTER_POOLS[i])
            if MUSTER_POOLS[i] == 'CINEMA4D':
                self.SetLong(SEL_POOL_ID, child_id)

        self.AddStaticText(id=1002, flags=c4d.BFH_LEFT, name='Job Name')
        self.AddEditText(JOB_NAME_ID, c4d.BFH_SCALEFIT, 100, 0)
        self.SetString(JOB_NAME_ID, get_job_name())
        self.AddStaticText(id=1003, flags=c4d.BFH_LEFT, name='Start Frame')
        self.AddEditNumber(FRAME_START_ID, c4d.BFH_SCALEFIT, 100, 0)
        self.SetInt32(FRAME_START_ID, get_frame_range()[0])
        self.AddStaticText(id=1004, flags=c4d.BFH_LEFT, name='End Frame')
        self.AddEditNumber(FRAME_END_ID, c4d.BFH_SCALEFIT, 100, 0)
        self.SetInt32(FRAME_END_ID, get_frame_range()[1])
        self.AddStaticText(id=1005, flags=c4d.BFH_LEFT, name='Packet Size')
        self.AddEditNumber(PACKET_SZ_ID, c4d.BFH_SCALEFIT, 100, 0)
        self.SetInt32(PACKET_SZ_ID, 1)
        self.AddStaticText(id=1006, flags=c4d.BFH_LEFT, name='Priority (1-100)')
        self.AddEditNumber(PRIORITY_ID, c4d.BFH_SCALEFIT, 100, 0)
        self.SetInt32(PRIORITY_ID, 50)
        self.GroupEnd()

        self.GroupBegin(id=2000, flags=c4d.BFH_SCALEFIT, cols=1)
        self.AddButton(SUBMIT_BUTTON, c4d.BFV_MASK, initw=100, name='Submit')
        self.GroupEnd()

        return True

    def Command(self, id, msg):
        if (id == SUBMIT_BUTTON):
            pool = MUSTER_POOLS[self.GetInt32(SEL_POOL_ID)-100100]
            job_name = self.GetString(JOB_NAME_ID)
            frame_start = self.GetString(FRAME_START_ID)
            frame_end = self.GetString(FRAME_END_ID)
            packet_sz = self.GetString(PACKET_SZ_ID)
            priority = self.GetString(PRIORITY_ID)

            cur_file = get_cur_file()
            if cur_file:
                new_file = save_render_file(cur_file)
                cur_file_path, cur_file_name = os.path.split(cur_file)

                c4d_ver = str(c4d.GetC4DVersion())
                majorver = 'R%s' %(c4d_ver[0:2])
                minorver = c4d_ver[2:len(c4d_ver)]

                musterflags = {}
                musterflags['-add']     = '-V %s -v %s --render \"' %(majorver, minorver)
                musterflags['-e']       = '1007'
                musterflags['-n']       = os.path.splitext(cur_file_name)[0]
                musterflags['-parent']  = '33409'
                musterflags['-group']   = gs.get_project_from_path(new_file)
                musterflags['-pool']    = pool
                musterflags['-sf']      = frame_start
                musterflags['-ef']      = frame_end
                musterflags['-bf']      = '1'
                musterflags['-pk']      = packet_sz
                musterflags['-pr']      = priority
                musterflags['-f']       = '%s' %(new_file.replace('\\','/'))

                if gs.properties['location'] == 'NYC' and musterflags['-pool'] != 'WKSTN-NY':
                    ascpupflags = {}
                    ascpupflags['-e']       = '43'
                    ascpupflags['-n']       = '%s: Asset Upload' %(cur_file_name)
                    ascpupflags['-parent']  = '33409'
                    ascpupflags['-group']    = gs.get_project_from_path(new_file)
                    ascpupflags['-pool']    = 'ASPERA'
                    
                    src = new_file.replace("\\", "/").replace(" ", "\ ").replace("//", "/")
                    dest = os.path.split(src)[0]
                    outputpathselected = get_output_path()
                    ascpupcmd = 'ascp -p -d -v -k 1 -i ~/.ssh/id_rsa -l 1G render@nycbossman:%s %s;' %(src, dest)
                    ascpupcmd = ascpupcmd + 'mkdir -p %s' %(outputpathselected.replace("\\","/").replace(" ", "\ ").replace("//","/"))
                    ascpupflags['-add'] = '-c \"%s\"' %(ascpupcmd)
                    ascpupsubmit = muster.submit(ascpupflags)

                    if ascpupsubmit:
                        musterflags['-wait'] = ascpupsubmit
                        rendersubmit = muster.submit(musterflags)
                        if rendersubmit:
                            ascpdownflags = {}
                            ascpdownflags['-e']         = '43'
                            ascpdownflags['-n']         = '%s: Render Download' %(cur_file_name)
                            ascpdownflags['-parent']    = '33409'
                            ascpdownflags['-group']      = gs.get_project_from_path(new_file)
                            ascpdownflags['-pool']      = 'ASPERA'
                            ascpdownflags['-wait']      = rendersubmit
                            
                            ascpdowncmd = ''
                            f = outputpathselected.replace("\\","/").replace(" ", "\ ").replace("//","/")
                            src = '%s/*' %(f)
                            dest = f
                            ascpdowncmd = ascpdowncmd + 'ascp -p -d -v -k 1 --remove-after-transfer -i ~/.ssh/id_rsa -l 1G %s render@nycbossman:%s;' %(src, dest)
                            ascpdownflags['-add'] = '-c \"%s\"' %(ascpdowncmd)
                            ascpdownsubmit = muster.submit(ascpdownflags)

                            if ascpdownsubmit:
                                message = 'Jobs successfully submitted to Muster!'
                            else:
                                message = 'There was an error submitting download job to Muster'
                        else:
                            message = 'There was an error submitting render job to Muster.'
                    else:
                        message = 'There was an error submitting upload job to Muster.'
                else:
                    rendersubmit = muster.submit(musterflags)
                    if rendersubmit:
                        message = 'Job ID %s successfully submitted to Muster!' %(rendersubmit)
                    else:
                        message = 'There was an error submitting your job to Muster.'
            else:
                message = 'Save file before submitting.'

            notify = NotificationDialog()
            notify.message = message
            notify.Open(dlgtype=c4d.DLG_TYPE_MODAL, defaultw=200, defaulth=150, xpos=-1, ypos=-1)
            self.Close()
            return True
        return True

class NotificationDialog(gui.GeDialog):
    message = ''

    def CreateLayout(self):
        self.GroupBegin(id=3000, flags=c4d.BFH_SCALEFIT, cols=1)
        self.AddStaticText(id=3001, flags=c4d.BFH_SCALEFIT, initw=100, name=self.message)
        self.GroupEnd()

        self.GroupBegin(id=4000, flags=c4d.BFH_SCALEFIT, cols=1)
        self.AddButton(id=4001, flags=c4d.BFV_MASK, initw=100, name="OK")
        self.GroupEnd()
        return True

    def Command(self, id, msg):
        if (id == 4001):
            self.Close()
            return True
        return True

### Initialize #########################################################################################
class MyMenuPlugin(plugins.CommandData):
    dialog = None

    def Execute(self, doc):
        if self.dialog is None:
            self.dialog = SubmitDialog()
        return self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, pluginid=PLUGIN_ID, defaultw=200, defaulth=100, xpos=-1, ypos=-1)

    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = SubmitDialog()
        return self.dialog.Restore(pluginid=PLUGIN_ID, secret=sec_ref)

def get_job_name():
    doc = documents.GetActiveDocument()
    job_name = os.path.splitext(doc.GetDocumentName())[0]
    return job_name

def get_frame_range():
    doc = documents.GetActiveDocument()
    fps = doc.GetFps()
    frame_range = [int(doc.GetMinTime().GetFrame(fps)), int(doc.GetMaxTime().GetFrame(fps))]
    return frame_range

def get_cur_file():
    doc = documents.GetActiveDocument()
    cur_file_path = doc.GetDocumentPath()
    cur_file_name = doc.GetDocumentName()
    cur_file = os.path.join(cur_file_path, cur_file_name)
    return cur_file

def get_output_path():
    doc = documents.GetActiveDocument()
    rd = doc.GetActiveRenderData().GetData()
    output_reg_path = rd[c4d.RDATA_PATH]
    output_reg_dir = os.path.split(output_red_path)[0]
    #output_multi_path = rd[c4d.RDATA_MULTIPASS_FILENAME]
    #output_multi_dir = os.path.split(output_multi_path)[0]
    return output_reg_dir

def save_render_file(cur_file):
    doc = documents.GetActiveDocument()
    cur_file_path, cur_file_name = os.path.split(cur_file)
    fnamebase, ext = os.path.splitext(cur_file_name)
    newdir = '%s/_musterfiles' %(cur_file_path)
    if not os.path.exists(newdir):
        os.makedirs(newdir)

    tstamp = str(int(time.time()))
    render_file = '%s/%s_%s%s' %(newdir,fnamebase,tstamp,ext)
    documents.SaveDocument(doc, render_file, c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, c4d.FORMAT_C4DEXPORT)
    return render_file

if __name__ == '__main__':
    try:
        if os.path.getmtime(muster.MUSTERJSON) > time.time() - 60*5:
            with open(muster.MUSTERJSON, 'r') as f:
                muster_json = json.load(f)
                MUSTER_POOLS = muster_json['pools']
        else:
            MUSTER_POOLS = muster.get_pools()
    except WindowsError:
        MUSTER_POOLS = muster.get_pools()

    path, fn = os.path.split(__file__)
    bmp = bitmaps.BaseBitmap()
    bmp.InitWith(os.path.join(path, 'res/icons/', 'icon.tif'))

    okyn = plugins.RegisterCommandPlugin(PLUGIN_ID, 'GS Muster Submit', 0, bmp, 'Plug-in to submit render jobs to Muster.', MyMenuPlugin())

    if (okyn): print 'Initialized.'