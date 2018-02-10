__author__ = 'adamb'

import sys, urllib2, subprocess, argparse, time, ctypes

from settings import *
from utils import *
# from ui import *
from environment import *

#PYQTPATH = os.path.join(ROOT,'lib','python','pyqt4','4.10.3')

def build_render_cmd(args):
    p = argparse.ArgumentParser(description='Render command handler')
    p.add_argument('-startframe')
    p.add_argument('-endframe')
    p.add_argument('-step')
    p.add_argument('-project')
    p.add_argument('-filename')
    p.add_argument('-x')
    p.add_argument('-y')
    r = p.parse_args(args[0].split())

    flags = {}
    flags['-s']     = '%s' %(r.startframe)
    flags['-e']     = '%s' %(r.endframe)
    flags['-b']     = '%s' %(r.step)
    if r.x: flags['-x'] = '%s' %(r.x)
    if r.y: flags['-y'] = '%s' %(r.y)
    if r.project: flags['-proj'] = '"%s"' %(r.project)

    commands = []
    for k,v in flags.items():
        commands += [k,v]
    commands.append(r.filename)

    return commands

def init():
    if args.app or args.file:
        project = ''
        filepath = ''
        # hard coded workgroup 'default'
        workgroup = 'default'
        version = ''
        initials = ''
        mode = 'ui'
        wrkgrp_config = ''
        add_args = ''

        if args.configfile:
            wrkgrp_config = args.configfile

        if args.job:
            project = args.job

        if args.file:
            filepath = args.file

        if args.MAJV:
            version = args.MAJV
            #if args.MINV:
            #    version += ('.'+args.MINV)

        if args.cli:
            add_args = ' '.join(pass_args)
            mode = 'cli'

        if args.args:
            add_args = args.args

        if args.render:
            mode = 'render'
            print pass_args
            add_args = ' '.join(pass_args)
            #add_args = build_render_cmd(args.renderargs)

        launch_app(args.app, version=version, mode=mode, wrkgrp_config=wrkgrp_config, workgroup=workgroup, initials=initials, project=project, filepath=filepath, add_args=add_args)

def get_project_config(project='',config_type='workgroups'):

    proj_config = os.path.join(STUDIO['servers']['jobs']['root_path'],project,"03_production",".pipeline","config","{0}.yml".format(config_type))
    #print ("Checking for project config: {0}".format(proj_config))
    found_config = ''
    if os.path.isfile(proj_config):
        found_config = proj_config
        #print ("GS Launcher: loading local project {1} config:{0}").format(found_config,config_type)
    return found_config 

