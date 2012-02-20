#!/usr/bin/python -tt
# -*- coding: utf-8 -*-


## 1. add ability to zip files after completion
## 2. Custom Filename Nomenclature
## 3. add a pause button
## 5. add username/password page under settings that saves to .xml file, save user/pass per booru. checkbox for using it or not.
## 6. switch from pickle to sqlite
## 7. add default to path field, update when tag field changes
## 8. take login as argument from both GUI and CLI on first run
##    then check for hashed password from settings.xml
## 9. move page/limit decision to parsers
## 10. merge parsers

from json import JSONDecoder as Decoder
import os
import Queue
from PyQt4.QtCore import SIGNAL, SLOT, Qt, QThread
import sys
import time
from time import strftime as current_time
from functions import *
from urldownloader import URLDownload as URLDownloader
from xml.etree import ElementTree
import hashlib

class Crawler(QThread):
    parsing_done = pyqtSignal(name="parsingDone")
    logMessage = pyqtSignal(QString,name="logMessage")

    def __init__(self, tags, limit='20', booru='danbooru', savepath='', rating=3, num_of_threads=4,bool_cache_files=False, parent=None):
        QThread.__init__(self, parent)

        ## ensures a tag was passed
        if tags == None or len(tags) == 0:
            if bool_cache_files == True:
                pass
            else:
                print 'No tag specified, please try again!'
                raise SystemExit


        self.tags = tags
        self.limit = limit
        self.booru = booru
        if self.booru != 'sankaku':
            self.parser = 'xml'
        else:
            self.parser = 'json'
        self.rating = rating
        self.hash = bool_cache_files
        options_xml = ElementTree.parse('settings.xml').findall('option')
        if self.booru == None:
            self.booru = options_xml[5].get('default_booru')
        if self.booru != 'gelbooru':
            self.login = options_xml[0].get('login')
            self.passwd = options_xml[1].get('unhashed_pass')
            self.password_hash = hash_pass(self.booru, self.passwd)
            self.logMessage.emit('Logging in as user: {}.'.format(self.login))
            
        # Decides default save path based on os platform
        if savepath == None or len(savepath) == 0:
            if sys.platform.startswith("linux"):
                self.savepath = os.path.join(os.environ['HOME'], self.tags)
            elif sys.platform.startswith("win32"):
                self.savepath = os.path.join(os.environ['USERPROFILE'], 'Downloads' , self.tags)
        else:
            self.savepath = savepath
        if os.path.exists(self.savepath) == False:
            os.makedirs(self.savepath)
        # Use only the minimum amount of threads required by the image limit
        # and the maximum of 8 threads.
        self.num_of_threads = min(min(num_of_threads, 8), limit)
        self.md5_dict = {}
        self.md5_queue = Queue.Queue()
        self.threads = []

    def hash_pickle(self):
        while True:
            try:
                md5, file_name = self.md5_queue.get_nowait()
                self.md5_dict[md5] = file_name
            except Queue.Empty:
                md5_pickler(self.md5_dict)
                return



    def get_json_booru(self):
        boorus_json = {
            'konachan': 'http://konachan.com/post/index.json', 
            'oreno': 'http://oreno.imouto.org/post/index.json', 
            'danbooru': 'http://danbooru.donmai.us/post/index.json',
            'sankaku': 'http://chan.sankakucomplex.com/post/index.json',
            'nekobooru': 'http://nekobooru.net/post/index.json',
            '3dbooru':'http://behoimi.org/post/index.json',
                }
        return boorus_json

    def get_xml_booru(self):
        boorus_xml = {
            'konachan': 'http://konachan.com/post/index.xml', 
            'oreno': 'http://oreno.imouto.org/post/index.xml', 
            'danbooru': 'http://danbooru.donmai.us/post/index.xml',
            'nekobooru': 'http://nekobooru.net/post/index.xml',
            'gelbooru': 'http://gelbooru.com/index.php',
            '3dbooru': 'http://behoimi.org/post/index.xml',
                }
        return boorus_xml

    def cache_files(self):
        # function for caching files from a local directory
        # so that local files aren't re-downloaded
        folder_path = self.savepath
        accepted_file_types = ['.jpg', '.png', '.gif']
        hash_directory = os.walk(folder_path, topdown=True)
        if folder_path != None:
            for root, subfolders, images in hash_directory:
                for filename in images:
                    try:
                        if filename[-4:] in accepted_file_types:
                            local_hash = hash_sum(os.path.join(root, filename))
                            self.logMessage.emit('File with name {0} hashed with an md5 of {1}.'.format(filename, local_hash))
                            self.md5_queue.put_nowait((local_hash, filename))
                    except IOError:
                        continue
        print 'Directory has finished caching, exiting...'
        return self.md5_queue


    def run(self):
        # references pickle file if available
        md5_path = os.path.join(os.path.dirname(__file__), 'md5.CirnoDB')

        try:
            self.md5_dict = md5_unpickler(md5_path)
        except IOError:
            pass
        if self.hash == True:
            self.cache_files()
            self.logMessage.emit("Caching of files is complete!")
            self.hash_pickle()
            self.logMessage.emit("Md5 cache has been saved to md5.CirnoDB!")
        else:
            self.build_queue()

    def build_queue(self):
        n_args = {
            'booru':self.booru, 
            'tags':self.tags,
            'limit':self.limit,
            'rating':self.rating, 
            'md5_dict':self.md5_dict, 
            'folder_path':self.savepath,
        }

        if self.booru != 'gelbooru':
            n_args['login'] = self.login
            n_args['password_hash'] = self.password_hash


        if self.parser == 'xml':
            self.boorus_xml = self.get_xml_booru()
            self.dl_url = self.boorus_xml[self.booru.lower()]
            self.dl_queue = xml_parser(self.dl_url, n_args)
        elif self.parser == 'json':
            self.boorus_json = self.get_json_booru()
            self.dl_url = self.boorus_json[self.booru.lower()]
            self.dl_queue = json_parser(self.dl_url, n_args)
        else:
            self.logMessage.emit('Oh dear, the pigs have begun to fly!')
            raise SystemExit
        self.logMessage.emit('A total of {} images to download!'.format(self.dl_queue.qsize()))
        self.parsing_done.emit()

    def init_threads(self, is_cli=False):   
        for download in range(self.num_of_threads):
            t = URLDownloader(self.dl_queue, self.md5_queue, is_cli)
            self.threads.append(t)
        return self.threads

    def start_threads(self):
        for t in self.threads:
            t.start()

    def cli_start(self):
        self.init_threads(is_cli = True)
        self.start_threads()
        for thread in self.threads:
            thread.wait()

#### parsing of arg.parse arguments if crawler.py is called on its own   
if __name__ == "__main__":
    import argparse

    parser = arg_parser()
    args = parser.parse_args()

    # hard limit for connections to prevent abuse
    if args.conn < 8:
        max_threads = args.conn
    else:
        print 'Maximum of 8 threads! Defaulting to 4!'
        max_threads = 4

    cli_tags = args.tags
    cli_limit = args.limit
    cli_save_path = args.save_path
    cli_booru = args.booru
    cli_rating = args.rating
    max_threads = args.conn
    bool_cache_files = args.hash
    crawler = Crawler(cli_tags, cli_limit, cli_booru, cli_save_path, cli_rating, max_threads, bool_cache_files)
    crawler.start()
    crawler.wait()
    if not bool_cache_files:
        crawler.cli_start()
        crawler.hash_pickle()