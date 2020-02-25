import os
from PyQt5 import QtGui

DIR = os.path.join(os.path.dirname(__file__))

xmlIcon = lambda : QtGui.QIcon(os.path.join(DIR, 'icons', 'xml.png'))
apkIcon = lambda : QtGui.QIcon(os.path.join(DIR, 'icons', 'apk.png'))
romIcon = lambda : QtGui.QIcon(os.path.join(DIR, 'icons', 'rom.png'))