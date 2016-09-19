import os
import sys
import maya.cmds as cmds

def seq_to_glob(in_path):
  head = os.path.dirname(in_path)
  base = os.path.basename(in_path)
  match = list(re.finditer('\d+', base))[-1]
  new_base = '%s*%s' % (base[:match.start()], base[match.end():])
  return '%s/%s' % (head, new_base)

def _file_handler(node):
    """Returns the file referenced by the given node"""
    texture_path = cmds.getAttr('%s.fileTextureName' % (node,))
    try:
        if cmds.getAttr('%s.useFrameExtension' % (node,)) == True:
            out_path = seq_to_glob(texture_path)
        elif texture_path.find('<UDIM>') != -1:
            out_path = texture_path.replace('<UDIM>', '*')
        else:
            out_path = texture_path
        yield (out_path,)
        arnold_use_tx = False
        try:
            arnold_use_tx = cmds.getAttr('defaultArnoldRenderOptions.use_existing_tiled_textures')
        except:
            arnold_use_tx = False
        if arnold_use_tx:
            head, ext = os.path.splitext(out_path)
            tx_path = '%s.tx' % (head,)
            if os.path.exists(tx_path):
                yield (tx_path,)
    except:
        yield (texture_path,)

def _cache_file_handler(node):
    """Returns the files references by the given cacheFile node"""
    path = cmds.getAttr('%s.cachePath' % node)
    cache_name = cmds.getAttr('%s.cacheName' % node)

    yield ('%s/%s.mc' % (path, cache_name),
        '%s/%s.mcx' % (path, cache_name),
        '%s/%s.xml' % (path, cache_name),)

def _diskCache_handler(node):
    """Returns disk caches"""
    yield (cmds.getAttr('%s.cacheName' % node),)

def _vrmesh_handler(node):
    """Handles vray meshes"""
    yield (cmds.getAttr('%s.fileName' % node),)

def _mrtex_handler(node):
    """Handles mentalrayTexutre nodes"""
    yield (cmds.getAttr('%s.fileTextureName' % node),)

def _gpu_handler(node):
    """Handles gpuCache nodes"""
    yield (cmds.getAttr('%s.cacheFileName' % node),)

def _mrOptions_handler(node):
    """Handles mentalrayOptions nodes, for Final Gather"""
    mapName = cmds.getAttr('%s.finalGatherFilename' % node).strip()
    if mapName != "":
        path = cmds.workspace(q=True, rd=True)
        if path[-1] != "/":
            path += "/"
        path += "renderData/mentalray/finalgMap/"
        path += mapName
        #if not mapName.endswith(".fgmap"):
        #   path += ".fgmap"
        path += "*"
        yield (path,)

def _mrIbl_handler(node):
    """Handles mentalrayIblShape nodes"""
    yield (cmds.getAttr('%s.texture' % node),)

def _abc_handler(node):
    """Handles AlembicNode nodes"""
    yield (cmds.getAttr('%s.abc_File' % node),)

def _vrSettings_handler(node):
    """Handles VRaySettingsNode nodes, for irradiance map"""
    irmap = cmds.getAttr('%s.ifile' % node)
    if cmds.getAttr('%s.imode' % node) == 7:
        if irmap.find('.') == -1:
            irmap += '*'
        else:
            last_dot = irmap.rfind('.')
            irmap = '%s*%s' % (irmap[:last_dot], irmap[last_dot:])
    yield (irmap,
             cmds.getAttr('%s.fnm' % node),)

def _particle_handler(node):
    project_dir = cmds.workspace(q=True, rd=True)
    if project_dir[-1] == '/':
        project_dir = project_dir[:-1]
    if node.find('|') == -1:
        node_base = node
    else:
        node_base = node.split('|')[-1]
    path = None
    try:
        startup_cache = cmds.getAttr('%s.scp' % (node,)).strip()
        if startup_cache in (None, ''):
            path = None
        else:
            path = '%s/particles/%s/%s*' % (project_dir, startup_cache, node_base)
    except:
        path = None
    if path == None:
        scene_base, ext = os.path.splitext(os.path.basename(cmds.file(q=True, loc=True)))
        path = '%s/particles/%s/%s*' % (project_dir, scene_base, node_base)
    yield (path,)

