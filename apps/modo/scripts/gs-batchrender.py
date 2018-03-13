#python

import lx
# from http://community.thefoundry.co.uk/discussion/topic.aspx?f=33&t=49104
# EXPECTED ARGUMENTS
# ||||||||||||||||||
#7: arguments
#args[0]=rendergroup
#args[1]=outputpath
#args[2]=format
#args[3]=start
#args[4]=end
#args[5]=step
#args[6]=file

lx.eval('log.toConsole true')
lx.eval('log.toConsoleRolling true')
args = lx.arg().split()
lx.out('Found {0}: arguments'.format(len(args)))
indx = 0
for ea in args:
    lx.out('args[{0}]="{1}"'.format(indx,ea))
    indx +=1

if (len(args)<7):
    lx.out("Could Not Find All 7 Required Render Arguments, rendergroup, outputpath, format, start, end, step, file")
else:
    #lx.trace( True );
    lx.eval('scene.open {0}'.format(args[6]))
    lx.eval('select.item Render') # select the render item in order to change its attributes
    lx.eval('item.channel first {0}'.format(args[3])) # range beginning
    lx.eval('item.channel last {0}'.format(args[4])) # range end
    lx.eval('item.channel step {0}'.format(args[5])) # frame steps

    rg = args[0]
    op = args[1]
    ft = args[2]
    if not rg: #rendergroup arg
        if ft:
            lx.eval( '!render.animation "%s" %s {*}\n' %(op, ft) )
        else:
            lx.eval( '!render.animation "%s" {*}\n' %(op) )
    else:
        lx.eval( '!render.animation "%s" %s {*} group:%s\n' %(op, ft, rg) )

lx.eval("app.quit") # quit the app



#lx.eval('item.channel polyRender$aa {0}'.format(args[7])) # setting the number antialiasing passes
#if (len(args)>4):
#    lx.eval('render.camera {0}'.format(args[4])) # setting the camera to render from

#lx.eval('render.animation {0}{1} {2}'.format(args[4],args[5],args[6])) # render the animation
# lx.eval('render.animation *')


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