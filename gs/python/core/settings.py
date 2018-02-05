__author__ = 'adamb'

import os,sys
import yaml


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

#this identifies the root of the launcher
CONFIG = os.path.join(os.environ['GSBRANCH'], 'config')
CORE = os.path.dirname(os.path.realpath(__file__))


f = open(CONFIG+"/studio.yml")
# use safe_load instead load
STUDIO = yaml.safe_load(f)
f.close()
print "Loaded Studio Config Successfully"

os.environ['ST_JOB_SERVERS'] = STUDIO['servers']['jobs']['root_path']


f = open(CONFIG+"/projects_old.yml")
# use safe_load instead load
PROJECTS = yaml.safe_load(f)
f.close()
# substitute known variables from STUDIO and internal variables

print "Loaded Project Config Successfully"


