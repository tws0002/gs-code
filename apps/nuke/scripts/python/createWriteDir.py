import nuke
import os

def main():
    file = nuke.filename(nuke.thisNode())
    dir = os.path.dirname( file )
    osdir = nuke.callbacks.filenameFilter( dir )
    if not os.path.isdir(osdir): 
    	try:
    		os.makedirs(osdir)
    	except:
    		pass