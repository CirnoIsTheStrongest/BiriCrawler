import os
import threading
from threading import Thread
import Queue
import sys
import hashlib
import shutil
import traceback
import urllib2
import time
import cPickle as pickle
import urllib



def hash_sum(path_to_file):
    file_path = path_to_file
    file_hash_temp = hashlib.md5()
    with open(file_path, 'rb') as file_to_be_checked:
        for chunk in iter(lambda: file_to_be_checked.read(8192), ''):
            file_hash_temp.update(chunk)
        return file_hash_temp.hexdigest()
        
def fetch_url(file_url, file_path, md5):
    r = urllib2.urlopen(urllib2.Request(file_url))
    try:
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(r,f, length=8192)
    finally: 
        r.close()

def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fTB' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fGB' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fMB' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fKB' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size        
        
def md5_pickler(md5_info):
    with open('md5.pickle', 'wb') as f:
        pickle.dump(md5_info, f)
        
def md5_unpickler(md5sum_file):
    with open(md5sum_file, 'rb') as f:
       return pickle.load(f)

class Url_Download(threading.Thread):
    def __init__(self, dl_queue, md5_queue):
        self.dl_queue = dl_queue
        self.md5_queue = md5_queue
        Thread.__init__(self)
    def run(self):
        while 1:
            try:
                count = 0
                file_url, file_path, md5, file_size = self.queue.get_nowait()
                file_extension = str(file_url)[-4:]
                file_name = md5 + file_extension
                while count < 3:
                    count +=1
                    fetch_url(file_url, file_path, md5)
                    if md5 == hash_sum(file_path):
                       #md5_dict[md5] = file_name
                       self.md5_queue.put_nowait((md5, file_name))
                       break
                       
                if count > 3:
                    print 'File failed to download, {} might be corrupt.'.format(file_name)       
                qsize = self.queue.qsize()
                if qsize > 0:
                    print 'Count Remaining: ', qsize
            except Queue.Empty:
                raise SystemExit 
            except:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()