__author__ = 'aburke'

# import os,sys
from glob import glob

from core_settings import *
import projects



# from subprocess import Popen, PIPE, STDOUT


# this serves as the brain of the project system. You can ask it about a file
# and it will be able to know what it is 

# it can read the global studio config and initialize a setup or it can read a custom config on a 
# per project level, or any custom config to alter or override it
# the brain
# reads a project config and uses it for identifying information about the project
# loads a given project into the datamodel based on the project config mapping

# import core

# initialize the project controller. specify a project.yml file to load as the template file
# proj_ctrlr = core.projects.ProjectController(self.config_path)

# get a python dictionary that parses the shot properties from the file
# p_dict = proj_ctrlr.parsePath(pathToProjectFile)
# result:

# get a list of shots
# item_tuple = proj_ctrlr.getAssetsList(upl_dict=p_dict, asset_type='shot')
# p_dict = proj_ctrlr.parsePath(pathToProjectFile)
# return: 2-tuple (string asset_lib_path, list assets) assets are prefixed with asset group eg. "asset_grp/asset_name"

# get a list of shots
# item_tuple = proj_ctrlr.getAssetsList(upl_dict=p_dict, asset_type='shot')
# p_dict = proj_ctrlr.parsePath(pathToProjectFile)
# return: 2-tuple (string asset_lib_path, list assets) assets are prefixed with asset group eg. "asset_grp/asset_name"




class CoreController():
    '''  The main funciton of gs_core is to act as an interface between the data model (our file system, //scholar/projects) and views of that model (Launcher & other in-app tools)
    This makes Core the 'controller' in standard model-view-controller software architecture. The primary way of interacting with the model is a psuedo REST API (representational
    state transfer) wherby data is queried and manipulated with resource locators (in this case the filesystem paths) to locate and query data on the file server '''

    def __init__(self):
        pass
        # config path should eventually be set by studio.yml
        self.config_path = (CONFIG+"/projects.yml")
        # load the Project Controller that interacts with project data
        self.proj_controller = projects.ProjectController(self.config_path)



        # load up project shares on server

        # load up list of jobs found in project shares

    def getFileShares(self, share_type):
        share_paths = []
        for share in STUDIO['servers']:
            if share_type == '':
                share_paths.append(STUDIO['servers'][share]['root_path'])
            else:
                if share_type == STUDIO['servers'][share]['share_type']:
                    share_paths.append(STUDIO['servers'][share]['root_path'])
        return share_paths

    def getProjectsList(self, proj_type):
        result = []
        file_share_list = self.getFileShares('job_share')
        for j in sorted(file_share_list,key=lambda v: v.upper()):
            for name in os.listdir(j):
                fp = '/'.join([j,name])
                if os.path.isdir(fp) and not name.startswith('.') and not name.startswith('_'):
                    result.append(fp)
        return result



def main():
    ''' this is run if the gs_core.py script is executed directly (not imported)'''
    # load the project config to enable the core to understand where files live on the server
    # based on this file, the core can map it to a data model storing information about the project


    # test the load matching
    #self.core_parser.testFilePaths()
    #self.core_parser.testDictToPath()
    testAPICalls()


    return


# OLD METHODS FOR QUERYING SHOT INFO. DEPRICATED. REPLACED BY the core.projects module

def list_servers():
    for share in STUDIO['servers']:
        print (share+": "+STUDIO['servers'][share]['root_path'])


def list_jobs(share):
    result = []
    try:
        path = STUDIO['servers'][share]['root_path']
        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path,name)) and not name.startswith('.') and not name.startswith('_'):
                result.append(name)
    except:
        print (share+" is not a valid share name as per config")
    return result


def list_shots(share,job):
    result = []
    try:
        #path = PROJECT['data_structs'][share]['root_path']
        path = STUDIO['servers'][share]['root_path']
        path = os.path.join(path,job,'03_production','01_cg','01_MAYA','scenes','02_cg_scenes')

        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path,name)) and not name.startswith('.') and not name.startswith('_'):
                result.append(name)
    except:
        print (job+" not found")
    return result


