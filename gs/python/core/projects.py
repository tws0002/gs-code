__author__ = 'adamb'
import os, shutil

class ProjectController():

    def __init__(self, pathParser ):
        ''' requires a pointer to the file parser to interpret paths and template paths'''
        #if not isinstance(pathParser,classmethod):
        #    raise TypeError

        self.pathParser = pathParser
        self.activeProject = ''
        self.activeStage = ''
        self.activeAsset = ''
        self.activeTask  = ''

    def copy_templ_tree(self, src, dst):
        ''' copies the template dir structure and substitutes any variable in filenames'''
        shutil.copytree(src, dst)

        #substitute path names with variables

    def new_project(self, upl='//diskstation/jobs/new_project'):
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

6
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




