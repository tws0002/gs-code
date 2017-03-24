__author__ = 'adamb'

import os, sys


# determines vars based on this files location
LAUNCHER = os.path.dirname(os.path.realpath(__file__))
RES = os.path.join(LAUNCHER, 'res')
PYTOOLS = os.path.dirname(LAUNCHER)
STUDIO = os.path.dirname(PYTOOLS)
BRANCH = os.path.dirname(STUDIO)
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
#try:
#    os.environ['PYTHONPATH'] += (';'+PYQTPATH)
#except:
#    os.environ['PYTHONPATH'] = (PYQTPATH)
sys.path.append(PYQTPATH)

## print os.environ['PYTHONPATH']
## print sys.path
sys.path.append(os.path.join(ROOT,'lib','python'))
sys.path.append(os.path.join(PYTOOLS))
import yaml



MODE = "pub"
SITE = "ny"
SERVER = "scholar"
SHARES = {
    'projects' : 'projects',
    'code' : 'pipeline',
    'home' : 'personal',
    'assets' : 'lib',
}

#load the apps dictionary
f = open(CONFIG+"/app.yml")
APPS = yaml.safe_load(f)
f.close()

#load the modules dictionary
f = open(CONFIG+"/modules.yml")
MODULES = yaml.safe_load(f)
f.close()

#load the workgroups dictionary
f = open(CONFIG+"/workgroups.yml")
WORKGRP = yaml.safe_load(f)
f.close()

from environment import *
# load the launcher environment
STUDIO_ENV = StudioEnvironment()
STUDIO_ENV.load_app_config_file(CONFIG + '/app.yml', app='studiotools', version='1.0')
STUDIO_ENV.setEnv()


AD_DNS_NAME = 'studio.gentscholar.com'
AD_NT4_DOMAIN = 'STUDIO' # This is the NT4/Samba domain name
#AD_SEARCH_DN = 'dc=pandapanther.pandapanther.com,dc=local'
AD_SEARCH_DN = 'dc=gentscholar,dc=studio,dc=com'
#AD_SEARCH_DN = 'CN=Users,dc=pandapanther,dc=com'
# this default port causes a failure in backends.py when getting user login info (email, givenname, sirname)
#AD_LDAP_PORT = 389
# this port fixes it according to googling AD django troubleshooting
AD_LDAP_PORT = 389