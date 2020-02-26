from PyQt5 import QtCore, QtGui, QtWidgets
from ...Logic import translator


class _BaseWrapper(QtCore.QObject, translator._BaseData):
    """
    Here we define all the common slots and signal.
    """

    # Signals
    dataChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(_BaseWrapper, self).__init__(*args, **kwargs)
        self.parent_el.childAdded.emit(self, self.parent_el.get_children().index(self)) if self.parent_el else None

    def _data_changed(self):
        self.dataChanged.emit()
        super(_BaseWrapper, self)._data_changed()


class _BaseTreeWrapper(_BaseWrapper, translator._BaseTree):
    """
    Here we define all the common slots and signal.
    """
    CHILD_TYPE = _BaseWrapper

    # Signals
    childAdded = QtCore.pyqtSignal('PyQt_PyObject', int, arguments=['Child', 'Index'])
    childDataChanged = QtCore.pyqtSignal('PyQt_PyObject', int, arguments=['Child', 'Index'])

    def __init__(self, *args, **kwargs):
        super(_BaseTreeWrapper,self).__init__(*args, **kwargs)

    def _child_data_changed(self, child):
        self.childDataChanged.emit(child, self.get_children().index(child))
        super(_BaseTreeWrapper, self)._child_data_changed(child)

    @QtCore.pyqtSlot()
    def _child_data_changed_slot(self):
        child = self.sender()
        index = self.get_children().index(child)
        self.childDataChanged.emit(child, index)

