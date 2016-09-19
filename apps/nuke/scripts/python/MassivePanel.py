import nuke
import nukescripts
import re



class MassivePanel(nukescripts.PythonPanel):
    def __init__(self):
        nukescripts.PythonPanel.__init__(self, 'MassivePanel', 'com.ohufx.MassivePanel')



############# setting help messages
        KnobInfo = " type knob's name in, also you can Ctrl+Drag&Drop from the knob you want to adjust , then if you will click in value knob and back click in Knob field it will automaticly extract knob name for you (trying to make it better in next version :)" 
        ArrayInfo = "You have to set what exactly you want to change, All - will set same value on xyz, X , Y , Z - will set value only on your selection x,y or z"
        ValueInfo = "set new value for selected nodes" 
        IncrInfo = "set here increment between values, for example if value=3 and increment 2 - you will have 3,5,7,9..."
        KindInfo = "put String if you want to set string and finally put Expression if you entering expression"


#############creating knobs

        self.Knob = nuke.String_Knob( KnobInfo, "Knob:")
        self.Value = nuke.String_Knob(ValueInfo,"Value:")
        self.Array = nuke.Enumeration_Knob(ArrayInfo,"Array:",[ "All","X","Y","Z"],)
        self.Kind = nuke.Enumeration_Knob(KindInfo,"Kind:",[ "Float","String", "Expression"],)
        self.Kind.clearFlag(nuke.STARTLINE)
        self.Increment = nuke.String_Knob(IncrInfo,"Increment:","0")
        self.Increment.clearFlag(nuke.STARTLINE)
        self.Go = nuke.PyScript_Knob("Go", "Go")

############applying knobs to panel in order
        for k in (self.Knob,self.Value,self.Increment,self.Array,self.Kind,self.Go):
            self.addKnob(k)


############### setting basic function
    def knobChanged(self,knob):
            if knob in (self.Knob,self.Value,self.Array,self.Increment):
              string = self.Knob.value()
              if ':' in string:
                  firstSplit = string.rsplit('.')[1] 
                  self.Knob.setValue(firstSplit)

            elif knob == self.Go:
              s = self.Value.value()
              Knob = self.Knob.value()
              Value = self.Value.value()
              array = self.Array.value()
              kind = self.Kind.value()
              incr = self.Increment.value()
              incr = float(incr)  
              u = 0
              n = nuke.selectedNodes()

######## setting float values
              if array== "All" and kind == "Float":
                 Value = float(Value)
                 for n in n:
                    n[Knob].setValue(Value+u)
                    u = incr+ u
              if array== "X" and kind == "Float":
                 Value = float(Value)
                 for n in n:
                    n[Knob].setValue(Value+u,0) 
                    u = incr+ u  
              if array== "Y" and kind == "Float":
                 Value = float(Value)
                 for n in n:
                    n[Knob].setValue(Value+u,1) 
                    u = incr+ u  
              if array== "Z" and kind == "Float":
                 Value = float(Value)
                 for n in n:
                    n[Knob].setValue(Value+u,2)
                    u = incr+ u
######## setting string values

              if array== "All" and kind == "String":
                 for n in n:
                    n[Knob].setValue(Value)
              if array== "X" and kind == "String":
                 for n in n:
                    n[Knob].setValue(Value,0) 
              if array== "Y" and kind == "String":
                 for n in n:
                    n[Knob].setValue(Value,1) 
              if array== "Z" and kind == "String":
                 for n in n:
                    n[Knob].setValue(Value,2)

######## setting expression  values

              if array== "All" and kind == "Expression":
                 for n in n:
                    n[Knob].setExpression(Value)
              if array== "X" and kind == "Expression":
                 for n in n:
                    n[Knob].setExpression(Value,0) 
              if array== "Y" and kind == "Expression":
                 for n in n:
                    n[Knob].setExpression(Value,1) 
              if array== "Z" and kind == "Expression":
                 for n in n:
                    n[Knob].setExpression(Value,2)

   




#def addMassivePanel():
####myPanel = MassivePanel()
####return myPanel.addToPane()
#paneMenu = nuke.menu('Pane')
#paneMenu.addCommand('MassivePanel', addMassivePanel)
#nukescripts.registerPanel( 'com.ohufx.MassivePanel', #addMassivePanel)
import nuke
import nukescripts
import re



