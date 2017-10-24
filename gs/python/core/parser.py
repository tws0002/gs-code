__author__ = 'adamb'

import sys, os
from settings import *
import yaml
import re

class CoreParser():
    '''Class that reads a project config and parses and stores information about the folder structure here'''

    def __init__ (self):
        self.vars = {}
        self.template_structs = {}
        self.task_structs = {}
        self.project_data = {}
        return

    def get_config_file(self,filepath):
        f = open(filepath)
        # use safe_load instead load
        dataMap = yaml.safe_load(f)
        f.close()
        return dataMap

    def load_project_config_file(self, filepath, version=None):
        print ("Loading Project file path {0}".format(filepath))
        dataMap = self.get_config_file(filepath)
        self.project_data = dataMap
        self.load_project_config(self.project_data)



    def load_project_config(self, dataMap, version='1.0'):
        ''' loads job data structs, expand any known variables wrapped in \%\%, and expands inherited structs'''

        for key, value in dataMap.iteritems():
            if key == 'path_vars':
                for var, val in dataMap[key].iteritems():
                    self.vars[var] = val
                self.parse_var_subst()
                self.parse_var_subst()

        # load template structs for possible reuse, although currently inherit calls are directly copied from the dataMap['template_structs']
        for key, value in dataMap.iteritems():
            if key == 'template_structs':
                for template, data in dataMap[key].iteritems():
                    self.template_structs[template] = dict(dataMap['template_structs'][template])        

        # first load all the dictionaries obeying calls for inheritance
        for key, value in dataMap.iteritems():
            if key == 'task_structs':
                for task, data in dataMap[key].iteritems():
                    self.task_structs[task] = dict(dataMap['task_structs'][task])
                    if 'inherits' in data:
                        # make a copy
                        val = data['inherits']
                        if val in dataMap['template_structs']:
                            self.task_structs[task] = dict(dataMap['template_structs'][val])
                        else:
                            print ("Could not inherit task_struct {0}, it could not be found".format(val))
        # then add overrides to inherited structs
        for key, value in dataMap.iteritems():
            if key == 'task_structs':
                for task, data in dataMap[key].iteritems():
                    if 'inherits' in data:
                        for var, val in data.iteritems():
                            # if struct has an inherits value
                            self.task_structs[task][var] = val   
        # then expand all vars with local and project config variables (run twice to ensure all vars are substituted)
        self.parse_task_subst()
        self.parse_task_subst()
        return

    def template_to_regex(self, filepath, limiters, exclude):
        ''' converts a template path into a regex with named capture groups
            special exceptions are made for groups that should capture mutliple directories or underscores'''
        lstr = ''
        for l in limiters:
            if l == '.':
                l = '\\.'
            lstr += l

        result = filepath.replace('<', '(?P<')
        result = result.replace('>', '>[^{0}]*)'.format(lstr))
        for e in exclude:
            result = result.replace('{0}[^{1}]*'.format(e,lstr), '{0}.*'.format(e))
        return str(result)

    def get_path(self, object_dict):
        ''' given a valid object (like the dict returned by parse_path), it returns a valid file path that represents that object'''
        # build a regex string of all the keys in dict
        # eg: "(<job>|<asset>|<share>)"
        re_match_str = "(<{0}>)".format('>|<'.join(object_dict.keys()))
        match_count = len(object_dict.keys())
        rp = re.compile(re_match_str)
        result_path = ""
        m = []

        for var, val in self.vars.iteritems():
            # swap all instances. make sure to remove the <> chars from the expression before calling the dict key
            resultn = rp.subn(lambda repl: '{0}'.format(object_dict[repl.group()[1:-1]]), self.vars[var])
            # if every key dict was matched
            if resultn[1] >= match_count:
                # and no other <key> template strings are left, then print match found
                if '<' not in resultn[0]:
                    m.append(resultn[0])
                #print "fucking path man:{0}".format(resultn[0]) 

        # for each task do a substition pass, then check for leftover templates keys
        for task, data in self.task_structs.iteritems():
            if 'work_path' in data:
                # swap all instances. make sure to remove the <> chars from the expression before calling the dict key
                # if it contains an extention key it is a file, so include the file_name template
                full_path = data['work_path']
                if 'ext' in object_dict:
                    full_path = '/'.join([data['work_path'],data['work_file']])
                resultn = rp.subn(lambda repl: '{0}'.format(object_dict[repl.group()[1:-1]]), full_path)
                # if every key dict was matched
                if resultn[1] >= match_count:
                    # and no other <key> template strings are left, then print match found
                    if '<' not in resultn[0]:
                        m.append(resultn[0])
                    #print "fucking path man:{0}".format(resultn[0])    

        if len(m):
            result_path = m[0]
            for i in range(len(m)):
                if len(m[i]) < len(result_path) or len(result_path) == 0:
                    result_path = m[i]

        return result_path

    def parse_path(self,filepath):
        ''' returns an object containing details about the file path based on the pathname given. Very similar to a url parser'''
        #filepath = '//scholar/projects/lenovo_legion/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/SH_040_CU/animation/SH_040_CU_C000_A014_L000_AB.mb'
        result_obj = {}
        # match against root variables
        # if the path fully matches the task root and task, but is longer, do further tests on other variables within the root
        if not os.path.exists(filepath):
            print ("Filepath: {0} does not exist, nice try".format(filepath))
            return
        split_path = os.path.split(filepath)
        if os.path.isdir(filepath):
            split_path = (filepath,"")
            

        # <file_share>/<job>/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/<shot>
        full_match = False
        partial_match = False
        task_path_match = False
        task_file_match = False

        for var, val in self.vars.iteritems():
            rgx_path = self.template_to_regex(filepath=val, limiters=['/'], exclude=['<server>'])
            rp = re.compile(rgx_path)
            #print ('checking path_vars: {0}'.format(var))
            if rp.match(split_path[0]):
                for m in rp.finditer(split_path[0]):
                    #print ('Matched path with path_vars: {0}'.format(var))
                    #print m.groupdict()
                    result_obj = dict(m.groupdict())


        #(?P<file_share>.*)/(?P<job>.*)/03_production/01_cg/01_MAYA/scenes/02_cg_scenes/(?P<shot>[^/]*)/(?P<task>[^/]*)/(?P<shot2>[^/]*)_(?P<cversion>.*)_(?P<aversion>.*)_(?P<lversion>.*)_(?P<initials>.*)\.(?P<ext>.*)
        for task, data in self.task_structs.iteritems():

            if 'work_path' in data:
                # should cache converted regexs
                rgx_path = self.template_to_regex(filepath=data['work_path'], limiters=['/'], exclude=['<server>'])
                rgx_file = self.template_to_regex(filepath=data['work_file'], limiters=['_','.'], exclude=['<shot>','<asset>'])

                #print ("task:{1} rgx_file={0}".format(rgx_file,task))

                rp = re.compile(rgx_path)
                rf = re.compile(rgx_file)
                #print ('checking task_struct: {0}'.format(task))

                # match the path first
                #if rp.match(split_path[0]):
                for m in rp.finditer(split_path[0]):
                    if task_path_match == True:
                        break
                    #print ('Matched path with task_struct: {0}'.format(task))
                    #print m.groupdict()
                    result_obj.update(m.groupdict())
                    task_path_match = True
                    if split_path[1] != "":
                        #if rf.match(split_path[1]):
                        # TODO: if its not a complete match with the regex, does it at least match a portion of the regex fully? (partial path)
                        # also need to handle searching other task paths other than work_path
                        for n in rf.finditer(split_path[1]):
                            if task_file_match == True:
                                break
                            #print ('{0} matched filename with task_struct: {1}'.format(split_path[1],task))
                            #print n.groupdict() 
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
        #print result_obj
        return result_obj

    def parse_var_subst(self):
        for var, val in self.vars.iteritems():
            # check if any string substitution is needed in the value
            val_subst = re.findall('<(.+?)>', val)
            for match in val_subst:
                if match in self.vars:
                    val = val.replace(('<'+match+'>'), self.vars[match])
                if match in os.environ:
                    val = val.replace(('%'+match+'%'), os.environ[match])
            self.vars[var] = val


    def parse_task_subst(self):
        ''' for each task_struct, expand any %% vars with project vars, task local vars, or environment vars'''
        for task, data in self.task_structs.iteritems():
            # load up the local vars
            localvars = dict(self.task_structs[task])
            for var, val in data.iteritems():
                # check if any string substitution is needed in the value
                val_subst = re.findall('%(.+?)%', str(val))
                for match in val_subst:
                    if match in self.vars:
                        val = val.replace(('%'+match+'%'), self.vars[match])
                    if match in localvars:
                        val = val.replace(('%'+match+'%'), localvars[match])
                    if match in os.environ:
                        val = val.replace(('%'+match+'%'), os.environ[match])
                self.task_structs[task][var] = val


    def test_file_paths(self):

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
            d = self.parse_path(filepath)
            print (d)
            if type(d) == type({}):
                p = self.get_path(d)
                print ("result dict to back to path:{0}".format(p))

    def test_dict_to_path(self,):

        d = {
            'server': '//scholar',
            'job': 'lenovo_legion',
            'asset': 'Lenovo_IdeacenterY900TW'
        }
        test_dicts = []
        test_dicts.append(d)
        for d in test_dicts:
            print ("testing dict to path:{0}".format(d))
            self.get_path(d)