def launch_app(app, version='', mode='ui', wrkgrp_config='', workgroup='default', initials='', project='', workspace='', filepath='', add_args=''):

    app_config = CONFIG+'/app.yml'
    wrkgrp_config = CONFIG+'/workgroups.yml'
    shell_mode = False

    # get a current working directory
    cwd = r'//{0}/{1}/{2}'.format(SERVER,SHARES['projects'],project)
    print ("Current Working Directory {0}".format(cwd))
    print 'Launching {0} version: {1}'.format(app,version)


    os.environ['GSINITIALS'] = initials
    os.environ['GSWORKGROUP'] = workgroup
    os.environ['GSPROJECT'] = project
    os.environ['GSWORKSPACE'] = workspace
    os.environ['SCRATCHDISK'] = utils.getScratchDrive()
    utils.createTempDir()

    # load the process env from the config files
    process_env = StudioEnvironment()

    # load studiotools env vars
    process_env.load_app_config_file(filepath=app_config, app='studiotools', version=version)
    process_env.load_app_config(process_env.app_data, 'studiotools', version)

    # load app from filepath if its not already specified
    if filepath != '':
        print "Filepath specified:{0}".format(filepath)
        if app == '' or app is None:
            extension = filepath.split('.')[-1]
            app = process_env.get_app_from_ext(extension)
            print ("App Guess: {0}".format(app))

    # if filepath is specified and project is not,
    if filepath != '':
        # get the project for the given path by calling core.pathsParser
        import gs_core
        controller = gs_core.CoreController()
        filepath_unix = filepath.replace('\\','/')
        if workspace == '':
            project = controller.proj_controller.pathParser.getProject(filepath_unix)
            workspace = controller.proj_controller.pathParser.getWorkspace(filepath_unix, app)
        if project == '':
            project = controller.proj_controller.pathParser.getProject(filepath_unix)

    print ("GSWORKSPACE={0}".format(workspace))
    os.environ['GSWORKSPACE'] = workspace
    print ("GSPROJECT={0}".format(project))
    os.environ['GSPROJECT'] = project
    # load the modules in the specified workgroup config, this is hardcoded for now but will be adjustable in future UI
    # its also important to note that we load env vars in a cascading order of apps, modules, workgroups
    # workgroups vars should be able to override any other vars
    process_env.load_app_config_file(filepath=app_config, app=app, version=version)
    process_env.load_workgroup_config_file(filepath=wrkgrp_config, workgroup=workgroup, app=app, version=version)

    w_data = dict(process_env.workgroup_data)

    if version == '':
        version = w_data[workgroup]['packages'][app]['version']

    # append any project local config files
    proj_wrkgrp = get_project_config(project,'workgroups')
    if os.path.isfile(proj_wrkgrp):
        process_env.append_workgroup_config_file(filepath=proj_wrkgrp, workgroup=workgroup, app=app, version=version)

    proj_app = get_project_config(project,'app')
    if os.path.isfile(proj_app):
        process_env.append_app_config_file(filepath=proj_app, app=app, version=version)

    process_env.load_workgroup_config(process_env.workgroup_data, workgroup, app, version, mode)
    process_env.load_app_config(process_env.app_data, app, version, mode)

    process_env.append_current_env()

    # validate data from config
    # TODO work this into the studio environment funcs validate_config(key, value)
    w_data = process_env.workgroup_data
    a_data = process_env.app_data

    os.environ['GS_MODULES'] = ''
    if 'modules' in w_data[workgroup]['packages'][app]:
        for m in w_data[workgroup]['packages'][app]['modules']:
            if os.environ['GS_MODULES'] == '':
                os.environ['GS_MODULES'] = str(m)
            else:
                os.environ['GS_MODULES'] += ';{0}'.format(str(m))

    if workgroup not in w_data:
        print ('Workgroup: {0} not found in current workgroup config: {1}'.format(workgroup,wrkgrp_config))
        return

    if app not in w_data[workgroup]['packages']:
        print ('Package: {0} not found in current workgroup config: {1}'.format(app,wrkgrp_config))
        return

    if version == '':
        version = w_data[workgroup]['packages'][app]['version']

    if version not in a_data[app]['versions']:
        print ('Version: {0} not found in package {1} in current workgroup config: {2}'.format(version,app,wrkgrp_config))
        return

    if mode not in a_data[app]['versions'][version]['modes']:
        print ('Mode: {0} not found in package {1} in current workgroup config: {2}'.format(mode,app,wrkgrp_config))
        return

    executable = os.path.join(a_data[app]['versions'][version]['path'][sys.platform], a_data[app]['versions'][version]['modes'][mode][sys.platform])
    
    # expand any env variables in pathnames before running the process
    executable = process_env.expandvars(executable)
    
    # create any necessary user variable folders if they don't exist
    # process_env.make_user_folders()

    #print executable
    #if not os.path.isfile(executable.split(' ')[0]):
    #    print ("Could Not Run: {0}. Is it installed?").format(executable.split(' ')[0])
    #    return

    # load the launcher environment
    STUDIO_ENV = StudioEnvironment()
    STUDIO_ENV.load_app_config_file(CONFIG + '/app.yml', app='studiotools', version='1.0')
    STUDIO_ENV.setEnv()

    # this should be replaced with a routine to merge key values instead of overwriting
    # env = dict(os.environ.items() + STUDIO_ENV.vars.items() + process_env.vars.items())
    env = dict(process_env.vars.items())

    # need to clear out pyqt from path and pythonpath
    # these need to be handled on an app by app basis
    # env['PATH'] = os.environ['PATH']

    # env['PATH'] = ';'.join([';'.join(sys.path),os.environ['PATH'],env['PATH']])
    #print ("Trying to remove: {0}".format(PYQTPATH))
    remove_paths = ['{0};'.format(PYQTPATH),'{0}\PyQt4;'.format(PYQTPATH)]
    for ea in remove_paths:
        env['PATH'] = env['PATH'].replace(ea, '')
        env['PYTHONPATH'] = env['PYTHONPATH'].replace(ea, '')

    if 'GSBRANCH' in os.environ:
        if os.environ['GSBRANCH'].split('/')[-1] != 'base':
            print "\n== ENV VARS =="
            for var, val in sorted(env.iteritems()):
                print "{0}={1}".format(var,env[var])
            print "== END ENV VARS ==\n"
            #process_env.printout()


    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESTDHANDLES
    cmd = executable + ' ' + add_args
    if project != '':
        flag = process_env.get_flag(app=app, flag='project')
        if flag != '':
            cmd += ' {0} "{1}"'.format(flag,os.environ['GSWORKSPACE'].replace('\\','/'))
    if filepath != '':
        flag = process_env.get_flag(app=app, flag='file')
        if flag != '':
            cmd += ' {0} "{1}"'.format(flag,filepath.replace('\\','/'))
        else:
            cmd += "{0}".format(filepath.replace('\\','/'))

    # check if shell mode is enabled
    if 'shell' in a_data[app]:
        #print ("shell mode detected {0}".format(a_data[app]['shell'] ))
        if a_data[app]['shell'] == True:
            shell_mode = True

    if mode == 'render':
        print cmd

        # supress error window on crash
        SEM_NOGPFAULTERRORBOX = 0x0002 # From MSDN
        ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX);
        sf = 0x8000000

        try:
            p = subprocess.Popen(cmd,bufsize=1, stdout=subprocess.PIPE, env=env, startupinfo=si, creationflags=sf)
        except WindowsError:
            print "\n\nError: GS Launcher Process: {0} failed to execute. \n\nDoes program exist?".format(cmd)
            sys.exit(-1)
        while True:
            output = p.stdout.readline()
            if output == '' and p.poll() is not None:
                break
            if output:
                print output.strip()
        rc = p.poll()
        if p.returncode != None:
            print ("GS Launcher: Render Process Ended with exit code {0}".format(p.returncode))
        else:
            print ("GS Launcher: Render Process Ended. No exit code reported.")

    elif mode == 'cli':
        executable = win_shell_safe(executable)
        cmd = 'start '+ executable + ' ' + add_args
        print cmd
        p = subprocess.Popen(cmd, env=env, startupinfo=si, shell=True)

    else:
        if shell_mode:
            executable = win_shell_safe(executable)
            cmd = 'start '+ executable + ' ' + add_args
            if filepath != '':
                flag = process_env.get_flag(app=app, flag='file')
                cmd += ' {0} "{1}"'.format(flag, filepath.replace('\\', '/'))
        print cmd
        p = subprocess.Popen(cmd, env=env, startupinfo=si, shell=shell_mode)

    if p.returncode != None and p.returncode != 0:
        sys.exit(p.returncode)

    return

