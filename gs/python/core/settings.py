__author__ = 'adamb'

import os,sys
import yaml

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


