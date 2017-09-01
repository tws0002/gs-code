#symmetryToolsXYZ_mari3.0.2
#By David Eschrich


# This is world space only. But as long as your model is centered at origin and is either symmetrical on the x,y, or z axis then this will allow for symmetrical baking. 
# Paint on one side of your model and then bake with symmetry across the desired axis with the details being mirrored properly.
# The camera and buffer will return to it's initial position after the symmetry baking is complete.
# No need for taking the time to setup symmetrical uvs :)

# For this script to work correctly go to the Projection Palette and ensure your projection Baking Behavior is set to "Manual" and Projection as "Front" 
# In your paint buffer set Reset on Bake to Disabled. Otherwise this will be messy :) 


# In addition you can just invert the canvas/buffer on any axis without baking by using keyboard shortcuts listed below or via the deTools menu.
# Apart from the deTools menu there is also a symmetry tools palette included with x,y,and z baking buttons
# The palette includes x,y,and z symmetry baking buttons with a menu to specify the buffer behavior after a symmetrical bake. It can be set to Auto or Manual Clear


# Baking Shortcuts:
# Shift+X
# Shift+Y
# Shift+Z

# Canvas Inversion Shortcuts:
# Crtl+Shift+X
# Crtl+Shift+Y
# Crtl+Shift+Z


# This has been tested on the most recent windows and linux versions of mari 3. Please let me know if you find any issues.


# version 3.0.2 added a small change to pause the viewport refresh until after the baking is done. This should help the more complex scenes where just moving the camera can cuase lag. i hope

import mari
import PySide
core = PySide.QtCore
gui = PySide.QtGui
w = gui.QWidget()

def symmetryBakeX():

    def bufferBake():
            paint_buffer = mari.canvases.paintBuffer()
            paint_buffer.bake()

    
    def cameraInversion():
        camera = mari.canvases.current().camera()

        lookAt = camera.lookAt()
        up = camera.up()
        translation = camera.translation()
        
        camera.setTranslation( mari.VectorN(-translation.x(),translation.y(),translation.z()))
        camera.setUp( mari.VectorN(-up.x(),up.y(),up.z()))
        camera.setLookAt( mari.VectorN(-lookAt.x(),lookAt.y(),lookAt.z()))

    def paintBufferFlip( scaleFactor ):
            paintBuffer = mari.canvases.paintBuffer()
            scale = paintBuffer.scale()
            scale = core.QSizeF( scale.width() * scaleFactor[0], scale.height() * scaleFactor[1] )
            paintBuffer.setScale( scale )

    def paintBufferRotate():
            paint_buffer = mari.canvases.paintBuffer()
            rotation = paint_buffer.rotation()
            paint_buffer.setRotation( 360-rotation )

    def paintBufferTranslation():
            paint_buffer = mari.canvases.paintBuffer()
            translation = paint_buffer.translation()
            paint_buffer.setTranslation(core.QPointF(-translation.x(), translation.y()))

    def bufferClear():
            paint_buffer = mari.canvases.paintBuffer()
            paint_buffer.clear()


    n = comboSymmetryXYZ.currentIndex()


    if n == 1:

        mari.canvases.setPauseShaderCompiles(1)
        bufferBake()
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferBake() 
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        mari.canvases.setPauseShaderCompiles(0)

    else:

        mari.canvases.setPauseShaderCompiles(1)
        bufferBake() 
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferBake()
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferClear()
        mari.canvases.setPauseShaderCompiles(0)




actionSymmetryBakeX = mari.actions.create( 'Bake Symmetry X', 'symmetryBakeX()' )

actionSymmetryBakeX.setShortcut("Shift+X")

mari.menus.addAction( actionSymmetryBakeX, "MainWindow/d&eTools/&Symmetry" )






