#!/usr/bin/env python
__author__ = "Adam Burke"
__version__ = "0.1.0"
__maintainer__ = "Adam Burke"
__email__ = "adam@adamburke.net"

## TODO LIST ##
# make sure import version pulls in latest or other 
# watch out for RN nodes being created in two different methods, ASSETRN1 or ASSET1RN
# properties pass through as well as UVs from the shade/ file after modifying EA._attach to deform before the ref node


'''pipeline functions for exporting look data, shaders, uvs, mesh properties, textures,'''

import os, sys, math, glob, re
import yaml
import settings, utils

# import maya
import maya.cmds as cmds
import maya.OpenMayaUI as mui
from maya.OpenMaya import MVector
import maya.mel as mel
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

# import pyQt
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance

# global pointers to prevent garbage collection until unload
wind=None
widg=None
wind_lyt=None

def get_maya_main_window():
    ptr = mui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QWidget)

def to_qt_object(maya_name):
    '''
    Given the name of a Maya UI element of any type,
    return the corresponding QWidget or QAction.
    If the object does not exist, returns None
    '''
    ptr = mui.MQtUtil.findControl(maya_name)
    if ptr is None:
        ptr = mui.MQtUtil.findLayout(maya_name)
    if ptr is None:
        ptr = mui.MQtUtil.findMenuItem(maya_name)
    if ptr is not None:
        return wrapInstance(long(ptr), QWidget)

def get_maya_window(window='main', title='New PySide Window'):
	''' Get the maya main window as a QMainWindow instance'''
	ptr = None
	if window == 'main':
		ptr = mui.MQtUtil.mainWindow()
	else:
		if cmds.window(window,q=True,exists=True) == False:
			new_window = cmds.window(window,title=title)
			ptr = to_qt_object(new_window) 
		else:
			ptr = to_qt_object(window)
	if ptr != None:
		return ptr 
	else:
		print("Could not find window:"+window)


#class StudioAlembicLayout(MayaQWidgetBaseMixin,QHBoxLayout):
#	''' wrapper layout  that includes Maya Base Mixin for correct naming in MEL '''
#	def __init__(self, parent=None):
#		super(StudioAlembicLayout, self).__init__(parent)
#		self.setContentsMargins(0,0,0,0)
#		#self.setDirection(QBoxLayout.LeftToRight)

class GSLookImport(MayaQWidgetBaseMixin,QWidget):
	''' Main Browser for Look Files'''
	def __init__(self, parent=None, *args, **kwargs):
		super(GSLookImport, self).__init__(parent=parent, *args, **kwargs) 

		self.parent = parent

		iconsize = QSize(48,48)

		vertical = QVBoxLayout()
		self.setLayout(vertical)

		title = "Alembic Import / Update"

		self.setWindowTitle('Alembic Import / Update')

		self.asset_list = QTreeView()
		self.asset_list.setUniformRowHeights(True)
		self.asset_model = QStandardItemModel(self.asset_list)
		self.asset_model.setHorizontalHeaderLabels(['Assets', 'Current Cache', 'Latest Cache', 'Date'])
		vertical.addWidget(self.asset_list)

		#self.asset_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.asset_list.setModel(self.asset_model)
		self.asset_list.setColumnWidth(0,200)

		bottomLyt = QBoxLayout(QBoxLayout.LeftToRight)
		bottomLyt.addStretch(1)
		vertical.addLayout(bottomLyt)
		self.bakeButton = QPushButton('UPDATE CACHES')
		self.cancelButton = QPushButton("CANCEL")
		bottomLyt.addWidget(self.bakeButton)
		bottomLyt.addWidget(self.cancelButton)


		# Set up slots and signals.
		self.bakeButton.clicked.connect(self.doUpdateAlembic)
		self.cancelButton.clicked.connect(self.doCancel)

		self.updateUi()

	def updateUi(self):
		# populate list with assets found in scene

		
		#self.asset_model.clear()

		assets = get_assets_in_scene()
		r = 0
		for a in assets:
			item = QStandardItem(a)
			#print (assets[a]['latest_cache'])
			cur_cache = QStandardItem(assets[a]['current_cache'])
			ver = QStandardItem(assets[a]['latest_cache'])
			item.setCheckable(True)
			item.setCheckState(Qt.Checked)
			self.asset_model.appendRow(item)
			self.asset_model.setItem(r,1,cur_cache)
			self.asset_model.setItem(r,2,ver)
			if assets[a]['current_cache'] != assets[a]['latest_cache']:
				item.setForeground(QColor('red'))
				cur_cache.setForeground(QColor('red'))
				ver.setForeground(QColor('red'))
			r = r + 1
		return
	# this should get an asset list from the UI and 
	def doUpdateAlembic(self):

		print("updating alembics")

		# get the assets from the UI as text strings
		asset_list = []
		for index in xrange(self.asset_model.rowCount()):
			asset_list.append(self.asset_model.item(index))
		asset_names = [str(i.text()) for i in asset_list]

		# this is a terrible hack for the time being
		file_path = cmds.file(q=1,sn=1)
		anim_path = file_path.replace("lighting", "animation")
		updateAlembicCache(in_path = anim_path, asset_list=[], add_missing=True, ref_replace='', version='latest')

		self.updateUi()

	def doCancel(self):

		self.parent.close()
	

