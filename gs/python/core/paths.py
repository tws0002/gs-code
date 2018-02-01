__author__ = 'adamb'

import sys, os
from settings import *
import yaml
import re


class PathParser:
    '''Class that reads a project config and parses and stores information about the folder structure here
    Core will internally pass file-based paths between functions as a means of communicating shot information
    and then methods can use the parser to turn the path into datasets. The parser also provides methods to read the server
    for list of objects, assets, tasks, and files
    UPL - a concept is used here called a Uniform Project Locator, this is analagous to a URL (Uniform Resource Locator)
    it is a string that when parsed through a template, it tells you information about your location in the project'''

    def __init__(self):
        self.vars = {}
        self.lib_templates = {}
        self.project_templates = {}
        self.stage_templates = {}
        self.asset_templates = {}
        self.task_templates = {}
        self.package_templates = {}
        self.project_data = {}
        return

    def getConfigFile(self, filepath):
        f = open(filepath)
        # use safe_load instead load
        dataMap = yaml.safe_load(f)
        f.close()
        return dataMap

    def parseVarSubst(self):
        for var, val in self.vars.iteritems():
            # check if any string substitution is needed in the value
            val_subst = re.findall('<(.+?)>', val)
            for match in val_subst:
                if match in self.vars:
                    val = val.replace(('<' + match + '>'), self.vars[match])
                if match in os.environ:
                    val = val.replace(('%' + match + '%'), os.environ[match])
            self.vars[var] = val

    def parseTaskSubst(self, parse_dict={}):
        ''' for each task_struct, expand any %% vars with project vars, task local vars, or environment vars'''
        for task, data in parse_dict.iteritems():
            # load up the local vars
            localvars = dict(parse_dict[task])
            for var, val in data.iteritems():
                # check if any string substitution is needed in the value
                val_subst = re.findall('%(.+?)%', str(val))
                for match in val_subst:
                    if match in self.vars:
                        val = val.replace(('%' + match + '%'), self.vars[match])
                    if match in localvars:
                        val = val.replace(('%' + match + '%'), localvars[match])
                    if match in os.environ:
                        val = val.replace(('%' + match + '%'), os.environ[match])
                parse_dict[task][var] = val

    def loadProjectConfigFile(self, filepath, version=None):
        print ("Loading Project file path {0}".format(filepath))
        dataMap = self.getConfigFile(filepath)
        self.project_data = dataMap

        self.vars = {}
        self.lib_templates = {}
        self.project_templates = {}
        self.stage_templates = {}
        self.asset_templates = {}
        self.task_templates = {}
        self.package_templates = {}

        self.loadProjectConfig(self.project_data)

    def loadProjectConfig(self, dataMap, version='1.0'):
        ''' loads job data structs, expand any known variables wrapped in \%\%, and expands inherited structs'''

        for key, value in dataMap.iteritems():
            if key == 'path_vars':
                for var, val in dataMap[key].iteritems():
                    self.vars[var] = val
                self.parseVarSubst()
                self.parseVarSubst()

        # load library templates
        for key, value in dataMap.iteritems():
            if key == 'lib_templates':
                for lib, data in dataMap[key].iteritems():
                    self.lib_templates[lib] = dict(dataMap['lib_templates'][lib])
            if key == 'stage_templates':
                for proj, data in dataMap[key].iteritems():
                    self.stage_templates[proj] = dict(dataMap['stage_templates'][proj])
            if key == 'project_templates':
                for proj, data in dataMap[key].iteritems():
                    self.project_templates[proj] = dict(dataMap['project_templates'][proj])
            if key == 'package_tempaltes':
                for package, data in dataMap[key].iteritems():
                    self.package_templates[package] = dict(dataMap['package_templates'][package])

        # load asset templates, although currently inherit calls are directly copied from the dataMap['asset_templates']
        for key, value in dataMap.iteritems():
            if key == 'asset_templates':
                for asset, data in dataMap[key].iteritems():
                    self.asset_templates[asset] = dict(dataMap['asset_templates'][asset])

        # load task templates. first load all the dictionaries obeying calls for inheritance
        for key, value in dataMap.iteritems():
            if key == 'task_templates':
                for task, data in dataMap[key].iteritems():
                    # print ("adding {0} to self.task_templates".format(task))
                    self.task_templates[task] = dict(dataMap['task_templates'][task])
                    if 'inherits' in data:
                        # make a copy
                        val = data['inherits']
                        if val in dataMap['asset_templates']:
                            self.task_templates[task] = dict(dataMap['asset_templates'][val])
                        else:
                            print ("Could not inherit task_struct {0}, it could not be found".format(val))
        # load task templates. phase 2 -add overrides to inherited structs
        for key, value in dataMap.iteritems():
            if key == 'task_templates':
                for task, data in dataMap[key].iteritems():
                    if 'inherits' in data:
                        for var, val in data.iteritems():
                            # if struct has an inherits value
                            self.task_templates[task][var] = val
        # then expand all vars with local and project config variables (run twice to ensure all vars are substituted)
        self.parseTaskSubst(self.asset_templates)
        self.parseTaskSubst(self.asset_templates)
        self.parseTaskSubst(self.task_templates)
        self.parseTaskSubst(self.task_templates)
        return

    def templateToRegex(self, filepath, limiters, exclude):
        """
        converts a simplified path pattern (defined in project.yml) <group>/<to>/<match> to a regex named
        capture group string (?P<group>)/(?P<to>)/(?P<match>)
        :param filepath: path string to convert to a named group
        :param limiters: exclude capture group from matching past certain characters (like a folder slash or underscore for example)
        :param exclude: string to exclude from matching
        :return:
        """

        # TODO make this limiter encoding more robust, needs to regex encode the string. maybe theres something for this
        lstr = ''
        for l in limiters:
            if l == '.':
                l = '\\.'
            lstr += l

        result = filepath.replace('<', '(?P<')
        result = result.replace('>', '>[^{0}]*)'.format(lstr))
        for e in exclude:
            result = result.replace('{0}[^{1}]*'.format(e, lstr), '{0}.*'.format(e))
        return str(result)

    def getTemplatePath(self, template_type, template_name, template_var):
        ''' returns the value of the template struct '''
        result = ''
        d = self.vars
        if template_type == 'var':
            if template_var in d:
                result = d[template_var]
        else:
            if template_type == 'asset':
                d = self.asset_templates
            elif template_type == 'task':
                d = self.task_templates
            elif template_type == 'project':
                d = self.project_templates
            elif template_type == 'stage':
                d = self.stage_templates
            elif template_type == 'package':
                d = self.package_templates
            if template_name in d:
                if template_var in d[template_name]:
                    result = d[template_name][template_var]
            else:
                print "Warning: core.paths.get_template_path(): {0} not found in self.{1}_templates for var {2}".format(
                    template_name, template_type, template_var)
                raise StandardError
        return result

    def substTemplatePath(self, upl_dict=None, upl='', template_type='', template_name='', template_var='',
                          template_file='', exists=True):
        ''' given a dict it will return a substituted template path that matches the search qualifications'''

        result = ''
        # if no upl dict is provided, parse it from the upl string
        if not isinstance(upl_dict, dict):
            if upl != '':
                upl_dict = self.parsePath(upl, exists=exists)
            else:
                raise ValueError('no upl_path or upl_dict was specified in call to subst_template_path')

        rp = re.compile("(<{0}>)".format('>|<'.join(upl_dict.keys())))
        #print ("core.paths.substTemplatePath getTemplatePath({0}, {1}, {2})".format(template_type, template_name, template_var))
        templ_path = self.getTemplatePath(template_type, template_name, template_var)
        if template_file != '':
            templ_file = self.getTemplatePath(template_type, template_name, template_file)
            if templ_file != '':
                templ_path = '/'.join([templ_path, templ_file])
        # print ("template path is: {0}".format(templ_path))
        resultn = rp.subn(lambda repl: '{0}'.format(upl_dict[repl.group()[1:-1]]), templ_path)
        # make sure that the number of matched groups is equal to or greater than the keys in the upl dictionary
        # this wont always be true however in cases where the variable requested only has
        # if resultn[1] >= len(upl_dict.keys()):
        # and no other <key> template strings are left, then print match found
        if '<' not in resultn[0]:
            result = resultn[0]

        # if result == '':
        #        print ("Warning: subst_template_path(): No Exact Match Found, Closest match is {0}".format(resultn[0]))

        return result

    def getPath(self, upl_dict, hint_type='', hint_name='', hint_var=''):
        """
        :param upl_dict: project location dictionary
        :param hint_type: suggests the type of template to search for (speeds up routine)
        :param hint_name: suggests the the defined name of the specified template type to search for
        :param hint_var: suggests the variable name to search for
        :return: a valid file path that represents that object
        """
        # build a regex string of all the keys in dict
        # eg: "(<job>|<asset>|<share>)"
        result_path = ''
        if not isinstance(upl_dict, dict):
            raise TypeError

        # re_match_str = "(<{0}>)".format('>|<'.join(object_dict.keys()))
        # match_count = len(object_dict.keys())
        # rp = re.compile(re_match_str)
        m = []

        if hint_type == 'var' or hint_type == '':
            if hint_var != '':
                subst_path = self.substTemplatePath(upl_dict=upl_dict, template_type='var', template_name='',
                                                    template_var=hint_var)
                if subst_path != '':
                    m.append(subst_path)
            else:
                for var, val in self.vars.iteritems():
                    subst_path = self.substTemplatePath(upl_dict=upl_dict, template_type='var', template_var=var)
                    if subst_path != '':
                        m.append(subst_path)

        if hint_type == 'asset' or hint_type == '':
            # for each asset do a substition pass, then check for leftover templates keys
            for asset, data in self.asset_templates.iteritems():
                if 'work_path' in data:
                    tfile = 'work_file' if 'ext' in upl_dict else ''
                    subst_path = self.substTemplatePath(upl_dict=upl_dict, template_type='asset',
                                                        template_name=asset, template_var='work_path',
                                                        template_file=tfile)
                    if subst_path != '':
                        m.append(subst_path)

        # for each task do a substition pass, then check for leftover templates keys
        if hint_type == 'task' or hint_type == '':
            for task, data in self.task_templates.iteritems():
                if 'work_path' in data:
                    tfile = 'work_file' if 'ext' in upl_dict else ''
                    # print ("subst_template_path({0},{1},{2},{3})".format('obj_dict', 'task', 'work_path', 'work_file'))
                    subst_path = self.substTemplatePath(upl_dict=upl_dict, template_type='task', template_name=task,
                                                        template_var='work_path', template_file=tfile)
                    if subst_path != '':
                        m.append(subst_path)

        # search through matches and return the shortest full match
        # print ("Possible Matches: {0}".format(m))
        if len(m):
            result_path = min(m, key=len)

        if not os.path.exists(result_path):
            print ("Warning: core.paths.getPath() path does not exists {0}".format(result_path))
            result_path = ''
        return result_path

    def parsePath(self, filepath, hint='', exists=True):
        """
        :param filepath: path to parse against the project templates
        :param hint: suggests the type of template to search for (speeds up routine)
        :param exists: if true, returns only existing objects, if false will return speculative paths as well
        :return: a project location dictionary (upl) that matches the given path against templates
        """
        ''' returns an object containing details about the file path based on the pathname given. Very similar to a url parser'''
        # filepath = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU/animation/SH_040_CU_C000_A014_L000_AB.mb'
        result_obj = {}
        # match against root variables
        # if the path fully matches the task root and task, but is longer, do further tests on other variables within the root
        if not isinstance(filepath, basestring):
            raise TypeError

        if exists and not os.path.exists(filepath):
            print ("Filepath: {0} does not exist, nice try".format(filepath))
            return result_obj

        split_path = (filepath, "")

        if exists and not os.path.isdir(filepath):
            split_path = os.path.split(filepath)

        # <file_share>/<job>/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/<shot>
        full_match = False
        partial_match = False
        task_path_match = False
        task_file_match = False

        if hint == 'var' or hint == '':
            for var, val in self.vars.iteritems():
                rgx_path = self.templateToRegex(filepath=val, limiters=['/'], exclude=['<server>'])
                rp = re.compile(rgx_path)
                # print ('checking path_vars: {0}'.format(var))
                if rp.match(split_path[0]):
                    for m in rp.finditer(split_path[0]):
                        # print ('Matched path with path_vars: {0}'.format(var))
                        # print m.groupdict()
                        result_obj = dict(m.groupdict())

        # look for path match in asset structs
        if hint == 'asset' or hint == '':
            for asset, data in self.asset_templates.iteritems():
                if 'work_path' in data:
                    rgx_path = self.templateToRegex(filepath=data['work_path'], limiters=['/'], exclude=['<server>'])
                    rp = re.compile(rgx_path)
                    # print ('checking path_vars: {0}'.format(var))
                    if rp.match(split_path[0]):
                        for m in rp.finditer(split_path[0]):
                            result_obj = dict(m.groupdict())

        # look for path match in task structs
        # (?P<file_share>.*)/(?P<job>.*)/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/(?P<shot>[^/]*)/(?P<task>[^/]*)/(?P<shot2>[^/]*)_(?P<cversion>.*)_(?P<aversion>.*)_(?P<lversion>.*)_(?P<initials>.*)\.(?P<ext>.*)
        if hint == 'task' or hint == '':
            for task, data in self.task_templates.iteritems():

                if 'work_path' in data:
                    # should cache converted regexs
                    rgx_path = self.templateToRegex(filepath=data['work_path'], limiters=['/'], exclude=['<server>'])
                    rgx_file = self.templateToRegex(filepath=data['work_file'], limiters=['_', '.'],
                                                    exclude=['<shot>', '<asset>'])

                    # print ("task:{1} rgx_file={0}".format(rgx_file,task))

                    rp = re.compile(rgx_path)
                    rf = re.compile(rgx_file)
                    # print ('checking task_struct: {0}'.format(task))

                    # match the path first
                    # if rp.match(split_path[0]):
                    for m in rp.finditer(split_path[0]):
                        if task_path_match == True:
                            break
                        # print ('Matched path with task_struct: {0}'.format(task))
                        # print m.groupdict()
                        result_obj.update(m.groupdict())
                        task_path_match = True
                        if split_path[1] != "":
                            # if rf.match(split_path[1]):
                            # TODO: if its not a complete match with the regex, does it at least match a portion of the regex fully? (partial path)
                            # also need to handle searching other task paths other than work_path
                            for n in rf.finditer(split_path[1]):
                                if task_file_match == True:
                                    break
                                # print ('{0} matched filename with task_struct: {1}'.format(split_path[1],task))
                                # print n.groupdict()
                                task_file_match = True
                                result_obj['task'] = task
                                # manually update the file name object data, if a key doesn't match though, we have to return false
                                for key, val in n.groupdict().iteritems():
                                    if key in result_obj:
                                        # if filename keys don't match the pathname keys, then the file isn't a match
                                        if not result_obj[key] == n.groupdict()[key]:
                                            task_file_match = False
                                if task_file_match:
                                    result_obj.update(n.groupdict())

        # validate the data, (does the file exist?, is the file itself resolved or just the path, does the project have valid structure?)
        # print result_obj
        return result_obj

    def getProjectList(self, server_path, full_path=True):
        ''' returns tuples of server projects '''
        result = ()
        server_path = server_path.replace('\\', '/')
        for name in os.listdir(server_path):
            proj_path = '/'.join(server_path, name)
            if os.path.isdir(os.path.join(server_path, name)) and not name.startswith('.') and not name.startswith('_'):
                d = self.parsePath(filepath=proj_path, hint_type='var')
                if 'project' in d:
                    result += proj_path

        return result

    def getLibList(self, project_path):
        ''' returns tuples of library paths'''
        result = ()
        for lib, data in self.lib_templates.iteritems():
            result += (lib,)

        return result

    def getProject(self, upl):
        """
        useful for setting projects variable when launching into a file
        :param upl: any filepath within the project
        :return: the path to the root of othe project
        """
        result = self.substTemplatePath(upl=upl, template_type='var', template_var='project_root')

        return result

    #def getAsset(self, upl_dict):
    #    """
    #    given a upl_dict it will return a filepath
    #    :param upl_dict:
    #    :return:
    #    """
    #    result = ''
    #    if 'asset' in upl_dict and 'asset_type' in upl_dict:
    #        result = self.substTemplatePath(upl_dict=upl_dict, template_type='asset',
    #                                        template_name=upl_dict['asset_type'], template_var='match_path')
    #    return result
