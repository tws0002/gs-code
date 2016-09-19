import AutoWrite
import musterSubmit
import CmdLineRender
import readwrites
import makewritefromread
import browseDir
import gatherPassesFromMasterBeauty
import collectFiles
import createExrCamVray
import EXplodeRDef
import AverageTrackDef
import LayerMagicDef
import ProjectorCamDef
import SideBySide3DDef
import SplitRGBADef
import RandomTile
import mochaImport
import TargetCamera
import animatedSnap3D
import zync_nuke
import mari_bridge

toolbar = nuke.toolbar("Nodes")
m = toolbar.addMenu("Gentleman Scholar", icon="GentlemanScholar.png")

#Set Random Custom Knob Defaults
nuke.knobDefault('Roto.output', 'alpha')

nuke.knobDefault('EXPTool.mode', 'Stops')
nuke.knobDefault('EXPTool.label', '[value mode]')

nuke.knobDefault('VectorBlur.uv', 'motion')
nuke.knobDefault('VectorBlur.scale', '0.5')
nuke.knobDefault('VectorBlur.method', 'forward')
nuke.knobDefault('VectorBlur.alpha', 'rgba.alpha')

nuke.knobDefault('Shuffle.label', '[value in]')

#Viewer Related Hotkeys
import saveImage
nuke.menu( 'Viewer' ).addCommand( 'Save Image As..', "saveImage.saveImage()", "F3") 
nuke.menu( 'Viewer' ).addCommand( 'Toggle Z', 'zToggle()', 'shift+d')


#Set Default Format
HD = '1920 1080 HD'
nuke.knobDefault('Root.format', HD)


#Massive Pane
import MassivePanel
def addMassivePanel():
    myPanel = MassivePanel.MassivePanel()
    return myPanel.addToPane()
paneMenu = nuke.menu('Pane')
paneMenu.addCommand('MassivePanel', addMassivePanel)
nukescripts.registerPanel( 'com.ohufx.MassivePanel', addMassivePanel)

# Mustache_AC Pane
import mustache_AC
def addPanel():
    return mustache_AC.mustache_AC().addToPane()

menu = nuke.menu('Pane')
menu.addCommand('}MUSTACHE{ Auto-Comp', addPanel)
nukescripts.registerPanel('mustache.AutoComp', addPanel)


#Depth Viewer Custom Begin
def zToggle():
    curViewer = nuke.activeViewer()
    viewerNode = curViewer.node()
 
    if not viewerNode['channels'].value() == 'depth':
        viewerNode['channels'].setValue( 'depth' )
    else:
        viewerNode['channels'].setValue( 'rgba' )

# Add menu items under the Axis Menu for animatedSnap3D
try:
    s = nuke.menu('Axis').findItem('Snap')
    s.addSeparator()
    s.addCommand('Match position - ANIMATED', 'animatedSnap3D.translateThisNodeToPointsAnimated()')
    s.addCommand('Match position, orientation - ANIMATED', 'animatedSnap3D.translateRotateThisNodeToPointsAnimated()')
    s.addCommand('Match position, orientation, scale - ANIMATED', 'animatedSnap3D.translateRotateScaleThisNodeToPointsAnimated()')
except:
    pass

#Python
m.addCommand('Auto Write', 'AutoWrite.dropAutoWrite()','ctrl+shift+w', icon='WriteNode.png')
m.addCommand("Submit To Muster", 'musterSubmit.main()', "ctrl+shift+d", "")
m.addCommand('Submit To Zync', 'zync_nuke.submit_dialog()')
m.addCommand('Command Line Render', 'CmdLineRender.CLrender(nuke.selectedNodes())', 'shift+c')
m.addCommand('Make Read of Write', 'readwrites.readwrites()','ctrl+r', icon='ReadNode.png')
m.addCommand("Make Write of Read (Mass Convert IMG)", 'makewritefromread.make_write_from_read()', '')
m.addCommand('Browse Read|Write Directory', 'browseDir.exploreMe()', 'shift+b', icon='' )
m.addCommand('Collect Files', 'collectFiles.collectFiles()')
m.addCommand('Red Timecode Overlay', 'nuke.nodes.Text(message="Time Code: [metadata r3d/absolute_time_code]", font="C:/Windows/Fonts/arial.ttf", size=100)' )
#m.addCommand('Create Multipass Read', 'gatherPassesFromMasterBeauty.main()', 'shift+m', icon='' )

