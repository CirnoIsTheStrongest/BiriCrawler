# -*- coding: utf-8 -*-


from xml.etree import ElementTree
import shutil
import urllib
import urllib2
from json import JSONDecoder as Decoder
import os
from PyQt4.QtCore import SIGNAL, SLOT, Qt, QThread, pyqtSignal, QString
from math import ceil
import Queue
import sys
import hashlib
import argparse
import time
import cPickle as pickle
import argparse
import re
import json


def hash_pass(booru, passwd):
    choujin_list = ['danbooru', 'oreno', 'nekobooru' ]
    if booru in choujin_list:
        pass_hash = hashlib.sha1('choujin-steiner--{}--'.format(passwd))
    elif booru == 'konachan':
        pass_hash = hashlib.sha1('So-I-Heard-You-Like-Mupkids-?--{}--'.format(passwd))
    elif booru == '3dbooru':
        pass_hash = hashlib.sha1('meganekko-heaven--{}--'.format(passwd))
    return pass_hash.hexdigest()

def arg_parser():
    parser = argparse.ArgumentParser(description='*Booru image crawler!')
        
    parser.add_argument('-t', '--tags', type=str,
                        help='tags to download')
    parser.add_argument('-l', '--limit', type=int, default=20,
                        help='maximum number of images per page')
    parser.add_argument('-b', '--booru', type=str,
                        help='Choose your booru. Choices are konachan, oreno,danbooru, sankaku')
    parser.add_argument('-c', '--conn', type=int, default=4,
                        help='max number of threads to use, maximum of 8')
    parser.add_argument('-r', '--rating', type=int, choices=[1,2,3], default=3,
                        help='desired rating for images. optional.')
    parser.add_argument('-x', '--partype', type=str, choices=['xml','json'], default='xml',
                        help='desired parsing type, xml or json.')
    parser.add_argument('-f', '--save_path', type=str, default='',
                        help='desired path to save files.')
    parser.add_argument('-z', '--hash', action='store_true', default=False,
                        help='Would you like to cache files from savepath?')
    return parser

def getFilename(file_url, md5):
    split = file_url.split(".")
    ext = split[-1]
    file_name = '.'.join((md5, ext))
    return file_name

def total_images(limit, booru, tags):
    if limit == 0:
        count = post_counter(booru, tags, limit)
        pages = int(ceil(int(count)/1000.0))
        image_limit = 1000
    elif limit in range(1,1000):
        image_limit = limit
        pages = 1
    elif limit > 1000:
        image_limit = 1000
        pages = int(ceil(limit/1000.0))
    return image_limit, pages

def hash_sum(path_to_file):
    file_path = path_to_file
    file_hash_temp = hashlib.md5()
    with open(file_path, 'rb') as file_to_be_checked:
        for chunk in iter(lambda: file_to_be_checked.read(8192), ''):
            file_hash_temp.update(chunk)
        return file_hash_temp.hexdigest()
        
def fetch_url(file_url, file_path, md5):
    request = urllib2.Request(file_url)
    r = urllib2.urlopen(request)
    try:
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(r,f, length=8192)
    finally: 
        r.close()

def md5_pickler(md5_info):
    with open('md5.CirnoDB', 'wb') as f:
        pickle.dump(md5_info, f)
        
def md5_unpickler(md5sum_file):
    with open(md5sum_file, 'rb') as f:
        return pickle.load(f)

def tagdb_loader():
    with open('tags.json', 'rb') as f:
        return json.load(f, encoding='utf-8')

## builds queue of md5, file save path, file url for
## use only with sankaku complex

def json_parser(url, n_args):
    url_queue = Queue.Queue()
    limit, pages = total_images(n_args['limit'], n_args['booru'], n_args['tags'])
    for current_page in range(1, pages +1):
        # if n_args['booru'] == 'danbooru'
        request_data = urllib.urlencode({
                            'tags': n_args['tags'],
                            'limit': limit,
                            'page': current_page,
                            # 'login':n_args['login'],
                            # 'password_hash':n_args['password_hash'],
                            })
        print 'Currently parsing page: {}'.format(current_page)
        if n_args['booru'] == 'konachan':
            time.sleep(2)
        print url + request_data
        req = urllib2.Request(url, request_data)
        response = urllib2.urlopen(req)
        response_data = response.read()
        if response_data == '[]':
            print 'No more images to parse, {} images for queue.'.format(json_queue.qsize())
            break
        query_results = Decoder().decode(response_data)
        for result in query_results:
            ratings = {'s': 1, 'q': 2, 'e': 3}
            rating = ratings[result['rating']]
            if rating > n_args['rating']:
                continue
            md5 = result['md5']
            if md5 in n_args['md5_dict']:
                continue
            file_url = result['file_url']
            file_name = getFilename(file_url, md5)
            file_tags = result['tags']
            file_path = os.path.join(n_args['folder_path'], file_name)
            url_queue.put((file_url, file_path, md5))
    return url_queue
        
 