#
    #def getTask(self, upl_dict):
    #    """
    #    given a upl_dict it will return a filepath
    #    :param upl_dict:
    #    :return: filepath that matches the task
    #    """
    #    result = ''
    #    if 'asset' in upl_dict and 'asset_type' in upl_dict:
    #        result = self.substTemplatePath(upl_dict=upl_dict, template_type='task',
    #                                        template_name=upl_dict['task'], template_var='match_path')
    #    return result

    def getAssetLibList(self, upl_dict=None, upl='', asset_type=''):
        ''' returns list of asset libraries defined in the project.yml'''
        result = self.substTemplatePath(upl_dict=upl_dict, template_type='asset', template_name=asset_type,
                                        template_var='lib_path')

        return result

    def getTaskTypes(self):
        """
        :return: a list of task types defined in projects.yml
        """
        result = []
        for task_typ in self.task_templates:
            result.append(task_typ)
        return result

    def getAssetTypes(self):
        """
        :return: a list of asset types defined in project.yml
        """
        result = []
        for asset_typ in self.asset_templates:
            result.append(asset_typ)
        return result

    def getPackageTypes(self):
        """
        :return: a list of package types defined in project.yml
        """
        result = []
        for package_typ in self.package_templates:
            result.append(package_typ)
        return result

    def getDefaultTasks(self,asset_type):
        """
        :return: a list of default templates in defined asset
        """
        return self.asset_templates[asset_type]['default_tasks']
    #def getLibAsset(self, lib_name, full_path=True):
    #    ''' deprecated
    #    returns tuples of objects within library, essentially a list of sub directories of the specified path'''
    #    result = ()
    #    for lib, data in self.lib_templates.iteritems():
    #        result += (lib,)
    #
    #    return result

    def testFilePaths(self):

        filepaths = []
        filepaths.append('//scholar/projects/made_up_project')
        filepaths.append('//scholar/projects/lenovo_legion')
        filepaths.append('//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/01_cg_elements/01_models/Lenovo_IdeacenterY900TW/_versions/Lenovo_IdeacenterY900TW_v023_CK.mb')
        filepaths.append('//scholar/projects/lenovo_legion/02_design/work.AB/02_styleframes/lenovo_legion_ab_001.psd')
        filepaths.append('//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU/lighting/SH_040_CU_C000_A031_L021_MP.mb')
        filepaths.append('//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU')
        filepaths.append('//scholar/projects/draft_kings/03_production/02_composite/Playbook/Sh_010/00_nuke/Playbook_Sh_010_comp_v16.nk')
        for filepath in filepaths:
            print ("testing path parser:{0}".format(filepath))
            d = {}
            d = self.parsePath(filepath)
            print (d)
            if type(d) == type({}):
                p = self.getPath(d)
                print ("result dict to back to path:{0}".format(p))

    def testDictToPath(self, ):

        d = {
            'server': '//scholar',
            'job': 'lenovo_legion',
            'asset': 'Lenovo_IdeacenterY900TW'
        }
        test_dicts = []
        test_dicts.append(d)
        for d in test_dicts:
            print ("testing dict to path:{0}".format(d))
            self.getPath(d)
            