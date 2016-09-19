import os

try:
	GSCODEBASE = os.environ['GSCODEBASE']
except:
	GSCODEBASE = '//scholar/code'
#
#   For single OS users.
#
#API_DIR = os.path.join(GSCODEBASE, 'general/scripts/python/zync-python')
API_DIR = os.path.join(GSCODEBASE, 'lib/python/zync-python')

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
API_KEY = '4fd6565bfa20dafebc9cea8cd1b85d8a'
