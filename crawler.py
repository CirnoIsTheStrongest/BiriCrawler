#!/usr/bin/python -tt

## 1. gelbooru API support
## 2. Custom Filename Nomenclature
## 3. cache images from directory


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
from functions import *

def main():
    
    start_time = time.time()

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
    parser.add_argument('-x', '--partype', type=str, choices=['x','j'], default='x',
                      help='desired parsing type, xml or json.')
        
    boorus_json = {
             'konachan': 'http://konachan.com/post/index.json', 
             'oreno': 'http://oreno.imouto.org/post/index.json', 
             'danbooru': 'http://danbooru.donmai.us/post/index.json',
             'sankaku': 'http://chan.sankakucomplex.com/post/index.json',
             'neko': 'http://nekobooru.net/post/index.json'
              }
         
    boorus_xml = {
             'konachan': 'http://konachan.com/post/index.xml', 
             'oreno': 'http://oreno.imouto.org/post/index.xml', 
             'danbooru': 'http://danbooru.donmai.us/post/index.xml',
             'neko': 'http://nekobooru.net/post/index.xml',
             'gelbooru': 'http://gelbooru.com/index.php',
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
        if args.partype == 'x':
            url = boorus_xml[args.booru.lower()]
        elif args.partype == 'j':
            url = boorus_json[args.booru.lower()]
    except KeyError:
        print 'No Such Booru!'
        raise SystemExit

    n_args = (args.booru, args.pages, args.limit, args.tags, args.rating, md5_dict, folder_path)

    if args.partype == 'j':
        queue = json_parser(url, n_args)
    elif args.partype == 'x':
        queue = xml_parser(url, n_args)
    
    if os.path.exists(folder_path) == False:
        os.makedirs(folder_path)
    while True:
        queue_proceed = raw_input('Would you like to proceed? Yes/No\n>> ').lower()

        if queue_proceed in ['yes', 'y']:
            print 'Proceeding to download...'
            break
        elif queue_proceed in ['no', 'n']:
            print 'Exiting script...'
            raise SystemExit
        else:
            print("Please input either 'Yes' or 'No'")
    md5_dict = {}
    md5_queue = Queue.Queue()
        
    num_conn = int(max_threads)
    threads = []
    for download in range(num_conn):
        t = Url_Download(queue, md5_queue)
        t.start()
        threads.append(t)
    for thread in threads:
        thread.join()
    
    while True:
        try:
            md5, file_name = md5_queue.get_nowait()
            md5_dict[md5] = file_name
        except Queue.Empty:
            break
    md5_pickler(md5_dict)
    time_elapsed = time.time() - start_time
    print 'All files downloaded! Total time elapsed: {0} {1}.'.format(round(time_elapsed, 3), 'seconds')
if __name__ == "__main__":
    main()