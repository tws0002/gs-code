import os
import sys
import subprocess
import win32clipboard
import socket

remote_servers = {'lax': 'nycnas01-node01', 'nyc': 'laxevs01'}

def get_dest_path(src_loc):
    src_path = sys.argv[1]
    if os.path.isfile(src_path):
        src_path = os.path.split(src_path)[0]
    dest = str(src_path[9:])
    
    if src_path[0:9] == "\\\\scholar":
        dest_path = "\\\\%s%s" %(remote_servers[src_loc], dest)
    else:
        dest_path = src_path

    while not os.path.exists(dest_path):
        dest_path = os.path.split(dest_path)[0]

    return dest_path

def clipboard(dest_path):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(dest_path)
    win32clipboard.CloseClipboard()

def main():
    office_loc = str(socket.gethostbyname(socket.gethostname())[0:5])
    if office_loc == "10.10":
        dest_path = get_dest_path('lax')
    elif office_loc == "10.30":
        dest_path = get_dest_path('nyc')

    subprocess.Popen('explorer %s'%(dest_path))

if __name__ == '__main__':
    main()