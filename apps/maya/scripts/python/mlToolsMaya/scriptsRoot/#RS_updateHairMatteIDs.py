

def main():
    import maya.cmds as cmds
    import maya.mel as mel
    #### Select renderLayer with geo, will create lighting passes and utility layer.
    message=''
    if cmds.objExists('rsAov_m_mortonC'):
        cmds.setAttr('rsAov_m_mortonC.blueId',509)
        message+='upated morton\n'
    if cmds.objExists('rsAov_m_miaYoungestB'):
        cmds.setAttr('rsAov_m_miaYoungestB.blueId',106)
        message+='upated miaYoungest\n'
    if cmds.objExists('rsAov_m_miaMidB'):
        cmds.setAttr('rsAov_m_miaMidB.blueId',206)  
        message+='upated miaMid\n'
    if cmds.objExists('rsAov_m_miaTeenB'):
        cmds.setAttr('rsAov_m_miaTeenB.blueId',306)  
        message+='upated miaTeen\n'
    if cmds.objExists('rsAov_m_miaAdultB'):
        cmds.setAttr('rsAov_m_miaAdultB.blueId',406)  
        message+='upated miaAdult\n'
    if message:
        cmds.confirmDialog(message=message)