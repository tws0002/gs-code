import pika
import re
import sys
import socket

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

if re.search('^10\.10', ip) or re.search('^lax', hostname):
    local = 'lax'
    remote = 'nyc'
elif re.search('^10\.30', ip) or re.search('^nyc', hostname):
    local = 'nyc'
    remote = 'lax'

def submit(src = '', queue_loc = ''):
    credentials = pika.PlainCredentials('render', 'render')
    connection = pika.BlockingConnection(pika.ConnectionParameters('%srabbit.studio.gentscholar.com' %(queue_loc), 5672, '/', credentials))
    channel = connection.channel()

    channel.queue_declare(queue='aspera', durable=True)
    channel.basic_publish(exchange='',
                          routing_key='aspera',
                          body=src)
    connection.close()

def main():
    src = sys.argv[1].replace('\\','/')
    depth = src.replace('//','/').count('/')
    if depth <= 3:
        print 'Error: Minimum folder depth is 3 levels. Must select deeper file. %s' %(src)
        raw_input('Press Enter to continue...')
        sys.exit()
    if re.search('^//scholar', src.lower()):
        submit(src, local)
    elif re.search('^//laxevs01', src.lower()) or re.search('^//laxnas02', src.lower()):
        src_scholar = src.replace('laxevs01', 'scholar').replace('laxnas02', 'scholar')
        submit(src=src_scholar, queue_loc='lax')
    elif re.search('^//nycnas01\-node01', src.lower()) or re.search('^//nycevs01', src.lower()):
        src_scholar = src.replace('nycnas01-node01', 'scholar').replace('nycevs01', 'scholar')
        submit(src=src_scholar, queue_loc='nyc')
    else:
        print 'Error: File(s) must live on the server. Cannot submit %s for Aspera transfer.' %(src)
        raw_input('Press Enter to continue...')

if __name__ == '__main__':
    main()