def symmetryBakeY():

    def bufferBake():
        paint_buffer = mari.canvases.paintBuffer()
        paint_buffer.bake()
   


    def cameraInversion():
        camera = mari.canvases.current().camera()

        lookAt = camera.lookAt()
        up = camera.up()
        translation = camera.translation()
    
        camera.setTranslation( mari.VectorN(translation.x(),-translation.y(),translation.z()))
        camera.setUp( mari.VectorN(up.x(),-up.y(),up.z()))
        camera.setLookAt( mari.VectorN(lookAt.x(),-lookAt.y(),lookAt.z()))


    def paintBufferFlip( scaleFactor ):
            paintBuffer = mari.canvases.paintBuffer()
            scale = paintBuffer.scale()
            scale = core.QSizeF( scale.width() * scaleFactor[0], scale.height() * scaleFactor[1] )
            paintBuffer.setScale( scale )

    def paintBufferRotate():
            paint_buffer = mari.canvases.paintBuffer()
            rotation = paint_buffer.rotation()
            paint_buffer.setRotation( 360-rotation )


    def paintBufferTranslation():
            paint_buffer = mari.canvases.paintBuffer()
            translation = paint_buffer.translation()
            paint_buffer.setTranslation(core.QPointF(-translation.x(), translation.y()))

    def bufferClear():
            paint_buffer = mari.canvases.paintBuffer()
            paint_buffer.clear()    


    n = comboSymmetryXYZ.currentIndex()


    if n == 1:

        mari.canvases.setPauseShaderCompiles(1)
        bufferBake() 
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferBake() 
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        mari.canvases.setPauseShaderCompiles(0)

    else:

        mari.canvases.setPauseShaderCompiles(1)
        bufferBake() 
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferBake()
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferClear()
        mari.canvases.setPauseShaderCompiles(0)

    




actionSymmetryBakeY = mari.actions.create( 'Bake Symmetry Y', 'symmetryBakeY()' )

actionSymmetryBakeY.setShortcut("Shift+Y")

mari.menus.addAction( actionSymmetryBakeY, "MainWindow/d&eTools/&Symmetry" )



def symmetryBakeZ():

    def bufferBake():
        paint_buffer = mari.canvases.paintBuffer()
        paint_buffer.bake()   


    def cameraInversion():
        camera = mari.canvases.current().camera()

        lookAt = camera.lookAt()
        up = camera.up()
        translation = camera.translation()
    
        camera.setTranslation( mari.VectorN(translation.x(),translation.y(),-translation.z()))
        camera.setUp( mari.VectorN(up.x(),up.y(),-up.z()))
        camera.setLookAt( mari.VectorN(lookAt.x(),lookAt.y(),-lookAt.z()))


    def paintBufferFlip( scaleFactor ):
            paintBuffer = mari.canvases.paintBuffer()
            scale = paintBuffer.scale()
            scale = core.QSizeF( scale.width() * scaleFactor[0], scale.height() * scaleFactor[1] )
            paintBuffer.setScale( scale )


    def paintBufferRotate():
            paint_buffer = mari.canvases.paintBuffer()
            rotation = paint_buffer.rotation()
            paint_buffer.setRotation( 360-rotation )


    def paintBufferTranslation():
            paint_buffer = mari.canvases.paintBuffer()
            translation = paint_buffer.translation()
            paint_buffer.setTranslation(core.QPointF(-translation.x(), translation.y()))


    def bufferClear():
            paint_buffer = mari.canvases.paintBuffer()
            paint_buffer.clear()    
    
    n = comboSymmetryXYZ.currentIndex()


    if n == 1:

        mari.canvases.setPauseShaderCompiles(1)
        ufferBake() 
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferBake() 
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        mari.canvases.setPauseShaderCompiles(0)

    else:

        mari.canvases.setPauseShaderCompiles(1)
        bufferBake() 
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferBake()
        cameraInversion()
        paintBufferFlip((-1,1))
        paintBufferRotate()
        paintBufferTranslation()
        bufferClear()
        mari.canvases.setPauseShaderCompiles(0)




actionSymmetryBakeZ = mari.actions.create( 'Bake Symmetry Z', 'symmetryBakeZ()' )

actionSymmetryBakeZ.setShortcut("Shift+Z")

mari.menus.addAction( actionSymmetryBakeZ, "MainWindow/d&eTools/&Symmetry" )


def cameraInverseX():

    camera = mari.canvases.current().camera()

    lookAt = camera.lookAt()
    up = camera.up()
    translation = camera.translation()


    
    camera.setTranslation( mari.VectorN(-translation.x(),translation.y(),translation.z()))
    camera.setUp( mari.VectorN(-up.x(),up.y(),up.z()))
    camera.setLookAt( mari.VectorN(-lookAt.x(),lookAt.y(),lookAt.z()))

    core = PySide.QtCore

    def paintBufferFlip( scaleFactor ):
            paintBuffer = mari.canvases.paintBuffer()
            scale = paintBuffer.scale()
            scale = core.QSizeF( scale.width() * scaleFactor[0], scale.height() * scaleFactor[1] )
            paintBuffer.setScale( scale )

    paintBufferFlip((-1,1))

    def paintBufferRotate():
            paint_buffer = mari.canvases.paintBuffer()
            rotation = paint_buffer.rotation()
            paint_buffer.setRotation( 360-rotation )

    paintBufferRotate()


    def paintBufferTranslation():

            paint_buffer = mari.canvases.paintBuffer()
            translation = paint_buffer.translation()
            paint_buffer.setTranslation(core.QPointF(-translation.x(), translation.y()))

    paintBufferTranslation()



