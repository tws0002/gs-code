import os
import sys
import re
import socket

properties = {
		'ip'		:	socket.gethostbyname(socket.gethostname()),
		'user'		:	os.environ.get("USERNAME"),
		'hostname'	:	socket.gethostname(),
}

if re.search('^10\.10', properties['ip']):
    properties['location'] = 'LAX'
if re.search('^10\.30', properties['ip']):
    properties['location'] = 'NYC'

def get_project_from_path(path):
    path = path.replace("\\", "/").replace(" ", "\ ").lower()
    m = re.search('^//scholar/projects/(.+?)/', path)
    try:
        project = m.group(1)
        return project
    except:
        return 0