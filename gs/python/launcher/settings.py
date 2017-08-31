__author__ = 'adamb'

import os, sys, time

START_TIME = time.time()

# determines vars based on this files location
LAUNCHER = os.path.dirname(os.path.realpath(__file__))
RES = os.path.join(LAUNCHER, 'res')
PYTOOLS = os.path.dirname(LAUNCHER)
AUTHOR = os.path.dirname(PYTOOLS)
BRANCH = os.path.dirname(AUTHOR)
TOOLS = os.path.join(BRANCH,'apps')
CONFIG = os.path.join(BRANCH,'config')
ROOT = os.path.dirname(BRANCH)



os.environ['GSROOT'] = ROOT.replace('\\','/')
os.environ['GSBRANCH'] = BRANCH.replace('\\','/')
os.environ['GSCONFIG'] = CONFIG.replace('\\','/')

# import the proper version of PYQT
# need to look at a better way of sourcing pyqt / pyside
PYQTPATH = os.path.join(ROOT,'lib','python','pyqt4','4.10.3')

#os.environ['PATH'] += (';'+pyQTPath)
#print ('setting PYQTPATH to '+PYQTPATH)
try:
    os.environ['PYTHONPATH'] += (';'+os.path.join(ROOT,'lib','python'))
except:
    os.environ['PYTHONPATH'] = (os.path.join(ROOT,'lib','python'))
sys.path.append(PYQTPATH)

## print os.environ['PYTHONPATH']
## print sys.path
sys.path.append(os.path.join(ROOT,'lib','python'))
sys.path.append(os.path.join(PYTOOLS))

import yaml

elapsed_time = time.time() - START_TIME
print("Launcher imported yaml module in {0} sec".format(elapsed_time))

MODE = "pub"
SITE = "ny"
SERVER = "scholar"
SHARES = {
    'projects' : 'projects',
    'code' : 'pipeline',
    'home' : 'personal',
    'assets' : 'lib',
}
#load the studio dictionary
f = open(CONFIG+"/studio.yml")
#STUDIO = yaml.safe_load(f)
STUDIO = yaml.load(f, Loader=yaml.CLoader)
f.close()

elapsed_time = time.time() - START_TIME
print("Launcher loaded yaml files in {0} sec".format(elapsed_time))
