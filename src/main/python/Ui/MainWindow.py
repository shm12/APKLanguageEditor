import os
import threading

from PyQt5 import QtCore, QtGui, QtWidgets
from Ui.UiLoader import getUiClass
from Ui.trees import ProjectTreeItem
from Ui.threads import Pool
from Ui.tabs import Tabs
from Logic.APKUtils import isFileOfType
from .translator import Apk, Xml, Rom

from appctx import ApplicationContext

UI_FILE = ApplicationContext.get_resource(os.path.join('ui', 'MainWindow.ui'))

class MainWindow(getUiClass(UI_FILE)):
    """
    Description for MainWindow.
    """
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # self.threadpool = t
    
    def setupUi(self):
        super(MainWindow, self).setupUi()
        self.projectsTree.itemClicked.connect(self.tabs.addTranslator)
        self.openEditors.itemClicked.connect(self.tabs.focus)
        self.tabs.translatorAdded.connect(self.openEditors.addTranslator)
        self.tabs.translatorClosed.connect(self.openEditors.removeTranslator)
        self.tabs.focused.connect(self.openEditors.focus)
        self.tabs.focused.connect(self.projectsTree.focus)
        self.action_Open_ROM.triggered.connect(self.menuOpenROM)
        self.action_Open_APK.triggered.connect(self.menuOpenAPK)
        self.action_Open_XML.triggered.connect(self.menuOpenXML)
        self.actionSave.triggered.connect(self.tabs.save)
        self.actionBuild.triggered.connect(self.tabs.build)

        
        # Shortcut
        self.shortcutSave = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+S'), self)
        self.shortcutSaveAs = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+S'), self)
        self.shortcutOpenAPK = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+O'), self)
        # self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+'), self)
        # self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+'), self)
        # self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+'), self)
        self.shortcutSave.activated.connect(self.tabs.save)
        # self.shortcutSaveAs.activated.connect(self.)
        self.shortcutOpenAPK.activated.connect(self.menuOpenAPK)
        
    
    def menuOpenROM(self):
        romDir = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select Rom Directory',)
        self.open(romDir) if romDir else None
    
    def menuOpenAPK(self):
        apkDir = QtWidgets.QFileDialog.getOpenFileName(None, 'Open APK File', filter='APK file (*.apk)')[0]
        print(apkDir)
        self.open(apkDir) if apkDir else None
    
    def menuOpenXML(self):
        xmlPath = QtWidgets.QFileDialog.getOpenFileName(None, 'Open XML File', filter='XML file (*.xml)')[0]
        self.open(xmlPath) if xmlPath else None

    def open(self, path):
        if os.path.isfile(path):

            if isFileOfType(path, 'xml'):
                treeItem = ProjectTreeItem(Xml(path=path, threadpool=Pool(), target_lang='Hebrew'))
            elif isFileOfType(path, 'apk'):
                treeItem = ProjectTreeItem(Apk(path=path, threadpool=Pool(), target_lang='Hebrew'), children=True)
        elif(Apk.is_decompiled_apk(path)):
            treeItem = ProjectTreeItem(Apk(path=path, threadpool=Pool(), target_lang='Hebrew'), children=True)
        else:
            treeItem = ProjectTreeItem(Rom(path=path, threadpool=Pool(), target_lang='Hebrew'), children=True)
        
        self.projectsTree.addTopLevelItem(treeItem)

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