m.addCommand('Python/Create Camera from EXR', 'createExrCamVray.createExrCamVray(nuke.selectedNode())', '', icon='Camera.png' )
m.addCommand('Python/Mocha Import', "mochaImport.importMocha()", icon='')
m.addCommand("Python/TargetCamera", "TargetCamera.TargetCamera()", icon = "TargetCamera.png")
m.addCommand('Python/EXplodeR', 'EXplodeRDef.MNE_EXplodeR()','',icon='EXplodeR.png')
m.addCommand("Python/AverageTrack", "AverageTrackDef.MNEaverageTrack()","",icon='AverageTrack.png')
m.addCommand('Python/LayerMagic', 'LayerMagicDef.MNElayerMagic()','',icon='LayerMagic.png')
m.addCommand('Python/ProjectorCam', 'ProjectorCamDef.MNE_ProjectorCam()','',icon='Camera.png')
m.addCommand("Python/SideBySide3DDef", "SideBySide3DDef.MNE_sideBySide3D()","",icon='Anaglyph.png')
m.addCommand('Python/SplitRGBA', 'SplitRGBADef.MNE_SplitRGBA()','',icon='SplitRGBA.png')
m.addCommand('Python/Random Tile', 'RandomTile.randomTile()','',icon='RandomTile.png')


#Gizmos
m.addCommand("Gizmos/MNE Tools/WaveMaker3", "nuke.createNode(\"mne_WaveMaker3\")", "", "WaveMaker.png")
#m.addCommand('Gizmos/MNE Tools/WaveMaker4', 'addGroupTool("mne_WaveMaker4.nk")' , icon='WaveMaker.png')
m.addCommand("Gizmos/MNE Tools/AspectCrop", "nuke.createNode(\"mne_AspectCrop\")", "", "AspectCrop.png")
m.addCommand("Gizmos/MNE Tools/CGDiffuse", "nuke.createNode(\"mne_CGDiffuse\")", "", "CGDiffuse.png")
m.addCommand("Gizmos/MNE Tools/QuickGrade", "nuke.createNode(\"mne_QuickGrade\")", "", "QuickGrade.png")
m.addCommand("Gizmos/MNE Tools/Wiper", "nuke.createNode(\"mne_Wiper\")", "", "Wiper.png")
m.addCommand("Gizmos/MNE Tools/EdgeRoughen", "nuke.createNode(\"mne_EdgeRoughen\")", "", "")
m.addCommand("Gizmos/MNE Tools/ChannelList", "nuke.createNode(\"mne_ChannelList\")", "", "")
m.addCommand("Gizmos/MNE Tools/CornerStabilize", "nuke.createNode(\"mne_CornerStabilize\")", "", "")
m.addCommand("Gizmos/MNE Tools/Depth2Stereo", "nuke.createNode(\"mne_Depth2Stereo\")", "", "")
m.addCommand("Gizmos/MNE Tools/OverallStereo", "nuke.createNode(\"mne_OverallStereo\")", "", "")
#m.addCommand('Gizmos/MNE Tools/AutoSlate', 'addGroupTool("mne_autoSlate.nk")' , icon='Ramp.png')
#m.addCommand('Gizmos/MNE Tools/CurveConverter', 'addGroupTool("mne_CurveConverter.nk")' , icon='CurveConverter.png')

