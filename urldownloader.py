import urllib
import urllib2
from PyQt4.QtCore import SIGNAL, SLOT, Qt, QThread, pyqtSignal, QString
import Queue
import sys
import traceback
from functions import *

class URLDownload(QThread):
    file_finished = pyqtSignal(QString, int, name="fileFinished")
    queue_empty = pyqtSignal(name="queueEmpty")
    logMessage = pyqtSignal(QString,name="logMessage")

    def __init__(self, dl_queue, md5_queue, is_cli=False, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.dl_queue = dl_queue
        self.md5_queue = md5_queue
        self.is_cli = is_cli
    def __del__(self):
        self.exiting = True

    def run(self):
        while not self.exiting:
            try:
                count = 0
                file_url, file_path, md5 = self.dl_queue.get_nowait()
                file_name = getFilename(file_url, md5)
                while count < 3:
                    count +=1
                    fetch_url(file_url, file_path, md5)
                    if md5 == hash_sum(file_path):
                        self.md5_queue.put_nowait((md5, file_name))
                        print 'File with md5 sum of {0} finished, {1} more images to process.'.format(md5, self.dl_queue.qsize())
                        self.logMessage.emit('File with md5 sum of {0} finished, {1} more images to process.'.format(md5, self.dl_queue.qsize()))
                        break
                if self.is_cli:       
                    if count >= 3:
                        self.logMessage.emit('File failed to download, {} might be corrupt.'.format(file_name))
                        print 'File failed to download, {} might be corrupt.'.format(file_name)                         
            except Queue.Empty:
                self.queue_empty.emit()
                self.__del__()
            except:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()