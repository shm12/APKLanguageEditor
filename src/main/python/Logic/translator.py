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
from concurrent.futures import ThreadPoolExecutor

DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(DIR, '..'))

from Logic.main import cache
from Logic.languages import langs
from Logic.APKUtils import *
from Ui.TranslateView import TranslateView
import Ui.PickLanguageDialog as langOptions
# from .common import apkToolPath

t = QtCore.QThreadPool()
t.setMaxThreadCount(1)
# t = ThreadPoolExecutor(max_workers=5)

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
                frameworks=[],
                newLang=None,
                destPath=None,
                parent=None,
                **kwargs):
        # self.moveTo
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
        # self.newLang = 'Hebrew'

        self.path = path
        self.dest = None
        self.name = os.path.basename(path)
        self.dest = destPath
        self.xml = []
        self.xmls = []
        self.apks = []
        self.frameworks = frameworks
        self.parent = parent

        # Threads things
        self.threadpool = t
        # self.threadpool = 
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
    
    def _decodeFinishCallback(self, *args, **kwargs):
        self.decodeFinished.emit(*args, **kwargs)

    def openDir(self, path):
        if 'apktool.yml' in os.listdir(path):
            self.openAPKDir(path)
        else:
            self.openRomDir(path)
    
    def test(self, s):
        print('\n\n', s, '\n\n')

    def openApk(self, path, frameworks=[]):
        # Are we need to decompile it?
        self.dest = path
        if cache.getDecompiled(path):
            self.path = cache.getDecompiled(path)
            return self.openAPKDir(cache.getDecompiled(path))
    
        if os.path.exists(path + DECOMPILED_SUFFIX):
            self.path = path + DECOMPILED_SUFFIX
            return self.openAPKDir(path + DECOMPILED_SUFFIX)
        
        # We need to decompile it!
        cdir = cache.getRandomCacheDir(prefix='apk')

        # s = WorkerSignals()
        thread = WorkerWrapper(target=decompileAPK, pool=self.threadpool,
                        tar_args=(path, cdir),
                        tar_kwargs={'frameworks': frameworks},)
                        # signals=s)
        # print(thread.signals.finishSignal)
        # thread.finishSignal.connect(self.decompileReturn)
        thread.finishSignal.connect(lambda *args, **kwargs: self.decompileReturn(*args, **kwargs))
        thread.finishEmptySignal.connect(self.test)
        thread.start()
                        # callbackSignal=self.decodeFinished,)
                        # callback=self.decompileReturn)
        # self.threadpool.start(thread)
        # Continue open the apk in self.decompileReturn

    def decompileReturn(self, target, args, kwargs, ret):
        print('return from decompile!!!\n\n\n\n\n\n')
        print(ret)
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
        self.path = path
        self.parent.apks.append(self) if self.parent else None
        langCode = langs[self.newLang]
        originDir, destDir, xmls = getAPKLang(path, langCode)
        # print(xmls)
        for xml in xmls:
            originXml = os.path.join(originDir, xml)
            print(originXml)
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
                            #  frameworks=frameworks,
                            #  newLang=self.newLang,
                            #  setupUi=False,
                             parent=self)
        
        for apkPath in findFile(f'*.apk{DECOMPILED_SUFFIX}', path):
            apkPath = apkPath[:-len(DECOMPILED_SUFFIX)]
            if apkPath not in apkFiles:
                apk = Translator(path=apkPath,)
                                #  frameworks=frameworks,
                                #  newLang=self.newLang,
                                #  setupUi=False,
                                #  parent=self)


    def openXml(self, path):
        print(path)
        self.parent.xmls.append(self) if self.parent else None
        #print(f'opening xml {path}')
        # if self.langPickRet and (not self.langPickRet['Exists'] or \
        #        self.langPickRet['onExists'] == langOptions.CREATE):

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
                # if 
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
            entry['Translation'] = entry['Translation'].text if entry['Translation'] is not None else entry['Origin']
            # print(entry['Translation'])
            entry['keep'] = entry['Translation'] is None
            l.append(entry)
        # print(l)
        self.data = l
    
    def getChildren(self):
        if self.apks:
            return self.apks
        elif self.xmls:
            return self.xmls
        return []

    def _translate(self, text):
        return trans(text, langs[self.newLang])

    def saveData(self):
        # return
        children = self.getChildren()
        if children:
            for child in children:
                child.saveData()
        else:
            data = list(self.data)
            if not data:
                return
            xml = data[0]['element'].getroottree()
            treeItems = {}
            for i in data:
                el = i['element']
                if i['keep']:
                    parent = el.getparent()
                    if el.tag == 'item':
                        # We inside a plural or a string-array. We save them for later.
                        # print(el.text)
                        treeItems[parent] = treeItems[parent] + [el] if parent in treeItems else [el]
                        el.text = i['Origin']
                    else:
                        # This is an ordinary string element. We can safely remove it.
                        el.getparent().remove(el)
                else:
                    el.text = i['Translation']
            
            # Now we take care of plurals and string-arrays
            for parent, items in treeItems.items():
                if len(items) == len(parent.items()[0]):
                    parent.getparent().remove(parent)
                else:
                    print('preserving' )
            
            if not self.dest:
                self.dest = self.getNewXMLPath(getRecommendedXMLName(self.path, langs[self.newLang]))
                if not self.dest:
                    return
            else:
                print(self.dest)
                if not xml.findall('//'):
                    # New xml is empty. Remove the old, if exists.
                    os.remove(self.dest) if os.path.exists(self.dest) else None
                else:
                    xml.write(self.dest, xml_declaration=True, encoding="UTF-8")
        self.readData() if not self.getChildren() else None
    
    def rebuild(self):
        # And What if this is not an apk file, but a rom or a xml??
        # if not self.getChildren():
        #     return
        for apk in self.apks:
            apk.rebuild()
        if not self.xmls:
            return
        
        # Build!
        if not self.dest:
            self.dest = self.getNewAPKPath(os.path.join(os.path.dirname(self.path), self.name))
            if not self.dest:
                return
        
        print('building', self.path, 'to', self.dest)
        # recompileAPK(self.path, self.dest, self.frameworks)

        thread = WorkerWrapper(target=recompileAPK, pool=self.threadpool,
                        tar_args=(self.path, self.dest, self.frameworks),)
                        # signals=s)
        # print(thread.signals.finishSignal)
        # thread.finishSignal.connect(self.decompileReturn)
        thread.finishSignal.connect(lambda *args, **kwargs: self.buildReturn(*args, **kwargs))
        thread.finishEmptySignal.connect(self.test)
        thread.start()
    
    def closeEvent(self, e):
        print('closeing')
        self.saveData()
        cache.save()
        e.accept()
    
    def buildReturn(self, target, args, kwargs, ret):
        ret, dstpath = ret
        if ret != 0:
            self.buildError(self.path, self.dest)

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