class GSLookBrowser(MayaQWidgetBaseMixin,QWidget):

	def __init__(self, parent=None, *args, **kwargs):
		super(GSLookBrowser, self).__init__(parent=parent, *args, **kwargs) 


		self.parent = parent
		iconsize = QSize(48,48)
		vertical = QVBoxLayout()

		title = "GS Lookbook"

		self.setLayout(vertical)
		self.setWindowTitle(title)

		self.asset_list = QTreeView()
		self.asset_list.setUniformRowHeights(True)
		self.asset_model = QStandardItemModel(self.asset_list)
		self.asset_model.setHorizontalHeaderLabels(['Assets', 'Latest Cache', 'Date'])
		vertical.addWidget(self.asset_list)

		self.asset_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.asset_list.setModel(self.asset_model)
		self.asset_list.setColumnWidth(0,200)

		rangeEditGroup = QBoxLayout(QBoxLayout.LeftToRight)
		vertical.addLayout(rangeEditGroup)
		self.rangeLbl1 = QLabel('Start:')
		rangeEditGroup.addWidget(self.rangeLbl1)
		self.rangeLE1 = QSpinBox()
		self.rangeLE1.setRange(0, 100000)
		self.rangeLE1.setValue(101)
		
		rangeEditGroup.addWidget(self.rangeLE1)
		self.rangeLbl2 = QLabel('End:')
		rangeEditGroup.addWidget(self.rangeLbl2)
		self.rangeLE2 = QSpinBox()
		self.rangeLE2.setRange(0, 100000)
		self.rangeLE2.setValue(201)
		
		rangeEditGroup.addWidget(self.rangeLE2)
		self.rangeLbl3 = QLabel('Step:')
		rangeEditGroup.addWidget(self.rangeLbl3)
		self.rangeLE3 = QSpinBox()
		self.rangeLE3.setRange(1, 100)
		self.rangeLE3.setValue(1)
		rangeEditGroup.addWidget(self.rangeLE3)

		optionsGroup = QBoxLayout(QBoxLayout.LeftToRight)
		vertical.addLayout(optionsGroup)
		self.uvCB = QCheckBox('Export UVs')
		optionsGroup.addWidget(self.uvCB)
		self.fhCB = QCheckBox('Flatten Hierarchy')
		self.fhCB.setChecked(1)
		optionsGroup.addWidget(self.fhCB)
		self.gsCB = QCheckBox('Globalspace')
		self.gsCB.setChecked(1)
		optionsGroup.addWidget(self.gsCB)

		pathEditGroup = QBoxLayout(QBoxLayout.LeftToRight)
		vertical.addLayout(pathEditGroup)
		self.pathLbl = QLabel('Output Path:')
		self.nameLE = QLineEdit(get_output_from_scene())
		pathEditGroup.addWidget(self.pathLbl)
		pathEditGroup.addWidget(self.nameLE)

		bottomLyt = QBoxLayout(QBoxLayout.LeftToRight)
		vertical.addLayout(bottomLyt)
		self.bakeButton = QPushButton("EXPORT CACHE")
		self.cancelButton = QPushButton("CANCEL")
		bottomLyt.addWidget(self.bakeButton)
		bottomLyt.addWidget(self.cancelButton)


		# Set up slots and signals.
		self.bakeButton.clicked.connect(self.exportAlembicUI)
		self.cancelButton.clicked.connect(self.doCancel)

		self.updateUi()

	def updateUi(self):

		# populate list with assets found in scene
		assets = get_assets_in_scene()
		r = 0
		for a in assets:
			item = QStandardItem(a)
			print (assets[a]['latest_cache'])
			ver = QStandardItem(assets[a]['latest_cache'])
			item.setCheckable(True)
			item.setCheckState(Qt.Checked)
			self.asset_model.appendRow(item)
			self.asset_model.setItem(r,2,ver)
			r = r + 1
		return

	def exportAlembicUI(self):
		print("exporting alembics")
		# get the assets from the UI as text strings
		asset_list = []
		for index in xrange(self.asset_model.rowCount()):
			asset_list.append(self.asset_model.item(index))
		asset_names = [str(i.text()) for i in asset_list]

		# get the export flags
		out_path = str(self.nameLE.text())
		in_frame = str(self.rangeLE1.value())
		out_frame = str(self.rangeLE2.value())
		step = str(self.rangeLE3.value())
		exportAlembicCache(out_path=out_path,asset_list=asset_names,in_frame=in_frame,out_frame=out_frame,step=step)
		self.parent.close()

	def doCancel(self):
		self.parent.close()

