__author__ = 'adamb'

class CoreModel():

    name = ""

    notes = ""
    date_created = ""
    date_modified = ""
    creator = ""
    user_modified = ""

    def __init__(self):
        return

class CoreProject(CoreModel):

    def __init__(self):
        return

class CoreDeliverable(CoreModel):

    format_type = "video" 
    colorspace = "rec709"
    frame_rate = 24
    render_width = 1920
    render_height = 1080
    duration = 30
    start_date = "1/1/2017"
    due_date = "4/2/2017"


    def __init__(self):
        return

# PITCH, PREVIS, PRODUCTION representation of data
class CoreStage(CoreModel):

    def __init__(self):
        return

class CoreItemGroup(CoreModel):

    members = []
    order = []
    deliverables = []

    def __init__(self):
        return

class CoreItem(CoreModel):

    item_type = ''
    parent_groups = []
    deliverables = []

    def __init__(self):
        return   

# root class of assets & shots which are both considered renderable components
class CoreRenderableItem(CoreItem):

    start_frame = 101
    end_frame = 101
    render_width = 1080
    render_height = 1920
    root_dir_path = ""
    output_path = ""
    output_type = "image"
    file_dependencies = []
    thumbnail_path = ""
    status = 'in_progress'
    tasks = []

    def __init__(self):
        return

class CoreShotGroup(CoreItemGroup):

    frame_in = 0
    frame_out = 720
    tc_in = '01:00:00:00'
    tc_out = '01:00:30:00'

    def __init__(self):
        return

class CoreShot(CoreRenderableItem):

    item_type = 'shot'
    frame_in = 0
    frame_out = 720
    tc_in = '01:00:00:00'
    tc_out = '01:00:30:00'

    def __init__(self):
        return

class CoreAssetGroup(CoreItemGroup):

    def __init__(self):
        return

class CoreAsset(CoreRenderableItem):

    item_type = 'asset'
    lod_level = 'base'

    def __init__(self):
        return

class CoreVariant(CoreRenderableItem):

    variant_type = 'look' # for assets: look, LOD, model; for shots: takes, 
    lod_level = 'base'

    def __init__(self):
        return

# model, uv, shade, rig, layout, anim, sim, light, comp
class CoreTask(CoreModel):

    dir_root = ""
    scenefile_path = ""
    def __init__(self):
        return

class CoreTask(CoreModel):

    def __init__(self):
        return