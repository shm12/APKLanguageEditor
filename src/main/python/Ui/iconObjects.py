import os
from PyQt5 import QtGui
from appctx import ApplicationContext


xmlIcon = lambda : QtGui.QIcon(ApplicationContext.get_resource(os.path.join('icons', 'xml.png')))
apkIcon = lambda : QtGui.QIcon(ApplicationContext.get_resource(os.path.join('icons', 'apk.png')))
romIcon = lambda : QtGui.QIcon(ApplicationContext.get_resource(os.path.join('icons', 'rom.png')))