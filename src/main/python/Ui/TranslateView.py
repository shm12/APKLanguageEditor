import os

from PyQt5 import QtCore, QtWidgets
from .UiLoader import getUiClass
from .PickLanguageDialog import PickLanguageDialog
from .Message import Message

from appctx import ApplicationContext

# Test
from wrap.wrrapers import Rom
from Ui.threads import Pool
from Ui.threads import Worker as Wrkr
from wrap.wrrapers import _BaseWrapper, _BaseTreeWrapper, Xml, Apk, Rom

# TranslatingDialog = getUiClass(path.abspath(path.join(path.dirname(__file__), 'TranslatingDialog.ui')))
TranslatingDialog = getUiClass(ApplicationContext.get_resource(os.path.join('ui', 'TranslatingDialog.ui')))
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                             #
# Important!  pyqt5 versions 5.12.0 to 5.13.0 when using Python 3.7.x has a bag. Be carefull  #
#             and don't use them.                                                             #
#                                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# UI_FILE = path.abspath(path.join(path.dirname(__file__), 'TranslateView.ui'))
# EXTENDEDEDIT_FILE = path.abspath(path.join(path.dirname(__file__), 'extendedEdit.ui'))
UI_FILE = ApplicationContext.get_resource(os.path.join('ui', 'TranslateView.ui'))
EXTENDEDEDIT_FILE = ApplicationContext.get_resource(os.path.join('ui','extendedEdit.ui'))
pool = Pool()


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, *args, **kwargs):
        super(QtCore.QAbstractTableModel, self).__init__(*args, **kwargs)
        self._data = []
        self._headers = []

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.internal_data)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.internal_headers)

    def headerData(self, column, Qt_Orientation, role=None):
        if role == QtCore.Qt.DisplayRole:
            if Qt_Orientation == QtCore.Qt.Horizontal:
                return self.internal_headers[column]
        return super(QtCore.QAbstractTableModel, self).headerData(column, Qt_Orientation, role)

    def data(self, QModelIndex, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()

        if role in (QtCore.Qt.EditRole, QtCore.Qt.DisplayRole):
            return self.internal_data[row][self.internal_headers[column]]

        # Default
        return QtCore.QVariant()

    def setData(self, QModelIndex, Any, role=None):
        if role in (QtCore.Qt.EditRole, QtCore.Qt.DisplayRole):
            row = QModelIndex.row()
            column = QModelIndex.column()
            self.internal_data[row][self.internal_headers[column]] = str(Any)
            self.dataChanged.emit(QModelIndex, QModelIndex)

            return True
        return False

    def flags(self, QModelIndex):
        column = QModelIndex.column()

        flags = QtCore.Qt
        ret = (
            flags.ItemIsEnabled |
            flags.ItemIsSelectable
        )

        if self.internal_headers[column] == 'Translation':
            ret = ret | flags.ItemIsEditable

        return ret

    @property
    def internal_data(self):
        return self._data

    @internal_data.setter
    def internal_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    @property
    def internal_headers(self):
        return self._headers

    @internal_headers.setter
    def internal_headers(self, headers):
        self.beginResetModel()
        self._headers = headers
        self.endResetModel()

class CustomTableWidget(QtWidgets.QTableWidget):

    # Signals
    currentRowChanged = QtCore.pyqtSignal(int,  arguments=['Row'])
    rowChangedSignal = QtCore.pyqtSignal(int,  arguments=['Row'])
    _addRowSignal = QtCore.pyqtSignal(int, list,  arguments=['Row', 'Items'])
    _removeRowSignal = QtCore.pyqtSignal(int, arguments=['Row'])

    def __init__(self, *args, **kwargs):
        super(CustomTableWidget, self).__init__(*args, **kwargs)
        self.headers = []
        self.data = []
        self._addRowSignal.connect(self._addRowSlot)
        self._removeRowSignal.connect(self._removeRowSlot)
        self.itemChanged.connect(self._rowChangedSlot)
        self.currentItemChanged.connect(self._currentChanged)

    def refresh(self):
        transColumn = self.headers.index('Translation')
        for i in range(len(self.data)):
            self.item(i, transColumn).setText(self.data[i]['Translation'])

    def _threadedSetData(self, data):
        old_data = self.data
        new_data = data
        self.data = data

        # To remove
        for i in old_data:
            if i in new_data:
                continue
            self._removeRowSignal.emit(old_data.index(i))

        # To add
        columns = range(len(self.headers))
        for i in new_data:
            if i in old_data:
                continue
            row = new_data.index(i)
            items = []
            for column in columns:
                header = self.headers[column]
                newCell = QtWidgets.QTableWidgetItem(data[row][header])
                newCell.setFlags(newCell.flags() ^ QtCore.Qt.ItemIsEditable) if header != 'Translation' else None
                items.append(newCell)
            self._addRowSignal.emit(row, items)

    def _addRowSlot(self, row, items):
        self.insertRow(row)
        for i in range(len(items)):
            self.setItem(row, i, items[i])

    def _removeRowSlot(self, row):
        self.removeRow(row)

    def setData(self, headers, data):
        if headers != self.headers:
            # Set headers
            columns = len(headers)
            self.setColumnCount(columns)
            for i in range(columns):
                h = QtWidgets.QTableWidgetItem()
                h.setText(headers[i])
                self.setHorizontalHeaderItem(i, h)
            self.headers = headers
            self.data = []
            self.clearContents()

        thread = Wrkr(target=self._threadedSetData, args=[data])
        pool.start(thread)

    def updateRow(self, row):
        item = self.item(row, self.headers.index('Translation'))
        item.setText(self.data[row]['Translation'])

    # Slots
    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def _currentChanged(self, current, *args, **kwargs):
        self.currentRowChanged.emit(self.currentRow())

    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def _rowChangedSlot(self, QTableWidgetItem):
        row = QTableWidgetItem.row()
        translationItem = self.item(row, self.headers.index('Translation'))
        if not translationItem:
            return
        self.data[row]['Translation'] = translationItem.text()
        self.data[row]['keep'] = True if self.data[row]['Translation'] == self.data[row]['Origin'] else False
        self.rowChangedSignal.emit(row)


class ExpendedEdit(getUiClass(EXTENDEDEDIT_FILE)):
    """
    More comfortable translation editor.
    Inner data must contain 'Origin', 'Translation' and 'keep'.

    Signals:
        translationChanged()
        autoTranslateClicked()
        keepOriginClicked()
    
    Slots:
        setData(data)
        refreshTranslation()
    """

    # Signals
    translationChanged = QtCore.pyqtSignal()
    autoTranslateClicked = QtCore.pyqtSignal()
    keepOriginClicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(ExpendedEdit, self).__init__(*args, **kwargs)
        self.data = None

    def setupUi(self):
        super(ExpendedEdit, self).setupUi()
        self.setEnabled(False)
        self.autoTranslateClicked = self.autoTranslateButton.clicked
        self.keepOriginClicked = self.keepOriginButton.clicked
        self.translationChanged = self.translationTextEdit.textChanged
        self.translationTextEdit.textChanged.connect(self._updateData)

    def setTitle(self, title):
        self.groupBox.setTitle(title)

    def title(self):
        return self.groupBox.title()

    # Slots
    @QtCore.pyqtSlot('PyQt_PyObject')
    def setData(self, data):
        # print(self.enabled())
        self.setEnabled(True)
        self.data = data
        self.originTextEdit.setText(data['Origin'])
        self.translationTextEdit.setText(data['Translation'])
        self.setTitle(data['Name'])


    @QtCore.pyqtSlot()
    def refreshTranslation(self, *args, **kwargs):
        """
        Refresh the translation in the view.
        :return: None
        """
        assert self.data, 'Trying to update data while no data has been set.'
        text = self.data['Translation']
        if text != self.translationTextEdit.toPlainText():
            self.translationTextEdit.setText(text)

    @QtCore.pyqtSlot()
    def _updateData(self):
        """
        Update the data from the view.
        :return: None
        """
        if not self.data:
            return
        text = self.translationTextEdit.toPlainText()
        if text != self.data['Translation']:
            self.data['Translation'] = text


class TranslateView(getUiClass(UI_FILE)):
    """
    global signals:
        translateRequested(items)
        keepRequested(items)
        saveRequested()
        buildRequested()

    global slots:
        setData(data)
        refresh()
    """
    translateRequested = QtCore.pyqtSignal(list, arguments=['Items'])
    keepRequested = QtCore.pyqtSignal(list, arguments=['Items'])
    saveRequested = QtCore.pyqtSignal()
    buildRequested = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(TranslateView, self).__init__(*args, **kwargs)
        self.activeRow = None

    def setupUi(self):
        super(TranslateView, self).setupUi()
        
        # Expended edit signals
        self.expendedEdit.translationChanged.connect(self.updateActiveRow)
        self.expendedEdit.autoTranslateClicked.connect(self._translateActive)
        self.expendedEdit.keepOriginClicked.connect(self._keepActive)

        # Translation Table signals
        self.translationTable.rowChangedSignal.connect(self._rowChangedSlot)
        self.translationTable.currentRowChanged.connect(self.setActiveRow)
        self.autoTranslateAllButton.clicked.connect(self._translateAll)

    # Inner things
    def _rowChangedSlot(self, row):
        if self.activeRow is not None and row == self.activeRow:
            self.expendedEdit.refreshTranslation()
 
    def setActiveRow(self, row):
        print('setting active row', row)
        self.activeRow = row
        self.expendedEdit.setData(self._data[row])

    def updateActiveRow(self):
        if self.activeRow is not None:
            self.translationTable.updateRow(self.activeRow)

    def setData(self, data):
        self._data = data
        self.translationTable.setData(['Name', 'Origin', 'Translation'], data)

    # exported things
    def _translateAll(self):
        self.translateRequested.emit(list(range(len(self._data))))

    def _translateActive(self):
        if self.activeRow is None:
            return
        self.translateRequested.emit([self.activeRow])

    def _keepAll(self):
        self.keepRequested.emit(list(range(len(self._data))))

    def _keepActive(self):
        if self.activeRow is None:
            return
        self.keepRequested.emit([self.activeRow])

    def updateRow(self, row_data, row):
        print('updating row')
        self.translationTable.updateRow(row)

    def save(self):
        self.saveRequested.emit()

    def build(self):
        self.buildRequested.emit()