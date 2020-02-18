import os
from os import path
import threading
import sys

DIR = path.join(path.dirname(__file__))
sys.path.append(path.join(DIR, '..'))

from PyQt5 import QtCore, QtGui, QtWidgets
from UiLoader import getUiClass
from Logic.translator import Translator
from Logic.APKUtils import isFileOfType

test_xml = path.join(DIR, '..', 'tmp', 'strings.xml')
test_apk = path.join(DIR, '..', 'tmp', 'Bluetooth.apk')
test_frw = path.join(DIR, '..', 'tmp', 'framework-res.apk')


UI_FILE = path.abspath(path.join(path.dirname(__file__), 'MainWindow.ui'))

class CustomTreeItem(QtWidgets.QTreeWidgetItem):
    """
    Description for CustomTreeItem.
    """
    def __init__(self, *args, **kwargs):
        super(CustomTreeItem, self).__init__(*args, **kwargs)
        self.tabPtr = None

class MainWindow(getUiClass(UI_FILE)):
    """
    Description for MainWindow.
    """
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # self.action_Open_ROM.trigge
    
    def open(self, path):
        newTab = Translator(path=path)
        name = os.path.basename(path)
        # 
        # treeItem = CustomTreeItem(self.openProjectsTree)
        # treeItem.setText(0, name)
        # treeItem.tabPtr = newTab
        # .addChild(treeItem)
        self.tabs.addTab(newTab, name)
        self.tabs.setCurrentWidget(newTab)
    
    def openROM(self, path):
        pass

    def openAPK(self, path):
        pass

    def openXML(self, path):
        pass

    # Slots
    @QtCore.pyqtSlot(int)
    def closeTabSlot(self, idx):
        w = self.tabs.widget(idx)
        w.close()
        self.tabs.removeTab(idx)
    
    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def treeItemActivated(self, item, idx):
        if item and item.tabPtr:
            self.tabs.setCurrentWidget(item.tabPtr)

    # Events
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