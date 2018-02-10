__author__ = 'aburke'
''' testing functions to ensure gs_core functionality is working '''
import unittest
import os
import core_settings
import paths
import gs_core

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
        self.pathParser = paths.PathParser()
        self.pathParser.loadProjectConfigFile(filepath=config_path)

    def tearDown(self):
        return

    def test_substTemplPath_orig(self):

        config_path = (CONFIG + "/projects_old.yml")
        self.pathParser.loadProjectConfigFile(filepath=config_path)

        d = {'job': 'ny_r_and_d', 'server': '//scholar'}
        var = 'project_root'
        r = '//scholar/projects/ny_r_and_d'
        self.assertEquals(r, self.pathParser.substTemplatePath(upl_dict=d, upl='', template_type='var', template_name='', template_var='project_root'))

        # test a file
        d = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion', 'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        r = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        file_path = self.pathParser.substTemplatePath(upl_dict=d, upl='', template_type='task', template_name='model', template_var='work_path', template_file='work_file')
        self.assertEquals(r, file_path)

    def test_parsePath_orig(self):

        config_path = (CONFIG + "/projects_old.yml")
        self.pathParser.loadProjectConfigFile(filepath=config_path)

        # test basic path
        s1 = '//scholar/projects/ny_r_and_d'
        d1 = {'job': 'ny_r_and_d', 'server': '//scholar'}
        self.assertEquals(d1, self.pathParser.parsePath(s1))
        s2 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        d2 = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion', 'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        self.assertEquals(d2, self.pathParser.parsePath(s2))
        # test false paths
        s3 = '//scholar/projects/made_up_project'
        d3 = {}
        self.assertEquals(d3, self.pathParser.parsePath(s3))

        # test partial path
        s4 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU'
        d4 = {'server': '//scholar', 'job': 'lenovo_legion', 'shot': 'SH_040_CU'}
        self.assertEquals(d4, self.pathParser.parsePath(s4))

        # test that it fails on wrong type
        with self.assertRaises(TypeError):
            self.pathParser.parsePath(d1)

    def test_GetPath_orig(self):

        config_path = (CONFIG + "/projects_old.yml")
        self.pathParser.loadProjectConfigFile(filepath=config_path)

        # test basic path
        s1 = '//scholar/projects/ny_r_and_d'
        d1 = {'job': 'ny_r_and_d', 'server': '//scholar'}
        self.assertEquals(s1, self.pathParser.getPath(d1))
        s2 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        d2 = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion', 'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        self.assertEquals(s2, self.pathParser.getPath(d2))
        # test false paths
        s3 = ''
        d3 = {'job': 'made_up_project','server': '//scholar'}
        self.assertEquals(s3, self.pathParser.getPath(d3))
        # test partial path
        s4 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU'
        d4 = {'server': '//scholar', 'job': 'lenovo_legion', 'shot': 'SH_040_CU'}
        self.assertEquals(s4, self.pathParser.getPath(d4))


        # test that it fails on wrong type
        with self.assertRaises(TypeError):
            self.pathParser.getPath(s1)

    def test_substTemplPath(self):
        config_path = (CONFIG + "/projects_old.yml")
        self.pathParser.loadProjectConfigFile(filepath=config_path)

        d = {'job': 'ny_r_and_d', 'server': '//scholar'}
        var = 'project_root'
        r = '//scholar/projects/ny_r_and_d'
        self.assertEquals(r,
                          self.pathParser.substTemplatePath(upl_dict=d, upl='', template_type='var', template_name='',
                                                            template_var='project_root'))

        # test a file
        d = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion',
             'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        r = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        file_path = self.pathParser.substTemplatePath(upl_dict=d, upl='', template_type='task', template_name='model',
                                                      template_var='work_path', template_file='work_file')
        self.assertEquals(r, file_path)

    def test_parsePath(self):
        config_path = (CONFIG + "/projects_old.yml")
        self.pathParser.loadProjectConfigFile(filepath=config_path)

        # test basic path
        s1 = '//scholar/projects/ny_r_and_d'
        d1 = {'job': 'ny_r_and_d', 'server': '//scholar'}
        self.assertEquals(d1, self.pathParser.parsePath(s1))
        s2 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        d2 = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion',
              'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        self.assertEquals(d2, self.pathParser.parsePath(s2))
        # test false paths
        s3 = '//scholar/projects/made_up_project'
        d3 = {}
        self.assertEquals(d3, self.pathParser.parsePath(s3))

        # test partial path
        s4 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU'
        d4 = {'server': '//scholar', 'job': 'lenovo_legion', 'shot': 'SH_040_CU'}
        self.assertEquals(d4, self.pathParser.parsePath(s4))

        # test that it fails on wrong type
        with self.assertRaises(TypeError):
            self.pathParser.parsePath(d1)

    def test_GetPath(self):
        config_path = (CONFIG + "/projects_old.yml")
        self.pathParser.loadProjectConfigFile(filepath=config_path)

        # test basic path
        s1 = '//scholar/projects/ny_r_and_d'
        d1 = {'job': 'ny_r_and_d', 'server': '//scholar'}
        self.assertEquals(s1, self.pathParser.getPath(d1))
        s2 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb'
        d2 = {'intials': 'CK', 'task': 'model', 'ext': 'mb', 'server': '//scholar', 'job': 'lenovo_legion',
              'version': 'v023', 'asset': 'Lenovo_IdeacenterY900TW'}
        self.assertEquals(s2, self.pathParser.getPath(d2))
        # test false paths
        s3 = ''
        d3 = {'job': 'made_up_project', 'server': '//scholar'}
        self.assertEquals(s3, self.pathParser.getPath(d3))
        # test partial path
        s4 = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU'
        d4 = {'server': '//scholar', 'job': 'lenovo_legion', 'shot': 'SH_040_CU'}
        self.assertEquals(s4, self.pathParser.getPath(d4))

        # test that it fails on wrong type
        with self.assertRaises(TypeError):
            self.pathParser.getPath(s1)

    def testAPICalls(self):
        pass
        ## # initialize the project controller. specify a project.yml file to load as the template file
        ## proj = core.projects.ProjectController('//scholar/pipeline/dev/config/projects.yml'     ##
        ## # get a python dictionary that parses the shot properties from the file
        ## p_dict = proj.pathParser.parsePath('//scholar/projects/ab_testjob/production'       ##
        ## # get a list of shots for a stage of production
        ## asset_lib, asset_names = proj.getAssetsList(upl_dict=p_dict, asset_type='shot')
        ## # returns: 2-tuple (string asset_lib_path, assets[]) assets are prefixed with asset group eg. "asset_grp/asset_name"
        ## # result: ('//scholar/projects/ab_testjob', ['s01/001_00', 's01/002_00', 's01/003_00', 's01/004_00', 's01/005_00']      ##
        ## # get a list of tasks within a shot
        ## task_root, task_names = proj.getTaskList(upl='/'.join([asset_lib, asset_names[0]))
        ## # returns: 2-tuple (string task_root_path, tasks[])
        ## # result: ('//scholar/projects/ab_testjob/s01/001_00', ['anim', 'light', 'comp']        ##
        ## # get a list of scenefiles within a given task
        ## task_path, rel_scenepath = proj.getTaskScenesList(upl='/'.join([task_root, task_names[0]))
        ## print (task_path+rel_scenepath)
        ## # returns: 2-tuple (string task_root_path, scenefile_paths[])
        ## # result: ('//scholar/projects/ab_testjob/s01/001_00/comp', ['work/nuke/s01_001_00_comp_main_v000.nk', 'work/nuke/s01_001_00_comp_main_v001.nk', 'work/nuke/s01_001_00_comp_main_v002.nk']      ##
        ## # get scene name and version info from a filepath
        ## f_data = proj.pathParser.parsePath('//scholar/projects/ab_testjob/s01/001_00/comp/work/nuke/s01_001_00_comp_main_v000.nk')
        ## print f_data
        ## # returns: python dict of any variables that it found in the path
        ## # result: {'server':'//scholar', 'share':'projects', 'job': 'ab_testjob', 'asset_type':'shot, 'asset_grp':'s01', 'asset':'001_00', 'task':'comp', 'package':'nuke', 'scenename':'main', 'version', 'v001', 'ext':'nk'       ##
        ## # get render sequence of a task/layer/pas       ##
        ## # get the latest version of a render sequence for a task/layer

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