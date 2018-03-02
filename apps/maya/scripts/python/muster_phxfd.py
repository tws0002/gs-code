import os
import re
import sys
import maya.cmds as cmds

try:
    GSCODEBASE = os.environ['GSCODEBASE']
except KeyError:
    GSCODEBASE = '//scholar/pipeline'

import gsstartup
from gsstartup import muster2

majorver = ''
minorver = ''

exePath = sys.argv[0]
m = re.search('Maya/(.*)/bin', exePath)
if m:
    fullver = m.group(1)
    n = re.search('(\d*)\.(\d*\.\d*)', fullver)
    if n:
        o = re.search('^5\.(\d*)', n.group(2))
        if o:
            majorver = n.group(1)+'.5'
            minorver = o.group(1)
        else:
            majorver = n.group(1)
            minorver = n.group(2)

window_height = 130
window_width = 230

top_margin = 10
left_margin = 10
line_height = 17
line_break = 10

col_1 = left_margin
col_2 = left_margin + 59
col_2_width = window_width - col_1 - col_2

row_1 = top_margin
row_2 = row_1 + line_height + line_break
row_3 = row_2 + line_height + line_break
row_4 = row_3 + line_height + line_break

def submit(window, simnode='', host='', priority='50'):
    file_name = cmds.file(q=1, sn=1)
    short_name = os.path.splitext(cmds.file(q=1, sn=1, shn=1))[0]
    job_name = '%s - %s' %(short_name, simnode)
    project_name = gsstartup.get_project_from_path(cmds.file(q=1, sn=1))
    launcher_path = '\\\\scholar\\pipeline\\base\\gs\\python\\launcher\\launcher.py'
    sim_cmd = '\\\"phxfdBatchSim(\\\\\\\"%s\\\\\\\")\\\"' %(simnode)
    print simnode, host, priority, job_name, project_name

    musterflags = {}
    if majorver and minorver:
        musterflags['-add']             = '%s --job %s --package maya --major %s --minor %s --render -r vray -preRender "%s" -noRender "%s"' %(launcher_path, project_name, majorver, minorver, sim_cmd, file_name)
    else:
        musterflags['-add']             = '%s --job %s --package maya --render -r vray -preRender "%s" -noRender "%s"' %(launcher_path, project_name, sim_cmd, file_name)

    musterflags['-e']               = '43'
    musterflags['-n']               = job_name
    musterflags['-pool']            = host
    musterflags['-parent']          = '33409'
    musterflags['-group']           = project_name
    musterflags['-pr']              = priority

    rendersubmit = muster2.submit(musterflags)
    if rendersubmit:
        cmds.confirmDialog(title='Submission successful.', message='Successfully submitted Job#%s to Muster.' %(rendersubmit), button='OK')
        cmds.deleteUI(window)
    else:
        cmds.confirmDialog(title='Submission failure.', message='Job failed to submit. Check Sript Editor window for details', button='OK')

def build_ui():
    simnodes = cmds.ls(type='PhoenixFDSimulator')

    window_name = 'muster_phoenixfd'
    window_title = 'Muster PhoenixFD Submitter'
    if cmds.window(window_name, q=1, exists=1):
        cmds.deleteUI(window_name)
    window = cmds.window(window_name, title=window_title)
    wrapper_form = cmds.formLayout(parent=window)
    main = cmds.formLayout(parent=wrapper_form)

    ctrl_simnode = cmds.optionMenu(l='Simulator:', parent=main, ann='Select simulator node.', w=col_2_width+col_2-left_margin)
    label_host = cmds.text(l='Host:', parent=main)
    ctrl_host = cmds.textField(tx='LAXFARM0000', w=col_2_width)
    label_priority = cmds.text(l='Priority:', parent=main)
    ctrl_priority = cmds.textField(tx='50', w=col_2_width)
    button_submit = cmds.button(l='Submit', w=window_width-2*col_2, h=line_height+line_break, parent=main,
        c=lambda *x: submit(window=window, 
                simnode = cmds.optionMenu(ctrl_simnode, q=1, v=1),
                host = cmds.textField(ctrl_host, q=1, tx=1),
                priority = cmds.textField(ctrl_priority, q=1, tx=1)
                )
    )

    for s in simnodes:
        cmds.menuItem(label=s)
    cmds.formLayout(main, e=1, attachForm=[
        (ctrl_simnode, 'top', row_1),
        (ctrl_simnode, 'left', col_1),
        (label_host, 'top', row_2 + 4),
        (label_host, 'left', col_1),
        (ctrl_host, 'top', row_2),
        (ctrl_host, 'left', col_2),
        (label_priority, 'top', row_3 + 4),
        (label_priority, 'left', col_1),
        (ctrl_priority, 'top', row_3),
        (ctrl_priority, 'left', col_2),
        (button_submit, 'top', row_4),
        (button_submit, 'left', col_2),
        ])

    cmds.showWindow(window)
    cmds.window(window, e=1, w=window_width, h=window_height)