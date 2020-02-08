from PyQt5 import QtCore, QtGui, QtWidgets, uic

class CustomTableWidget(QtWidgets.QTableWidget):

    # Signals
    rowClickedSignal = QtCore.pyqtSignal('PyQt_PyObject','PyQt_PyObject', arguments=['QTableWidgetItem', 'RowData'])
    rowChangedSignal = QtCore.pyqtSignal('PyQt_PyObject','PyQt_PyObject', arguments=['QTableWidgetItem', 'RowData'])

    def __init__(self, *args, **kwargs):
        super(CustomTableWidget, self).__init__(*args, **kwargs)
        self.itemClicked['QTableWidgetItem*'].connect(self.rowClickedSlot)
        self.itemChanged['QTableWidgetItem*'].connect(self.rowChangedSlot)
    
    def getRowData(self, rowNum):
        columnNum = self.columnCount()
        return [self.item(rowNum, i) for i in range(columnNum)]

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
    
    def setData(self, data):
        self.clearTableSlot()

        # Preperations 
        rows = len(data[0])
        cellsPerRow = len(data)

        # Initialize every cell
        self.setRowCount(rows)
        print('Row Count: ', self.rowCount())
        print('Column Count: ', self.columnCount())
        for row in range(rows):
            for cell in range(cellsPerRow):
                print('Setting (', row, ', ', cell, ') = ', str(data[cell][row]))
                newCell = QtWidgets.QTableWidgetItem()
                newCell.setText(str(data[cell][row]))
                self.setItem(row, cell, newCell)
        
class CustomTextEdit(QtWidgets.QTextEdit):

    # Signals
    cellTextChanged = QtCore.pyqtSignal('PyQt_PyObject','PyQt_PyObject', arguments=['tableIdx', 'Text'])

    def __init__(self, *args, **kwargs):
        super(CustomTextEdit, self).__init__(*args, **kwargs)
        self.origin = False
        self.tableIdx = None
        self.textChanged.connect(self.textChangedSlot)

    # Slots
    @QtCore.pyqtSlot('PyQt_PyObject','PyQt_PyObject')
    def rowChangedSlot(self, itemWidget, rowItems):
        idx = 0 if self.origin else 1

        print('RowChange')
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
        self.cellTextChanged.emit(self.tableIdx, self.toPlainText())

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
        self._translationData = None
        self.translationData = ([1,2,3,4,5,6,6], [1,2,3,4,5,6,6])
    
    @property
    def translationData(self):
        """
        A list of two lists (identicaly in the structure).
        """
        return self._translationData
    
    @translationData.setter
    def translationData(self, data):

        # Senity check
        assert (type(data) in (list, tuple)), 'TranslateView.translationData must be a list or tuple (got {})'.format(type(data))
        assert (len(data) == 2), 'TranslateView.translationData must be in lenght equal to 2 (got {})'.format(len(data))
        assert ({type(data[0]), type(data[0])}.issubset({list, tuple})), 'Every item in TranslateView.translationData must be either, list or tuple'
        assert (len(data[0]) == len(data[1])), 'TranslateView.translationData lists must be in same lenght'

        self.translationTable.setData(data)


