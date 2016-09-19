import nuke
import os

####################### importMocha() #########################################
# Asks the user for an exported mocha nuke ascii text file and a start frame. #
# Creates a tracker4 node with four tracks and imports the animation from the #
# four text files with the same prefix.                                       #
#                                                                             #
# by David Emeny 2013                                                         #
###############################################################################


def importMocha():

    #this is the default track name and file extension mocha uses
    #change these if new versions of mocha do it differently
    #example: face_Tracker1.txt
    mochaSuffix = "Tracker" 
    mochaFileExtension = ".txt"

    #Choose mocha ascii file
    asciiPath = nuke.getFilename('Choose one of the track files', '*.txt')
    if not asciiPath:
        return None

    thePath = os.path.dirname(asciiPath)
    theFile = os.path.basename(asciiPath)

    if not (mochaSuffix in theFile and mochaFileExtension in theFile):
        nuke.message('There was a problem with one of the ascii files, make sure there are four ascii files with the same prefix. For example:\nface_Tracker1.txt\nface_Tracker2.txt\nface_Tracker3.txt\nface_Tracker4.txt')
        return None

    #extract the file name prefix
    prefix = theFile.split(mochaSuffix)[0]

    try:
        startPos = int((nuke.getInput('Enter the start frame', '1')))
    except:
        nuke.message('That was not a number. Start again.')
        return None

    if not asciiPath:
        return None


    #create a tracker node with 4 tracks
    t = nuke.createNode('Tracker4')
    t['label'].setValue(prefix + 'mocha')
    for i in range(0,4):
        t['add_track'].execute()

    #set up field positions
    k = t['tracks'] 
    numColumns = 31 
    colTrackX = 2 
    colTrackY = 3 
 
    #for the four text files
    for track in range(1,5):
        
        #set path for this file
        currentPath =  "%s/%s%s%s%s" %(thePath,prefix,mochaSuffix,str(track),mochaFileExtension)

        try:
            f = open(currentPath , 'r')
        except:
            nuke.message('There was a problem with one of the ascii files, make sure there are four ascii files with the same prefix, numbered 1-4.\n\nFor example:\n\nface_Tracker1.txt\nface_Tracker2.txt\nface_Tracker3.txt\nface_Tracker4.txt')
            nuke.delete(t)
            return None

        currentPos = startPos

        for line in f:
            #get the x and y for this frame
            line = line.strip()
            columns = line.split()
            x = float(columns[0])
            y = float(columns[1])

            #set the x and y for this track on this frame 
            k.setValueAt(x, currentPos, numColumns*(track-1) + colTrackX)
            k.setValueAt(y, currentPos, numColumns*(track-1) + colTrackY)
            
            #advance the frame
            currentPos = currentPos + 1

        f.close()

    #do a quick cheat to unhighlight the last track
    t['add_track'].execute()
    t['del_tracks'].execute()