class WorkerWrapper(QtCore.QObject):
    """
    Description for WorkerWrapper.
    """
    finishSignal = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject')
    finishEmptySignal = QtCore.pyqtSignal(str)

    def __init__(self,target, pool, *args, tar_args=() ,tar_kwargs={}, **kwargs):
        super(WorkerWrapper, self).__init__(*args, **kwargs)
        self.pool = pool
        self.worker = Worker(target=target,tar_args=tar_args,tar_kwargs=tar_kwargs, callback=self.callback)
        self.target = target
        self.args = tar_args
        self.kwargs = tar_kwargs
    
    def exec_(self):
        ret = self.target(*self.args, **self.kwargs)
        print('emitting finish signals')
        self.finishSignal.emit(ret)
        self.finishEmptySignal.emit()

    def start(self):
        # self.pool.submit(self.exec_)
        self.pool.start(self.worker)
    
    def callback(self, *args):
        self.finishSignal.emit(*args)
        self.finishEmptySignal.emit('hdhhfgh')



class WorkerSignals(QtCore.QObject):
    """
    Description for WorkerSignals.
    """
    finishSignal = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject')
    finishEmptySignal = QtCore.pyqtSignal()

# class WorkerSignals(object):
#     """
#     Description for WorkerSignals.
#     """
#     def __init__(self, *args, **kwargs):
#         super(WorkerSignals, self).__init__(*args, **kwargs)
#         self.finishSignal = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject')
#         self.finishEmptySignal = QtCore.pyqtSignal()


class Worker(QtCore.QRunnable):

    def __init__(self, *args, target,callback, tar_args=() ,tar_kwargs={}, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)
        self.setAutoDelete(True)
        self.target = target
        self.args = tar_args
        self.kwargs = tar_kwargs
        self.signals = WorkerSignals()
        # self.signals = signals
        # self.callback = {
        #     'callbackSignal' : callbackSignal,
        #     'callBackEmptySignal': callBackEmptySignal,
        #     'callback' : callback
        # }
        # self.callbackSignal = callbackSignal
        # self.callBackEmptySignal = callBackEmptySignal
        self.callback = callback
    
    @QtCore.pyqtSlot()
    def run(self):
        ret = self.target(*self.args, **self.kwargs)
        self.callback(self.target,
                                       self.args,
                                       self.kwargs,
                                       ret)
        # print(id(self.signals.finishSignal))

        # self.signals.finishSignal.emit(self.target,
        #                                self.args,
        #                                self.kwargs,
        #                                ret)
        # self.signals.finishEmptySignal.emit()
        # self.callback['callback'](self.target,
        #               self.args,
        #               self.kwargs,
        #               ret) if self.callback['callback'] else None
        # self.callback['callbackSignal'].emit(self.target,
        #                          self.args,
        #                          self.kwargs,
        #                          ret) if self.callback['callbackSignal'] else None
        # self.callback['callBackEmptySignal'].emit() if self.callback['callBackEmptySignal'] else None
        # # self.callback(self.target,
        #               self.args,
        #               self.kwargs,
        #               ret) if self.callback else None
        # print(self.callbackSignal)
        # self.callbackSignal.emit(self.target,
        #                          self.args,
        #                          self.kwargs,
        #                          ret) if self.callbackSignal else None
        # self.callBackEmptySignal.emit() if self.callBackEmptySignal else None

def findFile(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result
