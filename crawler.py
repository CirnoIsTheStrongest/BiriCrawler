#!/usr/bin/python -tt

## 1. gelbooru API support
## 2. Custom Filename Nomenclature
## 3. add load queue state from image_counter.py
## 4. jpeg_url
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
from functions import *
       
def main():
    
    start_time = time.time()

    queue = Queue.Queue()
    parser = argparse.ArgumentParser(description='*Booru image crawler!')
    
    parser.add_argument('tags', type=str,
                        help='tags to download (required)')
    parser.add_argument('-l', '--limit', type=int, default=20,
                        help='maximum number of images per page')
    parser.add_argument('-b', '--booru', type=str, default='danbooru', 
                        help='Choose your booru. Choices are konachan, oreno,danbooru, sankaku')
    parser.add_argument('-p', '--pages', type=int, default=1,
                      help='maximum number of pages to download')
    parser.add_argument('-c', '--conn', type=int, default=4,
                      help='max number of threads to use, maximum of 8')
    parser.add_argument('-r', '--rating', type=int, choices=[1,2,3], default=3,
                      help='desired rating for images. optional.')
    
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
    
    
    try:
        md5_dict = md5_unpickler(md5_path)
    except IOError:
        md5_dict = {}
        
    data_downloaded = 0   
    folder_path = raw_input('Save File To:')
    
    if len(folder_path) == 0:
        if sys.platform.startswith("linux"):
            folder_path = os.path.join(os.environ['HOME'], args.tags)
        elif sys.platform.startswith("win32"):
            folder_path = os.path.join(os.environ['USERPROFILE'], 'Downloads' , args.tags)
    try:
        url = boorus[args.booru.lower()]
    except KeyError:
        print 'No Such Booru!'
        raise SystemExit
        
    ## encodes data in url readable format, builds manual request
    ## opens page, reads response and decodes JSON
    total_download = 0
    for current_page in range(1, args.pages + 1):
        request_data = urllib.urlencode({'tags':args.tags, 'limit':args.limit, 'page':current_page})
        print 'Currently parsing        page: {}'.format(current_page)
        if args.booru == 'konachan':
            time.sleep(2)
        req = urllib2.Request(url, request_data)
        response = urllib2.urlopen(req)
        response_data = response.read()
        query_results = Decoder().decode(response_data)
        folder_path = os.path.normpath(folder_path)
        folder_path = os.path.abspath(folder_path)
        for result in query_results:
            ratings = {'s':1, 'q':2, 'e':3}
            rating = ratings[result['rating']]
            if rating > args.rating:
                continue
            md5 = result['md5']
            if md5 in md5_dict:
                continue
            file_url = result['file_url']
            file_extension = str(file_url)[-4:]
            file_name = md5 + file_extension
            file_tags = result['tags']
            folder = str(folder_path)
            file_path = os.path.join(folder_path, file_name)
            file_size = result['file_size']
            queue.put((file_url, file_path, md5, file_size))
            total_download = total_download + file_size
    print 'Total images for queue: ', queue.qsize()
    if os.path.exists(folder_path) == False:
        os.makedirs(folder_path)
    
    md5_dict = {}
    
    num_conn = int(max_threads)
    threads = []
    for download in range(num_conn):
        t = Url_Download(queue)
        t.start()
        threads.append(t)
        
    for thread in threads:
        thread.join()
    md5_pickler(md5_dict)
    time_elapsed = time.time() - start_time
    print 'All files downloaded! Total time elapsed: {0} {1}.'.format(round(time_elapsed, 3), 'seconds')
    print 'Total data downloaded: {}'.format(convert_bytes(total_download))

if __name__ == "__main__":
    main()