def list_assets(share,job):
    result = []
    try:
        path = STUDIO['servers'][share]['root_path']
        path = os.path.join(path, job, '03_production', '01_cg', '01_MAYA', 'scenes', '01_cg_elements', '01_models')

        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path, name)) and not name.startswith('.') and not name.startswith('_'):
                result.append(name)

    except:
        print (job+" not found")
    return result


def list_scenes(share, job, shot):
    valid_result = []
    try:
        path = STUDIO['servers'][share]['root_path']
        paths = []
        paths.append(os.path.join(path,job,'03_production','01_cg','01_MAYA','scenes','02_cg_scenes',shot))
        paths.append(os.path.join(path,job,'03_production','01_cg','01_MAYA','scenes','01_cg_elements','01_models',shot))
        paths.append(os.path.join(path,job,'03_production', '02_composite',shot))
        paths.append(os.path.join(path,job,'03_production', '01_cg','04_houdini',shot))


        for p in paths:
            # iterates all subtree looking for patterns that match the glob *.mb
            result = [y for x in os.walk(p) for y in glob(os.path.join(x[0], '*.mb'))]
            for name in result:
                if not os.path.isdir(os.path.join(p,name)) and not name.startswith('.') and not name.startswith('_'):
                    rel_path = name[len(p)+1:]
                    valid_result.append(rel_path)


    except:
        print (shot+" not found")
    return valid_result


# given a file path determine shot info about it
#  0:Server 1:Job 2:ShotFolder 3:Seq 4:Shot 5:dept 6:subDept 7:take 8:version 9:ext
#def get_info_from_path(path):
    # get info

def where_am_i(filepath, sparse=True, ignoreCache=False):
    ''' given a filepath, it will attempt to identify the project, shot/asset, task, version etc.. and return a valid project model with that data only '''
    # take the given path and parse it through the StudioProject() object
    result = CoreProject()
    return

def load_project_model():
    ''' based on the projecy.yml, it will attempt to load and identify all assets and shots within a job'''
    return

def testAPICalls():
    import gs_core

    # initialize the project controller. specify a project.yml file to load as the template file
    #proj = gs_core.projects.ProjectController('//scholar/pipeline/dev/config/projects.yml')
    proj = gs_core.projects.ProjectController(CONFIG + "/projects.yml")

    # get a python dictionary that parses the shot properties from the file
    p_dict = proj.pathParser.parsePath('//scholar/projects/ab_testjob/production')

    # get a list of shots for a stage of production
    asset_lib, asset_names = proj.getAssetsList(upl_dict=p_dict, asset_type='shot')
    # returns: 2-tuple (string asset_lib_path, assets[]) assets are prefixed with asset group eg. "asset_grp/asset_name"
    # result: ('//scholar/projects/ab_testjob', ['s01/001_00', 's01/002_00', 's01/003_00', 's01/004_00', 's01/005_00'])

    # get a list of tasks within a shot
    task_root, task_names = proj.getTaskList(upl='/'.join([asset_lib, asset_names[0]]))
    # returns: 2-tuple (string task_root_path, tasks[])
    # result: ('//scholar/projects/ab_testjob/s01/001_00', ['anim', 'light', 'comp'])

    # get a list of scenefiles within a given task
    task_path, rel_scenepath = proj.getTaskScenesList(upl='/'.join([task_root, task_names[0]]), task_type=task_names[0])
    # result: ('//scholar/projects/ab_testjob/s01/001_00/comp', ['work/nuke/s01_001_00_comp_main_v000.nk', 'work/nuke/s01_001_00_comp_main_v001.nk', 'work/nuke/s01_001_00_comp_main_v002.nk'])

    # get scene name and version info from a filepath
    f_data = proj.pathParser.parsePath('//scholar/projects/ab_testjob/production/shots/s01/005_00/light/work/maya/scenes/s01_005_00_light_main_v003.mb')
    print f_data
    # returns: python dict of any variables that it found in the path
    # result: {'server':'//scholar', 'share':'projects', 'job': 'ab_testjob', 'asset_type':'shot, 'asset_grp':'s01', 'asset':'001_00', 'task':'comp', 'package':'nuke', 'scenename':'main', 'version', 'v001', 'ext':'nk'}

    # get the latest renders of a render sequence for a task/layer
    latest_render_paths = proj.getScenefileList(upl_dict=f_data, scene_type='render', latest_version=True)
    print latest_render_paths

    # get the latest version of a publish for a task/layer
    latest_publist_paths = proj.getScenefileList(upl_dict=f_data, scene_type='publish', latest_version=True)
    print latest_publist_paths

    ### define a uniform project location dictionary to pass to the getSceneList method.
    ##f_data ={
    ##    'scenename': 'main',
    ##    'task': 'light',
    ##    'package': 'maya',
    ##    'share': 'projects',
    ##    'ext': 'mb',
    ##    'server': '//scholar',
    ##    'job': 'ab_testjob',
    ##    'version': '',
    ##    'asset': '005_00',
    ##    'asset_grp': 's01',
    ##    'asset_type': 'shot',
    ##    'stage': 'production'
    ##}
