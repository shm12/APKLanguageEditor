from os import path
import threading

from PyQt5 import QtCore, QtGui, QtWidgets
from UiLoader import getUiClass
from PickLanguageDialog import PickLanguageDialog
from Message import Message

TranslatingDialog = getUiClass(path.abspath(path.join(path.dirname(__file__), 'TranslatingDialog.ui')))
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                             #
# Important!  pyqt5 versions 5.12.0 to 5.13.0 when using Python 3.7.x has a bag. Be carefull  #
#             and don't use them.                                                             #
#                                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

UI_FILE = path.abspath(path.join(path.dirname(__file__), 'TranslateView.ui'))
EXTENDEDEDIT_FILE = path.abspath(path.join(path.dirname(__file__), 'extendedEdit.ui'))
stop = False

class CustomTableWidget(QtWidgets.QTableWidget):

    # Signals
    rowClickedSignal = QtCore.pyqtSignal(int,  arguments=['Row'])
    rowChangedSignal = QtCore.pyqtSignal(int,  arguments=['Row'])
    # setCellTextSignal = QtCore.pyqtSignal(int, int, str, arguments=['Row', 'Column', 'Text'])

    def __init__(self, *args, **kwargs):
        super(CustomTableWidget, self).__init__(*args, **kwargs)
        self.headers = []
        self.currentItemChanged.connect(self.rowClickedSlot)
        self.itemChanged.connect(self.rowChangedSlot)
        self.rowChangedSignal.connect(self.updateRow)
        # self.setCellTextSignal.connect(self.setCellText)
    
    # Methodes
    # def getRowData(self, rowNum):
    #     columnNum = self.columnCount()
    #     return [self.item(rowNum, i) for i in range(columnNum)]
    
    # def getData(self):
    #     return [self.getColumnDataInRange(i, 0, self.rowCount()) for i in range(self.columnCount())]
    
    # def getColumnDataInRange(self, column, start, end):
    #     return [self.item(i, column).text() for i in range(start, end)]
    
    def updateRow(self, row):
        self.item(row, self.headers.index('Translation')).setText(self.data[row]['Translation'])
    
    def setColumnDataInRange(self, column, start, end, data, stop=None):
        idx = start
        for i in data:
            if stop and stop():
                break
            if type(i) != str:
                return i

            self.setCellTextSignal.emit(idx, column, i)
            idx += 1

    def setData(self, headers, data):
        self.headers = headers
        self.clearTableSlot()

        # Preperations
        data = list(data)
        rows = len(data)
        columns = len(headers)
        self.data = data

        # Set headers
        self.setColumnCount(columns)
        for i in range(columns):
            h = QtWidgets.QTableWidgetItem()
            h.setText(headers[i])
            self.setHorizontalHeaderItem(i,h)
        
        # Set data
        self.setRowCount(rows)
        for header in headers:
            column = headers.index(header)
            for row in range(rows):
                newCell = QtWidgets.QTableWidgetItem()
                newCell.setText(data[row][header])
                newCell.setFlags(newCell.flags() ^ QtCore.Qt.ItemIsEditable) if header != 'Translation' else None
                self.setItem(row, column, newCell)
        
    # Slots
    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def rowClickedSlot(self, current, *args, **kwargs):
        self.rowClickedSignal.emit(current.row())

    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def rowChangedSlot(self, QTableWidgetItem):
        row = QTableWidgetItem.row()
        translationItem = self.item(row, self.headers.index('Translation'))
        if not translationItem:
            return
        self.data[row]['Translation'] = translationItem.text()
        self.rowChangedSignal.emit(row)

    @QtCore.pyqtSlot()
    def clearTableSlot(self):
        self.setRowCount(0)
        self.setColumnCount(0)
    
    @QtCore.pyqtSlot(int, int, str)
    def setCellText(self, row, column, text):
        self.item(row, column).setText(text)

class ExpendedEdit(getUiClass(EXTENDEDEDIT_FILE)):
    """
    More comfortable translation editor.
    Inner data must contain 'Origin', 'Translation' and 'keep'.

    Signals:
        translationChanged()
        autoTranslateClicked()
    
    Slots:
        setData(data)
        updateTranslation()
        keepOrigin()
        updateData()
    """

    # Signals
    translationChangedSignal = QtCore.pyqtSignal()
    autoTranslateClicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(ExpendedEdit, self).__init__(*args, **kwargs)
        self.data = {}
    
    def setupUi(self):
        super(ExpendedEdit, self).setupUi()
        self.translationChangedSignal = self.translationTextEdit.textChanged
        self.autoTranslateClicked = self.autoTranslateButton.clicked
        self.translationTextEdit.textChanged.connect(self.updateData)
        self.keepOriginButton.clicked.connect(self.keepOrigin)

    # Slots
    @QtCore.pyqtSlot('PyQt_PyObject')
    def setData(self, data):
        self.data = data
        self.originTextEdit.setText(data['Origin'])
        self.translationTextEdit.setText(data['Translation'])

    @QtCore.pyqtSlot()
    def updateTranslation(self, *args, **kwargs):
        # assert self.data, 'Trying to update data while no data has been set.'
        text = self.data['Translation']
        if text != self.translationTextEdit.toPlainText():
            self.translationTextEdit.setText(text)

    @QtCore.pyqtSlot()
    def keepOrigin(self):
        if not self.data:
            return
        self.translationTextEdit.setText(self.data['Origin'])
        self.data['keep'] = True
    
    @QtCore.pyqtSlot()
    def updateData(self):
        if not self.data:
            return
        text = self.translationTextEdit.toPlainText()
        if text != self.data['Translation']:
            self.data['Translation'] = text


