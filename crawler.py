#!/usr/bin/python -tt

## Simple *booru crawler
## Usage: path\to\script
## Search parameters are in the form Parameter name = Parameter value
## Separate search parameters with ;
## Save File To is the location you want to save to
## Location must be an existing absolute path ending in \
## Feature Wishlist:
## 1. argument parsing
## 2. Hash Caching to DB
## 3. Custom Filename Nomenclature
## 4. choose between boorus (danbooru, konachan, oreno)
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

url = 'http://oreno.imouto.org/post/index.json'
queue = Queue.Queue()
input_parameters = {}
############ text input ####################################
##    parameters = raw_input('Search Parameters:')
folder_path = raw_input('Save File To:')
if len(folder_path) == 0:
    folder_path = os.environ['USERPROFILE'] + '\\Downloads\\cirno\\'
parameters = 'tags = cirno ; limit = 10'
# folder_path = str('C:\Users\Cirno\Downloads\Danbooru Images')
## splits the parameters, strips whitespace, assigns dict
splits = parameters.split(";")
for split in splits:
    subsplits = split.split('=')
    key = subsplits[0].strip()
    value = subsplits[1].strip()
    input_parameters[key]= value
input_parameters['limit'] = int(input_parameters['limit'])

print input_parameters
## encodes data in url readable format, builds manual request
## opens page, reads response and decodes JSON
request_data = urllib.urlencode(input_parameters)
req = urllib2.Request(url, request_data)
response = urllib2.urlopen(req)
response_data = response.read()
query_results = Decoder().decode(response_data)

## Normalizes folder path structure and converts it to absolute path if it is not
folder_path = os.path.normpath(folder_path)
folder_path = os.path.abspath(folder_path)
## checks if path exists, if not, creates it
if os.path.exists(folder_path) == False:
    os.makedirs(folder_path)
## takes results and sets a variable to values I want to use later

def hash_sum(path_to_file):
    file_path = path_to_file
    file_hash_temp = hashlib.md5()
    with open(file_path, 'rb') as file_to_be_checked:
        for chunk in iter(lambda: file_to_be_checked.read(8192), ''):
            file_hash_temp.update(chunk)
        return file_hash_temp.hexdigest()

for result in query_results:
    md5 = result['md5']
    file_url = result['file_url']
    file_tags = result['tags']
    folder = str(folder_path)
    file_extension = str(file_url)[-4:]
    file_name = md5 + file_extension
    file_path = os.path.join(folder_path, file_name)
    if os.path.exists(file_path) and md5 == hash_sum(file_path):
        continue
    else:
        queue.put((file_url, file_path, md5))
print 'Total images for queue: ', queue.qsize()

## function for retrieving data from server
def fetch_url((file_url, file_path, md5)):
    r = urllib2.urlopen(urllib2.Request(file_url))
    try:
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(r,f, length=8192)
    finally: 
        r.close()
        
## class for passing queue to thread
class url_download(threading.Thread):
    def __init__(self, queue):
        self.queue = queue
        Thread.__init__(self)
    def run(self):
        while 1:
            try:
                fetch_url(self.queue.get_nowait())
                qsize = self.queue.qsize()
                if qsize > 0:
                    print 'Count Remaining: ', qsize
            except Queue.Empty:
                raise SystemExit 
            except:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()


num_conn = 4
threads = []
for download in range(num_conn):
    t = url_download(queue)
    t.start()
    threads.append(t)
    
for thread in threads:
    thread.join()

print 'All files downloaded!'
