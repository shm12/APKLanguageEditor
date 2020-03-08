import os
from PyQt5 import QtCore, QtGui, QtWidgets
from Ui.UiLoader import getUiClass
from appctx import ApplicationContext

# UI_FILE = path.abspath(path.join(path.dirname(__file__), 'Message.ui'))
UI_FILE = ApplicationContext.get_resource(os.path.join('ui', 'Message.ui'))

class Message(getUiClass(UI_FILE)):
    DEFAUL_TITLE = 'Attention'
    DEFAUL_MESAGE = 'A message'
    DEFAUL_ICON = ApplicationContext.get_resource(os.path.join('icons', 'attention.png'))

    def __init__(self, *args,
                 title=None,
                 message=None,
                 icon=None,
                 **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        # Initialize properties
        self._icon_path = None
        self.ret = None
        self.title = title if title else self.DEFAUL_TITLE
        self.message = message if message else self.DEFAUL_MESAGE
        self.icon = icon if icon else self.DEFAUL_ICON

    @property
    def message(self):
        return self.messageLable.text()

    @message.setter
    def message(self, message):
        self.messageLable.setText(message)
        self.adjustSize()

    @property
    def title(self):
        return self.windowTitle()

    @title.setter
    def title(self, title):
        self.setWindowTitle(title)

    @property
    def icon(self):
        return self._icon_path

    @icon.setter
    def icon(self, path):
        self._icon_path = path
        self.iconLable.setPixmap(QtGui.QPixmap(path))

