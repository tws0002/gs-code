# Muster render checker for Mustache, v0.11 by renry 06/25/2012
#
# Support script set to run when a job is completed.

import sys
import smtplib
import string
import pickle
import subprocess
import os
import re
import random

# muster login params.

muster_server = 'dispatch'
muster_user = 'admin'
muster_port = '8681'
muster_pass = ''
muster_exe = os.path.join('C:\\','Program Files','Virtual Vertex','Muster 7','mrtool.exe')
muster_commandBase = muster_exe + ' -s '+muster_server+' -port '+muster_port+' -u '+muster_user
if muster_pass != '':
    muster_commandBase = muster_commandBase + ' -p '+muster_pass

# this function accepts command line arguments.
emailList = sys.argv[1]
jobName = sys.argv[2].replace('___',' ')
notes = sys.argv[3].replace('___',' ')
jobID = sys.argv[4]
supportID = sys.argv[5]
pcFile = sys.argv[6].replace('___',' ')
imgExt = sys.argv[7]
framePadding = sys.argv[8]
minSize = sys.argv[9]
renderLayers = sys.argv[10]
macFile = pcFile.replace('\\','/').replace('//','/')

if imgExt == 'exr (multichannel)': imgExt = 'exr'

def getChunkDetails():
    cmdLine = muster_commandBase + ' -q h -job '+jobID+' -hf id,sf,ef -H 0 -S 0'
    execute = subprocess.Popen(cmdLine, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout,stderr = execute.communicate()
    chunkDetails = [f.strip('\r\n') for f in stdout.split(' ') if f]
    # chunk ID, start frame, end frame in 3's
    # print chunkDetails
    chunksList = []
    for x in range(0,len(chunkDetails)-1,3):
        chunksList.append((chunkDetails[x],chunkDetails[(x+1)],chunkDetails[(x+2)]))
    return chunksList

def getJobDetails():
    cmdLine = muster_commandBase + ' -q j -job '+jobID+' -jf sf,ef,step,pksize,start,end,totalt -H 0'
    print 'executing command line:'
    print cmdLine
    execute = subprocess.Popen(cmdLine, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout,stderr = execute.communicate()
    if stderr:
        print stderr
        sys.exit(-1)
    jobDetails = [f.strip() for f in stdout.split('|') if f.strip()]
    print '\nstdout: '
    print stdout
    print '\njobDetails: '
    print jobDetails
    # start, end, step, packet, starttime, endtime, totaltime
    return jobDetails[0],jobDetails[1],jobDetails[2],jobDetails[3],jobDetails[4],jobDetails[5],jobDetails[6]

def frameCheck():
    # first, we need to run the framecheck on the file folder (and all subfolders). if any files are too small or missing, find the chunk that matches that frame number
    # and resubmit it. if everything checks out, run renderComplete().
    finalSeqs = []
    layers = renderLayers.split(',')
    # we are assuming that a period is used as the frame extension separator. mustache will enforce this upon rendering a scene.
    separator = '.'
    for root,dirs,files in os.walk(pcFile):
        # we can get the start, end, packetsize and step straight from the job ID in order to establish a range to search.
        images = [f for f in files if imgExt in os.path.splitext(f)[-1]]
        # strip the ### and extension and remove duplicates so we can search each sequence.
        imagesRoot = []
        for i in images:
            noExt = os.path.splitext(i)[0]
            noSep = separator.join(i.split(separator)[:-2])
            imagesRoot.append(os.path.join(root,noSep))
        imageSeqs = list(set(imagesRoot))
        finalSeqs.extend(imageSeqs)
    # when searching for layers, if the user rendered defaultRenderLayer, maya will interpret it as "masterLayer."
    if 'defaultRenderLayer' in layers:
        layers.append('masterLayer')
    print 'render layers: %s' % (','.join(layers))
    print 'unfiltered sequence list: %s' % (','.join(list(set(finalSeqs))))
    finalSeqs = [f for f in list(set(finalSeqs)) if f.split('_')[-1] in layers]
    print 'final sequence list: %s' % (','.join(finalSeqs))

    # finalSeqs gives us a list of paths to add extensions to and check for viability. we need to make sure to add the right separator before
    # the frame sequence. if any frame in a sequence is missing, find the chunk associated with that frame and restart it.

    fstart,fend,fstep,fpacket,start,end,total = getJobDetails()
    print 'sequence start: %s' % (fstart)
    print 'sequence end: %s' % (fend)
    print 'framestep: %s' % (fstep)
    print 'packetsize: %s' % (fpacket)
    missingFrames = []
    smallFrames = []
    print 'Searching for missing frames.'
    for sequence in finalSeqs:
        print 'Searching sequence: %s' % (sequence)
        # search each sequence for missing frames.
        for x in range(int(fstart),int(fend)+1,int(fstep)):
            testFrame = sequence+separator+str(x).zfill(int(framePadding))+'.'+imgExt
            print 'DEBUG: searching for file %s' % (testFrame)
            if not os.path.exists(testFrame):
                missingFrames.append(x)
            else:
                # test the file against minimum size threshold.
                if os.path.getsize(testFrame) < (float(minSize) * 1024.0):
                    smallFrames.append(x)
    missingFrames = list(set(missingFrames))
    smallFrames = list(set(smallFrames))
    if missingFrames:
        print 'MISSING FRAMES DETECTED: '
        print missingFrames
    else:
        print 'No missing frames detected.'
    if smallFrames:
        print 'SMALL FRAMES DETECTED: '
        print smallFrames
    else:
        print 'No small frames detected.'
    missingFrames.extend(smallFrames)
    missingFrames = list(set(missingFrames))
    if missingFrames:
        # find what chunks these frames belong to, and requeue them.
        # getChunkDetails returns list of tuples: chunk ID, startf, endf
        # for each chunk, find out if the value of missingFrames is equal to or greater than startf, but less than endf. if so, requeue this chunk.
        chunks = getChunkDetails()
        for f in missingFrames:
            print 'trying to find chunk for frame %s' % (f)
            for c in chunks:
                chunk = c[0]
                chunkStart = c[1]
                chunkEnd = c[2]
                print 'analyzing chunk %s, start frame %s, missing frame %s' % (chunk, chunkStart, f)
                if float(f) >= float(chunkStart) and float(f) <= float(chunkEnd):
                    # WE HAVE A WINNER
                    print 'requeueing chunk %s' % (chunk)
                    execStr = muster_commandBase + ' -chunkrq '+jobID+' '+chunk
                    execute = subprocess.Popen(execStr,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    stdout,stderr = execute.communicate()
                    # print stdout,stderr
                    continue
        # now re-init this job so it runs again when those chunks are done.
        execStr = muster_commandBase + ' -jobri '+supportID
        execute = subprocess.Popen(execStr,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = execute.communicate()
    else:
        renderComplete(1)

def renderComplete(terminateJob=False):
    if emailList and emailList != 'none':
        # annoyingSignatures = ['Forever Yours,','Suggestively,','Breathily,','Saucily,','Kisses,','Yearningly,','In Loving Service,','Hungrily,','Scantily,','Feverishly,','Seductively,','Fervently,','Lasciviously,','Licentiously,','Sensually,','Submissively,','Longingly,','Sexily,','Turgidly,']
        annoyingSignatures = ['Forever Yours,']
        rand = random.randint(0,len(annoyingSignatures)-1)
        start, end, step, packet, starttime, endtime, totaltime = getJobDetails()
        eSubject = 'Render completed: '+jobName
        eFrom = '}MUSTACHE{'
        eTo = emailList.split(',')
        eText = 'The following render just completed: \n%s \n\nImages are located at: \n(PC) %s\n(MAC) %s \n\nNotes for this job: \n%s \n\nJob statistics:\nStart time: %s\nEnd time: %s\nTotal processing time: %s\n\n%s\n}MUSTACHE{' % (jobName,pcFile,macFile,notes,starttime,endtime,totaltime,annoyingSignatures[rand])
        eBody = string.join((
                 'From: %s' % eFrom,
                 'To: %s' % eTo,
                 'Subject: %s' % eSubject,
                 '',
                 eText
                 ), '\r\n')
        server = smtplib.SMTP_SSL('smtp.gmail.com:465')
        server.set_debuglevel(False)
        server.login('mustache@gentscholar.com','h4ndl3b4r')
        try:
            server.sendmail(eFrom,eTo,eBody)
            server.quit()
            print 'Email sent!'
            # terminate job
            if terminateJob:
                execute = muster_commandBase + ' -jobrm '+supportID
                kill = subprocess.Popen(execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout,stderr = kill.communicate()
            else:
                print 'Pausing job.'
                execute = muster_commandBase + ' -jobp '+supportID
                kill = subprocess.Popen(execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout,stderr = kill.communicate()
        except Exception, e:
            print 'Could not send email: %s' % str(e)
    else:
        # terminate job
        if terminateJob:
            execute = muster_commandBase + ' -jobrm '+supportID
            kill = subprocess.Popen(execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout,stderr = kill.communicate()
        else:
            # debug mode: pause job to view logs
            print 'Pausing job.'
            execute = muster_commandBase + ' -jobp '+supportID
            kill = subprocess.Popen(execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout,stderr = kill.communicate()

frameCheck()