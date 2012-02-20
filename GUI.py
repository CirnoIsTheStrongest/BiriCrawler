#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, SLOT, Qt
from crawler import Crawler
from urldownloader import URLDownload as URLDownloader
import designerGUI
import Queue
from functions import post_counter, md5_unpickler, tagdb_loader
import os
from time import strftime as current_time

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.gui = designerGUI.Ui_crawler()
        self.gui.setupUi(self)
        self.tag_list = tagdb_loader()
        completer = QCompleter(self.tag_list, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.gui.tagLineEdit.setCompleter(completer)
        self.gui.tagLineEdit.setFocus()
        self.gui.crawlBtn.setDisabled(True)
        self.gui.postcountBtn.setDisabled(True)
        self.build_combobox()
        self.connect(self.gui.booruComboBox, SIGNAL("currentIndexChanged(int)"), self.EnableBtns)
        self.connect(self.gui.crawlBtn, SIGNAL("clicked()"), self.onCrawlClicked)
        self.connect(self.gui.cancelBtn, SIGNAL("clicked()"), self.onCancelClicked)
        self.connect(self.gui.browseBtn, SIGNAL("clicked()"), self.onBrowseClicked)
        self.connect(self.gui.postcountBtn, SIGNAL("clicked()"), self.onPostCountClicked)
        self.connect(self.gui.cachepathFileDialog, SIGNAL("clicked()"), self.onCacheDialogClicked)
        self.connect(self.gui.cacheBtn, SIGNAL("clicked()"), self.onCacheClicked)
        self.connect(self.gui.settingscancelBtn, SIGNAL("clicked()"), self.onCancelClicked)


    def EnableBtns(self, index):
        if index <= 0:
            self.gui.postcountBtn.setDisabled(True)
            self.gui.crawlBtn.setDisabled(True)
        else:
            self.gui.postcountBtn.setDisabled(False)
            self.gui.crawlBtn.setDisabled(False)

    def build_combobox(self):
        combo_box_list = ['Select Booru...', 'danbooru', 'konachan', 'oreno', 'nekobooru', 'sankaku', 'gelbooru']
        for item in combo_box_list:
            self.gui.booruComboBox.addItem(item)

    def onCacheDialogClicked(self):
        path = QFileDialog.getExistingDirectory(self,'Choose directory you would like to cache', '');
        self.gui.cachepathLineEdit.setText(path)

    def onCacheClicked(self):
        savepath = str(self.gui.cachepathLineEdit.text())
        self.crawler = Crawler(savepath, bool_cache_files=True)
        self.connect(self.crawler, SIGNAL("logMessage(QString)"), self.onLogMessage, Qt.QueuedConnection)
        self.crawler.start()
    def onPostCountClicked(self):
        gui_tags = unicode(self.gui.tagLineEdit.text())
        gui_image_limit = 1
        gui_page = 1
        gui_booru = unicode(self.gui.booruComboBox.currentText())
        post_count = post_counter(gui_booru, gui_tags, gui_image_limit)
        self.gui.postcountLineEdit.setText('Total {0} tagged images on {1}: {2}'.format(gui_tags, gui_booru, post_count))
        return post_count

    def onCrawlClicked(self):
        gui_tags = unicode(self.gui.tagLineEdit.text())
        if not self.validateTags(gui_tags):
            self.onInvalidTags()
            return
        else:
            self.gui.crawlBtn.setDisabled(True)
            gui_image_limit = int(self.gui.imageLimitBox.value())
            gui_savepath = unicode(self.gui.savepathLineEdit.text())
            gui_booru = unicode(self.gui.booruComboBox.currentText())
            max_threads = int(self.gui.threadSpinBox.value())
            if self.gui.safeRadio.isChecked():
                gui_rating=1
            elif self.gui.questionableRadio.isChecked():
                gui_rating=2
            elif self.gui.explicitRadio.isChecked():
                gui_rating=3
            self.crawler = Crawler(gui_tags, gui_image_limit, gui_booru, gui_savepath, gui_rating, max_threads)
            self.connect(self.crawler, SIGNAL("parsingDone()"), self.onParsingDone, Qt.QueuedConnection)
            self.connect(self.crawler, SIGNAL("logMessage(QString)"), self.onLogMessage, Qt.QueuedConnection)
            self.crawler.start()

    def onParsingDone(self):
        self.threads = self.crawler.init_threads()
        self.dl_threads_running = len(self.threads)
        for thread in self.threads:
            self.connect(thread, SIGNAL("logMessage(QString)"), self.onLogMessage, Qt.QueuedConnection)
            self.connect(thread, SIGNAL("queueEmpty()"), self.onDownloadQueueEmpty, Qt.QueuedConnection)
        self.crawler.start_threads()

    def validateTags(self, tags):
        tags = tags.split(' ')
        if tags[0] == '' or len(tags) > 2:
            return False
        return True

    def onInvalidTags(self):
        self.onLogMessage('Invalid tags, please enter new tags and try again.')
    
    def onDownloadQueueEmpty(self):
        self.dl_threads_running -= 1
        if self.dl_threads_running == 0:
            self.onLogMessage('All files have finished downloading!')
            self.onLogMessage('Caching md5sums of finished files...')
            self.crawler.hash_pickle()
            self.gui.crawlBtn.setDisabled(False)
            self.onLogMessage('Caching finished!')
    
    def onFileCorrupt(self, file_name):
        self.onLogMessage('File failed to download, {} might be corrupt.'.format(file_name))


    def onCancelClicked(self):
        raise SystemExit
    
    def onBrowseClicked(self):
        path = QFileDialog.getExistingDirectory(self,'Choose the save directory', '');
        self.gui.savepathLineEdit.setText(path)

    def onLogMessage(self, message):
        self.gui.outputTextEdit.append('{0} - {1}'.format(current_time('%I:%M:%S%p'), message))

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    MainApp = MainWindow()
    MainApp.show()

    sys.exit(app.exec_())