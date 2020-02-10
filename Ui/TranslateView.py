from PyQt5 import QtCore, QtGui, QtWidgets, uic


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                             #
# Important!  pyqt5 versions 5.12.0 to 5.13.0 when using Python 3.7.x has a bag. Be carefull  #
#             and don't use them.                                                             #
#                                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class CustomTableWidget(QtWidgets.QTableWidget):

    # Signals
    rowClickedSignal = QtCore.pyqtSignal('PyQt_PyObject','PyQt_PyObject', arguments=['QTableWidgetItem', 'RowData'])
    rowChangedSignal = QtCore.pyqtSignal('PyQt_PyObject','PyQt_PyObject', arguments=['QTableWidgetItem', 'RowData'])

    def __init__(self, *args, **kwargs):
        super(CustomTableWidget, self).__init__(*args, **kwargs)
        self.itemClicked['QTableWidgetItem*'].connect(self.rowClickedSlot)
        self.itemChanged['QTableWidgetItem*'].connect(self.rowChangedSlot)
    
    # Methodes
    def getRowData(self, rowNum):
        columnNum = self.columnCount()
        return [self.item(rowNum, i) for i in range(columnNum)]
    
    def getData(self):
        return [self.getColumnDataInRange(i, 0, self.rowCount()) for i in range(self.columnCount())]
    
    def getColumnDataInRange(self, column, start, end):
        return [self.item(i, column).text() for i in range(start, end)]
    
    def setColumnDataInRange(self, column, start, end, data):
        for i in range(end - start):
            self.item(start + i, column).setText(data[i])

    def setData(self, data):
        self.clearTableSlot()

        # Preperations 
        rows = len(data[0])
        cellsPerRow = len(data)

        # Initialize every cell
        self.setRowCount(rows)
        for row in range(rows):
            for cell in range(cellsPerRow):
                newCell = QtWidgets.QTableWidgetItem()
                newCell.setText(str(data[cell][row]))
                newCell.setFlags(newCell.flags() ^ QtCore.Qt.ItemIsEditable) if cell == 0 else None
                self.setItem(row, cell, newCell)
        
    # Slots
    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def rowClickedSlot(self, QTableWidgetItem):
        self.rowClickedSignal.emit(QTableWidgetItem, self.getRowData(QTableWidgetItem.row()))

    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def rowChangedSlot(self, QTableWidgetItem):
        self.rowChangedSignal.emit(QTableWidgetItem, self.getRowData(QTableWidgetItem.row()))

    @QtCore.pyqtSlot('PyQt_PyObject','PyQt_PyObject')
    def changeTextFromTextEdit(self, tableIdx, text):
        self.item(*tableIdx).setText(text)
    
    @QtCore.pyqtSlot()
    def clearTableSlot(self):
        self.setRowCount(0)
class CustomTextEdit(QtWidgets.QTextEdit):

    # Signals
    cellTextChanged = QtCore.pyqtSignal('PyQt_PyObject','PyQt_PyObject', arguments=['tableIdx', 'Text'])
    transalteSignal = QtCore.pyqtSignal(int, arguments=['Row'])

    def __init__(self, *args, **kwargs):
        super(CustomTextEdit, self).__init__(*args, **kwargs)
        self.origin = False
        self.tableIdx = None
        self.textChanged.connect(self.textChangedSlot)

    # Slots
    @QtCore.pyqtSlot('PyQt_PyObject','PyQt_PyObject')
    def rowChangedSlot(self, itemWidget, rowItems):
        idx = 0 if self.origin else 1

        if (itemWidget.row(), idx) == self.tableIdx:
            self.setTextByRowSlot(itemWidget, rowItems)
        
    @QtCore.pyqtSlot('PyQt_PyObject','PyQt_PyObject')
    def setTextByRowSlot(self, itemWidget, rowItems):
        idx = 0 if self.origin else 1
        txt = rowItems[idx].text()
        self.tableIdx = (itemWidget.row(), idx)
        self.setText(txt) if self.toPlainText() != txt else None
    
    @QtCore.pyqtSlot()
    def textChangedSlot(self):
        if self.tableIdx:
            self.cellTextChanged.emit(self.tableIdx, self.toPlainText())
            
    @QtCore.pyqtSlot()
    def translateSlot(self):
        if self.tableIdx:
            self.transalteSignal.emit(self.tableIdx[0])

    # Properties
    @QtCore.pyqtProperty(bool)
    def origin(self):
        return not self.translation
    
    @origin.setter
    def origin(self, value):
        self.translation = not value

class TranslateView(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(TranslateView, self).__init__(*args, **kwargs)
        uic.loadUi('TranslateView.ui', self)
        self.translationData = self.translationData
    
    def _translate(self, data):
        """
        Should be implemented in the logic part (this is the ui part)
        """
        pass
        return [i*2 for i in data]
    
    # Slots
    @QtCore.pyqtSlot(int, int)
    def translateRangeSlot(self, start, end):
        data = self.translationTable.getColumnDataInRange(0, start, end)
        translatedData = self._translate(data)
        self.translationTable.setColumnDataInRange(1, start, end, translatedData)

    @QtCore.pyqtSlot()
    def translateAllSlot(self):
        self.translateRangeSlot(0, self.translationTable.rowCount())
    
    @QtCore.pyqtSlot(int)
    def translateRowSlot(self, row):
        self.translateRangeSlot(row, row + 1)

    # properties
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


