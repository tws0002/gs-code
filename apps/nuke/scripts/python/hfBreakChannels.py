# get all channels of selected read nodes, convert channels list to layers, output layers to individual sequences

import os
import nuke

def hfBreakChannels( node )

        fileExt = '.tif'

        sel = nuke.selectedNodes()
        writeNodes = []
        for obj in sel:
            chans = obj.channels()
            layers = [f.split('.')[0] for f in chans]
            layers = list(set(layers))
            # for each layer, output the layer to a write node
            readName = obj.name()
            readPath = os.path.dirname(obj['file'].value())
            readFile = os.path.basename(obj['file'].value())
            for layer in layers:
                wLabel = readName+'_'+layer
                wFile = '.'.join(readFile.split('.')[:-2])+'.'+layer+'.####'+fileExt
                if not os.path.exists(os.path.join(readPath,layer)): os.makedirs(os.path.join(readPath,layer))
                wPath = os.path.join(readPath,layer,wFile).replace('\\','/')
                newShuf = nuke.nodes.Shuffle(label=layer,inputs=[obj])
                newShuf['in'].setValue(layer)
                newShuf['postage_stamp'].setValue(True)
                newWrite = nuke.nodes.Write(label=wLabel,file=wPath,file_type='tiff')
                newWrite.setInput(0,newShuf)
                newWrite['datatype'].setValue('16 bit')
                newWrite['compression'].setValue('LZW')