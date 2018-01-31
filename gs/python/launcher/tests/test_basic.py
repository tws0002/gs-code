__author__ = 'aburke'
''' testing functions to ensure launcher functionality is working '''
import unittest
import os
import launcher
import settings

# determines vars based on this files location
LAUNCHER = os.path.dirname(os.path.realpath(__file__))
RES = os.path.join(LAUNCHER, 'res')
PYTOOLS = os.path.dirname(LAUNCHER)
AUTHOR = os.path.dirname(PYTOOLS)
BRANCH = os.path.dirname(AUTHOR)
TOOLS = os.path.join(BRANCH,'apps')
CONFIG = os.path.join(BRANCH,'config')
ROOT = os.path.dirname(BRANCH)

class TestLauncher(unittest.TestCase):

    def setUp(self):
        return

    def tearDown(self):
        return

    def test_Launch(self):
        # launch maya, run test script, shutdown
        return

    def test_LaunchFromFile(self):
        return

    def test_RenderSubmit(self):
        # launch maya
        return

if __name__ == '__main__':
    unittest.main()