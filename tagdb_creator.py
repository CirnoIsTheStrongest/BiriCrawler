#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
## run tagdb_creator on first run
## add ability to rebuild tagdb from settings


import cPickle as pickle
import urllib
import urllib2
import os
from xml.etree import ElementTree
import json


url = 'http://danbooru.donmai.us/tag/index.xml'

def pickler(tag_list, encoding='utf8'):
    with open('tagdb.pickle', 'wb') as f:
        pickle.dump(tag_list, f)

def tag_db_builder(url, encoding='utf8'):
    page = 'page'
    data = {
        'order':'name',
        'limit':0,
        'login':'BiriBiriRG',
        'password_hash':'58eaf30d591d86f6ea62f4a62a5b332e77af8732'
        }
    tag_list = []
    request_data = urllib.urlencode(data)
    req = urllib2.Request('?'.join([url, request_data]))
    response = urllib2.urlopen(req)
    query_results = ElementTree.parse(response).findall('tag')
    for tags in query_results:
        tags = tags.attrib['name'].split()
        for tag in tags:
            tag_list.append(tag)
    print len(tag_list)
    return tag_list
try:
    tag_list = tag_db_builder(url)
except urllib2.HTTPError, err:
    print err
    tag_list = tag_db_builder(url)

with open('tags.json', 'wb') as f:
    json.dump(tag_list, f, encoding='utf-8', separators=(',',':'))