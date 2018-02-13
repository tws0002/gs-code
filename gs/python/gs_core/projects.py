__author__ = 'adamb'
import os, shutil
import paths
import time
import re
import subprocess


class ProjectController():
    ''' Project controller's main job is to manipulate the data model (the file system) and provide the view (launcher ui)
    this mainly handles interpreting the model (project template definitions) and creating a deleting data from the server'''

    def __init__(self, config_path ):
        """
        :param config_path: file path to projecy.yml to use as the interpreter
        """

        # init with the default project config path
        self.pathParser = paths.PathParser()
        self.pathParser.loadProjectConfigFile(filepath=config_path)

    def setConfig(self, config_path):
        self.pathParser.loadProjectConfigFile(filepath=config_path)

    def copyTemplTree(self, src, dst):
        """copies the template dir structure and substitutes any variable in filenames"""
        # TODO ideally this should eventually substitute any other varibales found within the copy tree
        print "dev: projects.copyTempTree('{0}','{1}')".format(src, dst)
        #try:
        shutil.copytree(os.path.normpath(src), os.path.normpath(dst))
        #except WindowsError:
        #    print 'gs_core.projects.copyTempTree() failed {0} to {1}'.format(src,dst)
        #    raise StandardError

        #substitute path names with variables

    def copyTemplFile(self, src, dst):
        """copies the template dir structure and substitutes any variable in filenames"""
        # TODO ideally this should eventually substitute any other varibales found within the copy tree
        print "dev: projects.copyTempTree('{0}','{1}')".format(src, dst)
        try:
            shutil.copy(os.path.normpath(src), os.path.normpath(dst))
        except WindowsError:
            print 'gs_core.projects.copyTempFile() failed {0} to {1}'.format(src,dst)
            raise StandardError

        #substitute path names with variables


    def newProject(self, upl_dict, upl='', add_stages=[], add_asset_types=[]):
        """
        create a new project structure based on the job. given a url path to the job to create it will generate
        the necessary dict and copy the template dir tree
        this function uses upl dict to ensure that project creation is abstracted and turned into valid paths via the parser
        upl_dict{'server':'//scholar/projects','job':'test_job', 'stage':'production'}
        :param upl_dict:
        :param upl:
        :param add_stages:
        :param add_asset_types:
        :return: returns a 3-tuple detailing success/failure and result: (success, response, result)
        """

        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict,dict):
            if upl != '':
                upl_dict = self.pathParser.parse_path(upl, exists=False)
            else:
                raise ValueError('gs_core.projects.newProject(): no upl_path or upl_dict was specified in call to subst_template_path')

        if 'job' in upl_dict:
            src = self.pathParser.substTemplatePath(upl_dict, template_type='project', template_name='basic', template_var='copy_tree', exists=False)
            proj = self.pathParser.substTemplatePath(upl_dict, template_type='var', template_var='project_root', exists=False)
            if proj != '':
                if os.path.isdir(proj):
                    print 'gs_core.projects.newProject(): Aborting Job Creation, Job Already Exists:{0}'.format(proj)
                    return False, "Job Exists", ""
                print 'gs_core.projects.newProject(): Creating Job:{0}'.format(proj)
                self.copyTemplTree(src, proj)

                print upl_dict
                for stage in  add_stages:
                    src = self.pathParser.substTemplatePath(upl_dict, template_type='stage', template_name=stage, template_var='copy_tree', exists=False)
                    dest = self.pathParser.substTemplatePath(upl_dict, template_type='stage', template_name=stage, template_var='match_path', exists=False)
                    if dest != "":
                        print 'gs_core.projects.newProject(): Creating Stage:{0} {1} from {2}'.format(stage,dest,src)
                        self.copyTemplTree(src, dest)
                    else:
                        return False, "Stage:{0} Not Defined".format(stage), ""

                # update the model which is then responsible for sending signals to attached UI elements to update
                # for now its a manual refresh
                return True, "Success", proj
            else:
                print ('gs_core.projects.newProject(): Could not Create Job, could not parse path from upl_dict:{0}'.format(upl_dict))
                return False, "Invalid Argument", ""
        else:
            print ('gs_core.projects.newProject(): Could not Create Job, No Valid Project was specified in upl_dict:{0}'.format(upl_dict))
            return False, "No Job Specified", ""


    def newStage(self, name='production'):
        """
        creates a new stage of production (pitch/previs/production)
        :param name:
        :return:
        """

        return

    def newAsset(self, upl_dict=None, upl='', add_tasks=[]):
        """
        create a new project structure based on the job. given a url path to the job to create it will generate
        the necessary dict and copy the template dir tree
        this function uses upl dict to ensure that project creation is abstracted and turned into valid paths via the parser
        upl_dict{'server':'//scholar/projects','job':'test_job', 'stage':'production'}
        :param upl_dict:
        :param upl:
        :return:
        """
        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict,dict):
            if upl != '':
                upl_dict = self.pathParser.parsePath(upl, exists=False)
            else:
                raise ValueError('no upl_path or upl_dict was specified in call to gs_core.project.new_asset()')

        if 'asset' in upl_dict:
            src = self.pathParser.substTemplatePath(upl_dict, template_type='asset', template_name=upl_dict['asset_type'], template_var='copy_tree', exists=False)
            asset = self.pathParser.substTemplatePath(upl_dict, template_type='asset', template_name=upl_dict['asset_type'], template_var='match_path', exists=False)

            if asset != '':
                if os.path.isdir(asset):
                    print 'gs_core.projects.newAsset(): Aborting Asset Creation, Asset Already Exists:{0}'.format(asset)
                    return False, "Job Exists", ""
                print 'gs_core.projects.newAsset(): Creating Asset:{0}'.format(asset)
                self.copyTemplTree(src, asset)

                print upl_dict
                for task in add_tasks:
                    src = self.pathParser.substTemplatePath(upl_dict, template_type='task', template_name=task, template_var='copy_tree', exists=False)
                    dest = self.pathParser.substTemplatePath(upl_dict, template_type='task', template_name=task, template_var='match_path', exists=False)
                    if dest != "":
                        print 'gs_core.projects.newAsset(): Creating Task:{0} {1} from {2}'.format(task,dest,src)
                        self.copyTemplTree(src, dest)
                    else:
                        return False, "Task:{0} Not Defined".format(task), ""

                # update the model which is then responsible for sending signals to attached UI elements to update
                # for now its a manual refresh
                return True, "Success", asset
            else:
                print ('gs_core.projects.newAsset(): Could not Create Asset, could not parse path from upl_dict:{0}'.format(upl_dict))
                return False, "Parser Could Not Determine Path", ""
        else:
            print ('gs_core.projects.newAsset(): Could not Create Asset, No Valid asset was specified in upl_dict:{0}'.format(upl_dict))
            return False, "No Asset Specified", ""

    def newScratch(self, upl_dict=None, upl='', allowExists=False):
        """
        creates a username folder and workspace to launch apps into
        :param upl_dict:
        :param upl:
        :return:
        """
        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict,dict):
            if upl != '':
                upl_dict = self.pathParser.parsePath(upl, exists=False)
            else:
                raise ValueError('no upl_path or upl_dict was specified in call to gs_core.project.newScratch()')
        if 'stage' in upl_dict:
            # copy package template
            src = self.pathParser.substTemplatePath(upl_dict, template_type='package', template_name=upl_dict['package'], template_var='copy_tree', exists=False, parent_override='stage')
            pkg = self.pathParser.substTemplatePath(upl_dict, template_type='package', template_name=upl_dict['package'], template_var='match_path', exists=False, parent_override='stage')
            if pkg != '':
                #print upl_dict
                if allowExists and os.path.isdir(pkg):
                    print 'gs_core.projects.newScratch(): Package Exists:{0}'.format(pkg)
                    # create the package folder if it doesnt exist
                    return True, "gs_core.projects.newScratch(): Package Exists", pkg
                else:
                    print 'gs_core.projects.newScratch(): Creating Package:{0}'.format(pkg)
                    # create the package folder if it doesnt exist
                    if not os.path.isdir(pkg):
                        self.copyTemplTree(src, pkg)
                        return True, "gs_core.projects.newScratch(): Package Created, Aborted", pkg
                    return False, "gs_core.projects.newScratch(): Package Already Exists, Aborted", ''

            else:
                print ('gs_core.projects.newScratch(): Could not Create Package, could not parse path from upl_dict:{0}'.format(upl_dict))
                return False, "Parser Could Not Determine Path", ""
        else:
            print ('gs_core.projects.newScratch(): Could not Create Package, No Valid Project Stage was specified in upl_dict:{0}'.format(upl_dict))
            return False, "No Stage Specified", ""
        return

    def newTask(self, upl_dict=None, upl=''):
        """
        create a new project structure based on the job. given a url path to the job to create it will generate
        the necessary dict and copy the template dir tree
        this function uses upl dict to ensure that project creation is abstracted and turned into valid paths via the parser
        upl_dict{'server':'//scholar/projects','job':'test_job', 'stage':'production'}
        :param upl_dict:
        :param upl:
        :return:
        """

        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict,dict):
            if upl != '':
                upl_dict = self.pathParser.parsePath(upl, exists=False)
            else:
                raise ValueError('no upl_path or upl_dict was specified in call to gs_core.project.new_asset()')

        if 'task' in upl_dict:
            src = self.pathParser.substTemplatePath(upl_dict, template_type='task', template_name=upl_dict['task'], template_var='copy_tree', exists=False)
            task = self.pathParser.substTemplatePath(upl_dict, template_type='task', template_name=upl_dict['task'], template_var='match_path', exists=False)

            if task != '':
                if os.path.isdir(task):
                    print 'gs_core.projects.newTask(): Aborting Task Creation, Task Already Exists:{0}'.format(task)
                    return False, "Job Exists", ""
                print 'gs_core.projects.newTask(): Creating Task:{0}'.format(task)
                self.copyTemplTree(src, task)

                print upl_dict
                # update the model which is then responsible for sending signals to attached UI elements to update
                # for now its a manual refresh
                return True, "Success", task
            else:
                print ('gs_core.projects.newTask(): Could not Create Task, could not parse path from upl_dict:{0}'.format(upl_dict))
                return False, "Parser Could Not Determine Path", ""
        else:
            print ('gs_core.projects.newTask(): Could not Create Task, No Valid task was specified in upl_dict:{0}'.format(upl_dict))
            return False, "No Task Specified", ""

    def newScenefile(self, upl_dict=None, upl=''):
        """
        creates a new scene, a new scene is defined by a package, a scene name, and a version number
        :param upl_dict:
        :param upl:
        :param add_tasks:
        :return:
        """
        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict,dict):
            if upl != '':
                upl_dict = self.pathParser.parsePath(upl, exists=False)
            else:
                raise ValueError('no upl_path or upl_dict was specified in call to gs_core.project.newScenefile()')
        if 'scenename' in upl_dict:
            # copy package template
            src = self.pathParser.substTemplatePath(upl_dict, template_type='package', template_name=upl_dict['package'], template_var='copy_tree', exists=False)
            pkg = self.pathParser.substTemplatePath(upl_dict, template_type='package', template_name=upl_dict['package'], template_var='match_path', exists=False)
            upl_dict['scenetype'] = self.pathParser.substTemplatePath(upl_dict, template_type='task', template_name=upl_dict['task'], template_var='scenefile_type', exists=False)
            ssrc = self.pathParser.substTemplatePath(upl_dict, template_type='scenefile', template_name=upl_dict['scenetype'], template_var='copy_path', exists=False)
            spath = self.pathParser.substTemplatePath(upl_dict, template_type='scenefile', template_name=upl_dict['scenetype'], template_var='workscene_path', exists=False)
            sfile = self.pathParser.substTemplatePath(upl_dict, template_type='scenefile', template_name=upl_dict['scenetype'], template_var='workscene_file', exists=False)

            if sfile != '':
                if os.path.isdir(sfile):
                    print 'gs_core.projects.newSceneFile(): Aborting Scenefile Creation, Scenefile Already Exists:{0}'.format(sfile)
                    return False, "Job Exists", ""
                print 'gs_core.projects.newTask(): Creating Package:{0}'.format(pkg)
                # create the package folder if it doesnt exist
                if not os.path.isdir(pkg):
                    self.copyTemplTree(src, pkg)

                # search and replace any files matching the scenfile to load
                print 'gs_core.projects.newTask(): Creating Scenefile:{0}'.format(sfile)
                self.copyTemplFile(ssrc, '/'.join([spath,sfile]))

                print upl_dict

                # update the model which is then responsible for sending signals to attached UI elements to update
                # for now its a manual refresh
                return True, "Success", '/'.join([spath,sfile])
            else:
                print ('gs_core.projects.newSceneFile(): Could not Create Scenefile, could not parse path from upl_dict:{0}'.format(upl_dict))
                return False, "Parser Could Not Determine Path", ""
        else:
            print ('gs_core.projects.newSceneFile(): Could not Create Scenefile, No Valid scenename was specified in upl_dict:{0}'.format(upl_dict))
            return False, "No Task Specified", ""
        return

    def getAssetsList(self, upl_dict=None, upl='', asset_type='', groups_only=False):
        ''' given a project path (upl), returns a list of assets found in the assets lib_path defined in projects.yml

        :param upl: universal project locator (project file system)
        :param asset_type:
        :param groups_only: only return asset groups (if any)
        :return: 2-tuple of asset_lib_path, list of assets (will include asset_group/asset_name if any are found)
        '''

        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict,dict):
            if upl != '':
                upl_dict = self.pathParser.parsePath(upl, exists=False)
            else:
                raise ValueError('gs_core.projects.getAssetsList() no upl_path or upl_dict was specified in call to gs_core.projects.getAssetsList()')
        #START_TIME = time.time()

        asset_list = []
        asset_lib_path = self.pathParser.getAssetLibList(upl_dict=upl_dict, asset_type=asset_type)
        qualifier = self.pathParser.getTemplatePath('asset', asset_type, 'qualifier_path')

        # SLOW INEFFICIENT WALK OF DIRS (ACTUALLY THIS IS FASTEST)
        if os.path.isdir(asset_lib_path):
            for base_dir in os.listdir(asset_lib_path):
                full_path = '/'.join([asset_lib_path, base_dir])
                if os.path.isdir(full_path) and not base_dir.startswith('.') :
                    sub_dirs = os.listdir(full_path)
                    # if its an empty folder show it as a possible asset group
                    if groups_only and len(sub_dirs) < 2:
                        asset_list.append(base_dir)
                    if qualifier != '' and qualifier in sub_dirs:
                        if not groups_only:
                            asset_list.append(base_dir)
                    else:
                        for sub_dir in sub_dirs:
                            full_sub_path = '/'.join([full_path, sub_dir])
                            if os.path.isdir(full_sub_path) and not base_dir.startswith('.'):
                                sub_grp_files = os.listdir(full_sub_path)
                                if qualifier != '' and qualifier in sub_grp_files:
                                    if groups_only:
                                        if base_dir not in asset_list:
                                            asset_list.append(base_dir)
                                    else:
                                        asset_list.append('/'.join([base_dir,sub_dir]))
        else:
            print ('asset_lib_path={0} not found'.format(asset_lib_path))


        ### if os.path.isdir(asset_lib_path):
        ###     list_dir = self.walk3deep(asset_lib_path)
        ###     qual_assets = [x for x in list_dir if x.find(qualifier)]
        ###     plen = len(asset_lib_path) + 1
        ###     qlen = (len(qualifier) + 1) * -1
        ###     for a in qual_assets:
        ###         s = a.replace('\\', '/')
        ###         if groups_only:
        ###             asset_list.append(s[plen:qlen].spit('/')[0])
        ###         else:
        ###             asset_list.append(s[plen:qlen])
        ### else:
        ###     print ('asset_lib_path={0} not found'.format(asset_lib_path))

        # NOT AS FAST AS I HOPED
        ###if os.path.isdir(asset_lib_path):
        ###
        ###    qual_assets = glob('{0}/*/*/{1}'.format(asset_lib_path,qualifier))
        ###    if not groups_only:
        ###        qual_assets.extend(glob('{0}/*/{1}'.format(asset_lib_path, qualifier)))
        ###    plen = len(asset_lib_path) + 1
        ###    qlen = (len(qualifier) + 1) * -1
        ###    for a in qual_assets:
        ###        s = a.replace('\\', '/')
        ###        if groups_only:
        ###            asset_list.append(s[plen:qlen].spit('/')[0])
        ###        else:
        ###            asset_list.append(s[plen:qlen])
        ###else:
        ###    print ('asset_lib_path={0} not found'.format(asset_lib_path))

        #TEST OF USING SYS CALLS TO GET LIST OF PATHS IN ASSET
        # get list of directories and sub directories for parsing
        #### base_list = self.multiFastGlob([asset_lib_path], ['*'], dir_only=True, all_subdirs=False)
        #### subdir_list = self.multiFastGlob(base_list, ['*'], dir_only=True, all_subdirs=False)
        #### subsubdir_list = self.multiFastGlob(subdir_list, ['*'], dir_only=True, all_subdirs=False)
        #### for base_dir in base_list:
        ####     if not os.path.basename(base_dir).startswith('.'):
        ####         if '/'.join([base_dir,qualifier]) in subdir_list:
        ####             if not groups_only:
        ####                 asset_list.append(os.path.basename(base_dir))
        #### for sub_dir in subdir_list:
        ####     if not os.path.basename(sub_dir).startswith('.'):
        ####         if '/'.join([sub_dir,qualifier]) in subsubdir_list:
        ####             if groups_only:
        ####                 if os.path.basename(sub_dir) not in asset_list:
        ####                     asset_list.append(os.path.basename(sub_dir))
        ####                 else:
        ####                     asset_list.append('/'.join(sub_dir.split('/')[-2:]))

        result = (asset_lib_path, asset_list)
        #elapsed_time = time.time() - START_TIME
        #print("core.projects.getAssetsList() ran in {0} sec".format(elapsed_time))
        return result

    def getDefaultTasks(self, asset_type):
        """

        :return: a list of default tasks string comma separated)
        """
        return self.pathParser.getDefaultTasks(asset_type).split(',')

    def getStageList(self):
        '''

        :return: 2-tuple of defined stage-type along with display-name
        '''
        result = []
        for template in self.pathParser.templates['stage_templates']:
            pair = (template,self.pathParser.getTemplatePath('stage', template, 'display_name'))
            result.append(pair)
        return result

    def getAssetTypeList(self):
        '''

        :return: 2-tuple of defined asset-type along with display-name
        '''
        unsorted, result = [], []
        order = 0,
        for template in self.pathParser.templates['asset_templates']:
            if 'display_order' in self.pathParser.templates['asset_templates'][template]:
                order = self.pathParser.templates['asset_templates'][template]['display_order']
            else:
                order += 1
            pair = (order, template,self.pathParser.getTemplatePath('asset', template, 'display_name'))
            unsorted.append(pair)

        # sort by order and unpack the order number
        for order, templ, path in sorted(unsorted, key=lambda x: x[0]):
            result.append((templ,path))

        return result

    def getScenesList(self, filepath='', file_types='all'):
        '''
        :param filepath: path to folder to check
        :return: sorted list of 2-tuple (fullpath, rel_path) found by globbing
        '''
        valid_result = []
        # iterates all subtree looking for patterns that match the glob *.mb
        result = [y for x in os.walk(filepath) for y in self.multiGlob(x[0], ['mb', 'ma', 'nk', 'aep', 'hip'])]
        #result = self.v(filepath, ['mb', 'ma', 'nk', 'aep'])
        for name in result:
            if not os.path.isdir(os.path.join(filepath, name)) and not name.startswith('.') and not name.startswith('_'):
                rel_path = name[len(filepath) + 1:]
                filename = os.path.basename(rel_path)
                valid_result.append((name,rel_path))
        return valid_result

    def getTaskTypesList(self):
        return self.pathParser.getTemplateTypesList('task')

    def getTaskList(self, upl_dict=None, upl='', asset_name=''):
        ''' given a project path (upl), returns a list of existing tasks found in the assets, the
         list is checked against valid tasks defined in projects.yml
        :param upl: universal project locator (project file system)
        :param asset_type:
        :return: 2-tuple of (asset_path, [(task_type, display_name)]) list of found qualified tasks
        '''
        START_TIME = time.time()

        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict, dict):
            if upl != '':
                upl_dict = self.pathParser.parsePath(upl, exists=False)
            else:
                raise ValueError(
                    'gs_core.projects.getTaskList() no upl_path or upl_dict was specified')

        task_types = self.getTaskTypesList()
        task_list = []
        #asset_path = self.pathParser.getAssetLib(upl,)
        #qualifier = self.pathParser.getTemplatePath('task', task_type, 'qualifier_path')
        print 'dev: gs_core.projects.getTaskTypeList asset_path ={0} task_types={1}'.format(upl, task_types)
        if upl != '':
            if os.path.isdir(upl):
                order = 0
                for base_dir in os.listdir(upl):
                    full_path = '/'.join([upl, base_dir])
                    #and not base_dir.startswith('_')
                    if base_dir in task_types:
                        if 'display_order' in self.pathParser.templates['task_templates'][base_dir]:
                            order = self.pathParser.templates['task_templates'][base_dir]['display_order']
                        else:
                            order += 1
                        if os.path.isdir(full_path) and not base_dir.startswith('.') :
                            sub_dirs = os.listdir(full_path)
                            #if qualifier != '' and qualifier in sub_dirs:
                            task_list.append((order,base_dir))
            else:
                print ('asset_path={0} not found'.format(upl))
        else:
            task_list = task_types

        # sort by order and unpack the order number
        sorted_task_list = []
        for order, task in sorted(task_list, key=lambda x: x[0]):
            sorted_task_list.append(task)

        result = (upl, sorted_task_list)
        elapsed_time = time.time() - START_TIME
        print("ProjectController.getTaskTypeList() ran in {0} sec".format(elapsed_time))
        return result

    def getPackageTypesList(self):
        return self.pathParser.getTemplateTypesList('package')

    def getTaskScenesList(self, upl_dict=None, upl='', task_type=''):
        """
        used to populate scene lists in the launcher and through other scene loaders
        :param upl_dict: optional project locator dictionary, if not provided upl path is used instead
        :param upl: a file path to interpret a upl_dict from, only used if upl_dict isn't provided
        :param task_type: specific type of task you're looking for
        :return: a list of scenes found. includes subdirectories to file based on package
        """
        valid_result = []

        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict,dict):
            if upl != '':
                upl_dict = self.pathParser.parsePath(upl, exists=False)
            else:
                raise ValueError('no upl_path or upl_dict was specified in call to gs_core.project.getTaskScenesList()')

        task_path = self.pathParser.substTemplatePath(upl_dict=upl_dict, template_type='task', template_name=task_type, template_var='match_path')
        #print "core.projects.getTaskScenesList() upl={0} task_path={1}".format(upl_dict, task_path)

        result_files = [y for x in os.walk(task_path) for y in self.multiGlob(x[0], ['mb', 'ma', 'nk', 'aep', 'hip'])]
        #result_files = self.multiFastGlob(upl, ['mb', 'ma', 'nk', 'aep'])
        for name in result_files:
            if not os.path.isdir(os.path.join(task_path,name)) and not name.startswith('.') and not name.startswith('_'):
                rel_path = name[len(task_path)+1:]
                filename = os.path.basename(rel_path)
                valid_result.append(rel_path)

        #return valid_result
        result = (task_path, valid_result)
        return result

    def getScenefileList(self, upl_dict=None, upl='', template_type='scene_basic', scene_type='workscene', latest_version=False, combine_seq=True):
        """
        used to populate scene lists in the launcher and through other scene loaders. renders may contain multiple paths
        :param upl_dict: optional project locator dictionary, if not provided upl path is used instead
        :param upl: a file path to interpret a upl_dict from, only used if upl_dict isn't provided
        :param task_type: specific type of task you're looking for
        :return: a list of scenes found. includes subdirectories to file based on package
        """
        valid_results = []
        valid_ver = []

        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict,dict):
            if upl != '':
                upl_dict = self.pathParser.parsePath(upl)
            else:
                raise ValueError('no upl_path or upl_dict was specified in call to gs_core.project.getTaskScenesList()')

        if 'scenename' in upl_dict:
            scene_path = self.pathParser.substTemplatePath(upl_dict=upl_dict, template_type='scenefile', template_name=template_type, template_var='{0}_path'.format(scene_type))
            #scene_file = self.pathParser.substTemplatePath(upl_dict=upl_dict, template_type='scenefile', template_name=template_type, template_var='{0}_file'.format(scene_type))
            #search_paths = [scene_path]
            ver = upl_dict['version'] if 'version' in upl_dict else ''
            paths_and_version = [(scene_path, '', ver)]
            root_path = scene_path
            # if there are layers in path, we must resolve them by looking at the file system and adding each to the search path
            if scene_type == 'render':
                if '/<layer>' in scene_path:
                    paths_and_version = []
                    search_paths = []
                    # get the found layers and search each one
                    root_layer_path = scene_path.split('/<layer>')[0]
                    root_path = root_layer_path
                    rlayers = os.listdir(root_layer_path)
                    # TODO: this works but it won't support paths where the version comes before the layer. need
                    # to think about a better way to do this
                    for rl in rlayers:
                        if not rl.startswith('.') and not rl.startswith('_'):
                            # if the latest version is requested, we must search all versions with the layer
                            if latest_version:
                                max_ver = 0
                                for ver in os.listdir('/'.join([root_layer_path,rl])):
                                    if not ver.startswith('.') and not ver.startswith('_'):
                                        v_int = int(re.search(r'[0-9]+', ver).group(0))
                                        if v_int > max_ver:
                                            max_ver = v_int
                                # TODO make the zfill use a project-wide variable
                                found_ver = 'v{0}'.format(str(max_ver).zfill(3))
                                found_path = '/'.join([root_layer_path, rl, found_ver])
                                paths_and_version.append((found_path, rl, found_ver))
                            else:
                                search_paths.append(scene_path.replace('<layer>',rl))

            for path, lyr, ver in paths_and_version:
                upl_dict['version'] = ver
                if lyr != '':
                    upl_dict['layer'] = lyr
                #scene_path = self.pathParser.substTemplatePath(upl_dict=upl_dict, template_type='scenefile', template_name=template_type, template_var='{0}_path'.format(scene_type))
                scene_file = self.pathParser.substTemplatePath(upl_dict=upl_dict, template_type='scenefile', template_name=template_type, template_var='{0}_file'.format(scene_type))
                scn_wo_vers = '_'.join(os.path.basename(scene_file).split('_')[:-3])

                result_files = [y for x in os.walk(path) for y in self.multiGlob(x[0], ['mb', 'ma', 'nk', 'aep', 'hip', 'exr','abc','mov'])]

                for name in result_files:
                    if not os.path.isdir(os.path.join(path,name)) and not name.startswith('.') and not name.startswith('_'):
                        if os.path.basename(name).startswith(scn_wo_vers):
                            rel_path = name[len(root_path)+1:]
                            valid_results.append(rel_path)

            # return sequences of frames as a single item
            #if combine_seq:
            #    combined_list = []
            #    for r in valid_results:
            #        frame = int(re.search(r'\.[0-9]+', ver).group(0))
            #
            #    valid_results = combined_list
            #
            return (root_path, valid_results)
        else:
            print ("core.projects.getScenefileList() could not dermine scenename from upl_dict: {0}".format(upl_dict))
            return ()

    def getLatestSceneVersion(self, upl_dict, upl, scene_type='workscene'):
        """
        returns the latest found version of a specific file
        :return:
        :param scene_type: defines which scene file to check for latest version (workscene, publish, render)
        """

    def multiGlob(self, path, filter_list):
        cpath = path.replace('\\','/')
        result = []
        filters = '.*\.{0}$'.format('$|.*\.'.join(filter_list))
        #print 'multi_glob checking path {0}'.format(cpath)
        for x in os.listdir(cpath):
            if re.match(filters, x):
                #print 'matched {0} with filter {1}'.format(x,filters)
                result.append('/'.join([cpath,x]))
        return result

    def multiFastGlob(self, path, filter_list, dir_only=False, all_subdirs=True):
        """ uses sys calls to try and speed up file listing. has issues tho since windows' DIR.exe command is
        agnostic about multiple input paths. aka... it only returns a dumb list of subfolders that you cant tell which
        input folder they were found in"""
        result_list = []

        cmds = []
        pl = ''
        for f in filter_list:
            for p in path:
                if len(pl) < 8000:
                    pl += " {0}\\{1}".format(p.replace('/', '\\'),f)
                else:
                    flags = " /S" if all_subdirs else ""
                    flags += " /AD" if dir_only else flags
                    cmds.append("dir {0} {1}".format(pl, flags))
                    pl = ''
        flags = " /S" if all_subdirs else ""
        flags += " /AD" if dir_only else flags
        cmds.append("dir {0} {1}".format(pl, flags))

        #path_str = ' '.join(filtered_paths)
        #cmd = "dir {0} ".format(path_str)
        result_list = []
        for c in cmds:
            print ("system cmd: {0}".format(c))
            result = subprocess.check_output(c, shell=True)
            # if recursion is off, dir doesn't return full path names, so we must do it ourselves
            pa = ''
            for ea in result.splitlines():
                path_prefix = ' Directory of'
                if ea.startswith(path_prefix):
                    print ('directory found {0}'.format(ea))
                    pa = ea[(len(path_prefix)+1):]
                    #print ('directory found {0}'.format(pa))
                else:
                    cols = ea.split()
                    if 4 < len(cols) < 6:
                        print ('found 5 cols: {0}'.format(cols))
                        if re.match(r'../../....',cols[0]):
                            if cols[-1] != '.' and cols[-1] != '..':
                                result_list.append('\\'.join([pa,cols[-1]]))

        return result_list

    def walk3deep(self, path):
        """ this is horribly slow, bad suggestion"""
        rslt = []
        for root, dirs, files in os.walk(path, topdown=True):
            depth = root[len(path) + len(os.path.sep):].count(os.path.sep)
            if depth == 2:
                # We're currently two directories in, so all subdirs have depth 3
                rslt += [os.path.join(root, d) for d in dirs]
                dirs[:] = []  # Don't recurse any deeper
        return rslt

    def loadProjectModel(self, project_path='', use_cache=False):
        # load project path
        self.pathParser.get_libraries(project_path)
        # for each library, load all library structures (assets 2d, assets 3d, shots,)

        # for each task struct
        return

    def loadLibrary(self, lib_name):
        return

    def loadProjLibModel(self, lib_path):
        result = []
        path = lib_path

        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path,name)) and not name.startswith('.') and not name.startswith('_'):
                result.append(name)

        # list all the shots/assets in the lib
        for asset in result:
            load_task_model(self,task_path)






