import sys
import os
from shutil import copyfile
from lxml import etree as ET
import translators as ts
import urllib
import requests
import json
import fnmatch
from PyQt5 import QtCore

DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(DIR, '..'))

from .main import cache
from .languages import langs
from .APKUtils import *
from Ui.TranslateView import TranslateView
import Ui.PickLanguageDialog as langOptions
# from .common import apkToolPath

t = QtCore.QThreadPool()
t.setMaxThreadCount(1)

frameworkDirNames = {'framework', 'system-framework', 'priv-app', 'app'}
frameworkFileName = 'framework-res.apk'

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

    def __init__(self,
                *args,
                path,
                frameworks=None,
                newLang=None,
                destPath=None,
                parent=None,
                **kwargs):
        super(Translator, self).__init__(*args, **kwargs, parent=parent)

        # Ask for destiniation language and return if canceled
        if newLang:
            self.newLang = newLang
            self.langPickRet = None
        else:
            self.pickLang(existLangs=cache.getExists(path),
                          onExist=langOptions.EDIT)
        if not self.newLang:
            return

        self.path = path
        self.name = os.path.basename(path)
        self.dest = destPath
        self.xml = []
        self.xmls = []
        self.apks = []
        self.frameworks = frameworks
        self.parent = parent

        # Threads things
        self.threadpool = t
        # self.threadpool.setMaxThreadCount(5)
        self.decodeFinished.connect(self.decompileReturn)

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

    def openApk(self, path, frameworks=[]):
        # Are we need to decompile it?
        if cache.getDecompiled(path):
            return self.openAPKDir(cache.getDecompiled(path))
    
        if os.path.exists(path + DECOMPILED_SUFFIX):
            return self.openAPKDir(path + DECOMPILED_SUFFIX)
        
        # We need to decompile it!
        cdir = cache.getRandomCacheDir(prefix='apk')

        thread = Worker(target=decompileAPK,
                        tar_args=(path, cdir),
                        tar_kwargs={'frameworks': frameworks},
                        callbackSignal=self.decodeFinished,
                        callback=self.decompileReturn)
        self.threadpool.start(thread)
        # Continue open the apk in self.decompileReturn

    def decompileReturn(self, target, args, kwargs, ret):
        path = args[0] if args else kwargs['path']
        err, dpath = ret
        if err:
            self.errOpen(path)
        
        # Save to cache
        cache.addDecompiled(path, dpath)
        cache.save()

        # Continue open
        self.openAPKDir(dpath)

    def openAPKDir(self, path):
        self.parent.apks.append(self) if self.parent else None
        langCode = langs[self.newLang]
        originDir, destDir, xmls = getAPKLang(path, langCode)
        for xml in xmls:
            originXml = os.path.join(originDir, xml)
            destXml = os.path.join(destDir, xml)
            Translator(path=originXml,
                            destPath=destXml,
                            newLang=self.newLang,
                            setupUi=False,
                            parent=self)

    
    def openRomDir(self, path):
        frameworks = findFile(frameworkFileName, path)
        self.frameworks = frameworks
        self.pickLang(default='Hebrew') if not self.newLang else None
        
        apkFiles = findFile('*.apk', path)
        for apkPath in apkFiles:
            apk = Translator(path=apkPath,
                             frameworks=frameworks,
                             newLang=self.newLang,
                             setupUi=False,
                             parent=self)
        
        for apkPath in findFile(f'*.apk{DECOMPILED_SUFFIX}', path):
            apkPath = apkPath[:-len(DECOMPILED_SUFFIX)]
            if apkPath not in apkFiles:
                apk = Translator(path=apkPath,
                                 frameworks=frameworks,
                                 newLang=self.newLang,
                                 setupUi=False,
                                 parent=self)


    def openXml(self, path):
        self.parent.xmls.append(self) if self.parent else None
        #print(f'opening xml {path}')
        # if self.langPickRet and (not self.langPickRet['Exists'] or \
        #        self.langPickRet['onExists'] == langOptions.CREATE):
        #     newXmlPath = None
        #     pass
        #     # xmlDir = os.path.dirname(path)
        #     # newXmlBaseName = '.'.join(os.path.basename(path).split('.')[:-1])
        #     # langCode = langs[self.langPickRet['Lang']]
        #     # newXmlName = f'{newXmlBaseName}.{langCode}.xml'
        #     # i = 0
        #     # while(True):
        #     #     newXmlName = newXmlName if not i else f'{newXmlBaseName}.{langCode}({i}).xml'
        #     #     newXmlPath = os.path.join(xmlDir, newXmlName)
        #     #     if os.path.exists(newXmlPath):
        #     #         i += 1
        #     #         continue
        #     #     else:
        #     #         break
        #     # copyfile(path, os.path.join(xmlDir, newXmlName))
        #     # cache.addExists(self.newLang, path, newXmlPath)
        # else:
        #     newXmlPath = cache.getExists(path)[self.newLang][0]
        # newXmlPath = self.dest
        self.readData()
        pass

    def readData(self):
        dst_xml = ET.parse(self.dest) if (self.dest and os.path.exists(self.dest)) else None
        l = []
        for element in getXmlTranslatables(self.path):
            entry = {}
            if 'name' in element.attrib:
                name = element.attrib['name']
                entry['Name'] = name
                entry['Translation'] = dst_xml.find(f"//{element.tag}[@name='{name}']") if dst_xml else None
            else:
                parent = element.getparent()
                if 'name' not in parent.attrib:
                    print('W: cannot process ', element)
                    continue
                parent_name = parent.attrib['name']
                idx = parent.index(element)
                entry['Name'] = '{0} [{1}]'.format(parent_name, idx)
                dstparent = dst_xml.find(f"//{parent.tag}[@name='{parent_name}']") if dst_xml else None
                entry['Translation'] = dstparent[idx] if dstparent else None
            entry['element'] = element
            entry['Origin'] = element.text
            entry['Translation'] = entry['Translation'].text if entry['Translation'] else None
            entry['keep'] = bool(entry['Translation'])
            l.append(entry)
        self.data = l
    
    def getChildren(self):
        if self.apks:
            return self.apks
        elif self.xmls:
            return self.xmls
        # return None

    def _translate(self, text):
        return trans(text, langs[self.newLang])

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
        # self.saveData()
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

    def __init__(self, *args, target, tar_args=() ,tar_kwargs={}, callbackSignal=None, callBackEmptySignal=None, callback=None, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)
        self.setAutoDelete(True)
        self.target = target
        self.args = tar_args
        self.kwargs = tar_kwargs
        self.callbackSignal = callbackSignal
        self.callBackEmptySignal = callBackEmptySignal
        self.callback = callback
    
    @QtCore.pyqtSlot()
    def run(self):
        ret = self.target(*self.args, **self.kwargs)
        self.callback(self.target,
                      self.args,
                      self.kwargs,
                      ret) if self.callback else None
        self.callbackSignal.emit(self.target,
                                 self.args,
                                 self.kwargs,
                                 ret) if self.callbackSignal else None
        self.callBackEmptySignal.emit() if self.callBackEmptySignal else None

def findFile(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result
