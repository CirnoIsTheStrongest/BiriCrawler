#!/usr/bin/python -tt

## script for checking how many images a given booru has for a tag


import urllib
import urllib2
from json import JSONDecoder as Decoder

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
for current_page in range(1, int(page_limit)):
    request_data = urllib.urlencode({'tags':requested_tag, 'limit':image_limit, 'page':current_page})
    print 'Currently parsing page: {}'.format(current_page)
    req = urllib2.Request(url, request_data)
    response = urllib2.urlopen(req)
    response_data = response.read()
    query_results = Decoder().decode(response_data)
    for result in query_results:
        total_images += 1

print 'Total images on selected booru {}'.format(total_images)