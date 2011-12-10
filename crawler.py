#!/usr/bin/python -tt

## 1. gelbooru API support
## 2. Custom Filename Nomenclature
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

queue = Queue.Queue()
parser = argparse.ArgumentParser(description='*Booru image crawler!')

parser.add_argument('tags', type=str,
                    help='tags to download (required)')
parser.add_argument('-l', '--limit', type=int,
                    help='maximum number of images per page')
parser.add_argument('-b', '--booru', type=str, default='danbooru', 
                    help='Choose your booru. Choices are konachan, oreno,danbooru, sankaku')
parser.add_argument('-p', '--pages', type=int,
                  help='maximum number of pages to download', default=2)
parser.add_argument('-c', '--conn', type=int, default=4,
                  help='max number of threads to use, maximum of 8')

boorus = {
          'konachan':'http://konachan.com/post/index.json', 
          'oreno':'http://oreno.imouto.org/post/index.json', 
          'danbooru':'http://danbooru.donmai.us/post/index.json',
          'sankaku':'http://chan.sankakucomplex.com/post/index.json',
          'neko':'http://nekobooru.net/post/index.json'
          }
args = parser.parse_args()
if args.conn < 8:
    max_threads = args.conn
else:
    print 'Maximum of 8 threads! Defaulting to 4!'
    max_threads = 4
    
md5_path = os.path.join(os.path.dirname(__file__), 'md5.pickle')

def hash_sum(path_to_file):
    file_path = path_to_file
    file_hash_temp = hashlib.md5()
    with open(file_path, 'rb') as file_to_be_checked:
        for chunk in iter(lambda: file_to_be_checked.read(8192), ''):
            file_hash_temp.update(chunk)
        return file_hash_temp.hexdigest()
        
def fetch_url((file_url, file_path, md5)):
    r = urllib2.urlopen(urllib2.Request(file_url))
    try:
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(r,f, length=8192)
    finally: 
        r.close()
        
def md5_pickler(md5_info):
    with open('md5.pickle', 'wb') as f:
        pickle.dump(md5_info, f)
        
def md5_unpickler(md5sum_file):
    with open(md5sum_file, 'rb') as f:
       return pickle.load(f)

try:
    md5_dict = md5_unpickler(md5_path)
except IOError:
    md5_dict = {}
    
    
    
folder_path = raw_input('Save File To:')
if len(folder_path) == 0:
    folder_path = os.path.join(os.environ['USERPROFILE'], 'Downloads' , args.tags)
try:
    url = boorus[args.booru.lower()]
except KeyError:
    print 'No Such Booru!'
    
## encodes data in url readable format, builds manual request
## opens page, reads response and decodes JSON
for current_page in range(1, args.pages):
    request_data = urllib.urlencode({'tags':args.tags, 'limit':args.limit, 'page':current_page})
    print 'Currently parsing page: {}'.format(current_page)
    if args.booru == 'konachan':
        time.sleep(2)
    req = urllib2.Request(url, request_data)
    response = urllib2.urlopen(req)
    response_data = response.read()
    query_results = Decoder().decode(response_data)
    folder_path = os.path.normpath(folder_path)
    folder_path = os.path.abspath(folder_path)
    for result in query_results:
        md5 = result['md5']
        if md5 in md5_dict:
            continue
        file_url = result['file_url']
        file_extension = str(file_url)[-4:]
        file_name = md5 + file_extension
        file_tags = result['tags']
        folder = str(folder_path)
        file_path = os.path.join(folder_path, file_name)
        queue.put((file_url, file_path, md5))
        
print 'Total images for queue: ', queue.qsize()
if os.path.exists(folder_path) == False:
    os.makedirs(folder_path)
    
class url_download(threading.Thread):
    def __init__(self, queue):
        self.queue = queue
        Thread.__init__(self)
    def run(self):
        while 1:
            try:
                count = 0
                file_url, file_path, md5 = self.queue.get_nowait()
                fetch_url((file_url, file_path, md5))
                file_extension = str(file_url)[-4:]
                file_name = md5 + file_extension
                if md5 == hash_sum(file_path):
                   md5_dict[md5] = file_name
                else:
                    count +=1
                if count > 3:
                    print 'File failed to download, might be corrupt.'
                    break                
                qsize = self.queue.qsize()
                if qsize > 0:
                    print 'Count Remaining: ', qsize
            except Queue.Empty:
                raise SystemExit 
            except:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                
num_conn = int(max_threads)
threads = []
for download in range(num_conn):
    t = url_download(queue)
    t.start()
    threads.append(t)
    
for thread in threads:
    thread.join()
    
md5_pickler(md5_dict)
print 'All files downloaded!'