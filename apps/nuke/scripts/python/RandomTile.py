import nuke
import random

#Copyright David Emeny 2011

################################ randomTile() ##############################################
#    Create RandomTile panel to get user input, then create the RandomTile node            #
#    (a group node with many other nodes inside and several controls on the front)         #
#                                                                                          #
#    Takes an image input and repeats it randomly at random sizes and rotations            #
#    Options to provide a source image to colour the tiles, a distort map to distort the   #
#    tiles, a weighting map to influence the distribution of the tiles and a ripple map    #
#    to makes the tiles move as a moving image passes underneath them.                     #
#                                                                                          #
#    Can make anything from 2 to 20,000 tiles (possibly much more), but will slow down the #
#    machine if the number is too high and too many options turned on. The upper limit     #
#    appears to be determined by the power of the machine and the time you are willing to  #
#    wait.                                                                                 #
############################################################################################


def randomTile():

    panel = randomTileMenu()
    panel.showModal()

    if panel.result == 0:
        return

if nuke.env['gui']:
    import nukescripts

    class randomTileMenu(nukescripts.PythonPanel):
        def __init__(self):
            nukescripts.PythonPanel.__init__(self, 'RandomTile options...', 'randomTilePanel')

            self.result = None
            
            #Title text
            titleText = nuke.Text_Knob("titleText"," ","<font color='white'><h3>RandomTile</h3></font>")
            self.addKnob(titleText)
            
            #Title text2
            titleText2 = nuke.Text_Knob("titleText2"," ","<font color='gray'><h5>David Emeny 2011</h5></font>")
            self.addKnob(titleText2)
            
            #horizontal rule
            separatorC = nuke.Text_Knob("separatorC","","")
            self.addKnob(separatorC)

            self.uAmount = nuke.String_Knob('uAmount','Amount of tiles:', '100')
            self.uAmount.setTooltip('This is the number of times your input image will be repeated. To fill the entire image, try a higher number such as 500-1000. Too high a number will slow things down, so be careful.')
            self.addKnob(self.uAmount)

            self.uScaleVariationX = nuke.String_Knob('uScaleVariationX','Scale Variation (0 to 1):', '0')
            self.uScaleVariationX.setTooltip('Use this to vary the width of the repeating image. 0 will keep them all the same size, 1 will choose random sizes between 0 and 100% of the chosen Tile Size.')
            self.addKnob(self.uScaleVariationX)

            self.uScaleVariationY = nuke.String_Knob('uScaleVariationY','                         ', '0')
            self.uScaleVariationY.setTooltip('Use this to vary the height of the repeating image. 0 will keep them all the same size, 1 will choose random sizes between 0 and 100% of the chosen Tile Size.')
            self.uScaleVariationY.setEnabled(False)
            self.addKnob(self.uScaleVariationY)

            self.uLockAspect = nuke.Boolean_Knob('uLockAspect','Lock aspect ratio',1)
            self.uLockAspect.setTooltip('When enabled it locks the Y scale to the X scale for each tile.')
            self.addKnob(self.uLockAspect)

            self.uRotateVariation = nuke.String_Knob('uRotateVariation','Rotation Variation (0 to 1):', '1')
            self.uRotateVariation.setTooltip('Use this to vary the rotation of the repeating image. 0 will not apply any rotation to the tiles, 1 will choose random rotations between -180 and 180 degrees.')
            self.addKnob(self.uRotateVariation)

            self.uTime = nuke.String_Knob('uTime','Time Variation (frames):', '0')
            self.uTime.setTooltip('For animated inputs, this will vary the time offset for each tile randomly. A value of 50 means the tiles will be offset by any number in the range -50 to 50. For best results, ensure your animated input has extra keyframes either side of your project timeline.')
            self.addKnob(self.uTime)


            self.uStackOrder = nuke.Enumeration_Knob('uStackOrder','Stack order:', ["No order", "Small at back", "Large at back"])
            self.uStackOrder.setTooltip('If you choose to have a size variation between tiles, this gives you the option to force the smaller tiles to be placed over the larger ones, or vice versa. Useful if you want to simulate distance.')
            self.uStackOrder.setEnabled(False)
            self.addKnob(self.uStackOrder)
            
            self.uDepth = nuke.Boolean_Knob('uDepth','Create depth matte',0)
            self.uDepth.setTooltip('When enabled, a depth matte is created in the depth channel, using the scale variation to simulate distance. Use a Z-Blur node afterwards to simulate depth of field, or grade using the depth channel.')
            self.uDepth.setEnabled(False)
            self.addKnob(self.uDepth)

            #horizontal rule
            separator1 = nuke.Text_Knob("separator","","")
            self.addKnob(separator1)

            self.uSecondInput = nuke.Boolean_Knob('uSecondInput','Use source image to colour tiles')
            self.uSecondInput.setTooltip('If this is selected, another input will appear. Plug in a second image and each tile will be coloured to the average colour of the pixels at that position on the second image. Use a brush stroke as an input and experiment with varying shapes, sizes and amounts to produce a "painted" image. Try using several different RandomTile nodes merged over each other')
            self.addKnob(self.uSecondInput)

            #horizontal rule
            separatorA = nuke.Text_Knob("separatorA",""," ")
            self.addKnob(separatorA)

            self.uEmboss = nuke.Boolean_Knob('uEmboss','Emboss tile')
            self.uEmboss.setTooltip('If this is selected, each tile will be highlighted along one side and darkened on the opposite side. Can only be used when a source image is used for the tile colour.')
            self.uEmboss.setEnabled(False)
            self.addKnob(self.uEmboss)

            #horizontal rule
            separator3 = nuke.Text_Knob("separator3","","")
            self.addKnob(separator3)

            self.uDistortMap = nuke.Boolean_Knob('uDistortMap','Use distort map (alpha)')
            self.uDistortMap.setTooltip('If this is selected, another input will appear. Plug in an image and the alpha will be used to distort the tile shapes. Try a lumakey of a moving image.')
            self.addKnob(self.uDistortMap)


            #horizontal rule
            separator4 = nuke.Text_Knob("separator4",""," ")
            self.addKnob(separator4)

            self.uWeighting = nuke.Boolean_Knob('uWeighting','Enable weighting map option (alpha)')
            self.uWeighting.setTooltip('If this is selected, another input and button will appear. Plug in an image and the alpha will be used to influence the randomness of the tile positions. White = very likely to attract tiles, Black = less likely, Mid grey = fairly likely.')
            self.addKnob(self.uWeighting)

            #horizontal rule
            separator5 = nuke.Text_Knob("separator5",""," ")
            self.addKnob(separator5)

            self.uRipple = nuke.Boolean_Knob('uRipple','Use ripple map (alpha)')
            self.uRipple.setTooltip('If this is selected, another input will appear. Plug in a moving image and the alpha will be used to push the tiles around over time. Try a lumakey of your source image. White = move tile max amount, Black = no movement, Mid grey = move halfway.')
            self.addKnob(self.uRipple)

            #horizontal rule
            separator6 = nuke.Text_Knob("separator6","","")
            self.addKnob(separator6)

            #buttons
            self.cancel = nuke.PyScript_Knob("Cancel","Cancel")
            self.ok = nuke.PyScript_Knob("OK","Ok")
            self.addKnob(self.cancel)
            self.addKnob(self.ok)
            

            self.setMinimumSize(450, 490)

        def knobChanged(self,knob):

            if (knob == self.ok):
                #check all input boxes are valid
                try:
                    #get values from the panel
                    uAmount = int(round(float(self.uAmount.value())))
                    uScaleVariationX = float(self.uScaleVariationX.value())
                    uScaleVariationY = float(self.uScaleVariationY.value())
                    uRotateVariation = float(self.uRotateVariation.value())
                    uTime = int(round(float(self.uTime.value())))

                    allValid = True
                except:
                    allValid = False

                #continue if so, do nothing if not
                if allValid == True:

                    #OK BUTTON PRESSED
                    self.result = 1
                    self.finishModalDialog(True)

                    #show progress window
                    task = nuke.ProgressTask("Random Tile")
                    task.setMessage("Creating RandomTile node...")
                    taskCancelled = False

                    #get boolean values from the panel
                    uLockAspect = self.uLockAspect.value()
                    uSecondInput = self.uSecondInput.value()
                    uEmboss = self.uEmboss.value()
                    uDistortMap = self.uDistortMap.value()
                    uWeighting = self.uWeighting.value()
                    uRipple = self.uRipple.value()
                    #set to default if the scale variation is zero
                    if (uScaleVariationX == 0 and uScaleVariationY == 0):
                        uStackOrder = "No order"
                        uDepth = False
                    else:
                        uStackOrder = self.uStackOrder.value()
                        uDepth = self.uDepth.value()

                    #set other values
                    uScale = max(min(1/(float(uAmount)/20),0.7),0.005) #the higher the amount of tiles, the smaller the scale by default
                    uBlur = 500

                    #create the nodes
                    noSelectedNode = False
                    try:
                        n = nuke.selectedNode()
                        nPos = [ n['xpos'].value(),n['ypos'].value() ]
                        n['selected'].setValue('False')
                    except:
                        noSelectedNode = True

                    #create group
                    g = nuke.createNode('Group')
                    if not noSelectedNode:
                    	#position RandomTile node below the selected node
                    	g['xpos'].setValue(nPos[0])
                    	g['ypos'].setValue(nPos[1] + 100)
                    g['name'].setValue(checkNodeName('RandomTile'))
                    #Add a custom tab
                    g.addKnob( nuke.Tab_Knob('RandomTile') )

                    #Add user controls
                    sizeKnob = nuke.Double_Knob('uSize','Tile scale')
                    sizeKnob.setValue(uScale)
                    sizeKnob.setRange(0,0.7)
                    sizeKnob.setTooltip('Adjust the overall size of all tiles. To change the scale variation, delete and create a new RandomTile node.')
                    g.addKnob(sizeKnob)

                    cropKnob = nuke.Boolean_Knob('cropChoice','Crop to format')
                    cropKnob.setValue(True)
                    cropKnob.setTooltip('Crop result to the project format.')
                    g.addKnob(cropKnob)

                    opKnob = nuke.Enumeration_Knob('uOperation','Merge operation', ["atop", "average", "color-burn", "color-dodge", "conjoint-over", "copy", "difference", "disjoint-over", "divide", "exclusion", "from", "geometric", "hard-light", "hypot", "in", "mask", "matte", "max", "min", "minus", "multiply", "out", "over", "overlay", "plus", "screen", "soft-light", "stencil", "under", "xor"])
                    opKnob.setValue('over')
                    opKnob.setTooltip('Change the merge operation on every tile.')
                    g.addKnob(opKnob)


                    if uSecondInput:
                        blurKnob = nuke.Int_Knob('uBlur2','Source blur')
                        blurKnob.setValue(uBlur)
                        blurKnob.setTooltip('Controls the amount the source image is blurred after being multiplied by the tile alpha. Decrease to reveal colour variation within each tile.')
                        g.addKnob(blurKnob)

                        if uEmboss:
                            embSizeKnob = nuke.WH_Knob('uEmbSize','Emboss size')
                            embSizeKnob.setValue([5,4])
                            embSizeKnob.setTooltip('Controls the amount of embossing applied to the tiles. Just a simple x and y offset.')
                            g.addKnob(embSizeKnob)

                            embMultKnob = nuke.Double_Knob('uEmbMult','Emboss highlight')
                            embMultKnob.setValue(1.3)
                            embMultKnob.setRange(1,3)
                            embMultKnob.setTooltip('Controls the brightness of the embossed edge. A simple multiply: 1 = no highlight.')
                            g.addKnob(embMultKnob)

                            embMultKnob2 = nuke.Double_Knob('uEmbMult2','Emboss shadow')
                            embMultKnob2.setValue(0.6)
                            embMultKnob2.setRange(0,1)
                            embMultKnob2.setTooltip('Controls the darkness of the embossed edge. A simple multiply: 1 = no shadow.')
                            g.addKnob(embMultKnob2)

                    if uDistortMap:
                        distortKnob = nuke.Int_Knob('uDistort','Tile distort')
                        distortKnob.setValue(50)
                        distortKnob.setTooltip('Amount the tiles are distorted by the Distort Map. Plug an image alpha into the Distort input. If you are also using a source image to colour the tiles, use a lumakey of that same image for your Distort map.')
                        g.addKnob(distortKnob)
                        bbKnob = nuke.Int_Knob('uBbox','Increase Bbox')
                        bbKnob.setValue(50)
                        bbKnob.setTooltip('If you see hard edges appearing, the tile has been distorted beyond its bounding box. Increase this value gradually until all artifacts are gone. Too high and it will slow things down.')
                        g.addKnob(bbKnob)

                    if uRipple:
                        rippleKnob = nuke.Int_Knob('uRippleAmount','Tile ripple')
                        rippleKnob.setValue(50)
                        rippleKnob.setTooltip('Amount the tiles are moved by based on the Ripple Map. Plug an image alpha into the Ripple input. If you are also using a source image to colour the tiles, try a lumakey of that same image for your Distort map. Your ripple map needs to be animated for any tile movement to happen over time.')
                        g.addKnob(rippleKnob)

                        fixButtonKnob = nuke.PyScript_Knob('Fix ripple')
                        fixButtonKnob.setValue('RandomTile.fixRipple()')
                        fixButtonKnob.setTooltip('If you change or rename the viewer in your script, the ripple effect will stop working. Press this button to fix the issue. It creates a new Viewer inside the RandomTile node (required for the pixel sampling to work correctly).')
                        g.addKnob(fixButtonKnob)

                    if uWeighting:
                        #horizontal rule
                        separator2 = nuke.Text_Knob("separator2","","")
                        g.addKnob(separator2)

                        weightButtonKnob = nuke.PyScript_Knob('Adjust for weighting')
                        weightButtonKnob.setValue('RandomTile.adjustWeighting()')
                        weightButtonKnob.setTooltip('Adjusts positions of all tiles based on the weighting image. Plug an image alpha into the Weight input.')
                        g.addKnob(weightButtonKnob)

                        avoidKnob = nuke.Boolean_Knob('avoidChoice','Avoid black')
                        avoidKnob.setValue(False)
                        avoidKnob.setTooltip('If this is selected, it will try its best not to place any tiles on a black (zero alpha) pixel. However, this will increase calculation time and some stray tiles may still appear on black if the white/grey areas are too small.')
                        g.addKnob(avoidKnob)

                    endHR = nuke.Text_Knob("endHR","","")
                    g.addKnob(endHR)
                    tilesNumKnob = nuke.Text_Knob('Number of tiles',"","Number of tiles: " + str(uAmount))
                    g.addKnob(tilesNumKnob)
                    if uAmount > 30:
                        warningKnob = nuke.Text_Knob('warning',"","<font color='gray'><h5>Do not attempt to open this group node\n</h5></font>")
                        g.addKnob(warningKnob)

                    if noSelectedNode == False:
                        g.setInput(0,n)

                    #update the progress bar
                    taskCounter = 1
                    task.setMessage("Generating tiles...")
                    task.setProgress(taskCounter)
                    if task.isCancelled():
                            taskCancelled = True
                            nuke.delete(g)

                    if taskCancelled == False:

                        g.begin()
                        inp = nuke.createNode('Input', inpanel = False)
                        inp['name'].setValue('Tile')
                        inp['selected'].setValue('False')

                        if uSecondInput:
                            inp2 = nuke.createNode('Input', inpanel = False)
                            inp2['name'].setValue('Source')
                            inp2['selected'].setValue('False')
                            shuff = nuke.createNode('Shuffle', inpanel = False)
                            shuff['alpha'].setValue('white')
                            shuff['selected'].setValue('False')

                        if uDistortMap:
                            dm = nuke.createNode('Input', inpanel = False)
                            dm['name'].setValue('Distort')
                            dm['selected'].setValue('False')

                            #along with the input, plus it with a shuffle set to black
                            #so the node doesn't cause an error when no alpha found

                            dmS = nuke.createNode('Shuffle', inpanel = False)
                            dmS['red'].setValue('black')
                            dmS['green'].setValue('black')
                            dmS['blue'].setValue('black')
                            dmS['alpha'].setValue('black')
                            dmS['selected'].setValue('False')

                            dmM = nuke.createNode('Merge2', inpanel = False)
                            dmM['operation'].setValue('plus')
                            dmM['selected'].setValue('False')

                            #connect them up
                            dmM.setInput(0,dm)
                            dmM.setInput(1,dmS)
                            dmS.setInput(0,dm)

                        if uWeighting:
                            wm = nuke.createNode('Input', inpanel = False)
                            wm['name'].setValue('Weight')
                            wm['selected'].setValue('False')

                        if uRipple:
                            rm = nuke.createNode('Input', inpanel = False)
                            rm['name'].setValue('Ripple')
                            rm['selected'].setValue('False')

                            vi = nuke.createNode('Viewer')
                            vi.setInput(0,rm)
                            vi['selected'].setValue('False')


                        #fit project width
                        r = nuke.createNode('Reformat', inpanel = False)
                        r['selected'].setValue('False')
                        r.setInput(0,inp)

                        #resize to user value
                        s = nuke.createNode('Transform', inpanel = False)
                        s['selected'].setValue('False')
                        s['label'].setValue('SCALE')
                        s['center'].setValue([0,0])
                        s['scale'].setExpression('uSize')

                        #create mini script for each tile-----------------------------------------------
                        dotNodes = []
                        tNodes = []
                        random.seed()

                        for i in range(0,uAmount):

                            #update the progress bar
                            task.setProgress(taskCounter)

                            if uTime > 0:
                                off = nuke.createNode('TimeOffset', inpanel = False)
                                timeVal = random.randint(-uTime,uTime)
                                off['time_offset'].setValue(timeVal)
                                off['selected'].setValue('False')
                                off.setInput(0,s)

                            t = nuke.createNode('Transform', inpanel = False)
                            t['selected'].setValue('False')

                            xVal = random.randint(0,r.width())
                            yVal = random.randint(0,r.height())

                            rotValue = random.randint(-180,180) * uRotateVariation
                            scaleValueX = float(((random.randint(-uScaleVariationX*100,uScaleVariationX*100))+100))/100
                            scaleValueX = max(scaleValueX,0.1)

                            if uLockAspect:
                                scaleValueY = scaleValueX
                                avgScale = scaleValueX
                            else:
                                scaleValueY = float(((random.randint(-uScaleVariationY*100,uScaleVariationY*100))+100))/100
                                scaleValueY = max(scaleValueY,0.1)
                                avgScale = (scaleValueX+scaleValueY)/2

                            t['translate'].setExpression(str(xVal) + '-((width * uSize)/2)',0)
                            t['translate'].setExpression(str(yVal) + '-((height * uSize)/2)',1)
                            t['center'].setExpression('(width * uSize)/2',0)
                            t['center'].setExpression('(width * uSize)/2',1)
                            t['rotate'].setValue(rotValue)
                            t['scale'].setValue(scaleValueX,0)
                            t['scale'].setValue(scaleValueY,1)
                            t['label'].setValue('main')

                            if uTime > 0:
                                t.setInput(0,off)
                            else:
                                t.setInput(0,s)

                            if uRipple:
                                rip = nuke.createNode('Transform', inpanel = False)
                                rip['label'].setValue('Ripple')
                                rip['translate'].setExpression('([sample Ripple red ' + t['name'].value() + '.translate.x ' + t['name'].value() + '.translate.y] * uRippleAmount) - (uRippleAmount/2)')
                                rip['selected'].setValue('False')

                            if uDistortMap:
                                #create AdjBBox node
                                adj = nuke.createNode('AdjBBox', inpanel = False)
                                adj['numpixels'].setValue(50)
                                adj['numpixels'].setExpression('uBbox')
                                #adj['selected'].setValue('False')

                                #create copy node
                                cpy2 = nuke.createNode('Copy', inpanel = False)
                                cpy2['from0'].setValue('rgba.alpha')
                                cpy2['from1'].setValue('rgba.alpha')
                                cpy2['to0'].setValue('forward.u')
                                cpy2['to1'].setValue('forward.v')
                                cpy2['bbox'].setValue('B')
                                cpy2['selected'].setValue('False')

                                #create iDistort node
                                dist = nuke.createNode('IDistort', inpanel = False)
                                dist['channels'].setValue('rgba')
                                dist['uv'].setValue('motion')
                                dist['uv_scale'].setExpression('uDistort')
                                dist['selected'].setValue('False')

                                #create BlackOutside node
                                blk = nuke.createNode('BlackOutside', inpanel = False)
                                blk['selected'].setValue('False')

                            if uSecondInput:
                                #create merge node
                                mer = nuke.createNode('Merge2', inpanel = False)
                                mer['bbox'].setValue('A')
                                mer['operation'].setValue('mask')
                                mer['selected'].setValue('False')

                                #create blur node
                                blr = nuke.createNode('Blur', inpanel = False)
                                blr['size'].setExpression(str(avgScale) + '*uBlur2*uSize*6')
                                blr['selected'].setValue('False')

                                #crop to original bbox after blur
                                blurCrop = nuke.createNode('Crop', inpanel = False)

                                #determine which was the previous node with the correct bbox
                                if uDistortMap:
                                    prevNodeName = mer.name()
                                else:
                                    if uRipple:
                                        prevNodeName = rip.name()
                                    else:
                                        prevNodeName = t.name()

                                blurCrop['box'].setExpression(prevNodeName + '.bbox.x',0)
                                blurCrop['box'].setExpression(prevNodeName + '.bbox.y',1)
                                blurCrop['box'].setExpression(prevNodeName + '.bbox.r',2)
                                blurCrop['box'].setExpression(prevNodeName + '.bbox.t',3)
                                blurCrop['selected'].setValue('False')

                                #create unpremult node
                                unp = nuke.createNode('Unpremult', inpanel = False)
                                unp['selected'].setValue('False')

                                #create copy node
                                cpy = nuke.createNode('Copy', inpanel = False)
                                cpy['selected'].setValue('False')

                                #create premult node
                                p = nuke.createNode('Premult', inpanel = False)
                                p['selected'].setValue('False')


                                if uEmboss:
                                    #create transform node
                                    embT = nuke.createNode('Transform', inpanel = False)
                                    embT['translate'].setExpression('uEmbSize')
                                    embT['selected'].setValue('False')

                                    #create multiply node
                                    embM = nuke.createNode('Multiply', inpanel = False)
                                    embM['value'].setExpression('uEmbMult')
                                    embM['channels'].setValue('rgb')
                                    embM['maskChannelMask'].setValue('rgba.alpha')
                                    embM['invert_mask'].setValue(True)
                                    embM['selected'].setValue('False')

                                    #create 2nd transform node
                                    embT2 = nuke.createNode('Transform', inpanel = False)
                                    embT2['translate'].setExpression('-uEmbSize')
                                    embT2['selected'].setValue('False')

                                    #create 2nd multiply node
                                    embM2 = nuke.createNode('Multiply', inpanel = False)
                                    embM2['value'].setExpression('uEmbMult2')
                                    embM2['channels'].setValue('rgb')
                                    embM2['maskChannelMask'].setValue('rgba.alpha')
                                    embM2['invert_mask'].setValue(True)
                                    embM2['selected'].setValue('False')


                                #link them all up-------------------------------------------------
                                mer.setInput(0,shuff)

                                if uDistortMap:
                                    if uRipple:
                                        adj.setInput(0,rip)
                                    else:
                                        adj.setInput(0,t)
                                    cpy2.setInput(0,adj)
                                    cpy2.setInput(1,dmM)
                                    dist.setInput(0,cpy2)
                                    blk.setInput(0,dist)
                                    mer.setInput(1,blk)
                                else:
                                    if uRipple:
                                        mer.setInput(1,rip)
                                    else:
                                        mer.setInput(1,t)

                                blr.setInput(0,mer)
                                blurCrop.setInput(0,blr)
                                unp.setInput(0,blurCrop)
                                cpy.setInput(0,unp)

                                if uDistortMap:
                                    cpy.setInput(1,blk)
                                else:
                                    if uRipple:
                                        cpy.setInput(1,rip)
                                    else:
                                        cpy.setInput(1,t)

                                p.setInput(0,cpy)


                            if uDepth:
                                    #create shuffle node
                                    #copy alpha to depth
                                    depS = nuke.createNode('Shuffle', inpanel = False)
                                    depS['black'].setValue('alpha')
                                    depS['out2'].setValue('depth')
                                    depS['selected'].setValue('False')

                                    #create multiply node
                                    #mult the depth based on the scale variation
                                    depM = nuke.createNode('Multiply', inpanel = False)
                                    depM['channels'].setValue('depth')
                                    if (uStackOrder == "Small at back"):
                                        depM['value'].setValue(1-((0 - (((scaleValueX+scaleValueY)/2)) /2)+1))
                                    else:
                                        depM['value'].setValue(1-(((scaleValueX+scaleValueY)/2)/2))

                                    depM['selected'].setValue('False')
                                    #connect the two
                                    depM.setInput(0,depS)

                            #create dot node for the end of each tile 'comp'
                            endDot = nuke.createNode('Dot', inpanel = False)
                            endDot['selected'].setValue('False')

                            if uDistortMap and not uSecondInput:
                                if uRipple:
                                    adj.setInput(0,rip)
                                else:
                                    adj.setInput(0,t)
                                cpy2.setInput(0,adj)
                                cpy2.setInput(1,dmM)


                            if uSecondInput:

                                if uEmboss:
                                    embT.setInput(0,p)
                                    embM.setInput(0,p)
                                    embM.setInput(1,embT)
                                    embT2.setInput(0,embM)
                                    embM2.setInput(0,embM)
                                    embM2.setInput(1,embT2)
                                    if uDepth:
                                        depS.setInput(0,embM2)
                                        endDot.setInput(0,depM)
                                    else:
                                        endDot.setInput(0,embM2)
                                else:
                                    if uDepth:
                                        depS.setInput(0,p)
                                        endDot.setInput(0,depM)
                                    else:
                                        endDot.setInput(0,p)
                            else:
                                if uDistortMap:
                                    if uDepth:
                                        depS.setInput(0,blk)
                                        endDot.setInput(0,depM)
                                    else:
                                        endDot.setInput(0,blk)
                                else:
                                    if uRipple:
                                        if uDepth:
                                            depS.setInput(0,rip)
                                            endDot.setInput(0,depM)
                                        else:
                                            endDot.setInput(0,rip)
                                    else:
                                        if uDepth:
                                            depS.setInput(0,t)
                                            endDot.setInput(0,depM)
                                        else:
                                            endDot.setInput(0,t)


                            if (uScaleVariationX > 0 or uScaleVariationY > 0)  and (uStackOrder == "Small at back" or uStackOrder == "Large at back"):
                                #sort the transform nodes into order of scale
                                #so the smallest ones are underneath the large ones
                                x = 0
                                inserted = False
                                for tn in tNodes:
                                    tnAvgScale = (tn['scale'].value()[0] + tn['scale'].value()[1]) / 2
                                    if (uStackOrder == "Small at back"):
                                        if tnAvgScale >= avgScale:
                                                tNodes.insert(x,t)
                                                dotNodes.insert(x,endDot)
                                                inserted = True
                                                break
                                    else:
                                        if tnAvgScale <= avgScale:
                                                tNodes.insert(x,t)
                                                dotNodes.insert(x,endDot)
                                                inserted = True
                                                break
                                    x = x + 1
                                if (inserted == False):
                                    tNodes.append(t)
                                    dotNodes.append(endDot)


                            else:
                                tNodes.append(t)
                                dotNodes.append(endDot)

                            taskCounter += 100/uAmount
                            if task.isCancelled():
                                taskCancelled = True
                                break

                        if taskCancelled == False:

                            #create merge
                            m = nuke.createNode('Merge2', inpanel = False)
                            m['operation'].setExpression('uOperation')
                            if uDepth:
                                m['also_merge'].setValue('depth')

                            m['selected'].setValue('False')


                            mInp = 0
                            for d in dotNodes:
                                #skip the mask input
                                if mInp == 2:
                                    mInp = 3
                                #connect the dot to the merge
                                m.setInput(mInp, d)
                                mInp = mInp + 1
                            m['selected'].setValue('False')

                            c = nuke.createNode('Crop', inpanel = False)
                            c['disable'].setExpression('1-cropChoice')
                            c['selected'].setValue('False')
                            c.setInput(0,m)

                            #close group
                            o = nuke.createNode('Output', inpanel = False)
                            o.setInput(0,c)
                            g.end()

                        else:
                            g.end()
                            nuke.delete(g)

            elif (knob == self.cancel):
                #CANCEL BUTTON PRESSED
                self.result = 0
                self.finishModalDialog(True)

            elif (knob == self.uLockAspect): #--------------------PANEL KNOB CALLBACKS-----------------------------
                #uLockAspect box UPDATED

                #check if either of the values is 'bad' (non numerical)
                xBad = False
                yBad = False

                try:
                    float(self.uScaleVariationX.value())
                except:
                    xBad = True

                try:
                    float(self.uScaleVariationY.value())
                except:
                    yBad = True

                if self.uLockAspect.value()==True:
                    if xBad:
                        self.uScaleVariationX.setLabel("<font color='red'>Scale Variation (0 to 1):</font>")
                    else:
                        self.uScaleVariationX.setLabel('Scale Variation (0 to 1):')
                    self.uScaleVariationY.setLabel('                         ')

                else:
                    if xBad:
                        self.uScaleVariationX.setLabel("<font color='red'>X Scale Variation (0 to 1):</font>")
                    else:
                        self.uScaleVariationX.setLabel('X Scale Variation (0 to 1):')

                    if yBad:
                        self.uScaleVariationY.setLabel("<font color='red'>Y Scale Variation (0 to 1):</font>")
                    else:
                        self.uScaleVariationY.setLabel('Y Scale Variation (0 to 1):')

                self.uScaleVariationY.setEnabled(not self.uLockAspect.value())

                if xBad:
                    self.uScaleVariationY.setValue('0')
                else:
                    self.uScaleVariationY.setValue(self.uScaleVariationX.value())


            elif (knob == self.uAmount): #--------------CLAMP VALUES ON OTHER FIELDS------------
                try:
                    boxVal = int(round(float(self.uAmount.value())))
                    self.uAmount.setLabel("Amount of tiles:")
                    if boxVal < 2:
                        self.uAmount.setValue('2')
                    else:
                        self.uAmount.setValue(str(boxVal))
                except:
                    self.uAmount.setLabel("<font color='red'>Amount of tiles:</font>")


            elif (knob == self.uScaleVariationX):
                try:
                    boxVal = float(self.uScaleVariationX.value())
                    if self.uLockAspect.value()==True:
                        self.uScaleVariationX.setLabel("Scale Variation (0 to 1):")
                    else:
                        self.uScaleVariationX.setLabel('X Scale Variation (0 to 1):')

                    if boxVal < 0:
                        self.uScaleVariationX.setValue('0')
                    elif boxVal > 1:
                        self.uScaleVariationX.setValue('1')

                    #check if the x and y are both zero
                    try:
                        yVal = float(self.uScaleVariationY.value())
                    except:
                        yVal = 0

                    if (boxVal == 0 and yVal == 0):
                        #disable the stack order and depth knobs
                        self.uStackOrder.setEnabled(False)
                        self.uDepth.setEnabled(False)
                    else:
                        #enable the stack order and depth knobs
                        self.uStackOrder.setEnabled(True)
                        self.uDepth.setEnabled(True)

                except:
                    if self.uLockAspect.value()==True:
                        self.uScaleVariationX.setLabel("<font color='red'>Scale Variation (0 to 1):</font>")
                    else:
                        self.uScaleVariationX.setLabel("<font color='red'>X Scale Variation (0 to 1):</font>")
                    self.uStackOrder.setEnabled(False)
                    self.uDepth.setEnabled(False)

            elif (knob == self.uScaleVariationY):
                try:
                    boxVal = float(self.uScaleVariationY.value())
                    if self.uLockAspect.value()==True:
                        self.uScaleVariationY.setLabel('                         ')
                    else:
                        self.uScaleVariationY.setLabel('Y Scale Variation (0 to 1):')

                    if boxVal < 0:
                        self.uScaleVariationY.setValue('0')
                    elif boxVal > 1:
                        self.uScaleVariationY.setValue('1')

                    #check if the x and y are both zero
                    try:
                        xVal = float(self.uScaleVariationX.value())
                    except:
                        xVal = 0

                    if (boxVal == 0 and xVal == 0):
                        #disable the stack order and depth knobs
                        self.uStackOrder.setEnabled(False)
                        self.uDepth.setEnabled(False)
                    else:
                        #enable the stack order and depth knobs
                        self.uStackOrder.setEnabled(True)
                        self.uDepth.setEnabled(True)

                except:
                    if self.uLockAspect.value()==True:
                        self.uScaleVariationY.setLabel('                         ')
                    else:
                        self.uScaleVariationY.setLabel("<font color='red'>Y Scale Variation (0 to 1):</font>")

                    self.uStackOrder.setEnabled(False)
                    self.uDepth.setEnabled(False)


            elif (knob == self.uRotateVariation):
                try:
                    boxVal = float(self.uRotateVariation.value())
                    self.uRotateVariation.setLabel("Rotation Variation (0 to 1):")

                    if boxVal < 0:
                        self.uRotateVariation.setValue('0')
                    elif boxVal > 1:
                        self.uRotateVariation.setValue('1')
                except:
                    self.uRotateVariation.setLabel("<font color='red'>Rotation Variation (0 to 1):</font>")

            elif (knob == self.uTime):
                try:
                    boxVal = int(round(float(self.uTime.value())))
                    self.uTime.setLabel("Time Variation (frames):")
                    if boxVal < 0:
                        self.uTime.setValue('0')
                    else:
                        self.uTime.setValue(str(boxVal))
                except:
                    self.uTime.setLabel("<font color='red'>Time Variation (frames):</font>")

            elif (knob == self.uSecondInput):
                if self.uSecondInput.value() == True:
                    self.uEmboss.setEnabled(True)
                else:
                    self.uEmboss.setValue(False)
                    self.uEmboss.setEnabled(False)



