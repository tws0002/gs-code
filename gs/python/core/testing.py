__author__ = 'aburke'
''' testing functions to ensure core functionality is working '''
import unittest
import os
import settings
import paths

# determines vars based on this files location
LAUNCHER = os.path.dirname(os.path.realpath(__file__))
RES = os.path.join(LAUNCHER, 'res')
PYTOOLS = os.path.dirname(LAUNCHER)
AUTHOR = os.path.dirname(PYTOOLS)
BRANCH = os.path.dirname(AUTHOR)
TOOLS = os.path.join(BRANCH,'apps')
CONFIG = os.path.join(BRANCH,'config')
ROOT = os.path.dirname(BRANCH)

class TestPathParser(unittest.TestCase):

    def setUp(self):
        config_path = (CONFIG + "/projects_old.yml")
        self.pathParser = paths.CoreParser()
        self.pathParser.load_project_config_file(filepath=config_path)

    def tearDown(self):
        return

    def test_substTemplPath(self):
        d = {'job': 'ny_r_and_d', 'server': '//scholar'}
        var = 'project_root'
        r = '//scholar/projects/ny_r_and_d'
        self.assertEquals(r, self.pathParser.subst_template_path(upl_dict=d, upl='', template_type='var', template_name='', template_var='project_root'))

        # test a file
        d = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion', 'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        r = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        file_path = self.pathParser.subst_template_path(upl_dict=d, upl='', template_type='task', template_name='model', template_var='work_path', template_file='work_file')
        self.assertEquals(r, file_path)

    def test_parsePath(self):
        # test basic path
        s1 = '//scholar/projects/ny_r_and_d'
        d1 = {'job': 'ny_r_and_d', 'server': '//scholar'}
        self.assertEquals(d1, self.pathParser.parse_path(s1))
        s2 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        d2 = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion', 'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        self.assertEquals(d2, self.pathParser.parse_path(s2))
        # test false paths
        s3 = '//scholar/projects/made_up_project'
        d3 = {}
        self.assertEquals(d3, self.pathParser.parse_path(s3))

        # test partial path
        s4 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU'
        d4 = {'server': '//scholar', 'job': 'lenovo_legion', 'shot': 'SH_040_CU'}
        self.assertEquals(d4, self.pathParser.parse_path(s4))

        # test that it fails on wrong type
        with self.assertRaises(TypeError):
            self.pathParser.parse_path(d1)

    def test_GetPath(self):
        # test basic path
        s1 = '//scholar/projects/ny_r_and_d'
        d1 = {'job': 'ny_r_and_d', 'server': '//scholar'}
        self.assertEquals(s1, self.pathParser.get_path(d1))
        s2 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        d2 = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion', 'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        self.assertEquals(s2, self.pathParser.get_path(d2))
        # test false paths
        s3 = ''
        d3 = {'job': 'made_up_project','server': '//scholar'}
        self.assertEquals(s3, self.pathParser.get_path(d3))
        # test partial path
        s4 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU'
        d4 = {'server': '//scholar', 'job': 'lenovo_legion', 'shot': 'SH_040_CU'}
        self.assertEquals(s4,self.pathParser.get_path(d4))


        # test that it fails on wrong type
        with self.assertRaises(TypeError):
            self.pathParser.get_path(s1)


class TestProject(unittest.TestCase):

    def setUp(self):
        return

    def tearDown(self):
        return

    #def test_loadProject(self):
    #    return
#
    #def test_createProject(self):
    #    return


if __name__ == '__main__':
    unittest.main()