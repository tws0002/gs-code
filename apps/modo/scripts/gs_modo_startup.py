#! /usr/bin/python

import lx
lx.eval('log.toConsole true')
lx.eval('log.toConsoleRolling true')
args = lx.arg().split()
lx.out('Starting GS Modo Init')

# attempt to set the muster submit ui
# NOT WORKING, I THINK script is run before the sheet is created in modo, 
# maybe there is a way to runn the commands defferred until after startup completes
#lx.out('Adding Render Submit UI')
#lx.eval('select.attr {49634997570:sheet} set')
#lx.eval('attr.parent {frm_modomodes_render:sheet} 19')