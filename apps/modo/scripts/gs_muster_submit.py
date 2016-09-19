# python

import os
import sys
import re
import time
import getopt
import json

import lx, modo
scene = modo.scene.Scene()

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/code'

sys.path.append(os.path.join(GSCODEBASE, 'general', 'scripts', 'python'))
import gs
from gs import muster

MUSTER_POOLS = []

#FORMATS = ['$Targa', 'BMP', 'COLLADA_141', 'DXF', 'HDR', 'JPG', 'LayeredPSD', 'PNG', 'PNG16', 'PSD', 'PSDScene', 'SGI', 'SVG_SceneSaver', 'TIF', 'TIF16', 'TIF16BIG', 'openexr', 'openexr_32', 'openexr_tiled16', 'openexr_tiled32', 'openexrlayers', 'openexrlayers32']
FORMATS_DICT = {
    'TIF (16-bit)':'TIF16',
    'EXR (Scanline)':'openexr',
    'EXR (Tiled)':'openexr_tiled16',
    'EXR (Layered)':'openexrlayers',
    'JPG': 'JPG',
    'Layered PSD': 'LayeredPSD',
    'PNG':'PNG',
    'SGI':'SGI',
    'TGA':'$Targa'
}

FORMATS = [
    'TIF (16-bit)',
    'SGI',
    'EXR (Scanline)',
    'EXR (Tiled)',
    'EXR (Layered)',
    'PNG',
    'TGA',
    'JPG',
    'Layered PSD'
]

ITYPES = [
    lx.symbol.sITYPE_VIDEOCLIP,
    lx.symbol.sITYPE_VIDEOSEQUENCE,
    lx.symbol.sITYPE_VIDEOSTILL,
    lx.symbol.sITYPE_AUDIOFILE,
    lx.symbol.sITYPE_PHOTOMETRYLIGHT
]

def save_render_file(cur_file):
    tstamp = str(int(time.time()))
    fdir,fname = os.path.split(cur_file)
    fnamebase, ext = os.path.splitext(fname)

    newdir = '%s/_musterfiles' %(fdir)

    if not os.path.exists(newdir):
        os.makedirs(newdir)

    newname = '%s/%s_%s%s' %(newdir,fnamebase,tstamp,ext)

    lx.eval('scene.saveAs "%s"' %(newname))
    return newname

def submit():
    cur_file = scene.filename
    if cur_file:
        new_file = save_render_file(cur_file)
        lx.eval('scene.saveAs "%s"' %(cur_file))
        cur_file_path, cur_file_name = os.path.split(cur_file)

        version = os.path.split(lx.eval('query platformservice path.path ? program'))[1]
        majorver,minorver = version.split('_')
        
        poolslistmodo = lx.eval('user.def muster.pools listnames ?').split(';')
        rendergroupsmodo = lx.eval('user.def muster.rgrp listnames ?').split(';')

        rendergroupselected = rendergroupsmodo[int(lx.eval('!user.value muster.rgrp ?'))]
        outputpathselected = lx.eval('!user.value muster.outputpath ?')
        fulloutputpathselected = os.path.join(outputpathselected, lx.eval('!user.value muster.outputfilename ?'))
        outputfileformatselected = FORMATS_DICT[FORMATS[int(lx.eval('user.value muster.outputfileformat ?'))]]

        musterflags = {}
        musterflags['-add']     = '-V %s -v %s --render \"-rendergroup \"%s\" -outputpath \"%s\" -format \"%s\"' %(majorver, minorver, rendergroupselected, fulloutputpathselected.replace('\\','/'), outputfileformatselected)
        musterflags['-e']       = '1004'
        musterflags['-n']       = cur_file_name
        musterflags['-parent']  = '33409'
        musterflags['-group']   = gs.get_project_from_path(new_file)
        musterflags['-pool']    = poolslistmodo[ int(lx.eval('user.value muster.pools ?' ))]
        musterflags['-sf']      = str(lx.eval('user.value muster.start ?'))
        musterflags['-ef']      = str(lx.eval('user.value muster.end ?'))
        musterflags['-bf']      = '1'
        musterflags['-pk']      = str(lx.eval('user.value muster.batch ?'))
        musterflags['-pr']      = str(lx.eval('user.value muster.priority ?'))
        musterflags['-f']       = '"%s"' %(new_file.replace('\\','/'))

        if gs.properties['location'] == 'NYC' and musterflags['-pool'] != 'WKSTN-NY':
            ascpupflags = {}
            ascpupflags['-e']       = '43'
            ascpupflags['-n']       = '%s Asset Upload' %(cur_file_name)
            ascpupflags['-parent']  = '33409'
            ascpupflags['-group']    = gs.get_project_from_path(new_file)
            ascpupflags['-pool']    = 'ASPERA'
            
            src = new_file.replace("\\", "/").replace(" ", "\ ").replace("//", "/")
            dest = os.path.split(src)[0]
            ascpupcmd = 'ascpgs render@nycbossman:%s %s;' %(src, dest)
            for r in get_upload_files():
                f = r.replace("\\","/").replace(" ", "\ ").replace("//","/")
                src = re.sub('%\d+d','*',f)
                dest = os.path.split(src)[0]
                ascpupcmd = ascpupcmd + 'ascpgs render@nycbossman:%s %s;' %(src, dest)
            outputfolder = outputpathselected.replace("\\","/").replace(" ", "\ ").replace("//","/")
            ascpupcmd = ascpupcmd + 'mkdir -p %s;' %(outputfolder)
            ascpupflags['-add'] = '-c \"%s\"' %(ascpupcmd)
            lx.out(ascpupflags)
            ascpupsubmit = muster.submit(ascpupflags)

            if ascpupsubmit:
                musterflags['-wait'] = ascpupsubmit
                rendersubmit = muster.submit(musterflags)
                if rendersubmit:
                    ascpdownflags = {}
                    ascpdownflags['-e']         = '43'
                    ascpdownflags['-n']         = '%s Render Download' %(cur_file_name)
                    ascpdownflags['-parent']    = '33409'
                    ascpdownflags['-group']      = gs.get_project_from_path(new_file)
                    ascpdownflags['-pool']      = 'ASPERA'
                    ascpdownflags['-wait']      = rendersubmit
                    
                    ascpdowncmd = ''
                    f = fulloutputpathselected.replace("\\","/").replace(" ", "\ ").replace("//","/")
                    src = '%s*' %(f).replace("\\","/").replace(" ", "\ ").replace("//","/")
                    dest = outputpathselected.replace("\\","/").replace(" ", "\ ").replace("//","/")
                    ascpdowncmd = ascpdowncmd + 'ascp -p -d -v -k 1 --remove-after-transfer -i ~/.ssh/id_rsa -l 1G %s render@nycbossman:%s;' %(src, dest)
                    ascpdownflags['-add'] = '-c \"%s\"' %(ascpdowncmd)
                    ascpdownsubmit = muster.submit(ascpdownflags)

                    if ascpdownsubmit:
                        lx.out('Jobs successfully submitted to Muster!')
                    else:
                        lx.out('There was an error submitting download job to Muster')
                else:
                    lx.out('There was an error submitting render job to Muster.')
            else:
                lx.out('There was an error submitting upload job to Muster.')
        else:
            rendersubmit = muster.submit(musterflags)
            if rendersubmit:
                lx.out('Job ID %s successfully submitted to Muster!' %(rendersubmit))
            else:
                lx.out('There was an error submitting your job to Muster.')
    else:
        lx.out('Save file before submitting.')
        exit()

