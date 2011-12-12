#!/usr/bin/python -tt

## script for checking how many images a given booru has for a tag


import urllib
import urllib2
from json import JSONDecoder as Decoder

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
    
booru = raw_input('What booru would you like to check?')
requested_tag = raw_input('What tag would you like to search?')
image_limit = raw_input('How many images returned per page?')
page_limit = raw_input('How many pages would you like to parse?')


boorus = {
          'konachan':'http://konachan.com/post/index.json', 
          'oreno':'http://oreno.imouto.org/post/index.json', 
          'danbooru':'http://danbooru.donmai.us/post/index.json',
          'sankaku':'http://chan.sankakucomplex.com/post/index.json',
          'neko':'http://nekobooru.net/post/index.json'
          }          
try:
    url = boorus[booru]
except KeyError:
    print 'Unknown Booru!'
total_images = 0
total_size = 0
for current_page in range(1, int(page_limit) + 1):
    request_data = urllib.urlencode({'tags':requested_tag, 'limit':image_limit, 'page':current_page})
    print 'Currently parsing page: {}'.format(current_page)
    req = urllib2.Request(url, request_data)
    response = urllib2.urlopen(req)
    response_data = response.read()
    query_results = Decoder().decode(response_data)
    for result in query_results:
        file_size = result['file_size']
        total_images += 1
        total_size = total_size + file_size

print 'Total images on selected booru {0}. Total Filesize of batch: {1}'.format(total_images, convert_bytes(total_size))