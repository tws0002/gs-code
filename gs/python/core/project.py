__author__ = 'adamb'

import os,sys
from glob import glob
from settings import *

import urllib2
from subprocess import Popen, PIPE, STDOUT



# this serves as the brain of the project system. You can ask it about a file
# and it will be able to know what it is 

# it can read the global studio config and initialize a setup or it can read a custom config on a 
# per project level, or any custom config to alter or override it

# the brain



def list_servers():
	for share in STUDIO['servers']:
		print (share+": "+STUDIO['servers'][share]['root_path'])

def list_jobs(share):
	try:
		path = STUDIO['servers'][share]['root_path']
		valid_proj = []
		for name in os.listdir(path):
			if os.path.isdir(os.path.join(path,name)) and not name.startswith('.') and not name.startswith('_'):
				valid_proj.append(name)
		return valid_proj
	except:
		print (share+" is not a valid share name as per config")

def list_shots(share,job):
	result = []
	try:
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
		path = os.path.join(path,job,'03_production','01_cg','01_MAYA','scenes','01_cg_elements','01_models')
		
		for name in os.listdir(path):
			if os.path.isdir(os.path.join(path,name)) and not name.startswith('.') and not name.startswith('_'):
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





list_servers()