def get_upload_files():
    files = []
    for itype in ITYPES:
        for item in scene.items(itype):
            f = item.channel('filename').get()
            files.append(f)
    dedupe_files = list(set(files))
    return dedupe_files

def get_render_groups():
    render_groups = [x.name for x in scene.renderPassGroups]
    return render_groups

def path_explorer(title='Choose a folder'):
    path = modo.dialogs.dirBrowse(title, lx.eval('!user.value muster.outputpath ?'))
    return path

def refresh_ui():
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

    poolslist = ''
    poolslistname = ''
    if MUSTER_POOLS:
        for i,p in enumerate(MUSTER_POOLS):
            poolslist = '%s%s;' %(poolslist, i)
            poolslistname = '%s%s;' %(poolslistname,p)
        lx.eval('user.def muster.pools list %s' %(poolslist))
        lx.eval('user.def muster.pools listnames "%s "' %(poolslistname))

    render_groups = get_render_groups()
    if not render_groups: render_groups = ['']
    rgrplist = ''
    rgrplistname = ''
    if render_groups:
        for i,r in enumerate(render_groups):
            rgrplist = '%s%s;' %(rgrplist, i)
            rgrplistname = '%s%s;' %(rgrplistname, r)
        lx.eval('user.def muster.rgrp list %s' %(rgrplist))
        lx.eval('user.def muster.rgrp listnames "%s "' %(rgrplistname))

    formatlist = ''
    formatlistname = ''
    for i,f in enumerate(FORMATS):
        formatlist = '%s%s;' %(formatlist, i)
        formatlistname = '%s%s;' %(formatlistname, f)
        lx.eval('user.def muster.outputfileformat list %s' %(formatlist))
        lx.eval('user.def muster.outputfileformat listnames "%s "' %(formatlistname)) 

def init_ui():
    try:
        lx.eval('!user.value muster.outputpath ?')
    except:
        lx.eval('user.defNew muster.outputpath string')

    lx.eval('user.defNew muster.outputfilename string temporary')

    lx.eval('user.defNew muster.outputfileformat integer temporary')

    lx.eval('user.defNew muster.rgrp integer temporary')

    lx.eval('user.defNew muster.pools integer temporary')
    lx.eval('user.defNew muster.poolsjson string temporary')

    lx.eval('user.defNew muster.priority integer temporary')
    lx.eval('user.def muster.priority max 100')
    lx.eval('user.def muster.priority min 1')
    lx.eval('user.value muster.priority 50')

    lx.eval('user.defNew muster.start integer temporary')
    lx.eval('user.value muster.start 0')

    lx.eval('user.defNew muster.end integer temporary')
    lx.eval('user.value muster.end 10')

    lx.eval('user.defNew muster.batch integer temporary')
    lx.eval('user.value muster.batch 1')

    refresh_ui()

def main():
    try:
        lx.eval('!user.defNew muster.initui integer temporary')
        lx.eval('user.value muster.initui 1')
        init_ui()
    except:
        refresh_ui()

try:
    arg = lx.args()[0]
    if arg == 'init_ui':
        init_ui()
    elif arg == 'refresh_ui':
        refresh_ui()
    elif arg == 'submit':
        submit()
    elif arg == 'outputpath':
        path = path_explorer('Choose an output folder...')
        if path: lx.eval('user.value muster.outputpath "%s"' %(path))
except:
    main()