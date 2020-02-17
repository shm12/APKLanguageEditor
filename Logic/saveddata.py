import os
import sys
import shutil
import appdirs
import json
import string
import random

# from main import AUTHOR, APP_NAME
AUTHOR = 'ShmBia'
APP_NAME = 'APKLanguageEditor'


class BaseData(object):

    DIR = '.'
    FILE = 'data.json'
    DEFAULT_DATA = {}

    def __init__(self, *args, **kwargs):
        super(BaseData, self).__init__(*args, **kwargs)
        self._path = os.path.join(self.DIR, self.FILE)
        print(self.DIR)
        
        # Create data dir if not exists.
        if not os.path.exists(self.DIR):
            os.makedirs(self.DIR)
        
        # Load the data (if exists).
        self._data = json.loads(open(self._path).read()) \
            if os.path.exists(self._path) \
            else self.DEFAULT_DATA
    
    def save(self):
        with open(self._path, 'w') as fil:
            fil.write(json.dumps(self._data))
    

class Settings(BaseData):
    """
    Description for Settings.
    """
    DIR = appdirs.user_config_dir(APP_NAME, AUTHOR)
    FILE = 'settings.json'
    DEFAULT_DATA = {}

class Caching(BaseData):
    """
    Description for Caching.
    """
    DIR = appdirs.user_cache_dir(APP_NAME, AUTHOR)
    FILE = 'cache.json'
    DEFAULT_DATA = {
        'exists': {},
        'open': {},
        'decompiled': {}
    }

    def getRandomCacheDir(self, nameLen=6, prefix=''):
        while True:
            name = ''.join(random.choice(string.ascii_lowercase) for i in range(nameLen))
            name = prefix + '-' + name if prefix else name
            path = os.path.join(self.DIR, name)
            if not os.path.exists(path):
                os.mkdir(path)
                return path

    def addExists(self, lang, origin, translation):
        origin = os.path.abspath(origin)
        translation = os.path.abspath(translation)
        if origin in self._data['exists']:
            if lang in self._data['exists'][origin]:
                self._data['exists'][origin][lang].append(translation)
            else:
                self._data['exists'][origin][lang] = [translation]
        else:
            self._data['exists'][origin] = {lang: [translation]}
    
    def getExists(self, path):
        return [] if not path in self._data['exists'] \
            else self._data['exists'][path]
            
    def addOpen(self, path, data):
        self._data['open'][path] = data
    
    def addDecompiled(self, apkPath, destpath):
        apkPath = os.path.abspath(apkPath)
        destpath = os.path.abspath(destpath)
        self._data['decompiled'][apkPath] = destpath
    
    def getDecompiled(self, apkPath):
        apkPath = os.path.abspath(apkPath)
        print(self.DIR)
        if apkPath in self._data['decompiled']:
            return self._data['decompiled'][apkPath]
        
    
