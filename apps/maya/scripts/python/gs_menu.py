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
		cmds.menuItem(l="Quicksave",c='')
		cmds.menuItem(l="Publish Scene",c='')
		cmds.menuItem(divider=True)
		cmds.menuItem(l="Shot Loader",c='')
		cmds.menuItem(l="Asset Manager",c='')
		cmds.menuItem(divider=True)
		cmds.menuItem(l="Render Submit",c='import gs_submit_muster;reload(gs_submit_muster)')
		cmds.menuItem(divider=True,dl="DANDY TOOLS")
		cmds.menuItem(l="AssetMaker",c='import gs_assetmaker;reload(gs_assetmaker)')
		cmds.menuItem(l="LookBook",c='import gs_lookbook;reload(gs_lookbook)')
		cmds.menuItem(l="Alembic Export",c='import gs_alembic;reload(gs_alembic);gs_alembic.loadExporterUI()')
		cmds.menuItem(l="Alembic Import",c='import gs_alembic;reload(gs_alembic);gs_alembic.loadImporterUI()')
		cmds.menuItem(divider=True,dl="LOAD RENDERER")
		cmds.menuItem(l='Load VRay',c='cmds.loadPlugin("vrayformaya")')
		cmds.menuItem(l='Load Redshift',c='cmds.loadPlugin("redshift4maya")')