################################ adjustWeighting() ############################################
#    Takes each tile and chooses new Translate coordinates for its main Transform node.       #
#    Samples the Weighting Map input and uses probability to encourage the random coordinates #
#    to cluster on the whiter areas of the Weighting Map. It chooses a random position,       #
#    samples the Map, converts that alpha value to something in the range 0-10, where 0 is    #
#    white and 10 is black. It then loops, picking a random number between 0 and that number  #
#    generating a new coordinate each time and only decides on that coordinate when the       #
#    number hits 0. The effect is, if the pixel is white, it picks a number between 0 and 0   #
#    and there's a 1 in 1 chance of it picking 0, so that coordinate is used. If the pixel is #
#    black, it picks a number between 0 and 10, so there's a 1 in 10 chance it will be 0.     #
#    A mid grey pixel would have a 1 in 5 chance of being chosen. There is a timeout of 100   #
#    loops in case a coordinate is never chosen (if the map was all black for example).       #
#    There is also the option to Avoid Black, in which case it will always discard            #
#    coordinates on a black pixel, unless the timeout is reached.                             #
###############################################################################################


def adjustWeighting():
    g = nuke.thisNode()
    avoidBlack = g['avoidChoice'].value()

    #get width and height
    for r in g.nodes():
        if r.Class()=='Reformat':
            w = r.width()
            h = r.height()
            break

    #get weight input node
    for wi in g.nodes():
        if wi.Class()=='Input' and wi['name'].value()=='Weight':
            wm = wi
            break

    random.seed()

    timeOut=100

    for n in g.nodes():
        if n.Class()=='Transform' and n['label'].value()=='main':
            zeroReached = False
            i = 0
            while (not zeroReached) and (i < timeOut):
                xVal = random.randint(0,w)
                yVal = random.randint(0,h)
                try:
                    v = wm.sample("a", xVal, yVal) #get alpha value at this pixel in the weight map
                    v = max(0,v)
                    v = min(1,v)
                    v = int(10 - (v * 10)) #white=0, black=10, midGrey=5
                except:
                    v = 0

                r = random.randint(0,v)
                if (r==0):
                    if avoidBlack:
                        if v!=10: #if black, don't use that position, unless timeout happens
                            zeroReached = True
                    else:
                        zeroReached = True
                i = i + 1 #timeout after 100

                n['translate'].setExpression(str(xVal) + '-((width * uSize)/2)',0)
                n['translate'].setExpression(str(yVal) + '-((height * uSize)/2)',1)


################################ fixRipple() ##############################################
#   If user creates a new viewer in their script, the ripple effect will stop working     #
#   because the TCL sample function needs to be 'looking' at the ripple image input       #
###########################################################################################


def fixRipple():
    g = nuke.thisNode()

    #delete any viewer nodes inside the group
    for n in g.nodes():
        if n.Class()== 'Viewer':
            nuke.delete(n)

    #open the group and connect a new viewer to the Ripple input
    g.begin()
    v = nuke.createNode('Viewer')
    v.setInput(0,nuke.toNode('Ripple'))
    g.end()



################################ checkNodeName() ##########################################
#    Takes a string and checks if there is another node with that name already            #
#    Adds numbers to the end until it makes one that doesn't already exist and returns it #
###########################################################################################

def checkNodeName(theName):
    #adds a number to the string if another node
    #exists with that name, otherwise just returns the string
    i = 1
    stillChecking = True
    origName = theName
    while stillChecking:
        alreadyUsed = False
        for a in nuke.allNodes():
            if (a['name'].value()==(theName)):
                alreadyUsed = True  
                break
        if alreadyUsed:
            theName = origName + str(i)
            i = i+1 
        else:
            stillChecking=False

    return theName

