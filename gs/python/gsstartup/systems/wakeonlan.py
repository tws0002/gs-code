#!/usr/bin/env python
# wol.py

import argparse

import socket
import struct

MACS = {
        'LAXGENT001':'002500f386a1',
        'LAXGENT002':'002500f2ebeb',
        'LAXGENT003':'e80688ca3196',
        'LAXGENT004':'e80688ca3e30',
        'LAXGENT005':'002500f4f336',
        'LAXGENT006':'002500f38c77',
        'LAXGENT007':'002500f3b820',
        'LAXGENT008':'002500f3897d',
        'LAXGENT009':'002500f43fd6',
        'LAXGENT010':'70cd60aa4a33',
        'LAXGENT011':'3c07547c977e',
        'LAXGENT012':'e80688cb6b13',
        'LAXGENT013':'e80688cb4963',
        'LAXGENT014':'e80688cb434f',
        'LAXGENT015':'e80688cb621f',
        'LAXGENT016':'406c8fb81427',
        'LAXGENT017':'001f290680bd',
        'LAXGENT018':'001fbc0e12d2',
        'LAXGENT019':'001fbc0e12d6',
        'LAXGENT020':'d8d385943951',
        'LAXGENT021':'1cc1de32cc81',
        'LAXGENT022':'e83935313c5f',
        'LAXGENT023':'2c27d7efe303',
        'LAXGENT024':'78acc03d960d',
        'LAXGENT025':'002590e6ed6c',
        'LAXGENT026':'002590ea6a70',
        'LAXGENT027':'002590c419b0',
        'LAXGENT028':'002590c41886',
        'LAXGENT029':'0cc47a6c2414',
        'LAXGENT030':'002590c5c38a',
        'LAXGENT031':'0cc47a6982a6',
        'LAXGENT032':'0cc47a6c25ac',
        'LAXGENT033':'0cc47a6a2278',
        'LAXGENT034':'78acc03d56f7',
        'LAXGENT035':'0cc47ad8bfbc',
        'LAXGENT036':'0cc47ad8c04a',
        'LAXGENT037':'0cc47ad8b90e',
        'LAXGENT038':'0cc47ad9577a',
        'LAXGENT039':'0cc47ad957da',
        'LAXGENT040':'0cc47aa88da0',
        'LAXGENT041':'0cc47a6c2544'        
    }


def wake_on_lan(macaddress):
    """ Switches on remote computers using WOL. """

    # Check macaddress format and try to compensate.
    if len(macaddress) == 12:
        pass
    elif len(macaddress) == 12 + 5:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, '')
    else:
        raise ValueError('Incorrect MAC address format')
 
    # Pad the synchronization stream.
    data = ''.join(['FFFFFFFFFFFF', macaddress * 20])
    send_data = '' 

    # Split up the hex values and pack.
    for i in range(0, len(data), 2):
        send_data = ''.join([send_data,
                             struct.pack('B', int(data[i: i + 2], 16))])

    # Broadcast it to the LAN.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, ('<broadcast>', 7))


    # Parser takes computer name input (Format: LAXGENT###)

def main():
    parser = argparse.ArgumentParser(description='Wake Up on Lan by computer name.')
    parser.add_argument('names', nargs='*', help='Computer Name(s) separated by space to wake up.')
    args = parser.parse_args()

    names = args.names

    # Sends wake on lan packet to each computer name sent through parser
    for name in names:
        try:
            wake_on_lan(MACS[name])
            print 'Magic Packet sent to %s' %(name)
        except KeyError:
            print '%s is an invalid MAC address' %(name)

if __name__ == '__main__':
    main()