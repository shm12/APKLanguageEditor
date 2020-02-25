from os import path
import sys
DIR = path.join(path.dirname(__file__))
sys.path.append(path.join(DIR, '..'))

from PyQt5 import QtCore, QtGui, QtWidgets
from UiLoader import getUiClass

UI_FILE = path.abspath(path.join(path.dirname(__file__), 'Message.ui'))

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
