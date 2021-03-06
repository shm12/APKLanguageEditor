from PyQt5 import QtCore, QtGui, QtWidgets, uic
from Ui.UiLoader import getUiClass
from Logic.languages import langs

from appctx import ApplicationContext

UI_FILE = ApplicationContext.get_resource('LangPicker.ui')


class LangPicker(getUiClass(UI_FILE)):

    # Signals
    exitSignal = QtCore.pyqtSignal()

    def __init__(self, *args, setupUi=True, default=None, langs=langs, **kwargs,):
        super(LangPicker, self).__init__(*args, setupUi=False, **kwargs)
        self.default = default
        self.langs = langs
        self.noDefaultText = 'Choose Language...'
        if setupUi:
            self.setupUi()
    
    def setupUi(self):
        super(LangPicker, self).setupUi()
        self._langList = list(self.langs.keys())
        self._langList.sort()
        self.languageComboBox.addItem(self.noDefaultText)
        for lang in self._langList:
            self.languageComboBox.addItem(lang)

    # Slots
    @QtCore.pyqtSlot()
    def acceptedSlot(self, lang):
        self.exitSignal.emit()


