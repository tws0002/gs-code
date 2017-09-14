import nuke

toolbar = nuke.toolbar("Nodes")
m = toolbar.addMenu("Gentleman Scholar", icon="GentlemanScholar.png")

def add_gizmos_menu():
    var = os.environ.get('ST_NUKE_GIZMOS')
    gizmos = []
    if var != None:
        gizmos = var.split(';')
    for g in gizmos:
        gizmopath = os.path.expandvars(g)
        for path, dirs, files in os.walk(gizmopath):
            dirs.sort()
            files.sort()
            for f in files:
                if f.endswith(".gizmo"):
                    path = os.path.split(path)[1].replace("\\","/")
                    gizmo = f.replace(".gizmo","")
                    m.addCommand("Gizmos/%s/%s" %(path, gizmo), "nuke.createNode('%s')" %(f), icon="")

def set_default_values():
    #Set Random Custom Knob Defaults
    nuke.knobDefault('Roto.output', 'alpha')

    nuke.knobDefault('EXPTool.mode', 'Stops')
    nuke.knobDefault('EXPTool.label', '[value mode]')

    nuke.knobDefault('VectorBlur.uv', 'motion')
    nuke.knobDefault('VectorBlur.scale', '0.5')
    nuke.knobDefault('VectorBlur.method', 'forward')
    nuke.knobDefault('VectorBlur.alpha', 'rgba.alpha')

    nuke.knobDefault('Shuffle.label', '[value in]')

    #Set Default Format
    HD = '1920 1080 HD'
    nuke.knobDefault('Root.format', HD)

    #Viewer Related Hotkeys
    nuke.menu( 'Viewer' ).addCommand( 'Save Image As..', "saveImage.saveImage()", "F3") 
    nuke.menu( 'Viewer' ).addCommand( 'Toggle Z', 'zToggle()', 'shift+d')


#Depth Viewer Custom Begin
def zToggle():
    curViewer = nuke.activeViewer()
    viewerNode = curViewer.node()
 
    if not viewerNode['channels'].value() == 'depth':
        viewerNode['channels'].setValue( 'depth' )
    else:
        viewerNode['channels'].setValue( 'rgba' )

def animatedSnap3D():
    # Add menu items under the Axis Menu for animatedSnap3D
    try:
        s = nuke.menu('Axis').findItem('Snap')
        s.addSeparator()
        s.addCommand('Match position - ANIMATED', 'animatedSnap3D.translateThisNodeToPointsAnimated()')
        s.addCommand('Match position, orientation - ANIMATED', 'animatedSnap3D.translateRotateThisNodeToPointsAnimated()')
        s.addCommand('Match position, orientation, scale - ANIMATED', 'animatedSnap3D.translateRotateScaleThisNodeToPointsAnimated()')
    except:
        pass

def add_python_scripts_menu():
    m.addCommand('Auto Write', 'import AutoWrite;AutoWrite.dropAutoWrite()','ctrl+shift+w', icon='WriteNode.png')
    m.addCommand("Submit To Muster", 'import musterSubmit;musterSubmit.main()', "ctrl+shift+d", "")
    #m.addCommand('Submit To Zync', 'import zync_nuke;zync_nuke.submit_dialog()')
    m.addCommand('Command Line Render', 'import CmdLineRender;CmdLineRender.CLrender(nuke.selectedNodes())', 'shift+c')
    m.addCommand('Make Read of Write', 'import readwrites;readwrites.readwrites()','ctrl+r', icon='ReadNode.png')
    m.addCommand("Make Write of Read (Mass Convert IMG)", 'import makewritefromread;makewritefromread.make_write_from_read()', '')
    m.addCommand('Browse Read|Write Directory', 'import browseDir;browseDir.exploreMe()', 'shift+b', icon='' )
    m.addCommand('Collect Files', 'import collectFiles;collectFiles.collectFiles()')
    m.addCommand('Red Timecode Overlay', 'nuke.nodes.Text(message="Time Code: [metadata r3d/absolute_time_code]", font="C:/Windows/Fonts/arial.ttf", size=100)' )
    #m.addCommand('Create Multipass Read', 'gatherPassesFromMasterBeauty.main()', 'shift+m', icon='' )

    m.addCommand('Python/Create Camera from EXR', 'import createExrCamVray;createExrCamVray.createExrCamVray(nuke.selectedNode())', '', icon='Camera.png' )
    m.addCommand('Python/Mocha Import', "import mochaImport;mochaImport.importMocha()", icon='')
    m.addCommand("Python/TargetCamera", "import TargetCamera;TargetCamera.TargetCamera()", icon = "TargetCamera.png")
    m.addCommand('Python/EXplodeR', 'import EXplodeRDef;EXplodeRDef.MNE_EXplodeR()','',icon='EXplodeR.png')
    m.addCommand("Python/AverageTrack", "import AverageTrackDef;AverageTrackDef.MNEaverageTrack()","",icon='AverageTrack.png')
    m.addCommand('Python/LayerMagic', 'import LayerMagicDef;LayerMagicDef.MNElayerMagic()','',icon='LayerMagic.png')
    m.addCommand('Python/ProjectorCam', 'import ProjectorCamDef;ProjectorCamDef.MNE_ProjectorCam()','',icon='Camera.png')
    m.addCommand("Python/SideBySide3DDef", "import SideBySide3DDef;SideBySide3DDef.MNE_sideBySide3D()","",icon='Anaglyph.png')
    m.addCommand('Python/SplitRGBA', 'import SplitRGBADef;SplitRGBADef.MNE_SplitRGBA()','',icon='SplitRGBA.png')
    m.addCommand('Python/Random Tile', 'import RandomTile;RandomTile.randomTile()','',icon='RandomTile.png')

def init():
    add_python_scripts_menu()
    add_gizmos_menu()
    set_default_values()
    animatedSnap3D()

init()