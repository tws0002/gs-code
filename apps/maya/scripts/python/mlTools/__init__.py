import os
import maya.cmds as cmds
import maya.mel as mel

def init_mlTools_menu():

    GMAIN_SHELF = mel.eval('$temp1=$gShelfTopLevel')
    GMAIN_WIND = mel.eval('$tmpVar=$gMainWindow')

    MLTOOLSMENU = cmds.menu('mlTools',p=GMAIN_WIND,tearOff=True,allowOptionBoxes=True,l='mlTools')


    if cmds.menu(MLTOOLSMENU,exists=True):
        cmds.setParent(MLTOOLSMENU,menu=True)

        cmds.menuItem(divider=True,dl="Redshift Automatte Tools")
        cmds.menuItem(l='A_setupRenderElements',c='from mlTools import RS_A_setupRenderElements;RS_A_setupRenderElements.main()')
        cmds.menuItem(l='B_setupUtilityLayer',c='from mlTools import RS_B_setupUtilityLayer;RS_B_setupUtilityLayer.main()')
        cmds.menuItem(l='C_setupMatteLayer',c='from mlTools import RS_C_setupMatteLayer;RS_C_setupMatteLayer.main()')
        cmds.menuItem(l='C_option_setupIDsOnly',c='from mlTools import RS_Coption_setupIDsOnly;RS_Coption_setupIDsOnly.main()')
        cmds.menuItem(l='C_option_setupLayerOnly',c='from mlTools import RS_Coption_setupLayerOnly;RS_Coption_setupLayerOnly.main()')
        cmds.menuItem(l='D_option_setupPuzzleMatteLayer',c='from mlTools import RS_Doption_setupMaterialPuzzleMatteLayer;RS_Doption_setupMaterialPuzzleMatteLayer.main()')
        