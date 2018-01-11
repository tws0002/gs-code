__author__ = 'adamb'
import os, shutil
import paths
import time
from glob import glob
import re


class ProjectController():
    ''' Project controller's main job is to manipulate the data model (the file system) and provide the view (launcher ui)
    this mainly handles interpreting the model (project template definitions) and creating a deleting data from the server'''

    def __init__(self, config_path ):
        ''' requires a pointer to the file parser to interpret paths and template paths'''
        #if not isinstance(pathParser,classmethod):
        #    raise TypeError

        # init with the default project config path
        self.pathParser = paths.CoreParser()
        self.pathParser.load_project_config_file(filepath=config_path)

        self.activeProject = ''
        self.activeStage = ''
        self.activeAsset = ''
        self.activeTask  = ''

        self.activeProjectData = None

    def set_config(self,config_path):
        self.pathParser.load_project_config_file(filepath=config_path)

    def copy_templ_tree(self, src, dst):
        ''' copies the template dir structure and substitutes any variable in filenames'''
        shutil.copytree(src, dst)

        #substitute path names with variables


    def new(self, upl='//diskstation/jobs/new_project'):
        ''''create a new project structure based on the job. given a url path to the job to create it will generate
        the necessary dict and copy the template dir tree'''

        # parse the given upl path, if it matches the template structure as a valid but non existant path then it is able
        # to be created
        d = self.pathParser.parse_path(upl)
        src = subst_template_path(upl=upl)

        print 'src parsed path = {0}'.format(src)
        #src = self.pathParser.project_templates['copy_tree']
        dst = upl
        #self.copy_templ_tree(src, dst)

    def get_assets_list(self, upl, asset_type, asset_grp):
        ''' given a project path (upl), returns a list of assets found in the assets lib_path defined in projects.yml

        :param upl: universal project locator (project file system)
        :param asset_type:
        :param asset_grp: if there is a subfolder
        :return: 2-tuple of asset_lib_path, list of assets (will include asset_group/asset_name if any are found)
        '''
        START_TIME = time.time()


        asset_list = []
        asset_lib_path = self.pathParser.get_asset_lib(upl, asset_type)
        qualifier = self.pathParser.get_template_path('asset',asset_type,'qualifier_path')

        if os.path.isdir(asset_lib_path):
            for base_dir in os.listdir(asset_lib_path):
                full_path = '/'.join([asset_lib_path, base_dir])
                if os.path.isdir(full_path) and not base_dir.startswith('.') and not base_dir.startswith('_'):
                    sub_dirs = os.listdir(full_path)
                    if qualifier != '' and qualifier in sub_dirs:
                        asset_list.append(base_dir)
                    else:
                        for sub_dir in sub_dirs:
                            full_sub_path = '/'.join([full_path, sub_dir])
                            if os.path.isdir(full_sub_path) and not base_dir.startswith('.') and not base_dir.startswith('_'):
                                sub_grp_files = os.listdir(full_sub_path)
                                if qualifier != '' and qualifier in sub_grp_files:
                                    asset_list.append('/'.join([base_dir,sub_dir]))
        else:
            print ('asset_lib_path={0} not found'.format(asset_lib_path))

        result = (asset_lib_path, asset_list)
        elapsed_time = time.time() - START_TIME
        print("ProjectController.get_assets_list() in {0} sec".format(elapsed_time))
        return result

    def get_asset_type_list(self):
        '''

        :return: 2-tuple of defined asset-type along with display-name
        '''
        result = []
        for template in self.pathParser.asset_templates:
            pair = (template,self.pathParser.get_template_path('asset',template,'display_name'))
            result.append(pair)
        return result

    def get_scenes_list(self, upl='', file_types='all'):
        '''

        :return: sorted list of 2-tuple (fullpath, rel_path) found by globbing
        '''
        valid_result = []
        # iterates all subtree looking for patterns that match the glob *.mb
        # result = [y for x in os.walk(upl) for y in glob(os.path.join(x[0], '*.mb'))]
        result = [y for x in os.walk(upl) for y in self.multi_glob(x[0],['mb','ma','nk','aep'])]
        for name in result:
            if not os.path.isdir(os.path.join(upl,name)) and not name.startswith('.') and not name.startswith('_'):
                rel_path = name[len(upl)+1:]
                filename = os.path.basename(rel_path)
                valid_result.append((name,rel_path))
        return valid_result

    def multi_glob(self, path, filter_list):
        cpath = path.replace('\\','/')
        result = []
        filters = '.*\.{0}$'.format('$|.*\.'.join(filter_list))
        #print 'multi_glob checking path {0}'.format(cpath)
        for x in os.listdir(cpath):
            if re.match(filters, x):
                #print 'matched {0} with filter {1}'.format(x,filters)
                result.append('/'.join([cpath,x]))
        return result

    def new_stage(self, name='production'):
        ''' creates a new stage of production (pitch/previs/production)'''
        return

    def new_asset(self, template_type='shot_2d'):
        '''creates a 3d asset or shot'''

    def new_task(self, name= '', template_type='anim'):
        ''' creates a new task for a specified path '''

    def load_project_model(self, project_path='', use_cache=False):
        # load project path
        self.pathParser.get_libraries(project_path)
        # for each library, load all library structures (assets 2d, assets 3d, shots,)

        # for each task struct
        return

    def load_libary(self,lib_name):
        return

    def load_proj_lib_model(self, lib_path):
        result = []
        path = lib_path

        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path,name)) and not name.startswith('.') and not name.startswith('_'):
                result.append(name)

        # list all the shots/assets in the lib
        for asset in result:
            load_task_model(self,task_path)

# loads a storage definition file either from a template or defined within a job structure
# also provides helper functions to retreive paths and to find data on the server. mostly through the various project models
class CoreProjectStorage():

    root_path = None


    def __init__(self):
        return

    # reads a project definition stores these as local and absolute paths
    def load_definition_from_config(self):
        return

    def get_local_path(self,file_path=""):
        return

    # by resolving all the data by file path lookup you can resolve




