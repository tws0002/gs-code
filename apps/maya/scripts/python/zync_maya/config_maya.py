import os

try:
	GSCODEBASE = os.environ['GSCODEBASE']
except:
	GSCODEBASE = '//scholar/code'
GSTOOLS = os.path.join(GSCODEBASE,'tools')
GSBIN = os.path.join(GSCODEBASE,'bin')
#
#   For single OS users.
#
API_DIR = os.path.join(GSTOOLS, 'general','scripts','python','zync-python')

#
#   For multiple OS users. Detects user's operating system and 
#   sets path to zync-python folder accordingly.  
#
#import platform
#if platform.system() in ('Windows', 'Microsoft'):
#    API_DIR = 'Z:/plugins/zync-python'
#else:
#    API_DIR = '/Volumes/server/plugins/zync-python'

#
#   API_KEY - Check your My Account page to get your key.
#
API_KEY = 'dfbedea3ada897da2d7989da902c45cc'