class TranslateView(getUiClass(UI_FILE)):

    transaltionErrorSignal = QtCore.pyqtSignal('PyQt_PyObject', arguments=['Exception'])
    translationCanceledSignal = QtCore.pyqtSignal()
    dataUpdated = QtCore.pyqtSignal()
    rowUpdated = QtCore.pyqtSignal(int, arguments=['Exception'])

    def __init__(self, *args, setupUi=False, parent=None, **kwargs):
        self._uiSet = False
        super(TranslateView, self).__init__(*args, setupUi=setupUi, **kwargs)
        self._langPicker = None
        self.langPickRet = {}
        self.activeRow = None
        self._data = []
        self._stopTransThread = [False]
        self.dataUpdated.connect(self.refreshTable)
        self.dataUpdated.connect(parent.childDataUpdated) if parent else None

    def setupUi(self):
        super(TranslateView, self).setupUi()
        self.tg = None
        self.translationTable.setData(['Name', 'Origin', 'Translation'], list(self.data))
        self.transaltionErrorSignal.connect(self.transaltionErrorSlot)
        self.translationTable.rowClickedSignal.connect(self.setActiveRow)
        self.translationTable.rowChangedSignal.connect(self.updateExpendedEdit)
        self.expendedEdit.translationChangedSignal.connect(self.updateActiveRow)
        self.expendedEdit.autoTranslateClicked.connect(self.translateActiveRow)
        self.translationCanceledSignal.connect(self.closeTg)
        
        if self.activeRow != None:
            self.translationTable.selectRow(self.activeRow)
            self.setActiveRow(self.activeRow)
        self._uiSet = True
    
    @QtCore.pyqtSlot(int)
    def updateExpendedEdit(self, row):
        self.expendedEdit.updateTranslation() if row == self.activeRow else None
    
    @QtCore.pyqtSlot()
    def updateActiveRow(self):
        self.translationTable.updateRow(self.activeRow) if self.activeRow != None else None

    @QtCore.pyqtSlot(int)
    def setActiveRow(self, row):
        if self._uiSet and self.data:
            self.expendedEdit.setData(list(self.translationTable.data)[row])
            self.expendedEditBorder.setTitle(self.translationTable.data[row]['Name'])
        self.activeRow = row

    def refreshTable(self):
        if self._uiSet:
            self.translationTable.setData(['Name', 'Origin', 'Translation'], list(self.data))
    
    def childDataUpdated(self):
        self.dataUpdated.emit()

    def getChildren(self):
        """
        Should be implemented in the logic part.
        """
        return []

    def _translate(self, data):
        """
        Should be implemented in the logic part (this is the ui part)
        """
        pass
        return [i*2 for i in data]
    
    def pickLang(self, *args, **kwargs):
        if not self._langPicker:
            self._langPicker = PickLanguageDialog(*args, **kwargs)
            self._langPicker.acceptedSignal.connect(self.pickLangSlot)
            self._langPicker.rejectedSignal.connect(self.pickLangSlot)
        else:
            self._langPicker.__init__(*args, **kwargs)
        self._langPicker.exec()

    def isTransThreadStopped(self):
        return self._stopTransThread[-1]

    # Slots
    @QtCore.pyqtSlot()
    def stopTransThread(self, *args, **kwargs):
        if self.isTransThreadStopped():
            return
        self._stopTransThread.append(True)
        self.translationCanceledSignal.emit()
    
    def closeTg(self):
        self.tg.close()
    
    @QtCore.pyqtSlot('PyQt_PyObject')
    def pickLangSlot(self, ret):
        self.langPickRet = ret
        self.newLang = ret['Lang']

    # @QtCore.pyqtSlot(int, int)
    def startTranslateData(self, data):
        self._stopTransThread = [False]
        self.tg = TranslatingDialog() if not self.tg else self.tg
        thread = Worker(target=self.translateData,
                        tar_args=(data, self.isTransThreadStopped),
                        callBackEmptySignal=self.translationCanceledSignal,
                        callback=self.stopTransThread)
        self.threadpool.start(thread)
        self.tg.rejected.connect(self.stopTransThread)
        self.tg.exec()
    
    def _translateRange(self, start, end):
        data = self.translationTable.getColumnDataInRange(0, start, end)
        translatedData = self._translate(data)
        ret = self.translationTable.setColumnDataInRange(1, start, end, translatedData, self.isTransThreadStopped)
        if ret:
            self.transaltionErrorSignal.emit(ret)

    @QtCore.pyqtSlot('PyQt_PyObject')
    def transaltionErrorSlot(self, exception):
        m = Message(message=f'An error occure while translating: {exception}')
        m.exec()

    @QtCore.pyqtSlot()
    def translateAllSlot(self):
        self.startTranslateData(self.data)
        # self.translateRangeSlot(0, self.translationTable.rowCount())
    
    @QtCore.pyqtSlot(int)
    def translateRowSlot(self, row):
        self.translateRangeSlot(row, row + 1)
    
    def translateData(self, data, stopFlagGetter, from_='Origin'):
        for i in data:
            if stopFlagGetter():
                return
                
            translated = self._translate(i[from_])
            if type(translated) != str:
                self.transaltionErrorSignal.emit(translated)
                return
            i['Translation'] =translated
            self.translationTable.rowChangedSignal.emit(self.translationTable.data.index(i))
    
    def translateActiveRow(self):
        self.startTranslateData([self.expendedEdit.data]) if self.activeRow != None else None

    # properties
    @property
    def data(self):
        if self.getChildren():
            for child in self.getChildren():
                for i in child.data:
                    yield i
        else:
            for i in self._data:
                yield i
    
    @data.setter
    def data(self, data):
        self._data = data
        self.dataUpdated.emit()

    @property
    def translationData(self):
        """
        A list of two lists (identicaly in the structure).
        """
        self._translationData = self.translationTable.getData()
        return self._translationData
    
    @translationData.setter
    def translationData(self, data):

        # Senity check
        assert (type(data) in (list, tuple)), 'TranslateView.translationData must be a list or tuple (got {})'.format(type(data))
        assert (len(data) == 2), 'TranslateView.translationData must be in lenght equal to 2 (got {})'.format(len(data))
        assert ({type(data[0]), type(data[0])}.issubset({list, tuple})), 'Every item in TranslateView.translationData must be either, list or tuple'
        assert (len(data[0]) == len(data[1])), 'TranslateView.translationData lists must be in same lenght'

        self.translationTable.setData(data)
        self.translationTextEdit.tableIdx = None
        self.originTextEdit.tableIdx = None

