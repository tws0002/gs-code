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
		cmds.menuItem(divider=True,dl="MUSTACHE")
		cmds.menuItem(l="Re-Init (Hello)",c='mustache.M.setUserUI(True)',i='mustache_M.bmp')
		cmds.menuItem(divider=True)
		cmds.menuItem(l="Quicksave",c='mustache.M.quickSave()',i='mustache_QS.bmp')
		cmds.menuItem(divider=True)
		cmds.menuItem(l="Asset Manager",c='mustache.M.AM.assetManagerUI()',i='mustache_AM.bmp')
		cmds.menuItem(l="Scene Manager",c='mustache.M.SM.sceneManagerUI()',i='mustache_SM.bmp')
		cmds.menuItem(l="Asset Library",c='mustache.M.DB.libraryUI()',i='mustache_DB.bmp')
		cmds.menuItem(divider=True)
		cmds.menuItem(l="Render Submit",c='mustache.M.MSUB.submitUI()', i='mustache_MSUB.bmp')

		cmds.menuItem(divider=True,dl="QUICKLOAD PLUGINS")
		cmds.menuItem(l='Load VRay',c='cmds.loadPlugin("vrayformaya")')
		cmds.menuItem(l='Load Redshift',c='cmds.loadPlugin("redshift4maya")')

		
		#cmds.menuItem(sm=True,l='Autodesk')
		# Quick Loader
		#cmds.menuItem(divider=True,dl="AUTODESK")
		#autod = "xgenToolkit;BifrostMain;Substance;MASH;curveWarp;ATFPlugin"
		#mod = sorted(autod.split(';'))
		#for m in mod:
		#	cmds.menuItem(l=m.title(),c='cmds.loadPlugin("{0}")'.format(str(m)))		
		#
		#cmds.setParent(GS_MENU,menu=True)
		#cmds.menuItem(sm=True,l='GS Modules')
		#cmds.menuItem(divider=True,dl="GS MODULES")
		#
		#if 'GS_MODULES' in os.environ:
		#	mod = sorted(os.environ['GS_MODULES'].split(';'))
		#	for m in mod:
		#		cmds.menuItem(l=m.title(),c='cmds.loadPlugin("{0}")'.format(str(m)))




		# Tools

