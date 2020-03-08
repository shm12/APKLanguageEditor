from typing import Union
from PyQt5 import QtCore, QtGui, QtWidgets
from Logic import translator
from Ui.threads import Worker, Pool

class _BaseWrapper(QtCore.QObject, translator._BaseData):
    """
    Here we define all the common slots and signal.
    Signals:
        dataChanged()             - When someone do _BaseWrapperObject.data = somedata.
        itemChanged(item, index) - When one item of the data is being changed.

    Slots:
        auto_translate_item(item) - Item can be an item or index to the item in data.
        save()                    - Save the data to disk.
    """

    # Signals
    dataChanged = QtCore.pyqtSignal()
    itemChanged = QtCore.pyqtSignal('PyQt_PyObject', int, arguments=['Item', 'DataIndex'])

    def __init__(self, threadpool: Pool, *args, **kwargs):
        self.threadpool = threadpool
        super(_BaseWrapper, self).__init__(*args, **kwargs)
        self.parent_el.childAdded.emit(self, self.parent_el.get_children().index(self)) if self.parent_el else None

    def _data_changed(self):
        self.dataChanged.emit()
        super(_BaseWrapper, self)._data_changed()

    def auto_translate_item(self, item: Union[dict, int]):
        super(_BaseWrapper, self).auto_translate_item(item)
        item = self.data[item] if type(item) is int else item
        index = self.data.index(item)
        self.itemChanged.emit(item, index)

    def keep_item(self, item: Union[dict, int]):
        super(_BaseWrapper, self).keep_item(item)
        item = self.data[item] if type(item) is int else item
        index = self.data.index(item)
        self.itemChanged.emit(item, index)

    def _set_parent(self, parent):
        super(_BaseWrapper, self)._set_parent(parent)
        self.parent_el.childAdded.emit(self, self.parent_el.get_children().index(self))


class _BaseTreeWrapper(_BaseWrapper, translator._BaseTree):
    """
    Here we define all the common slots and signal.
    Signals:
        dataChanged()             - When someone do _BaseWrapperObject.data = somedata.
        itemChanged(child, index) - When one item of the data is being changed.
        childAdded(child, index)  - When a child is added to the tree.

    Slots:
        auto_translate_item(item) - Item can be an item or index to the item in data.
        save()                    - Save the data to disk.
        build()                   - Build the Apk or the whole Rom (which is apks tree).
    """
    CHILD_TYPE = _BaseWrapper

    # Signals
    childAdded = QtCore.pyqtSignal('PyQt_PyObject', int, arguments=['Child', 'Index'])

    def add_child(self, *args, **kwargs):
        super(_BaseTreeWrapper, self).add_child(*args, threadpool=self.threadpool, **kwargs)

    def _open(self):
        # print('Wrapper open')
        thread = Worker(target=super(_BaseTreeWrapper, self)._open)
        self.threadpool.start(thread)

class Xml(_BaseWrapper, translator.Xml):
    pass


class Apk(_BaseTreeWrapper, translator.Apk):
    CHILD_TYPE = Xml


class Rom(_BaseTreeWrapper, translator.Rom):
    CHILD_TYPE = Apk
    pass