actionCameraInverseX = mari.actions.create( 'Invert Canvas X', 'cameraInverseX()' )

actionCameraInverseX.setShortcut("Ctrl+Shift+X")

mari.menus.addAction( actionCameraInverseX, "MainWindow/d&eTools/&Symmetry" )



def cameraInverseY():

    camera = mari.canvases.current().camera()

    lookAt = camera.lookAt()
    up = camera.up()
    translation = camera.translation()


    
    camera.setTranslation( mari.VectorN(translation.x(),-translation.y(),translation.z()))
    camera.setUp( mari.VectorN(up.x(),-up.y(),up.z()))
    camera.setLookAt( mari.VectorN(lookAt.x(),-lookAt.y(),lookAt.z()))

    core = PySide.QtCore

    def paintBufferFlip( scaleFactor ):
            paintBuffer = mari.canvases.paintBuffer()
            scale = paintBuffer.scale()
            scale = core.QSizeF( scale.width() * scaleFactor[0], scale.height() * scaleFactor[1] )
            paintBuffer.setScale( scale )

    paintBufferFlip((-1,1))

    def paintBufferRotate():
            paint_buffer = mari.canvases.paintBuffer()
            rotation = paint_buffer.rotation()
            paint_buffer.setRotation( 360-rotation )

    paintBufferRotate()


    def paintBufferTranslation():

            paint_buffer = mari.canvases.paintBuffer()
            translation = paint_buffer.translation()
            paint_buffer.setTranslation(core.QPointF(-translation.x(), translation.y()))

    paintBufferTranslation()



actionCameraInverseY = mari.actions.create( 'Invert Canvas Y', 'cameraInverseY()' )

actionCameraInverseY.setShortcut("Ctrl+Shift+Y")

mari.menus.addAction( actionCameraInverseY, "MainWindow/d&eTools/&Symmetry" )


def cameraInverseZ():

    camera = mari.canvases.current().camera()

    lookAt = camera.lookAt()
    up = camera.up()
    translation = camera.translation()


    
    camera.setTranslation( mari.VectorN(translation.x(),translation.y(),-translation.z()))
    camera.setUp( mari.VectorN(up.x(),up.y(),-up.z()))
    camera.setLookAt( mari.VectorN(lookAt.x(),lookAt.y(),-lookAt.z()))

    core = PySide.QtCore

    def paintBufferFlip( scaleFactor ):
            paintBuffer = mari.canvases.paintBuffer()
            scale = paintBuffer.scale()
            scale = core.QSizeF( scale.width() * scaleFactor[0], scale.height() * scaleFactor[1] )
            paintBuffer.setScale( scale )

    paintBufferFlip((-1,1))

    def paintBufferRotate():
            paint_buffer = mari.canvases.paintBuffer()
            rotation = paint_buffer.rotation()
            paint_buffer.setRotation( 360-rotation )

    paintBufferRotate()


    def paintBufferTranslation():

            paint_buffer = mari.canvases.paintBuffer()
            translation = paint_buffer.translation()
            paint_buffer.setTranslation(core.QPointF(-translation.x(), translation.y()))

    paintBufferTranslation()



actionCameraInverseZ = mari.actions.create( 'Invert Canvas Z', 'cameraInverseZ()' )

actionCameraInverseZ.setShortcut("Ctrl+Shift+Z")

mari.menus.addAction( actionCameraInverseZ, "MainWindow/d&eTools/&Symmetry" )







pal = mari.palettes.create("Symmetry Tools",w)
pal.setBodyWidget(w)
pal.show()
gui = PySide.QtGui
dir(PySide)
layout = gui.QHBoxLayout()
w.setLayout(layout)

pbSymmetryX = gui.QPushButton("Bake X")
layout.addWidget(pbSymmetryX)

pbSymmetryY = gui.QPushButton("Bake Y")
layout.addWidget(pbSymmetryY)

pbSymmetryZ = gui.QPushButton("Bake Z")
layout.addWidget(pbSymmetryZ)



connect(pbSymmetryX.clicked, symmetryBakeX)
connect(pbSymmetryY.clicked, symmetryBakeY)
connect(pbSymmetryZ.clicked, symmetryBakeZ)

comboSymmetryXYZ = gui.QComboBox()
comboSymmetryXYZ.addItem("Auto Clear Buffer")
comboSymmetryXYZ.addItem("Manually Clear Buffer")
layout.addWidget(comboSymmetryXYZ)

