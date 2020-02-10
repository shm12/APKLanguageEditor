from PyQt5 import QtCore, QtGui, QtWidgets, uic

class ChooseTargetLocaleDialog(QtWidgets.QDialog):
    """
    Doc String for ChooseTargetLocaleDialog.
    """
    def __init__(self, *args, **kwargs):
        super(ChooseTargetLocaleDialog, self).__init__(*args, **kwargs)
        uic.loadUi('ChooseTargetLocaleDialog.ui', self)