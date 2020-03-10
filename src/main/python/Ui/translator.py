import os
from PyQt5 import QtCore, QtWidgets
from .TranslateView import TranslateView
from .threads import Worker
from .processDialog import ProcessDialog
from .Message import Message
from appctx import ApplicationContext
from wrap import wrrapers


class Translator(wrrapers._BaseWrapper):
    def __init__(self, *args, **kwargs):
        super(Translator, self).__init__(*args, **kwargs)
        self._ui = None
        self._stop = False

    @property
    def ui(self):
        if not self._ui:
            self._ui = TranslateView()
            self._ui.setData(self.data)
            self.itemChanged.connect(self._ui.updateRow)
            self.dataChanged.connect(self._dataChangedSlot)
            self._ui.translateRequested.connect(self.auto_translate_items)
            self._ui.keepRequested.connect(self.keep_items)
            self._ui.makeUntraslatableRequested.connect(self.set_items_untranslatable)
            self._ui.saveRequested.connect(self.save)
        return self._ui

    def _dataChangedSlot(self):
        self._ui.setData(self.data)

    def auto_translate_items(self, items):
        self._stop = False
        d = ProcessDialog(title='Translating',
                          message='Please wait while translating...',
                          icon=ApplicationContext.get_resource(os.path.join('icons', 'translation.png')))
        thread = Worker(target=self._threaded_translate, args=[items, lambda:self._stop])
        thread.finished.connect(d.reject)
        thread.exceptionRaised.connect(lambda e: Message(
            title='Error',
            message=f'An error occure while translating: \n{e}',
            icon=ApplicationContext.get_resource(os.path.join('icons', 'error.png'))
        ).exec())
        self.threadpool.start(thread)
        d.exec()
        if d.ret == 'cancel':
            self._stop = True

    def _threaded_translate(self, items, stop_getter):
        for item in items:
            if stop_getter():
                break
            self.auto_translate_item(item)

    def keep_items(self, items):
        for item in items:
            self.keep_item(item)

    def set_items_untranslatable(self, items):
        for item in items:
            self.set_item_untraslatable(item)

    def set_items_translatable(self, items):
        for item in items:
            self.set_item_translatable(item)

    def focused(self, *args, **kwargs):
        pass


class Xml(Translator, wrrapers.Xml):

    def save(self):
        if not self.dest:
            d = QtWidgets.QFileDialog(None, 'Save To XML', self.path, 'XML file (*.xml)')
            d.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            d.setDefaultSuffix('xml')
            d.exec()
            self.dest = d.selectedFiles()[0]
        super(Xml, self).save()
    pass


class Apk(wrrapers.Apk, Translator):
    CHILD_TYPE = Xml
    pass


class Rom(wrrapers.Rom, Translator):
    CHILD_TYPE = Apk
    pass

