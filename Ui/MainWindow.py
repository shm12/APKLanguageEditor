import os
import threading
import sys

DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(DIR, '..'))

from PyQt5 import QtCore, QtGui, QtWidgets
from UiLoader import getUiClass
from trees import ProjectTreeItem
from Logic.translator import Translator, t
from Logic.APKUtils import isFileOfType

test_xml = os.path.join(DIR, '..', 'tmp', 'strings.xml')
test_apk = os.path.join(DIR, '..', 'tmp', 'Bluetooth.apk')
test_frw = os.path.join(DIR, '..', 'tmp', 'framework-res.apk')


UI_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'MainWindow.ui'))

sys._excepthook = sys.excepthook 
def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1) 
sys.excepthook = exception_hook 


class MainWindow(getUiClass(UI_FILE)):
    """
    Description for MainWindow.
    """
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.threadpool = t
        # self.action_Open_ROM.trigge
    
    def setupUi(self):
        super(MainWindow, self).setupUi()
        self.projectsTree.itemClicked.connect(self.tabs.addTranslator)
        self.openEditors.itemClicked.connect(self.tabs.focus)
        self.tabs.translatorAdded.connect(self.openEditors.addTranslator)
        self.tabs.translatorClosed.connect(self.openEditors.removeTranslator)
        self.tabs.focused.connect(self.openEditors.focus)
        self.tabs.focused.connect(self.projectsTree.focus)

    def open(self, path):
        treeItem = ProjectTreeItem(Translator(path=path), children=True)
        self.projectsTree.addTopLevelItem(treeItem)
        if isFileOfType(path, 'xml'):
            self.projectsTree.itemActivated.emit(treeItem, 0)

    # Events
    def startDrag(self):
        print('start drag')

    def dragEnterEvent(self, e):
        for url in e.mimeData().urls():
            if url.scheme() == 'file':
                path = os.path.normpath(url.path()[1:])
                if isFileOfType(path, 'xml') or isFileOfType(path, 'apk') or os.path.isdir(path):
                    e.accept()
                    return
        e.ignore() 

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            path = os.path.normpath(url.path()[1:])
            if isFileOfType(path, 'xml') or isFileOfType(path, 'apk') or os.path.isdir(path):
                self.open(path)