##
    ### get the latest renders of a render sequence for a task/layer
    ##latest_render_paths = proj.getScenefileList(upl_dict=f_data, scene_type='render', latest_version=True)
    ##print latest_render_paths
##
    ### get the latest version of a publish for a task/layer
    ##latest_publish_paths = proj.getScenefileList(upl_dict=f_data, scene_type='publish', latest_version=True)
    ##print latest_publish_paths


    # alternatively you can simply specify a filepath to determine the shot info and it will try to find the renders
    # or published scenefiles / alembics that go to that version or the latest version

    #latest_render_paths = proj.getScenefileList(upl='//scholar/projects/ab_testjob/production/shots/s01/005_00/light/work/maya/scenes/s01_005_00_light_main_v003.mb', scene_type='render', latest_version=True)
    #print latest_render_paths

    #latest_publish_paths = proj.getScenefileList(upl='//scholar/projects/ab_testjob/production/shots/s01/005_00/light/work/maya/scenes/s01_005_00_light_main_v003.mb', scene_type='publish', latest_version=True)
    #print latest_publish_paths

    # get formatted render paths
    #latest_render_paths = proj.getScenefileListFormatted(upl='//scholar/projects/ab_testjob/production/shots/s01/005_00/light/work/maya/scenes/s01_005_00_light_main_v003.mb', scene_type='render', latest_version=True, style='nuke')
    #print latest_render_paths

    #latest_render_paths = proj.getScenefileListFormatted(upl='//scholar/projects/ab_testjob/production/shots/s01/005_00', scene_type='render', latest_version=True, style='nuke')
    #print latest_render_paths

    ## test passing just an asset folder
    #f_data = proj.pathParser.parsePath('//scholar/projects/ab_testjob/production/assets/3d/char/testCharA')
    #f_data['task'] = 'model'
    #f_data['scenename'] = 'main'
    #f_data['package'] = 'maya'
    #f_data['ext'] = 'mb'

    ## get the latest version of publish path
    #pub_root, pub_files = proj.getScenefileList(upl_dict=f_data, scene_type='publish', latest_version=True)
    #print ('latest_publish={0} {1}'.format(pub_root,  pub_files))
    ## get a list of available renderLayers for a given scenename

    f_data = proj.pathParser.parsePath('//scholar/projects/ab_testjob/production/assets/3d/char/testCharA/rig/work/maya/scenes/char_testCharA_rig_main_v001.mb')
    print f_data

    next_avail = proj.getScenefileList(upl='//scholar/projects/ab_testjob/production/assets/3d/char/testCharA/rig/work/maya/scenes/char_testCharA_rig_main_v000.mb', scene_type='workscene', latest_version=True, new_version=True)
    print next_avail

if __name__ == '__main__':
    main()


