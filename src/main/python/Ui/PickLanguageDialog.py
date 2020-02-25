from os import path
import sys
DIR = path.join(path.dirname(__file__))
sys.path.append(path.join(DIR, '..'))

from PyQt5 import QtCore, QtGui, QtWidgets
from Ui.UiLoader import getUiClass
from Logic.languages import langs

from fbs_runtime.application_context.PyQt5 import ApplicationContext
ApplicationContext = ApplicationContext()

UI_FILE = path.abspath(path.join(path.dirname(__file__), 'PickLanguageDialog.ui'))
UI_FILE = path.abspath(ApplicationContext.get_resource('PickLanguageDialog.ui'))

# On exist options
CREATE = 0
EDIT = 1
ASK = 3


class PickLanguageDialog(getUiClass(UI_FILE)):

    # Signals
    acceptedSignal = QtCore.pyqtSignal('PyQt_PyObject', arguments=['ReturnDict'])
    rejectedSignal = QtCore.pyqtSignal('PyQt_PyObject', arguments=['ReturnDictNoLang'])

    def __init__(self, *args, langs=langs, setupUi=True, default="Hebrew", existLangs={}, onExist=CREATE, **kwargs):
        super(PickLanguageDialog, self).__init__( *args, setupUi=False, **kwargs)
        self.default = default
        self._langs = dict()
        self.langs = langs
        self.noDefaultText = 'Choose Language...'
        self.onExist = onExist
        self.langExist = False
        self.existLangs = existLangs
        if setupUi:
            self.setupUi()
    
    # Methodes
    def setupUi(self):
        super(PickLanguageDialog, self).setupUi()
        # self.langExistGroupBox.setVisible(False)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setAutoDefault(True)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setAutoDefault(True)

        # Setup combo box
        if not self.default:
            self.langComboBox.addItem(self.noDefaultText)
        for lang in self._langList:
            self.langComboBox.addItem(lang)
        defaultIdx = self._langList.index(self.default) if self.default else 0
        self.langComboBox.setCurrentIndex(defaultIdx)

        # Setup on Exists
        if self.onExist == EDIT:
            self.editExistTranslation.setChecked(True)
        elif self.onExist == CREATE:
            self.createNewTranslation.setChecked(True)

        self.adjustSize()
    
    def _checkLangExists(self, lang):
        self.langExist = lang in self.existLangs
        if self.langExist:
            self.langExistGroupBox.show()
        else:
            self.langExistGroupBox.hide()

        self.adjustSize()

    # Properties
    @QtCore.pyqtProperty(dict)
    def langs(self):
      return  self._langs
    
    @langs.setter
    def langs(self, langs):
        self._langs = langs
        self._langList = list(self._langs.keys())
        self._langList.sort()
    
    # Slots
    @QtCore.pyqtSlot(str)
    def onLangPick(self, lang):
        if lang in self._langList:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setDefault(True)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setDefault(False)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setDefault(True)
        self._checkLangExists(lang)
    
    @QtCore.pyqtSlot()
    def acceptedSlot(self):
        ret = {
            'Lang': self.langComboBox.currentText(),
            'Exists': self.langExist,
            'onExists': CREATE if self.createNewTranslation.isChecked() else EDIT
        }
        self.acceptedSignal.emit(ret)
    
    @QtCore.pyqtSlot()
    def rejectedSlot(self):
        ret = {
            'Lang': '',
        }
        self.rejectedSignal.emit(ret)


