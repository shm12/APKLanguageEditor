import os
import threading
import sys

DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(DIR, '..'))

from PyQt5 import QtCore, QtGui, QtWidgets
from Ui.UiLoader import getUiClass
from Logic.APKUtils import isFileOfType
from Ui.iconObjects import xmlIcon, romIcon, apkIcon


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
        if self.indexOf(translator.ui) == -1:
            self.focused.connect(translator.focused)
            self.addTab(translator.ui, treeItem.icon(0), translator.name)
            self.translatorAdded.emit(translator, self.indexOf(translator.ui))
        self.setCurrentWidget(translator.ui)
    
    @QtCore.pyqtSlot(int)
    def closeTab(self, idx):
        translator = self.widget(idx)
        translator.close()
        self.removeTab(idx)
        self.translatorClosed.emit(translator, idx)
    
    # @QtCore.pyqtSlot('PyQt_PyObject')
    def focus(self, treeItem, *args, **kwargs):
        translator = treeItem.translator
        self.setCurrentWidget(translator.ui)
    
    def _focused(self, idx):
        self.focused.emit(self.widget(idx), idx)
    
    @QtCore.pyqtSlot()
    def save(self):
        w = self.currentWidget()
        if w:
            w.save()
    
    @QtCore.pyqtSlot()
    def build(self):
        w = self.currentWidget()
        if w:
            w.build()   
