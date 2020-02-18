import sys
import os
from shutil import copyfile
import xml.etree.ElementTree as ET
import translators as ts
import urllib
import requests
import json
from PyQt5 import QtCore

DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(DIR, '..'))

from .main import cache
from .languages import langs
from .APKUtils import *
from Ui.TranslateView import TranslateView, CustomQTThread
import Ui.PickLanguageDialog as langOptions
# from .common import apkToolPath

class Translator(TranslateView):

    XML = 0
    APK = 1
    DIR = 2
    APK_LIST = 3

    decodeFinished = QtCore.pyqtSignal('PyQt_PyObject',
                                 'PyQt_PyObject',
                                 'PyQt_PyObject',
                                 'PyQt_PyObject',arguments=['Target',
                                                            'args',
                                                            'kwargs',
                                                            'Return'])

    def __init__(self, *args, path, framework=None, newLang=None, **kwargs):
        super(Translator, self).__init__(*args, **kwargs)

        self.newLang = newLang
        self.path = path
        self.framework = framework
        self.xmls = []
        self.apks = []
        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(5)
        self.decodeFinished.connect(self.decompileReturn)
        # self.newLang = 'Hebrew'

        if os.path.isdir(path):
            self.openDir(path)
        elif isFileOfType(path, 'apk'):
            self.openApk(path)
        elif isFileOfType(path, 'xml'):
            self.openXml(path)
        else:
            raise Exception('Cannot open {}'.format(path))
    
    def openDir(self, path):
        if 'apktool.yml' in os.listdir(path):
            self.openAPKDir(path)
        else:
            self.openRomDir(path)

    def openApk(self, path, framework=None):
        if cache.getDecompiled(path):
            return self.openAPKDir(cache.getDecompiled(path))
    
        if os.path.exists(path + DECOMPILED_SUFFIX):
            return self.openAPKDir(path + DECOMPILED_SUFFIX)
        
        cdir = cache.getRandomCacheDir(prefix='apk')

        thread = Worker(target=decompileAPK,
                        tar_args=(path, cdir),
                        tar_kwargs={'framework': framework},
                        callbackSignal=self.decodeFinished)
        # thread.finished.connect(self.decompileReturn)
        self.threadpool.start(thread)

    def decompileReturn(self, target, args, kwargs, ret):
        path = args[0] if args else kwargs['path']
        err, dpath = ret
        if err:
            self.errOpen(path)
        
        cache.addDecompiled(path, dpath)
        cache.save()
        self.openAPKDir(dpath)

    def openAPKDir(self, path):
        print('opening path')
        if not self.newLang:
            self.pickLang(default='Hebrew')
        self.newLang = self.langPickRet['Lang']
        langCode = langs[self.newLang]

        originDir, destDir, xmls = getAPKLang(path, langCode)
        for xml in xmls:
            originXml = os.path.join(originDir, xml)
            destXml = os.path.join(destDir, xml)

            self.xmls.append((originXml, destXml))
        try:
            self.translationData = self.readData()
        except Exception as e:
            print(e)
            print(self.xmls)


    def openRomDir(self, path):
        pass
    
    def openXml(self, path):
        if not self.newLang:
            self.pickLang(existLangs=cache.getExists(path), onExist=langOptions.EDIT)
        self.newLang = self.langPickRet['Lang']
        
        if not self.langPickRet['Exists'] or self.langPickRet['onExists'] == langOptions.CREATE:
            xmlDir = os.path.dirname(path)
            newXmlBaseName = '.'.join(os.path.basename(path).split('.')[:-1])
            langCode = langs[self.langPickRet['Lang']]
            newXmlName = f'{newXmlBaseName}.{langCode}.xml'
            i = 0
            while(True):
                newXmlName = newXmlName if not i else f'{newXmlBaseName}.{langCode}({i}).xml'
                newXmlPath = os.path.join(xmlDir, newXmlName)
                if os.path.exists(newXmlPath):
                    i += 1
                    continue
                else:
                    break
            copyfile(path, os.path.join(xmlDir, newXmlName))
            cache.addExists(self.newLang, path, newXmlPath)
        else:
            newXmlPath = cache.getExists(path)[self.newLang][0]
            pass
        self.xmls.append((path, newXmlPath))
        self.translationData = self.readData()
        



    def _translate(self, data):
        for text in data:
            trnaslated = trans(text, langs[self.newLang])
            yield trnaslated
            if type(trnaslated) == dict:
                break
        # return [trans(i, langs[self.newLang]) for i in data]

    

    def readXml(self, path):
        return [i.text for i in getXmlTranslatables(path)]

    def readData(self):
        final_list = [[],[]]
        for origin, translation in self.xmls:
            origData = self.readXml(origin)
            final_list[0] += origData
            final_list[1] += self.readXml(translation) if os.path.exists(translation) else origData
        return final_list


    def saveData(self):
        newData = self.translationData
        translate = iter(newData[1])
        for originXml, translateXML in self.xmls:
            xml = ET.parse(originXml)
            print(f'Saving to {translateXML}...')
            for item in xml.iter():
                if not item.tag == 'string':
                    continue
                item.text = next(translate)
            
            xml.write(translateXML)

    def closeEvent(self, e):
        self.saveData()
        cache.save()
        e.accept()

def trans(string, outLang='en'):
    fmt = ['a',
            'b',
            'c',
            'd',
            'e',
            'f',
            'g',
            'h',
            'n',
            'o',
            's',
            't',
            'x',]
    try:
        translated = ts.google(string, 'auto', outLang)
        for i in fmt:
            translated = translated.replace(f'% {i}', f' %{i}')
        return translated
    except Exception as e:
        print(e)
        return {'error': e}


def trans2(string, outLang):
    from googletrans import Translator
    translator = Translator()
    return translator.translate(string, dest=outLang).text


class Worker(QtCore.QRunnable):

    def __init__(self, *args, target, tar_args=() ,tar_kwargs={}, callbackSignal=None, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)
        self.target = target
        self.args = tar_args
        self.kwargs = tar_kwargs
        self.callbackSignal = callbackSignal
    
    @QtCore.pyqtSlot()
    def run(self):
        ret = self.target(*self.args, **self.kwargs)
        self.callbackSignal.emit(self.target,
                                 self.args,
                                 self.kwargs,
                                 ret) if self.callbackSignal else None

