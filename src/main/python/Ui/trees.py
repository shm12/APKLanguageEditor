import os
import threading
import sys

DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(DIR, '..'))

from PyQt5 import QtCore, QtGui, QtWidgets
from Ui.UiLoader import getUiClass
from Ui.iconObjects import xmlIcon, romIcon, apkIcon
from Logic.translator import Translator, t
from Logic.APKUtils import isFileOfType

      
class ProjectTreeItem(QtWidgets.QTreeWidgetItem):
    """
    Description for ProjectTreeItem.
    """
    
    def __init__(self, translator, children=False, *args, **kwargs):
        super(ProjectTreeItem, self).__init__(*args, **kwargs)
        self.translator = translator
        self.setText(0, translator.name)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsSelectable)
        self.exists = []

        typ = self.translator.name.split('.')[-1]
        icon = xmlIcon() if typ == 'xml' else apkIcon() if typ == 'apk' else romIcon()

        self.setIcon(0, icon)
        if children:
            self.updateChildren()
            self.translator.dataUpdated.connect(self.updateChildren)

    def updateChildren(self):
        # self.takeChildren()
        children = [i for i in self.translator.getChildren() if not i in self.exists]
        self.addChildren([ProjectTreeItem(i, True) for i in children])
        self.exists += children

class OpenEditors(QtWidgets.QTreeWidget):
    """
    Description for OpenEditors.
    """
    def __init__(self, *args, **kwargs):
        super(OpenEditors, self).__init__(*args, **kwargs)
        self.map = {}
    
    def addTranslator(self, translator, idx):
        treeItem = ProjectTreeItem(translator)
        self.addTopLevelItem(treeItem)
        self.map[translator] = treeItem
    
    def removeTranslator(self, translator, idx):
        self.takeTopLevelItem(self.indexOfTopLevelItem(self.map[translator]))
        del self.map[translator]
    
    def focus(self, translator, idx):
        if not translator in self.map:
            return
        treeItem = self.map[translator]
        self.setCurrentItem(treeItem, 0)
