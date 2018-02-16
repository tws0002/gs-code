__author__ = 'adamb'

from core_settings import *
import yaml
import re


class PathParser:
    '''Class that reads a project config and parses and stores information about the folder structure here
    Core will internally pass file-based paths between functions as a means of communicating shot information
    and then methods can use the parser to turn the path into datasets. The parser also provides methods to read the server
    for list of objects, assets, tasks, and files
    UPL - a concept is used here called a Uniform Project Locator, this is analagous to a URL (Uniform Resource Locator)
    it is a string that when parsed through a template, it tells you information about your location in the project
    '''

    def __init__(self):
        self.vars = {}
        self.templates = {}

        return

    def getConfigFile(self, filepath):
        f = open(filepath)
        # use safe_load instead load
        #dataMap = yaml.safe_load(f)
        try:
            dataMap = yaml.load(f, Loader=yaml.CLoader)
        except AttributeError:
            dataMap = yaml.load(f, Loader=yaml.Loader)
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

    def parseSubst(self,d):
        for var, val in d.iteritems():
            localvars = dict(d)
            # check if any string substitution is needed in the value
            val_subst = re.findall('%(.+?)%', str(val))
            for match in val_subst:
                if match in self.vars:
                    val = val.replace(('%' + match + '%'), self.vars[match])
                if match in localvars:
                    if type(val) is dict:
                        print ("val is a dict!! {0}  and d={1}".format(val,d))
                    val = val.replace(('%' + match + '%'), localvars[match])
                if match in os.environ:
                    val = val.replace(('%' + match + '%'), os.environ[match])
            d[var] = val

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
        self.templates = {}

        self.loadProjectConfig(self.project_data)

    def loadProjectConfigNew(self,dataMap, version='1.0'):
        # assemble the templates
        pass

    def loadProjectConfig(self, dataMap, version='1.0'):
        ''' loads job data structs, expand any known variables wrapped in \%\%, and expands inherited structs'''

        for key, value in dataMap.iteritems():
            if key == 'path_vars':
                for var, val in dataMap[key].iteritems():
                    self.vars[var] = val
                self.parseVarSubst()
                self.parseVarSubst()

        # (inheritance pass) resolve any 'inherits'
        for key, value in dataMap.iteritems():
            self.templates[key] = {}
            if key.endswith('_templates'):
                for template, data in dataMap[key].iteritems():
                    print ("adding {0} to self.templates[{1}]".format(template, key))
                    self.templates[key][template] = dict(dataMap[key][template])
                    if 'inherits' in data:
                        # make a copy
                        inherit = data['inherits']
                        if inherit in dataMap[key]:
                            self.templates[key][template] = dict(dataMap[key][inherit])
                        else:
                            print ("Could not inherit task_struct {0}, it could not be found".format(inherit))

        # (2nd pass) restore overrides to inherited structs on key,value at a time
        for key, value in dataMap.iteritems():
            if key.endswith('_templates'):
                for template, data in dataMap[key].iteritems():
                    if 'inherits' in data:
                        for var, val in data.iteritems():
                            # if struct has an inherits value
                            self.templates[key][template][var] = val

        # then expand all vars with local and project config variables (run twice to ensure all vars are substituted)
        for key, value in self.templates.iteritems():
            self.parseTaskSubst(self.templates[key])
            self.parseTaskSubst(self.templates[key])

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

    def inheritParent(self, upl_dict, d, parent_override=''):
        """ recursive template loading and substitution. this allows for template types to inherit their parents key/values
        which can then help resolve substitution vars"""
        r = {}
        if 'parent' in d:
            p_val = d['parent']
            if parent_override != '':
                p_val=parent_override
            p_tmplt = '{0}_templates'.format(p_val)
            if p_tmplt in self.templates:
                # if the upl_dict tells us which parent template to load we can recursively resolve parent
                if p_val in upl_dict:
                    # TODO 'asset' conflicts with 'asset_type', need a proper solution
                    p_val = 'asset_type' if p_val == 'asset' else p_val
                    p_val = 'scenefile_type' if p_val == 'scenefile' else p_val
                    p_dict = self.templates[p_tmplt][upl_dict[p_val]]
                    # recurse
                    r = self.inheritParent(upl_dict, p_dict)
                #else:
                #    r = self.templates[p_tmplt]

        # override the parent dict with the original dict keys
        for key in d:
            r[key] = d[key]

        # then expand all vars with local and project config variables
        self.parseSubst(r)
        return r

    def getTemplatePath(self, template_type, template_name, template_var, upl_dict={}):
        ''' returns the value of the template struct '''
        result = ''
        d = self.vars
        if template_type == 'var':
            if template_var in d:
                result = d[template_var]
        else:
            #d = self.templates['{0}_templates'.format(template_type)]

            # recurslivly solve vars that to parent templates
            d = self.templates['{0}_templates'.format(template_type)][template_name]
            inherited_template = self.inheritParent(upl_dict,d)
            result = inherited_template[template_var]

            #if template_name in d:
            #    if template_var in d[template_name]:
            #        result = d[template_name][template_var]
            #else:
            #    print "Warning: core.paths.get_template_path(): {0} not found in self.{1}_templates for var {2}".format(template_name, template_type, template_var)
            #    raise StandardError
        return result



    def substTemplatePath(self, upl_dict=None, upl='', template_type='', template_name='', template_var='', template_file='', exists=True, parent_override=''):
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

        # ORIGINAL METHOD TO JUST SIMPLY GET THE PATH
        #templ_path = self.getTemplatePath(template_type, template_name, template_var)


        # NEW METHOD to get the path by recursively solving the parent of each template type

        if template_type != 'var':
            d = self.templates['{0}_templates'.format(template_type)][template_name]
            inherited_template = self.inheritParent(upl_dict,d,parent_override=parent_override)
            templ_path = inherited_template[template_var]
        else:
            templ_path = self.getTemplatePath(template_type, template_name, template_var)
        # END NEW METHOD

        if template_file != '':
            templ_file = self.getTemplatePath(template_type, template_name, template_file)
            if templ_file != '':
                templ_path = '/'.join([templ_path, templ_file])
        # print ("template path is: {0}".format(templ_path))
        # workaround for <layer> and <pass> attributes since they can only be known at render time

        resultn = rp.subn(lambda repl: '{0}'.format(upl_dict[repl.group()[1:-1]]), templ_path)

        # make sure that the number of matched groups is equal to or greater than the keys in the upl dictionary
        # this wont always be true however in cases where the variable requested only has
        # if resultn[1] >= len(upl_dict.keys()):
        # and no other <key> template strings are left, then print match found
        if '<' in resultn[0]:
            print "gs_core.paths.substTemplatePath() Warning, path wasn't fully resolved: {0} returning partial result".format(resultn)
        result = resultn[0]

        # if result == '':
        #        print ("Warning: subst_template_path(): No Exact Match Found, Closest match is {0}".format(resultn[0]))

        print result
        return result

    def getPath(self, upl_dict=None, hint_type='', hint_name='', hint_var=''):
        """
        given a generic upl dictionary, it will match that against all available templates and return the path
        that matches. This is useful for vague calls where you aren't sure what you have
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
                subst_path = self.substTemplatePath(upl_dict=upl_dict, template_type='var', template_name='', template_var=hint_var)
                if subst_path != '':
                    m.append(subst_path)
            else:
                for var, val in self.vars.iteritems():
                    subst_path = self.substTemplatePath(upl_dict=upl_dict, template_type='var', template_var=var)
                    if subst_path != '':
                        m.append(subst_path)

        if hint_type == 'asset' or hint_type == '':
            # for each asset do a substition pass, then check for leftover templates keys
            for asset, data in self.templates['asset_templates'].iteritems():
                if 'match_path' in data:
                    tfile = 'work_file' if 'ext' in upl_dict else ''
                    subst_path = self.substTemplatePath(upl_dict=upl_dict, template_type='asset', template_name=asset, template_var='match_path', template_file=tfile)
                    if subst_path != '':
                        m.append(subst_path)

        # for each task do a substition pass, then check for leftover templates keys
        if hint_type == 'task' or hint_type == '':
            for task, data in self.templates['task_templates'].iteritems():
                if 'match_path' in data:
                    tfile = 'work_file' if 'ext' in upl_dict else ''
                    # print ("subst_template_path({0},{1},{2},{3})".format('obj_dict', 'task', 'work_path', 'work_file'))
                    subst_path = self.substTemplatePath(upl_dict=upl_dict, template_type='task', template_name=task, template_var='match_path', template_file=tfile)
                    if subst_path != '':
                        m.append(subst_path)

        # search through matches and return the shortest full match
        # print ("Possible Matches: {0}".format(m))
        if len(m):
            result_path = min(m, key=len)

        if not os.path.exists(result_path):
            print ("Warning: gs_core.paths.getPath() path does not exists {0}".format(result_path))
            result_path = ''
        return result_path

    # TODO clean up this code a bit, its a little long and can be shortened with better commenting
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

        #if exists and not os.path.isdir(filepath):
        if not os.path.isdir(filepath):
            split_path = os.path.split(filepath)

        # <file_share>/<job>/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/<shot>
        full_match = False
        partial_match = False
        task_path_match = False
        task_file_match = False
        upl_guess = {}
        type_match = ''

        if hint == 'var' or hint == '':
            type_match = 'var'
            for var, val in self.vars.iteritems():
                rgx_path = self.templateToRegex(filepath=val, limiters=['/'], exclude=['<server>'])
                rp = re.compile(rgx_path)
                # print ('checking path_vars: {0}'.format(var))
                if rp.match(split_path[0]):
                    for m in rp.finditer(split_path[0]):
                        # print ('Matched path with path_vars: {0}'.format(var))
                        # print m.groupdict()
                        result_obj = dict(m.groupdict())
                    for key, val in result_obj.iteritems():
                        upl_guess[key] = val
        if hint == 'stage' or hint == '':
            type_match = 'stage'
            for stage, data in self.templates['stage_templates'].iteritems():
                if 'match_path' in data:
                    rgx_path = self.templateToRegex(filepath=self.getTemplatePath('stage', stage, 'match_path', upl_dict=upl_guess ), limiters=['/'], exclude=['<server>'])
                    rp = re.compile(rgx_path)
                    # print ('checking path_vars: {0}'.format(var))
                    # THIS SHOULD RETURN TRUE BUT IT DOESN't
                    if rp.match(split_path[0]):
                        for m in rp.finditer(split_path[0]):
                            result_obj = dict(m.groupdict())
                            result_obj['stage']=stage
                            # store a best guess for project location to help
                        for key, val in result_obj.iteritems():
                            upl_guess[key] = val

        # look for path match in asset structs
        # TODO conisder depricating since work_path isn't in use
        if hint == 'asset' or hint == '':
            type_match = 'asset'
            for asset_type, data in self.templates['asset_templates'].iteritems():
                if 'match_path' in data:
                    rgx_path = self.templateToRegex(filepath=self.getTemplatePath( 'asset', asset_type, 'match_path', upl_dict=upl_guess), limiters=['/'], exclude=['<server>'])
                    rp = re.compile(rgx_path)
                    # print ('checking path_vars: {0}'.format(var))
                    if rp.match(split_path[0]):
                        for m in rp.finditer(split_path[0]):
                            result_obj = dict(m.groupdict())
                            result_obj['asset_type'] = asset_type
                        for key, val in result_obj.iteritems():
                            upl_guess[key] = val

        if hint == 'task' or hint == '':
            type_match = 'task'
            for task, data in self.templates['task_templates'].iteritems():
                if 'match_path' in data:
                    rgx_path = self.templateToRegex(filepath=self.getTemplatePath( 'task', task, 'match_path', upl_dict=upl_guess), limiters=['/'], exclude=['<server>'])
                    rp = re.compile(rgx_path)
                    # print ('checking path_vars: {0}'.format(var))
                    if rp.match(split_path[0]):
                        for m in rp.finditer(split_path[0]):
                            result_obj = dict(m.groupdict())
                            result_obj['task'] = task
                        for key, val in result_obj.iteritems():
                            upl_guess[key] = val

        if hint == 'package' or hint == '':
            type_match = 'package'
            for pkg, data in self.templates['package_templates'].iteritems():
                if 'match_path' in data:
                    fp = self.getTemplatePath('package', pkg, 'match_path', upl_dict=upl_guess )
                    rgx_path = self.templateToRegex(filepath=fp, limiters=['/'], exclude=['<server>'])
                    rp = re.compile(rgx_path)
                    # print ('checking path_vars: {0}'.format(var))
                    # THIS SHOULD RETURN TRUE BUT IT DOESN't
                    if rp.match(split_path[0]):
                        for m in rp.finditer(split_path[0]):
                            result_obj = dict(m.groupdict())
                            result_obj['package']=pkg
                            # store a best guess for project location to help
                        for key, val in result_obj.iteritems():
                            upl_guess[key] = val

        # look for path match in task structs
        # (?P<file_share>.*)/(?P<job>.*)/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/(?P<shot>[^/]*)/(?P<task>[^/]*)/(?P<shot2>[^/]*)_(?P<cversion>.*)_(?P<aversion>.*)_(?P<lversion>.*)_(?P<initials>.*)\.(?P<ext>.*)
        # TODO conisder depricating since work_path isn't in use
        if hint == 'scene' or hint == '':
            type_match = 'scene'
            if 'package' not in upl_guess:
                upl_guess['package'] = 'none'
            for scn, data in self.templates['scenefile_templates'].iteritems():
                #print ("checking scene_type={0}".format(scn))
                # check all 3 types of paths defined in a scene template
                scene_type_list = ['workscene','render','publish']
                for st in scene_type_list:
                    if 'workscene_path' in data:
                        # should cache converted regexs
                        tp = self.getTemplatePath('scenefile', scn, '{0}_path'.format(st), upl_dict=upl_guess)
                        rgx_path = self.templateToRegex(filepath=tp, limiters=['/'], exclude=['<server>'])
                        tfp = self.getTemplatePath( 'scenefile', scn, '{0}_file'.format(st), upl_dict=upl_guess)
                        rgx_file = self.templateToRegex(filepath=tfp, limiters=['_', '.'], exclude=['<shot>', '<asset>'])

                        # print ("task:{1} rgx_file={0}".format(rgx_file,task))
                        rp = re.compile(rgx_path)
                        rf = re.compile(rgx_file)
                        # print ('checking task_struct: {0}'.format(task))

                        # match the path first
                        # if rp.match(split_path[0]):
                        for m in rp.finditer(split_path[0]):
                            #if task_path_match == True:
                            #    break
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
                                    print ('{0} matched filename with scenefile_template: {1}'.format(split_path[1],scn))
                                    print n.groupdict()
                                    task_file_match = True
                                    result_obj['scene_type'] = scn
                                    # manually update the file name object data, if a key doesn't match though, we have to return false
                                    for key, val in n.groupdict().iteritems():
                                        if key in result_obj:
                                            # if filename keys don't match the pathname keys, then the file isn't a match
                                            if not result_obj[key] == n.groupdict()[key]:
                                                task_file_match = False
                                    if task_file_match:
                                        result_obj.update(n.groupdict())
                                    for key, val in result_obj.iteritems():
                                        upl_guess[key] = val

        # validate the data, (does the file exist?, is the file itself resolved or just the path, does the project have valid structure?)
        # print result_obj
        print ('core.paths.pathParser() type_match={0}'.format(type_match))
        return upl_guess

    # NOT USED ?
    def getProjectList(self, server_path, full_path=True):
        ''' returns tuples of server projects '''
        result = ()
        server_path = server_path.replace('\\', '/')
        for name in os.listdir(server_path):
            proj_path = '/'.join([server_path, name])
            if os.path.isdir(os.path.join(server_path, name)) and not name.startswith('.') and not name.startswith('_'):
                d = self.parsePath(filepath=proj_path, hint_type='var')
                if 'project' in d:
                    result += proj_path

        return result

    # NOT USED ?
    def getLibList(self, project_path):
        ''' returns tuples of library paths'''
        result = ()
        for lib, data in self.lib_templates.iteritems():
            result += (lib,)

        return result

    def getProject(self, upl):
        """
        gets the path to the project that matches the upl_dict given
        :param upl: any filepath within the project
        :param app:
        :return: the path to the root of othe project
        """
        result = self.substTemplatePath(upl=upl, template_type='var', template_var='project_root')
        #result = self.substTemplatePath(upl=upl, template_type='package', template_name=app, template_var='match_path')

        return result

    def getWorkspace(self, upl, package):
        """
        gets the location of the maya project / houdini project / or any other applications project workspace
        :param upl: any filepath within the project
        :param package: defines which package to search for
        :return: the path to the root of the app/package workspace
        """
        result = self.substTemplatePath(upl=upl, template_type='package', template_name=package, template_var='match_path')

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
        result = self.substTemplatePath(upl_dict=upl_dict, template_type='asset', template_name=asset_type, template_var='lib_path')
        return result

    def getTemplateTypesList(self, template):
        """
        used to get a list of available asset types, avail tasks types, avail
        package types etc. useful for filling UI comboBox dropdowns with data
        :param template: the template struct to look at in the projects.yml ({template}_templates:)
        :return: a list of types defined under the specified template
        """
        result = []
        for type in self.templates['{0}_templates'.format(template)]:
            if type.startswith('proto_') == False:
                result.append(type)
        return result

    def getPackageExtension(self, package):
        return self.templates['package_templates'][package]['extension']

    def getDefaultTasks(self,asset_type):
        """
        :return: a list of default templates in defined asset
        """
        return self.templates['asset_templates'][asset_type]['default_tasks']