## gelbooru, aka gheybooru requires a different
## method of building/passing the request
## also only available xml format
## does not support file_size or jpeg_file_size

## this function builds a queue of urls, md5s and save paths
## using the xml api. n_args is a dict of parameters to be used in
## the function. As of 1/14/12 login and password_hash are required
## fields for danbooru.
def xml_parser(url, (n_args)):
    url_queue = Queue.Queue()
    limit, pages = total_images(n_args['limit'], n_args['booru'], n_args['tags'])
    if n_args['booru'] == 'gelbooru':
        page = 'pid'
        data = {
            'page': 'dapi',
            's': 'post',
            'q': 'index',
            'tags': n_args['tags'],
            'limit': n_args['limit'],
            'pid': 1
        }
    elif n_args['booru'] == 'danbooru':
        page = 'page'
        data = {
            'tags':n_args['tags'],
            'limit':n_args['limit'],
            'page':1,
            'login':n_args['login'],
            'password_hash':n_args['password_hash'],
        }
           
    else:
        page = 'page'
        data = {
            'tags': n_args['tags'],
            'limit': n_args['limit'],
            'page': 1
        }
    for current_page in range(1, data['page'] + 1):   
        data[page] = current_page
        request_data = urllib.urlencode(data)
        if n_args['booru'] == 'konachan':
            time.sleep(2)
        req = urllib2.Request('?'.join([url, request_data]))
        response = urllib2.urlopen(req)
        query_results = ElementTree.parse(response).findall('post')
        if query_results == []:
            print 'No more images to parse, {} images for queue.'.format(xml_queue.qsize())
            break
        ratings = {'s': 1, 'q': 2, 'e': 3}
        for post in query_results:
            rating = ratings[post.attrib['rating']]
            if rating > n_args['rating']:
                continue
            md5 = post.attrib['md5']
            if md5 in n_args['md5_dict']:
                continue
            file_url = post.attrib['file_url']
            file_name = getFilename(file_url, md5)
            file_path = os.path.join(n_args['folder_path'], file_name)
            tags = post.attrib['tags'].split()
            url_queue.put((file_url, file_path, md5))
    return url_queue

def get_xml_booru():
    boorus_xml = {
        'konachan': 'http://konachan.com/post/index.xml', 
        'oreno': 'http://oreno.imouto.org/post/index.xml', 
        'danbooru': 'http://danbooru.donmai.us/post/index.xml',
        'nekobooru': 'http://nekobooru.net/post/index.xml',
        'gelbooru': 'http://gelbooru.com/index.php',
        '3dbooru': 'http://behoimi.org/post/index.xml',
            }
    return boorus_xml


def post_counter(booru, tags, limit):
    boorus = get_xml_booru()
    boorus['sankaku'] = 'http://chan.sankakucomplex.com/post/index.xml'
    try:
        url = boorus[booru.lower()]
    except KeyError:
        print 'Booru doesn\'t exist!'
    if url == 'http://gelbooru.com/index.php':
        page = 'pid'
        data = {
            'page': 'dapi',
            's': 'post',
            'q': 'index',
            'tags':tags,
            'limit': 1,
            'pid': 1,
        }
    elif boorus['danbooru']:
        page = 'page'
        data = {
            'tags':tags, 
            'limit':1, 
            'page': 1,
            'login':'BiriBiriRG',
            'password_hash':'58eaf30d591d86f6ea62f4a62a5b332e77af8732',
        }        
    else:
        page = 'page'
        data = {
            'tags':self.tags, 
            'limit':1, 
            'page': 1,
        }

    request_data = urllib.urlencode(data)
    req = urllib2.Request('?'.join([url, request_data]))
    response = urllib2.urlopen(req)
    post_count = ElementTree.parse(response).getroot()
    return post_count.attrib['count']