def get_assets_in_scene():
	asset_list = {}
	
	ref_nodes = cmds.file(q=1,r=1)
	for r in ref_nodes:

		ref_path = cmds.referenceQuery(r,f=1,wcn=1)
		# NEED TO ADD: check if the reference is within an asset library
		ref_ns = cmds.file(r,q=1,namespace=1)
		ref_cacheset = cmds.ls((ref_ns+':CACHEset'),type='objectSet')
		asset_name = ref_ns

		# search for attached cache
		found_cache = ''
		abc_nodes = cmds.ls((ref_ns)+(':*'),type='ExocortexAlembicFile',r=1,long=1)
		if len(abc_nodes)>0:
			file_path = cmds.getAttr(abc_nodes[0]+'.fileName')
			found_cache = get_shot_version(file_path,'cache','current',False,asset_name=asset_name)

		print('Asset name is '+asset_name)
		asset_list[asset_name] = {}
		asset_list[asset_name]['cache_set'] = ref_cacheset
		asset_list[asset_name]['ref_node'] = r
		asset_list[asset_name]['file_path'] = ref_path
		asset_list[asset_name]['current_cache'] = found_cache
		asset_list[asset_name]['latest_cache'] = get_shot_version(cmds.file(q=1,sn=1),'cache','latest',False,asset_name=asset_name,dept='animation')
		#except:
		#	print (a+' is not a referenced asset, skipping')

	return asset_list

def get_output_from_scene():
	''' returns the output path from the currently open scenefile'''
	scenefile = cmds.file(q=1,sn=1)
	shot_info = get_shot_info_from_path(scenefile)
	return get_alembic_output_path(shot_info)

def get_shot_info_from_path(file_path=''):
	''' returns shot information based on the file path '''
	shot_info = {}
	shot_info['valid'] = False
	if file_path == '':
		file_path = cmds.file(q=1,sn=1)

	if file_path != '':
		basename = os.path.basename(file_path)
		ext = basename.split('.')[-1]
		dir_folder = os.path.dirname(file_path)
		server_split = os.path.splitunc(file_path)
		#print ("server split="+server_split[1])
		shot_info['server'] = server_split[0].replace('/','\\')
		shot_info['job'] = server_split[1].split('/')[1]
		shot_info['shot'] = server_split[1].split('/')[7]
		shot_info['dept'] = server_split[1].split('/')[8]
		try: 
			shot_info['cam_version'] = basename.split('_')[1] 
			shot_info['anim_version'] = basename.split('_')[2]
			shot_info['light_version'] = basename.split('_')[3]
		except:
			shot_info['cam_version'] = ''
			shot_info['anim_version'] = ''
			shot_info['light_version'] = ''	
		shot_info['valid'] = True
		#except:
		#	print("Not a valid shot")
	return shot_info

