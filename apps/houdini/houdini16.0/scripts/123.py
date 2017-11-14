# executed when houdini is start with an empty scene

def create_camera():
    cam = hou.node("/obj").createNode("cam", "renderCam")
    cam.setParms({"resx": 1920, "resy": 1080})
    cam.setDisplayFlag(False)
# Create Mantra - PBR driver
def mantra_driver():
    rop = hou.node("/out").createNode("ifd")
    rop.setParms({"vm_renderengine": "pbrraytrace", "override_camerares": True, "camera": "/obj/renderCam"}) 
def main():
    create_camera()
    mantra_driver()

if __name__ == '__main__':
  main()