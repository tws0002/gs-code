__author__ = 'adamb'
import os

class ProjectView():

    def __init__(self, pathParser ):
        ''' requires a pointer to the file parser to interpret paths and template paths'''
        #if not isinstance(pathParser,classmethod):
        #    raise TypeError

        self.pathParser = pathParser

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




