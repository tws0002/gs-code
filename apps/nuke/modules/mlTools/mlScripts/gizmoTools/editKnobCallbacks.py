import nuke,nukescripts

class ShapeAndCVPanel( nukescripts.PythonPanel ):
    def __init__( self, node ):
        nukescripts.PythonPanel.__init__( self, 'edit callbacks' )
        # CREATE KNOBS
        self.callback = nuke.Multiline_Eval_String_Knob( 'callback', 'callback', node['knobChanged'].value() )       
        self.update = nuke.PyScript_Knob('update', 'update')

        # ADD KOBS
        for k in ( self.callback, self.update):
            self.addKnob(k)

    def knobChanged( self, knob ):
        # IF AN INVALID INDEX IS SHOWN DISPLAY THE WARNING TEXT
        if knob == self.update:
            cmd= self.callback.value()
            n=nuke.selectedNode()
            n['knobChanged'].setValue(cmd)
            print 'knobSet'
            

            
            
def main():
    ShapeAndCVPanel(nuke.selectedNode()).showModalDialog()