m.addCommand("Gizmos/BL/bl_Arc", "nuke.createNode(\"bl_Arc\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_BlurChroma", "nuke.createNode(\"bl_BlurChroma\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Bokeh", "nuke.createNode(\"bl_Bokeh\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Bulge", "nuke.createNode(\"bl_Bulge\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Bytes", "nuke.createNode(\"bl_Bytes\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_ChannelBox", "nuke.createNode(\"bl_ChannelBox\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_ChromaticAberation", "nuke.createNode(\"bl_ChromaticAberation\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_CleanOUT", "nuke.createNode(\"bl_CleanOUT\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_ColorEdge", "nuke.createNode(\"bl_ColorEdge\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_ColorSupress", "nuke.createNode(\"bl_ColorSupress\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Compress", "nuke.createNode(\"bl_Compress\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Convolve", "nuke.createNode(\"bl_Convolve\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_CurveFilter", "nuke.createNode(\"bl_CurveFilter\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Despillator", "nuke.createNode(\"bl_Despillator\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_EdgeExtend2", "nuke.createNode(\"bl_EdgeExtend2\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Emboss", "nuke.createNode(\"bl_Emboss\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Expand", "nuke.createNode(\"bl_Expand\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Filler", "nuke.createNode(\"bl_Filler\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_GUISwitch", "nuke.createNode(\"bl_GUISwitch\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_HSVKeyer", "nuke.createNode(\"bl_HSVKeyer\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_IBlur", "nuke.createNode(\"bl_IBlur\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_IBokeh", "nuke.createNode(\"bl_IBokeh\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_IDilateErode", "nuke.createNode(\"bl_IDilateErode\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_IDisplace", "nuke.createNode(\"bl_IDisplace\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_ITime", "nuke.createNode(\"bl_ITime\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_LayerAE", "nuke.createNode(\"bl_LayerAE\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Line", "nuke.createNode(\"bl_Line\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Match", "nuke.createNode(\"bl_Match\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_mf_Binary", "nuke.createNode(\"bl_mf_Binary\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_mf_Border", "nuke.createNode(\"bl_mf_Border\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_mf_DirectionalBlur", "nuke.createNode(\"bl_mf_DirectionalBlur\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_mf_Occlusion", "nuke.createNode(\"bl_mf_Occlusion\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_mf_ShapeSofter", "nuke.createNode(\"bl_mf_ShapeSofter\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Monochrome", "nuke.createNode(\"bl_Monochrome\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Mosaic", "nuke.createNode(\"bl_Mosaic\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Normalizer", "nuke.createNode(\"bl_Normalizer\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Random", "nuke.createNode(\"bl_Random\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Randomizer", "nuke.createNode(\"bl_Randomizer\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Sample", "nuke.createNode(\"bl_Sample\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_SaturationRGB", "nuke.createNode(\"bl_SaturationRGB\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_ScanLines", "nuke.createNode(\"bl_ScanLines\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Scanner", "nuke.createNode(\"bl_Scanner\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_ScanSlice", "nuke.createNode(\"bl_ScanSlice\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Scatterize", "nuke.createNode(\"bl_Scatterize\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Scroll", "nuke.createNode(\"bl_Scroll\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_SetBBOXColor", "nuke.createNode(\"bl_SetBBOXColor\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Shape", "nuke.createNode(\"bl_Shape\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Slice", "nuke.createNode(\"bl_Slice\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Solarize", "nuke.createNode(\"bl_Solarize\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_SpillSupress", "nuke.createNode(\"bl_SpillSupress\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Star", "nuke.createNode(\"bl_Star\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Threshold", "nuke.createNode(\"bl_Threshold\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_TileMosaic", "nuke.createNode(\"bl_TileMosaic\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_ToBBOX", "nuke.createNode(\"bl_ToBBOX\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Twirl", "nuke.createNode(\"bl_Twirl\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Wave", "nuke.createNode(\"bl_Wave\")", icon="BL.png")
m.addCommand("Gizmos/BL/bl_Zebrafy", "nuke.createNode(\"bl_Zebrafy\")", icon="BL.png")

