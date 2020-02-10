import os
from ..Ui.cutomWidgets import TranslateView
from .common import apkToolPath

def isFileOfType(path, typ):
    return path.split('.')[-1].lower() == typ.lower()

class Translator(TranslateView):

    XML = 0
    APK = 1
    DIR = 2
    APK_LIST = 3

    def __init__(self, path, newLocale, *args, **kwargs):
        super(Translator, self).__init__(*args, **kwargs)

        self.newLocale = newLocale
        self.path = path

        if os.path.isdir(path):
            self.openDir(path)
        elif isFileOfType(path, 'apk'):
            self.openApk(path)
        elif isFileOfType(path, 'xml'):
            self.openXml(path)
        else:
            raise Exception('Cannot open {}'.format(path))

        self.addLocale()
        self.readData()

    def openDir(self, path):
        pass
    
    def openXml(self, path):
        pass

    def openApk(self, path):
        pass

    def readData(self):
        pass

    def saveData(self):
        pass


