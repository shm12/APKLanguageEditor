import os
import threading
import sys

DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(DIR, '..'))

from PyQt5 import QtCore, QtGui, QtWidgets
from UiLoader import getUiClass
from Logic.translator import Translator, t
from Logic.APKUtils import isFileOfType
from iconObjects import xmlIcon, romIcon, apkIcon


class Tabs(QtWidgets.QTabWidget):
    """
    Description for Tabs.
    """

    # Signals
    translatorAdded = QtCore.pyqtSignal('PyQt_PyObject',int,  arguments=['Translator', 'TabIndex'])
    translatorClosed = QtCore.pyqtSignal('PyQt_PyObject',int,  arguments=['Translator', 'TabIndex'])
    focused = QtCore.pyqtSignal('PyQt_PyObject',int,  arguments=['Translator', 'TabIndex'])

    def __init__(self, *args, **kwargs):
        super(Tabs, self).__init__(*args, **kwargs)
        self.tabCloseRequested.connect(self.closeTab)
        self.currentChanged.connect(self._focused)

    # Slots
    def addTranslator(self, treeItem, *args, **kwargs):
        translator = treeItem.translator
        if self.indexOf(translator) == -1:
            translator.setupUi()
            
            # Determain icon
            icon = treeItem.icon(0)

            # Add the Tab
            self.addTab(translator,icon, translator.name)
            self.translatorAdded.emit(translator, self.indexOf(translator))
        self.setCurrentWidget(translator)
    
    # @QtCore.pyqtSlot('PyQt_PyObject')
    def focus(self, treeItem, *args, **kwargs):
        translator = treeItem.translator
        self.setCurrentWidget(translator)
    
    def _focused(self, idx):
        self.focused.emit(self.widget(idx), idx)
    
    @QtCore.pyqtSlot(int)
    def closeTab(self, idx):
        translator = self.widget(idx)
        translator.close()
        self.removeTab(idx)
        self.translatorClosed.emit(translator, idx)
    
    