def get_shot_version(file_path='', type='', which='latest',full_path=False, asset_name='', dept=''):
	''' Given a file path, determine shot info and return the latest found version
	type=cache||work||publish||master) version=A001||latest||current'''

	shot_info = get_shot_info_from_path(file_path)
	if dept != '':
		shot_info['dept'] =  dept
	ext, subd, dir_name, file_name = '', '', '', ''

	if type == 'cache':
		subd = 'cache'
		ext = 'abc'
	elif type == 'work': 
		subd = ''
		ext = 'mb'

	# gather information based on file path given
	if shot_info['valid'] == True:
		if shot_info['dept'] != '':
			search_path = os.path.join(shot_info['server'],shot_info['job'],'03_production','01_cg','01_MAYA','scenes','02_cg_scenes',shot_info['shot'],shot_info['dept'],subd)

			# determine which version info is of interest and set it to input if avail
			v_str, v_prefix, ver_placement = '', '', 1
			if shot_info['dept'] == 'camera':
				ver_placement = 2
				v_prefix = 'C'
				v_str = shot_info['cam_version'] 
			elif shot_info['dept'] == 'animation':
				ver_placement = 2
				v_prefix = 'A'
				v_str = shot_info['anim_version'] 
			elif shot_info['dept'] == 'lighting':
				ver_placement = 3
				v_prefix = 'L'
				v_str = shot_info['light_version'] 
			
			file_name = (shot_info['shot']+'_*.'+ext)

			# if its a cache we need to search within a subfolder so lets add it to the glob search <scene_name>/<scene_name>_<asset>.abc
			if type == 'cache':
				if which == 'latest':
					file_name = (shot_info['shot']+'_*')
				elif which == 'current':
					file_name = '_'.join((shot_info['shot'],shot_info['cam_version'],shot_info['anim_version'],shot_info['light_version']))
				if asset_name != '':
					file_name += ('/'+shot_info['shot']+'_*_'+asset_name+'.'+ext)

			glob_path = os.path.join(search_path,file_name)
			file_list = glob.glob(glob_path)	
			print ('Searching Glob: '+glob_path)
			print (file_list)

			# if latest found version is requested
			if which == 'latest':
				max_ver, max_file, f = 0, '', ''
				for f in file_list:
					bn = os.path.basename(f)
					v = bn.split('_')[ver_placement]
					num_only = re.search(r'[0-9]+', v).group(0)
					v_int = int(num_only)
					if v_int > max_ver:
						max_ver = v_int
						max_file = f
					v_str = (v_prefix+str(max_ver).zfill(3))

			if full_path == True:
				return f #os.path.join(search_path,max_file)
			else:
				return v_str

		else:
			print ("Could not determine Department from shot_info:")
			print shot_info
			return ''
	else:
		print ("Not a valid shot")
		return ''


def get_alembic_output_path(shot_info={}):
	''' given a shot_info (returned from a call to get_shot_info_from_path()) this will return an abc output path '''
	output_path = ''
	if len(shot_info) > 1:
		dir_name = "_".join((shot_info['shot'],shot_info['cam_version'],shot_info['anim_version'],shot_info['light_version']))
		file_name = (dir_name+'.abc')
		output_path = os.path.join(shot_info['server'],shot_info['job'],'03_production','01_cg','01_MAYA','scenes','02_cg_scenes',shot_info['shot'],shot_info['dept'],'cache',dir_name)
	return output_path


def exportAlembicCache(out_path='', asset_list=[], in_frame=101, out_frame=201, step=1):
	""" exports the alembic cache to a preconfigured location """
	job_strings = []
	print asset_list

	for a in asset_list:
		cache_set = (a+':CACHEset')
		try:
			obj_list = cmds.sets(str(cache_set),q=1)
		except:
			obj_list = ()
		obj_str= ','.join(obj_list)
		out_filename = os.path.basename(out_path)+'_'+a+'.abc'
		asset_out_path = os.path.join(out_path,out_filename)
		try: 
			os.makedirs(os.path.join(out_path))
		except OSError:
			if not os.path.isdir(os.path.join(out_path)):
				raise

		job_str = ('filename='+asset_out_path+';')
		job_str += ('objects='+obj_str+';')
		job_str += ('uvs=0;')
		job_str += ('globalspace=1;')
		job_str += ('withouthierarchy=1;')
		job_str += ('in='+in_frame+';')
		job_str += ('out='+out_frame+';')
		job_str += ('step='+step+';')
		job_str += ('ogawa=1')
		job_strings.append(job_str)
	cmds.ExocortexAlembic_export(j=job_strings)
	writeAssetDetails(out_path)