def _ies_handler(node):
    """Handles VRayLightIESShape nodes, for IES lighting files"""
    yield (cmds.getAttr('%s.iesFile' % node),)

def _fur_handler(node):
    """Handles FurDescription nodes"""
    #
    #  Find all "Map" attributes and see if they have stored file paths.
    #
    for attr in cmds.listAttr(node):
        if attr.find('Map') != -1 and cmds.attributeQuery(attr, node=node, at=True) == 'typed':
            index_list = ['0', '1']
            for index in index_list:
                try:
                    map_path = cmds.getAttr('%s.%s[%s]' % (node, attr, index))
                    if map_path != None and map_path != '':
                        yield (map_path,)
                except:
                    pass

def _ptex_handler(node):
    """Handles Mental Ray ptex nodes"""
    yield(cmds.getAttr('%s.S00' % node),)

def _substance_handler(node):
    """Handles Vray Substance nodes"""
    yield(cmds.getAttr('%s.p' % node),)

def _imagePlane_handler(node):
    """Handles Image Planes"""
    # only return the path if the display mode is NOT set to "None"
    if cmds.getAttr('%s.displayMode' % (node,)) != 0:
        texture_path = cmds.getAttr('%s.imageName' % (node,))
        try:
            if cmds.getAttr('%s.useFrameExtension' % (node,)) == True:
                yield (seq_to_glob(texture_path),)
            else:
                yield (texture_path,)
        except:
            yield (texture_path,)

def _mesh_handler(node):
    """Handles Mesh nodes, in case they are using MR Proxies"""
    try:
        proxy_path = cmds.getAttr('%s.miProxyFile' % (node,))
        if proxy_path != None:
            yield (proxy_path,)
    except:
        pass

def _dynGlobals_handler(node):
    """Handles dynGlobals nodes"""
    project_dir = cmds.workspace(q=True, rd=True)
    if project_dir[-1] == '/':
        project_dir = project_dir[:-1]
    cache_dir = cmds.getAttr('%s.cd' % (node,))
    if cache_dir not in (None, ''):
        path = '%s/particles/%s/*' % (project_dir, cache_dir.strip())
        yield (path,)

def _aiStandIn_handler(node):
    """Handles aiStandIn nodes"""
    yield (cmds.getAttr('%s.dso' % (node,)),)

def _aiImage_handler(node):
    """Handles aiImage nodes"""
    yield (cmds.getAttr('%s.filename' % (node,)),)

def _aiPhotometricLight_handler(node):
    """Handles aiPhotometricLight nodes"""
    yield (cmds.getAttr('%s.aiFilename' % (node,)),)

def _exocortex_handler(node):
    """Handles Exocortex Alembic nodes"""
    yield (cmds.getAttr('%s.fileName' % (node,)),)

def get_scene_files():
    """Returns all of the files being used by the scene"""
    file_types = {'file': _file_handler,
        'cacheFile': _cache_file_handler,
        'diskCache': _diskCache_handler,
        'VRayMesh': _vrmesh_handler,
        'mentalrayTexture': _mrtex_handler,
        'gpuCache': _gpu_handler,
        'mentalrayOptions': _mrOptions_handler,
        'mentalrayIblShape': _mrIbl_handler,
        'AlembicNode': _abc_handler,
        'VRaySettingsNode': _vrSettings_handler,
        'particle': _particle_handler,
        'VRayLightIESShape': _ies_handler,
        'FurDescription': _fur_handler,
        'mib_ptex_lookup': _ptex_handler,
        'substance': _substance_handler,
        'imagePlane': _imagePlane_handler,
        'mesh': _mesh_handler,
        'dynGlobals': _dynGlobals_handler,
        'aiStandIn': _aiStandIn_handler,
        'aiImage': _aiImage_handler,
        'aiPhotometricLight': _aiPhotometricLight_handler,
        'ExocortexAlembicFile': _exocortex_handler}

    for file_type in file_types:
        handler = file_types.get(file_type)
        nodes = cmds.ls(type=file_type)
        for node in nodes:
            for files in handler(node):
                for scene_file in files:
                    if scene_file != None:
                        yield scene_file.replace('\\', '/')