if __name__ == '__main__':
    # this thing sucks in 2.7 since it forces an automatic abbreviation system, -proj and -p can't be unique
    # only using double dash arguments since i can avoid 
    parser = argparse.ArgumentParser(description='GS Launcher.')
    #parser.add_argument('file', nargs='?', help='File to open.')
    parser.add_argument('-ui', dest='ui', action='store_true', help='launch into UI mode')
    parser.add_argument('--add', dest='args', help='Additional arguments to pass to the executable.')
    parser.add_argument('--package', dest='app', help='Launch Specific Package')
    parser.add_argument('--render', dest='render', action='store_true', help='Specify to use render executable.')
    parser.add_argument('--major', dest='MAJV', help='Specify the major version to run.')
    parser.add_argument('--minor', dest='MINV', help='Specify the minor version to run.')
    parser.add_argument('--file', dest='file', help='Specify file to open on launch, if no package/job flag specified it will guess')
    parser.add_argument('--job', dest='job', help='Specify Target Job ')
    parser.add_argument('--prompt', dest='cli', action='store_true', help='Specify to use command line input')
    parser.add_argument('--config', dest='configfile', help='Specify alternate pipeline config to load')
    parser.add_argument('--wrkgrp', dest='workgroup', help='Specify workgroup to load within config, defaults to "default"')

    #args = parser.parse_args()
    parsed_args = parser.parse_known_args()
    args = parsed_args[0]
    pass_args = parsed_args[1]


    if not args.app and not args.file:
        elapsed_time = time.time() - START_TIME
        print("Launcher settings loaded in {0} sec".format(elapsed_time))
        import gui
        app = gui.LauncherApp(sys.argv)
        wind = gui.LauncherWindow()
        elapsed_time = time.time() - START_TIME
        print("Launcher GUI loaded in {0} sec".format(elapsed_time))
        wind.setWindowTitle('Gentleman Scholar Launcher')
        wind.show()
        elapsed_time = time.time() - START_TIME
        print("Launcher GUI Shown in {0} sec".format(elapsed_time))
        app.exec_()

    else:
        init()


