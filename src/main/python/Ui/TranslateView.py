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
    
    def refreshRow(self, row):
        self.dataChanged.emit(self.createIndex(row, 0), self.createIndex(row, len(self.internal_headers)))

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
        self.model = TableModel()
        super(TranslateView, self).__init__(*args, **kwargs)
        self.activeRow = None

    def setupUi(self):
        super(TranslateView, self).setupUi()
        
        # Expended edit signals
        self.expendedEdit.translationChanged.connect(self.updateActiveRow)
        self.expendedEdit.autoTranslateClicked.connect(self._translateActive)
        self.expendedEdit.keepOriginClicked.connect(self._keepActive)

        # Translation Table signals
        self.translationTable.setModel(self.model)
        self.translationTable.selectionModel().currentChanged.connect(self.setActiveRow)
        self.model.dataChanged.connect(self._rowChangedSlot)
        self.autoTranslateAllButton.clicked.connect(self._translateAll)

    # Inner things
    def _rowChangedSlot(self, start, end):
        if self.activeRow is not None and start.row() <= self.activeRow <= end.row():
            self.expendedEdit.refreshTranslation()
 
    def setActiveRow(self, new, prev):
        row = new.row()
        self.activeRow = row
        self.expendedEdit.setData(self.model.internal_data[row])

    def updateActiveRow(self):
        if self.activeRow is not None:
            self.model.refreshRow(self.activeRow)

    def setData(self, data):
        self.model.internal_data = data
        self.model.internal_headers = ['Name', 'Origin', 'Translation']

    # exported things
    def _translateAll(self):
        print(self.receivers(self.translateRequested))
        self.translateRequested.emit(list(range(len(self.model.internal_data))))

    def _translateActive(self):
        if self.activeRow is None:
            return
        self.translateRequested.emit([self.activeRow])

    def _keepAll(self):
        self.keepRequested.emit(list(range(len(self.model.internal_data))))

    def _keepActive(self):
        if self.activeRow is None:
            return
        self.keepRequested.emit([self.activeRow])

    def updateRow(self, row_data, row):
        self.model.refreshRow(row)

    def save(self):
        self.saveRequested.emit()

    def build(self):
        self.buildRequested.emit()