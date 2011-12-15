from xml.etree import ElementTree
import shutil
import traceback
import urllib
import urllib2
from json import JSONDecoder as Decoder
import os
import threading
from threading import Thread
import Queue
import sys
import hashlib
import argparse
import time
import cPickle as pickle



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

def json_parser(url,(args_booru, args_pages, args_limit, args_tags, args_rating, md5_dict, folder_path)):
    json_queue = Queue.Queue()
    for current_page in range(1, args_pages + 1):   
        request_data = urllib.urlencode({'tags':args_tags, 'limit':args_limit, 'page':current_page})
        print 'Currently parsing page: {}'.format(current_page)
        if args_booru == 'konachan':
            time.sleep(2)
        req = urllib2.Request(url, request_data)
        response = urllib2.urlopen(req)
        response_data = response.read()
        query_results = Decoder().decode(response_data)
        for result in query_results:
            ratings = {'s':1, 'q':2, 'e':3}
            rating = ratings[result['rating']]
            if rating > args_rating:
                continue
            md5 = result['md5']
            if md5 in md5_dict:
                continue
            file_url = result['file_url']
            file_extension = str(file_url)[-4:]
            file_name = md5 + file_extension
            file_tags = result['tags']
            file_path = os.path.join(folder_path, file_name)
            json_queue.put((file_url, file_path, md5))
    print ' Total images for queue: {}.'.format(json_queue.qsize())
    return json_queue
        
 
def xml_parser(url, (args_booru, args_pages, args_limit, args_tags, args_rating, md5_dict, folder_path)):
    xml_queue = Queue.Queue()
    if args_booru == 'gelbooru':
        page = 'pid'
    else:
        page = 'page'
    for current_page in range(1, args_pages + 1):   
        request_data = urllib.urlencode({'tags':args_tags, 'limit':args_limit, page:current_page})
        print 'Currently parsing page: {}'.format(current_page)
        if args_booru == 'konachan':
            time.sleep(2)
        req = urllib2.Request(url, request_data)
        ## make case to build url from scratch if it is gelbooru
        #response = urllib2.urlopen('http://gelbooru.com/index.php?page=dapi&s=post&q=index&tags={0}&limit={1}&pid={2}'.format(args_tags, args_limit, current_page))
        response = urllib2.urlopen(req)
        query_results = ElementTree.parse(response).findall('post')
        for post in query_results:
            ratings = {'s':1, 'q':2, 'e':3}
            rating = ratings[post.attrib['rating']]
            if rating > args_rating:
                continue
            md5 = post.attrib['md5']
            if md5 in md5_dict:
                continue
            file_url = post.attrib['file_url']
            file_extension = str(file_url)[-4:]
            file_name = md5 + file_extension
            file_path = os.path.join(folder_path, file_name)
            tags = post.attrib['tags'].split()
            xml_queue.put((file_url, file_path, md5))
    print 'Total images for queue: {}.'.format(xml_queue.qsize())
    return xml_queue

class Url_Download(threading.Thread):
    def __init__(self, dl_queue, md5_queue):
        self.dl_queue = dl_queue
        self.md5_queue = md5_queue
        Thread.__init__(self)
    def run(self):
        while 1:
            try:
                count = 0
                file_url, file_path, md5 = self.dl_queue.get_nowait()
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
                qsize = self.dl_queue.qsize()
                if qsize > 0:
                    print 'Count Remaining: ', qsize
            except Queue.Empty:
                raise SystemExit 
            except:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()