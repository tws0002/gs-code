#python

import lx
# from http://community.thefoundry.co.uk/discussion/topic.aspx?f=33&t=49104
# EXPECTED ARGUMENTS
# ||||||||||||||||||
# 0 scene
# 1 frame range start
# 2 frame range end
# 3 frame step
# 4 camera


# 4 render path
# 5 render name
# 6 image type
# 7 antialiasing samples
# ||||||||||||||||||
args = lx.arg().split()

if (len(args)<1):
    print ("No Render Arguments Found")
else:

    lx.eval('log.toConsole true')
    lx.eval('log.toConsoleRolling true')
    lx.eval('scene.open {0}'.format(args[0]))
    lx.eval('select.item Render') # select the render item in order to change its attributes
    lx.eval('item.channel first {0}'.format(args[1])) # range beginning
    lx.eval('item.channel last {0}'.format(args[2])) # range end
    lx.eval('item.channel step {0}'.format(args[3])) # frame steps
    #lx.eval('item.channel polyRender$aa {0}'.format(args[7])) # setting the number antialiasing passes
    if (len(args)>4):
        lx.eval('render.camera {0}'.format(args[4])) # setting the camera to render from

    #lx.eval('render.animation {0}{1} {2}'.format(args[4],args[5],args[6])) # render the animation
    lx.eval('render.animation *')

lx.eval("app.quit") # quit the app






#def main(output_path=None, format=None, rendergroup=None, start_frame, end_frame, step, filename):
#    ''' set the start end and step size for the current chunk
#    '''
#
#    lx.eval( 'log.toConsole true' )
#    lx.eval( 'log.toConsoleRolling true' )
#    lx.eval( 'scene.open "%s"' %(filename) )
#    lx.eval( 'select.itemType polyRender' )
#    lx.eval( 'item.channel first %s' %(start_frame) )
#    lx.eval( 'item.channel last %s' %(end_frame) )
#    lx.eval( 'item.channel step %s' %(step) )
#    if not rendergroup:
#        if format:
#            lx.eval( '!render.animation "%s" %s {*}\n' %(output_path, format) )
#        else
#            lx.eval( '!render.animation "%s" {*}\n' %(output_path) )
#    else:
#        lx.eval( '!render.animation "%s" %s {*} group:%s\n' %(output_path, format, rendergroup) )
#    lx.eval( 'app.quit' )#