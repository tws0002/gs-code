from __future__ import with_statement
import nuke

def setupCards():
    node=nuke.thisNode()
    min=node['minZ'].value()
    max=node['maxZ'].value()
    count=int(node['count'].value())
    size=(max-min)/float(count)
    for n in node.nodes():
        print n.name()
        if not n.Class()=='Input' and not n.Class()=='Output':
            nuke.delete(n)
    with node:
        input=nuke.toNode('Input1')
        output=nuke.toNode('Output1')
        scene=nuke.nodes.Scene()
        output.setInput(0,scene)
        for i in range(count+1):
            start=min+(i*size)
            end=min+(i*size)+size
            crop=nuke.nodes.DeepCrop()
            crop['znear'].setValue(start)
            crop['zfar'].setValue(end)
            crop['use_bbox'].setValue(0)
            crop.setInput(0,input)
            convert=nuke.nodes.DeepToImage()
            convert.setInput(0,crop)
            card=nuke.nodes.Card2()
            card['translate'].setValue([0,0,-start])
            card.setInput(0,convert)
            card['uniform_scale'].setExpression('parent.scale')
            scene.setInput(i,card)