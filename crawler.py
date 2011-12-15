#!/usr/bin/python -tt

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
             'konachan':'http://konachan.com/post/index.json', 
             'oreno':'http://oreno.imouto.org/post/index.json', 
             'danbooru':'http://danbooru.donmai.us/post/index.json',
             'sankaku':'http://chan.sankakucomplex.com/post/index.json',
             'neko':'http://nekobooru.net/post/index.json'
              }
         
    boorus_xml = {
             'konachan':'http://konachan.com/post/index.xml', 
             'oreno':'http://oreno.imouto.org/post/index.xml', 
             'danbooru':'http://danbooru.donmai.us/post/index.xml',
             'neko':'http://nekobooru.net/post/index.xml'
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
    
    def json_parser(url):
        total_download = 0
        json_queue = Queue.Queue()
        for current_page in range(1, args.pages + 1):   
            request_data = urllib.urlencode({'tags':args.tags, 'limit':args.limit, 'page':current_page})
            print 'Currently parsing page: {}'.format(current_page)
            if args.booru == 'konachan':
                time.sleep(2)
            req = urllib2.Request(url, request_data)
            response = urllib2.urlopen(req)
            response_data = response.read()
            query_results = Decoder().decode(response_data)
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
                file_path = os.path.join(folder_path, file_name)
                file_size = result['file_size']
                json_queue.put((file_url, file_path, md5, file_size))
                total_download = total_download + file_size
        print ' Total images for queue: {0}. Total queue filesize: {1}.'.format(json_queue.qsize(), convert_bytes(total_download))
        return json_queue
            
     
    def xml_parser(url):
        total_download = 0
        xml_queue = Queue.Queue()
        for current_page in range(1, args.pages + 1):   
            request_data = urllib.urlencode({'tags':args.tags, 'limit':args.limit, 'page':current_page})
            print 'Currently parsing page: {}'.format(current_page)
            if args.booru == 'konachan':
                time.sleep(2)
            request = urllib2.Request(url, request_data)
            response = urllib2.urlopen(request)
            query_results = ElementTree.parse(response).findall('post')
            for post in query_results:
                md5 = post.attrib['md5']
                if md5 in md5_dict:
                    continue
                file_url = post.attrib['file_url']
                file_extension = str(file_url)[-4:]
                file_name = md5 + file_extension
                file_path = os.path.join(folder_path, file_name)
                tags = post.attrib['tags'].split()
                rating = post.attrib['rating']
                file_size = post.attrib['file_size']
                xml_queue.put((file_url, file_path, md5, file_size))
                print total_download
                total_download = total_download + int(file_size)
        print ' Total images for queue: {0}. Total queue filesize: {1}.'.format(xml_queue.qsize(), convert_bytes(total_download))
        return xml_queue
    queue_proceed = raw_input('Would you like proceed? Yes/No: ')    
    if os.path.exists(folder_path) == False:
            os.makedirs(folder_path
    if queue_proceed == 'no':
        print 'Exiting Crawler...'
        raise SystemExit
    if queue_proceed == 'yes':
         print 'Proceeding to download...'

    md5_dict = {}
    md5_queue = Queue.Queue()
        
    num_conn = int(max_threads)
    threads = []
    for download in range(num_conn):
        if args.partype == 'j':
            t = Url_Download(json_queue, md5_queue)
        elif args.parype == 'x':
            t = Url_Download(xml_queue, md5_queue)
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
    print 'Total data downloaded: {}'.format(convert_bytes(total_download))

if __name__ == "__main__":
    main()