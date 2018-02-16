import os
import maya.cmds as cmds
import maya.mel as mel

def init_gs_menu():

	GMAIN_SHELF = mel.eval('$temp1=$gShelfTopLevel')
	GMAIN_WIND = mel.eval('$tmpVar=$gMainWindow')

	GS_MENU = cmds.menu('mainGSWindow',p=GMAIN_WIND,tearOff=True,allowOptionBoxes=True,l='GentScholar')


	if cmds.menu(GS_MENU,exists=True):
		cmds.setParent(GS_MENU,menu=True)

		# MUSTACHE
		cmds.menuItem(divider=True,dl="PIPELINE")
		cmds.menuItem(l="Quicksave",c='import gs_quicksave;reload(gs_quicksave);gs_quicksave.main()')
		cmds.menuItem(l="Publish Scene",c='import gs_publish;reload(gs_publish);gs_publish.main()')
		cmds.menuItem(divider=True)
		cmds.menuItem(l="Scene Loader",c='import gs_sceneloader;reload(gs_sceneloader);gs_sceneloader.main()')
		cmds.menuItem(l="Asset Loader",c='import gs_assetloader;reload(gs_assetloader);gs_assetloader.main()')
		cmds.menuItem(divider=True)
		cmds.menuItem(l="Render Submit",c='import gs_submit_muster;reload(gs_submit_muster);gs_submit_muster.main()')
		cmds.menuItem(divider=True,dl="DANDY TOOLS")
		cmds.menuItem(l="AssetMaker",c='import gs_assetmaker;reload(gs_assetmaker);gs_assetmaker.main()')
		cmds.menuItem(l="LookBook",c='import gs_lookbook;reload(gs_lookbook);gs_lookbook.main()')
		cmds.menuItem(l="Alembic Export",c='import gs_alembic;reload(gs_alembic);gs_alembic.loadExporterUI()')
		cmds.menuItem(l="Alembic Import",c='import gs_alembic;reload(gs_alembic);gs_alembic.loadImporterUI()')
		cmds.menuItem(divider=True,dl="LOAD RENDERER")
		cmds.menuItem(l='Load VRay',c='cmds.loadPlugin("vrayformaya")')
		cmds.menuItem(l='Load Redshift',c='cmds.loadPlugin("redshift4maya")')