def writeAssetDetails(out_path='', asset_list=[]):
	asset_info = get_assets_in_scene()
	remove_assets = []
	# remove any asset data that isn't in the asset_list argument
	for a in asset_info:
		if any(a in s for s in asset_list):
			remove_assets.append(str(a))

	for a in remove_assets:
		del asset_info[a]

	if out_path != '':
		out_filename = os.path.basename(out_path)+'.yml'
		out_file =os.path.join(out_path,out_filename)
		with open(out_file, 'w') as f:
			f.write( yaml.safe_dump(asset_info, default_flow_style=False, encoding='utf-8', allow_unicode=False) )

# this needs to be broken down to doing a single alembic cache at a time
# the UI is what should handle doing multiple assets
# given a file path, locate the relavent shot info
# determine if there is a newer version

def updateAlembicCache(in_path='', asset_list=[], add_missing=True, ref_replace='', version='latest'):
	# locate asset details.yml
	# shot_info = 
	abc_version = get_shot_version(in_path,'cache','latest',True)
	abc_filename = os.path.basename(abc_version)
	asset_details_file = os.path.join(abc_version,(abc_filename+".yml"))
	if not os.path.isfile(asset_details_file):
		cmds.error("Cache Header File not found. Are you in a pipeline scenefile?")
	try:
		f = open(asset_details_file)
		asset_details = yaml.safe_load(f)
		f.close()
	except:
		print ('Could not locate ' + asset_details_file)
		raise
	

	# go to the master layer
	# if no assets are specified, update all assets from the details file
	if len(asset_list) < 1:
		for a in asset_details:
			asset_list.append(a)

	# for each asset in asset_list
	for a in asset_list:
		cache_file = get_shot_version(in_path,'cache','latest',True,a)
		print ('CACHE FILE='+cache_file)
		# if add_missing is true
		if asset_details[a]:
			print ('checking for '+asset_details[a]['ref_node'])
			if not cmds.objExists(asset_details[a]['ref_node']):
				# create missing references
				anim_ref_path = asset_details[a]['file_path']
				light_ref_path = os.path.join(os.path.dirname(anim_ref_path),'shade',os.path.basename(anim_ref_path))
				cmds.file(light_ref_path,r=1,loadReferenceDepth='all',namespace=a,options="v=0")
				cmds.namespace(set=a)
				job_str = ('filename='+cache_file+';')
				job_str += ('attachToExisting=1;')
				job_str += ('uvs=0;')
				job_str += ('facesets=0;')
				job_str += ('search=(Deformed)|(Orig);')
				job_str += ('replace=(?1)(?2)')
				try:
					cmds.ExocortexAlembic_import (j=job_str)
				except:
					print ("Errors while running ExocortexAlembic_import")
				cmds.namespace(set=':')
			
			# if alembic node exists
			file_node = (a+":ExocortexAlembicFile1")
			if cmds.objExists(file_node):
				file_node_path = cmds.getAttr((file_node+'.fileName'))
				expanded_path =  cmds.workspace(expandName=file_node_path)
				if not expanded_path == cache_file:
					cmds.setAttr((file_node+'.fileName'), cache_file, type='string');
					print ("Remapped "+file_node+" to "+cache_file)
				else:
					print ("Skipping "+file_node)
				# update to version
				# confirm alembic node connections to all geo
				# call alembic crate update Callback
			# else
				# call alembic crate attach function

def get_alembic_in_scene():
	abc_list = {}

	ea_file_nodes = cmds.ls(type='ExocortexAlembicFile',long=1)
	for e in ea_file_nodes:
		abc_ns = cmds.ls(e,sns=1)[-1]
		abc_list[e] = {}
		abc_list[e]['name_space'] = abc_ns
		abc_list[asset_name]['file_path'] = cmds.getAttr((e+'.fileName'))
		abc_list[asset_name]['latest_cache'] = get_shot_version(cmds.file(q=1,sn=1),'cache','latest',False,asset_name=abc_ns)

	return abc_list



def load(standalone=False):
	
	if standalone:
		wind = get_maya_main_window()
		widg = GSLookBrowser(wind)
		widg.setWindowFlags( Qt.FramelessWindowHint )
		widg.show()
	else:
		wind = get_maya_window(window='studioAlembicWindow', title='GS Lookbook V 0.1a')
		wind_lyt = QHBoxLayout()
		widg = GSLookBrowser(wind)
		wind_lyt.setContentsMargins(0,0,0,0)
		wind_lyt.addWidget(widg)
		wind.setLayout(wind_lyt)
		cmds.showWindow('studioAlembicWindow')