class MassivePanel(nukescripts.PythonPanel):
    def __init__(self):
        nukescripts.PythonPanel.__init__(self, 'MassivePanel', 'com.ohufx.MassivePanel')



############# setting help messages
        KnobInfo = " type knob's name in, also you can Ctrl+Drag&Drop from the knob you want to adjust , then if you will click in value knob and back click in Knob field it will automaticly extract knob name for you (trying to make it better in next version :)" 
        ArrayInfo = "You have to set what exactly you want to change, All - will set same value on xyz, X , Y , Z - will set value only on your selection x,y or z"
        ValueInfo = "set new value for selected nodes" 
        IncrInfo = "set here increment between values, for example if value=3 and increment 2 - you will have 3,5,7,9..."
        KindInfo = "put String if you want to set string and finally put Expression if you entering expression"


#############creating knobs

        self.Knob = nuke.String_Knob( KnobInfo, "Knob:")
        self.Value = nuke.String_Knob(ValueInfo,"Value:")
        self.Array = nuke.Enumeration_Knob(ArrayInfo,"Array:",[ "All","X","Y","Z"],)
        self.Kind = nuke.Enumeration_Knob(KindInfo,"Kind:",[ "Float","String", "Expression"],)
        self.Kind.clearFlag(nuke.STARTLINE)
        self.Increment = nuke.String_Knob(IncrInfo,"Increment:","0")
        self.Increment.clearFlag(nuke.STARTLINE)
        self.Go = nuke.PyScript_Knob("Go", "Go")

############applying knobs to panel in order
        for k in (self.Knob,self.Value,self.Increment,self.Array,self.Kind,self.Go):
            self.addKnob(k)


############### setting basic function
    def knobChanged(self,knob):
            if knob in (self.Knob,self.Value,self.Array,self.Increment):
              string = self.Knob.value()
              if ':' in string:
                  firstSplit = string.rsplit('.')[1] 
                  self.Knob.setValue(firstSplit)

            elif knob == self.Go:
              s = self.Value.value()
              Knob = self.Knob.value()
              Value = self.Value.value()
              array = self.Array.value()
              kind = self.Kind.value()
              incr = self.Increment.value()
              incr = float(incr)  
              u = 0
              n = nuke.selectedNodes()

######## setting float values
              if array== "All" and kind == "Float":
                 Value = float(Value)
                 for n in n:
                    n[Knob].setValue(Value+u)
                    u = incr+ u
              if array== "X" and kind == "Float":
                 Value = float(Value)
                 for n in n:
                    n[Knob].setValue(Value+u,0) 
                    u = incr+ u  
              if array== "Y" and kind == "Float":
                 Value = float(Value)
                 for n in n:
                    n[Knob].setValue(Value+u,1) 
                    u = incr+ u  
              if array== "Z" and kind == "Float":
                 Value = float(Value)
                 for n in n:
                    n[Knob].setValue(Value+u,2)
                    u = incr+ u
######## setting string values

              if array== "All" and kind == "String":
                 for n in n:
                    n[Knob].setValue(Value)
              if array== "X" and kind == "String":
                 for n in n:
                    n[Knob].setValue(Value,0) 
              if array== "Y" and kind == "String":
                 for n in n:
                    n[Knob].setValue(Value,1) 
              if array== "Z" and kind == "String":
                 for n in n:
                    n[Knob].setValue(Value,2)

######## setting expression  values

              if array== "All" and kind == "Expression":
                 for n in n:
                    n[Knob].setExpression(Value)
              if array== "X" and kind == "Expression":
                 for n in n:
                    n[Knob].setExpression(Value,0) 
              if array== "Y" and kind == "Expression":
                 for n in n:
                    n[Knob].setExpression(Value,1) 
              if array== "Z" and kind == "Expression":
                 for n in n:
                    n[Knob].setExpression(Value,2)

   




#def addMassivePanel():
####myPanel = MassivePanel()
####return myPanel.addToPane()
#paneMenu = nuke.menu('Pane')
#paneMenu.addCommand('MassivePanel', addMassivePanel)
#nukescripts.registerPanel( 'com.ohufx.MassivePanel', #addMassivePanel)