m.addCommand("Gizmos/Nukepedia/Lens Sim + Vignette", "nuke.createNode(\"nukepedia_LensSim_Vignette\")", "", "")
m.addCommand("Gizmos/Nukepedia/Magic Carpet - Multi Point Gradient", "nuke.createNode(\"nukepedia_magicCarpet\")", "", icon='magicCarpet.png')
m.addCommand("Gizmos/Nukepedia/TXFog - Volume Sprites Box", "nuke.createNode(\"nukepedia_TxFog\")", icon="BL.png")

m.addCommand("Gizmos/Internal/Chromatic Abberation", "nuke.createNode(\"internal_RGB_split\")", "", "")
m.addCommand("Gizmos/Internal/AdvandcedEdgeDetect", "nuke.createNode(\"internal_AdvancedEdgeDetectPrecise\")", icon="BL.png")

m.addCommand("Gizmos/Lyons/Abberation", "nuke.createNode(\"lyons_Abberation_v01\")", "", "")
m.addCommand("Gizmos/Lyons/Channel Control", "nuke.createNode(\"lyons_ChannelControl_v03\")", "", "")
m.addCommand("Gizmos/Lyons/Compare Values", "nuke.createNode(\"lyons_CompareValues_v04\")", "", "")
m.addCommand("Gizmos/Lyons/Exponential Blur", "nuke.createNode(\"lyons_ExponBlur_v02\")", "", "")
m.addCommand("Gizmos/Lyons/GWrap", "nuke.createNode(\"lyons_GWrap_v02\")", "", "")
m.addCommand("Gizmos/Lyons/High Pass", "nuke.createNode(\"lyons_HighPass_v01\")", "", "")
m.addCommand("Gizmos/Lyons/ID Matte Mixer", "nuke.createNode(\"lyons_ID_MatteMixer_v01\")", "", "")
m.addCommand("Gizmos/Lyons/Kill Outline", "nuke.createNode(\"lyons_KillOutline_v01\")", "", "")
m.addCommand("Gizmos/Lyons/Lighting Match", "nuke.createNode(\"lyons_LightingMatch_v03\")", "", "")
m.addCommand("Gizmos/Lyons/Luma Despill", "nuke.createNode(\"lyons_LumaDespill_v08\")", "", "")
m.addCommand("Gizmos/Lyons/Luma Grain", "nuke.createNode(\"lyons_LumaGrain_v02\")", "", "")
m.addCommand("Gizmos/Lyons/Randomizer", "nuke.createNode(\"lyons_Randomizer_v01\")", "", "")

m.addCommand("Gizmos/Misc/dGrad", "nuke.createNode(\"misc_dGrad\")", "", "")
m.addCommand("Gizmos/Misc/Mask 3D Gradient", "nuke.createNode(\"misc_Mask3DGradient_IK\")", "", "")
m.addCommand("Gizmos/Misc/Point Cloud Grapher", "nuke.createNode(\"misc_PointCloudGrapher_v01\")", "", "")
m.addCommand("Gizmos/Misc/Rotate Normals", "nuke.createNode(\"misc_RotateNormals\")", "", "")
m.addCommand("Gizmos/Misc/Slice Tool", "nuke.createNode(\"misc_SliceTool\")", "", "")
m.addCommand("Gizmos/Misc/ThreeD Mattes", "nuke.createNode(\"misc_ThreeDMattes_v02\")", "", "")
m.addCommand("Gizmos/Misc/Zebra Slicer", "nuke.createNode(\"misc_ZebraSlicer\")", "", "")

v = toolbar.addMenu("VideoCopilot", icon="VideoCopilot.png")
v.addCommand( "OpticalFlares", "nuke.createNode('OpticalFlares')", icon="OpticalFlares.png")