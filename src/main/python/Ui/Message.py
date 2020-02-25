import os
from PyQt5 import QtCore, QtGui, QtWidgets
from Ui.UiLoader import getUiClass
from appctx import ApplicationContext

# UI_FILE = path.abspath(path.join(path.dirname(__file__), 'Message.ui'))
UI_FILE = ApplicationContext.get_resource(os.path.join('ui', 'Message.ui'))

class Message(getUiClass(UI_FILE)):

    def __init__(self, *args, message='An error occure', **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        self.message = message
    
    @property
    def message(self):
        return self._message
    
    @message.setter
    def message(self, message):
        self._message = message
        self.label.setText(self._message)
        self.adjustSize()
