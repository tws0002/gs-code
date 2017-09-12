__author__ = 'adamb'

import sys, os
from settings import *
import yaml
import re
import utils

class StudioEnvironment():



    def __init__ (self):
        self.vars = {}
        self.workgroup_data = {}
        self.module_data = {}
        self.app_data = {}
        if 'PYTHONPATH' in os.environ:
            self.add('PYTHONPATH',os.environ['PYTHONPATH'])
        return


    def load_app_config_file(self, filepath, app=None, version=None):
        print ("Loading file path {0}".format(filepath))
        dataMap = self.get_config_file(filepath)
        self.app_data = dataMap
        #self.load_app_config(self.app_data, app, version)

    def load_module_config_file(self, filepath, module, version):
        dataMap = self.get_config_file(filepath)
        self.module_data = dataMap
        #self.load_module_config(self.module_data, module, version)

    def load_workgroup_config_file(self, filepath, workgroup=None, app=None, version=''):
        dataMap = self.get_config_file(filepath)
        self.workgroup_data = dataMap
        #self.load_workgroup_config(self.workgroup_data, workgroup, app, version)

    def append_app_config_file(self, filepath, app=None, version=None):
        dataMap = self.get_config_file(filepath)
        if type(self.app_data) == type(dict()):
            print ("Appending App Config File = {0}".format(filepath))
            self.config_merge(self.app_data,dataMap)
            #self.load_app_config(self.app_data, app, version)

    def append_workgroup_config_file(self, filepath, workgroup=None, app=None, version=''):
        dataMap = self.get_config_file(filepath)
        if type(self.workgroup_data) == type(dict()):
            print ("Appending Workgroup Config File = {0}".format(filepath))
            self.config_merge(self.workgroup_data,dataMap)
           # self.load_workgroup_config(self.workgroup_data, workgroup, app, version)

    def append_module_config_file(self, filepath, module, version):
        dataMap = self.get_config_file(filepath)
        if type(self.workgroup_data) == type(dict()):
            print ("Appending Module Config File = {0}".format(filepath))
            self.config_merge(self.module_data,dataMap)
            #self.load_module_config(self.module_data, module, version)


    def get_config_file(self,filepath):
        #print (filepath)
        f = open(filepath)
        # use safe_load instead load
        dataMap = yaml.load(f, Loader=yaml.CLoader)
        f.close()
        return dataMap

    def config_merge(self, orig_dict, new_dict):
        #print new_dict
        for key, val in new_dict.iteritems():
            if key in orig_dict:
                if type(val) == type(dict()):
                    self.config_merge(orig_dict[key],val)
                else:
                    orig_dict[key] = val
            else:
                orig_dict[key] = val

    def load_app_config(self, dataMap, app='studiotools', version='1.0'):

        if app in dataMap:
            for key, value in dataMap.iteritems():
                if key == app:
                    if 'env' in dataMap[key]:
                        for var, val in dataMap[key]['env'].iteritems():
                            self.add(var, val)
                    if 'versions' in dataMap[key]:
                        if version in dataMap[key]['versions']:
                            if 'env' in dataMap[key]['versions'][version]:
                                for var, val in dataMap[key]['versions'][version]['env'].iteritems():
                                    self.add(var, val)

        #if dataMap[]
        self.parse_subst()
        self.parse_subst()
        return

    def load_module_config(self, dataMap, module=None, package=None, version=None):
        print ("loading module: "+module+","+version)
        if module in dataMap:
            #print ("found:"+module)
            for key, value in dataMap.iteritems():
                if key == module:
                    # add module env vars
                    if 'env' in dataMap[key]:
                        for var, val in dataMap[key]['env'].iteritems():
                            #print ("loading env:"+var)
                            self.add(var, val)
                    # add module/package env vars
                    if 'packages' in dataMap[key]:
                        for app, data in dataMap[key]['packages'].iteritems():
                            if app == package or package == None:
                                if 'env' in dataMap[key]['packages'][app]:
                                    for var, val in dataMap[key]['packages'][app]['env'].iteritems():
                                        self.add(var, val)
                                if 'versions' in dataMap[key]['packages'][app]:
                                    if version in dataMap[key]['packages'][app]['versions']:
                                        if 'env' in dataMap[key]['packages'][app]['versions'][version]:
                                            for var, val in dataMap[key]['packages'][app]['versions'][version]['env'].iteritems():
                                                #print ("Loading module env: {0}={1}".format(var,val))
                                                self.add(var, val)

        #if dataMap[]
        self.parse_subst()
        self.parse_subst()

        return

    def load_workgroup_config(self, dataMap, workgroup=None, app=None, version=''):
        if workgroup in dataMap:
            for key, value in dataMap.iteritems():
                if key == workgroup:
                    # add module env vars
                    if 'env' in dataMap[key]:
                        for var, val in dataMap[key]['env'].iteritems():
                            self.add(var, val)
                    # add module/package env vars
                    if 'packages' in dataMap[key]:
                        for package, data in dataMap[key]['packages'].iteritems():
                            if app == None or package == app:
                                if 'env' in dataMap[key]['packages'][package]:
                                    for var, val in dataMap[key]['packages'][package]['env'].iteritems():
                                        self.add(var, val)
                                if 'version' in dataMap[key]['packages'][package]:
                                    if version == '':
                                        version = dataMap[key]['packages'][package]['version']
                                    # was causing double load of app data
                                    #self.load_app_config(dataMap=APPS, app=package, version=version)

                                if 'modules' in dataMap[key]['packages'][package]:
                                    for m, mv in dataMap[key]['packages'][package]['modules'].iteritems():
                                        self.load_module_config(dataMap=MODULES, module=m, package=app, version=mv)
                                        if 'env' in dataMap[key]['packages'][app]['modules']:
                                            for var, val in dataMap[key]['packages'][package]['modules']['env'].iteritems():
                                                self.add(var, val)

        #if dataMap[]
        self.parse_subst()
        self.parse_subst()


    def write_to_bat(self, output_path):
        return

    def write_to_shellscript(self, output_path):
        return

    def add(self, var, val):
        new_val = val
        is_explicit = False
        if val[:2] == '#!':
            is_explicit = True
            new_val = val[2:]

        #if adding to an existing var then add the val to the original value, else just add it 
        if var in self.vars and is_explicit == False:
            self.vars[var] += (';'+new_val)
        else:
            self.vars[var] = new_val
        #os.environ[var] = self.vars[var]

    def setEnv(self):

        for var, value in self.vars.iteritems():
            os.environ[var] = value

            # lets not add PATH variables just yet, we should pass them through to subprocess only
            #if var != 'PATH':
            #    os.environ[var] = value
            #else:
            #    os.path.append(value)

    def parse_subst(self):
        trashvars = []
        for var, val in self.vars.iteritems():
            var_subst = re.findall('%(.+?)%', var)
            for match in var_subst:
                if match in self.vars:
                    trashvars.append(var)
                    var = var.replace(('%'+match+'%'), self.vars[match])
                if match in os.environ:
                    trashvars.append(var)
                    var = var.replace(('%'+match+'%'), os.environ[match])

            # check if any string substitution is needed in the value
            val_subst = re.findall('%(.+?)%', val)
            for match in val_subst:
                if match in self.vars:
                    val = val.replace(('%'+match+'%'), self.vars[match])
                if match in os.environ:
                    val = val.replace(('%'+match+'%'), os.environ[match])
            self.vars[var] = val
            #os.environ[var] = val

            #remove old junk var names that were substituted therefore changed to a new var name
            for key in trashvars:
                print ("trashing vars {0}".format(self.vars[key]))
                del self.vars[key]
                #del os.environ[key]

    def expandvars(self,path):

        # expand any local var as well as previously declared system environment vars
        var_subst = re.search('%(.+?)%', path)
        if var_subst:
            if var_subst.group(1) in self.vars:
                path = path.replace(('%'+var_subst.group(1)+'%'), self.vars[var_subst.group(1)])
            if var_subst.group(1) in os.environ:
                path = path.replace(('%'+var_subst.group(1)+'%'), os.environ[var_subst.group(1)])
        path = os.path.expandvars(path)
        return path

    def remove(self, var):
        del self.vars[var]
        #del os.environ[var]

    def printout(self):
        print '\n== ENV VARS =='
        for key, value in self.vars.iteritems():
            print (key+'='+value)
        print '== END ENV VARS ==\n'

    def make_user_folders(self):
        # check for any paths that reference the user and create the directory before launching app
        # this is implemented to help applications store user prefs on the server
        for var, val in self.vars.iteritems():
            if '/user/' in val or '\\user\\' in val:
                if not os.path.isdir(val):
                    # hard-coded rules to grab template prefs and copy to user folder
                    copy_dir = None
                    if 'MAYA_APP_DIR' in var:
                        # need to add platform handling
                        copy_dir = os.path.expandvars('%USERPROFILE%/documents/maya')
                    if 'XSI_USERROOT' in var:
                        copy_dir = os.path.expandvars('%USERPROFILE%/Autodesk')
                    # if no local prefs exist then copy from the default network user
                    if not os.path.isdir(copy_dir):
                        user_name = ''
                        user_name = re.search('/user/(.+?)/', val)
                        copy_dir = val.replace(("/user/"+user_name+"/"), "/user/default/")
                    #if a local dir exists then copy it to the network user prefs, otherwise create an empty folder on network
                    if copy_dir:
                        print ("Copying Local Prefs from:"+copy_dir+" to "+val)
                        utils.copyDirTree(copy_dir,val)
                    else:
                        print ("No Local Prefs found in: "+copy_dir)
                        print ("Making User Folder:"+var+":"+val)
                        os.makedirs(val)