class CustomQTThread(QtCore.QThread):
    def __init__(self, *args, target, tar_args=() ,tar_kwargs={},  **kwargs):
        super(CustomQTThread, self).__init__(*args, **kwargs)
        self.target = target
        self.args = tar_args
        self.kwargs = tar_kwargs
    
    def run(self):
        self.target(*self.args, **self.kwargs)



class Worker(QtCore.QRunnable):
    
    def __init__(self, *args, target, tar_args=() ,tar_kwargs={}, callbackSignal=None, callBackEmptySignal=None, callback=None, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)
        self.setAutoDelete(True)
        self.target = target
        self.args = tar_args
        self.kwargs = tar_kwargs
        self.callbackSignal = callbackSignal
        self.callBackEmptySignal = callBackEmptySignal
        self.callback = callback
    
    @QtCore.pyqtSlot()
    def run(self):
        ret = self.target(*self.args, **self.kwargs)
        self.callback(self.target,
                      self.args,
                      self.kwargs,
                      ret) if self.callback else None
        self.callbackSignal.emit(self.target,
                                 self.args,
                                 self.kwargs,
                                 ret) if self.callbackSignal else None
        self.callBackEmptySignal.emit() if self.callBackEmptySignal else None


# class CustomTextEdit(QtWidgets.QTextEdit):

#     # Signals
#     cellTextChanged = QtCore.pyqtSignal('PyQt_PyObject','PyQt_PyObject', arguments=['tableIdx', 'Text'])
#     transalteSignal = QtCore.pyqtSignal(int, arguments=['Row'])

#     def __init__(self, *args, **kwargs):
#         super(CustomTextEdit, self).__init__(*args, **kwargs)
#         self.origin = False
#         self.tableIdx = None
#         self.textChanged.connect(self.textChangedSlot)

#     # Slots
#     @QtCore.pyqtSlot('PyQt_PyObject','PyQt_PyObject')
#     def rowChangedSlot(self, itemWidget, rowItems):
#         idx = 0 if self.origin else 1

#         if (itemWidget.row(), idx) == self.tableIdx:
#             self.setTextByRowSlot(itemWidget, rowItems)
        
#     @QtCore.pyqtSlot('PyQt_PyObject','PyQt_PyObject')
#     def setTextByRowSlot(self, itemWidget, rowItems):
#         idx = 0 if self.origin else 1
#         txt = rowItems[idx].text()
#         self.tableIdx = (itemWidget.row(), idx)
#         self.setText(txt) if self.toPlainText() != txt else None
    
#     @QtCore.pyqtSlot()
#     def textChangedSlot(self):
#         if self.tableIdx:
#             self.cellTextChanged.emit(self.tableIdx, self.toPlainText())
            
#     @QtCore.pyqtSlot()
#     def translateSlot(self):
#         if self.tableIdx:
#             self.transalteSignal.emit(self.tableIdx[0])

#     # Properties
#     @QtCore.pyqtProperty(bool)
#     def origin(self):
#         return not self.translation
    
#     @origin.setter
#     def origin(self, value):
#         self.translation = not value

