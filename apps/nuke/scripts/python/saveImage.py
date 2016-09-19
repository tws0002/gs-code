'''
Created on 19-jan-2013
@author: satheesh-R
mail - satheesrev@gmail.com
'''

import nuke
import nukescripts
def saveImage ():
    ### creating panel and assign buttons
    ef = nuke.Panel("saveImage As......  by satheesh-r", 420)
    ef.addFilenameSearch("Save Image As:\nchoose path & file type", "")
    ef.addButton("cancel")
    ef.addEnumerationPulldown('channels', "rgb rgba all")

    ef.addEnumerationPulldown('Exr data type', "16bit-half 32bit-float")
    ef.addButton("ok")
    window=ef.show()
    exrtype = ef.value('Exr data type')
    channel = ef.value('channels')
    path = ef.value("Save Image As:\nchoose path & file type")
    fileType = path.split('.')[-1]
    if window == 0 :
        return

    ### getting path from user input
    if path == "":
        nuke.message('no file path selected ')
    if path == "":
        return

    ### getting active node
    curViewer = nuke.activeViewer()
    curNode = curViewer.node()
    acticeVinput = curViewer.activeInput()
    curN = curNode.input(acticeVinput)

    ### creating temp write
    w = nuke.createNode("Write")
    w.setName("tempWrite")
    w.setInput(0, curN)
    w['file'].setValue(path)

    ### if file type is jpg
    if fileType == 'jpg' :
        w['_jpeg_sub_sampling'].setValue(2)
        w['_jpeg_quality'].setValue(1)

    ### if file type is exr
    if fileType == 'exr' :
        w['datatype'].setValue(exrtype)
        w['compression'].setValue(2)
        w['metadata'].setValue(0)

    if channel == 'rgba' :
        w['channels'].setValue('rgba')

    if channel == 'all' :
        w['channels'].setValue('all')

    ### setting current frame for render
    result = nuke.frame()
    if result =="":
      result = result

    ### execute write node
    nuke.execute(nuke.selectedNode(), (int(result)), result)
    name = w.knob('file').value()
    nukescripts.node_delete(popupOnError=True)

    ### create Read node
    r = nuke.createNode("Read")
    r['file'].setValue(name)
    result = nuke.frame()
    r['first'].setValue(int(result))
    r['last'].setValue(int(result))
    r['xpos'].setValue( 200 )

    if fileType == "":
        return
