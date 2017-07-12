import sys,nuke,os,mlTools


def main():
	
    shotManagerDir=os.path.dirname(mlTools.__file__).replace("\\","/")+'/mlShotManager'
    
    #del sys.modules['shotManager']
    sys.path.append(shotManagerDir)
    from nukescripts import panels
    nuke.pluginAddPath(shotManagerDir)
    from mlTools.mlShotManager import shotManager
    reload(shotManager)
    
    from shotManager import shotManagerWindow

    win=panels.registerWidgetAsPanel('mlTools.mlShotManager.shotManager.shotManagerWindow', 'shotManager', 'farts', True)
    pane=nuke.getPaneFor('Viewer.1')
    #pane = nuke.getPaneFor('Properties.1')
    #pane = nuke.getPaneFor('DAG.1')
    #win.show()
    win.addToPane(pane)