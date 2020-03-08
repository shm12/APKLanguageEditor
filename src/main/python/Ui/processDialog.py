import os
from PyQt5 import QtGui
from appctx import ApplicationContext
from .UiLoader import getUiClass

_UI_FILE = ApplicationContext.get_resource(os.path.join('ui', 'processDialog.ui'))
_BaseUi = getUiClass(_UI_FILE)


class ProcessDialog(_BaseUi):
    DEFAUL_TITLE = 'Process'
    DEFAUL_MESAGE = 'A work is in process...'
    DEFAUL_ICON = ApplicationContext.get_resource(os.path.join('icons', 'process.png'))

    def __init__(self, *args,
                 title=None,
                 message=None,
                 icon=None,
                 **kwargs):
        kwargs['setupUi'] = True
        super(ProcessDialog, self).__init__(*args, **kwargs)

        # Initialize properties
        self._icon_path = None
        self.ret = None
        self.title = title if title else self.DEFAUL_TITLE
        self.message = message if message else self.DEFAUL_MESAGE
        self.icon = icon if icon else self.DEFAUL_ICON

        self.CancelButton.clicked.connect(self.cancel)
        self.BackgroundButton.clicked.connect(self.background)

    def cancel(self):
        self.ret = 'cancel'
        self.reject()

    def background(self):
        self.ret = 'background'
        self.reject()

    def exec(self):
        self.ret = None
        super(_BaseUi, self).exec()

    def closeEvent(self, e):
        self.cancel()

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

