import os
import maya.cmds as cmds
import maya.mel as mel

def init_gs_menu():

	GMAIN_SHELF = mel.eval('$temp1=$gShelfTopLevel')
	GMAIN_WIND = mel.eval('$tmpVar=$gMainWindow')

	GS_MENU = cmds.menu('mainGSWindow',p=GMAIN_WIND,tearOff=True,allowOptionBoxes=True,l='GentScholar')


	if cmds.menu(GS_MENU,exists=True):
		cmds.setParent(GS_MENU,menu=True)

		if '01_cg/01_MAYA' in os.environ['GSPROJECT'] or os.path.exists('/'.join([os.environ['GSPROJECT'],'03_production', '01_cg','01_MAYA'])):
			# MUSTACHE
			cmds.menuItem(divider=True,dl="MUSTACHE")
			cmds.menuItem(l="Re-Init (Hello)",c='mustache.M.setUserUI(True)',i='mustache_M.bmp')
			cmds.menuItem(divider=True)
			cmds.menuItem(l="Quicksave",c='mustache.M.quickSave()',i='mustache_QS.bmp')
			cmds.menuItem(divider=True)
			cmds.menuItem(l="Asset Manager",c='mustache.M.AM.assetManagerUI()',i='mustache_AM.bmp')
			cmds.menuItem(l="Scene Manager",c='mustache.M.SM.sceneManagerUI()',i='mustache_SM.bmp')
			cmds.menuItem(l="Asset Library",c='mustache.M.DB.libraryUI()',i='mustache_DB.bmp')

		else:	
			# NEW CORE PIPELINE
			cmds.menuItem(divider=True,dl="Pipeline")
			cmds.menuItem(l="Quicksave",c='import gs_quicksave;reload(gs_quicksave);gs_quicksave.main()')
			cmds.menuItem(l="Publish Scene", en=True, c='import gs_publish;reload(gs_publish);gs_publish.main()')
			cmds.menuItem(divider=True)
			#cmds.menuItem(l="Scene Loader",en=False,c='import gs_sceneloader;reload(gs_sceneloader);gs_sceneloader.main()')
			cmds.menuItem(l="Asset Manager",c='import gs_assetloader;reload(gs_assetloader);gs_assetloader.main()')
			cmds.menuItem(divider=True)
			cmds.menuItem(l="Render Submit",c='import gs_submit_muster;reload(gs_submit_muster);gs_submit_muster.main()')
			cmds.menuItem(divider=True,dl="Asset Tools")
			cmds.menuItem(l="Asset Maker",c='import gs_assetmaker;reload(gs_assetmaker);gs_assetmaker.main()')
			#cmds.menuItem(l="Clean Scene",en=False,c='')
			#cmds.menuItem(l="Turntable Setup",c='import gs_assetmaker;reload(gs_assetmaker);gs_assetmaker.main()')
			cmds.menuItem(divider=True,dl="Animation Tools")
			cmds.menuItem(l="Playblaster",en=False,c='')
			cmds.menuItem(l="Animation Transfer",en=False,c='')
			cmds.menuItem(l="Pose Library",en=False,c='import gs_alembic;reload(gs_alembic);gs_alembic.loadExporterUI()')
			cmds.menuItem(l="Alembic Import",c='import gs_alembic;reload(gs_alembic);gs_alembic.loadImporterUI()')
			#cmds.menuItem(l="Alembic Export",c='import gs_alembic;reload(gs_alembic);gs_alembic.loadExporterUI()')
			#cmds.menuItem(l="Sticky Nulls",c='import gs_alembic;reload(gs_alembic);gs_alembic.loadExporterUI()')
			cmds.menuItem(divider=True,dl="Render Tools")
			cmds.menuItem(l="LookBook", en=False, c='import gs_lookbook;reload(gs_lookbook);gs_lookbook.main()')
			cmds.menuItem(l="Render Setup", en=False, c='import gs_alembic;reload(gs_alembic);gs_alembic.loadImporterUI()')
			cmds.menuItem(divider=True)
			cmds.menuItem(l="Render Submit",c='mustache.M.MSUB.submitUI()', i='mustache_MSUB.bmp')
		cmds.menuItem(divider=True)
		cmds.menuItem(l='Load VRay',c='cmds.loadPlugin("vrayformaya")')
		cmds.menuItem(l='Load Redshift',c='cmds.loadPlugin("redshift4maya")')


