import os
from shutil import copyfile
from lxml import etree as ET
import translators as ts
import fnmatch
import subprocess
from PyQt5 import QtCore
from concurrent.futures import ThreadPoolExecutor

from .main import cache
from .languages import langs
from .APKUtils import *
from ..Ui.TranslateView import TranslateView

frameworkDirNames = {'framework', 'system-framework', 'priv-app', 'app'}
frameworkFileName = 'framework-res.apk'


class _BaseData(object):
    """
    Description for _BaseData.
    """
    def __init__(self,
                 path,
                 target_lang,
                 *args,
                 dest=None,
                 additional_langs=None,
                 **kwargs,
                 ):
        super(_BaseData, self).__init__(*args, **kwargs)
        assert os.path.exists(path), f'The path: {path} does not exists.'
        self.path = os.path.abspath(os.path.normpath(path))
        self.dest = dest
        self.target_lang = target_lang
        self.additional_langs = additional_langs

        self.name = os.path.basename(path)

    def add_language(self, lang):
        pass

    def _open(self):
        pass

    def save(self):
        pass

    def _auto_translate(self, text):
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
               'x', ]
        translated = ts.google(text, 'auto', self.target_lang_code)
        for i in fmt:
            translated = translated.replace(f'% {i}', f' %{i}')
        return translated

    @property
    def target_lang_code(self):
        return langs[self.target_lang]

class _BaseTree(_BaseData):
    """
    A basic tree of translation data.
    """

    def __init__(self, *args, frameworks=None, **kwargs):
        self.children = []
        self.frameworks = frameworks if frameworks else []
        super(_BaseTree, self).__init__(*args, **kwargs)

    def get_children(self):
        return self.children

    def add_child(self, arg):
        pass

    def build(self):
        pass

    def save(self):
        for child in self.get_children():
            child.save()

    @property
    def data(self):
        for child in self.get_children():
            for i in child.data:
                yield i

class Xml(_BaseData):
    """
    Description for Xml.
    """

    def __init__(self, *args, **kwargs):
        super(Xml, self).__init__(*args, **kwargs)
        self._open()

    def _open(self):
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
                entry['Translation'] = dstparent[idx] if dstparent is not None else None
            entry['element'] = element
            entry['Origin'] = element.text
            entry['Translation'] = entry['Translation'].text if entry['Translation'] is not None else entry['Origin']
            entry['keep'] = entry['Translation'] is None
            l.append(entry)
        self.data = l

    def save(self):
        if not self.data:
            return

        # Initialize
        xml = self.data[0]['element'].getroottree()
        tree_items = {}

        # Start loop...
        for i in self.data:
            el = i['element']
            if i['keep']:
                parent = el.getparent()
                if el.tag == 'item':
                    # This is a plural or a string-array. We save them for later care.
                    tree_items[parent] = tree_items[parent] + [el] if parent in tree_items else [el]
                    el.text = i['Origin']
                else:
                    # This is an ordinary string element. We can safely remove it.
                    el.getparent().remove(el)
            else:
                el.text = i['Translation']

        # Now we take care of plurals and string-arrays
        for parent, items in tree_items.items():
            if len(items) == len(parent.items()[0]):
                parent.getparent().remove(parent)

        if not xml.findall('//'):
            # New xml is empty. Remove the old, if exists.
            os.remove(self.dest) if os.path.exists(self.dest) else None
        else:
            xml.write(self.dest, xml_declaration=True, encoding="UTF-8")

        # Ropen (for xml elements reload)
        self._open()

class Apk(_BaseTree):
    """
    Description for Apk.
    """
    def __init__(self, *args, **kwargs):
        super(Apk, self).__init__(*args, **kwargs)

        self._values_dir = str()
        self._dest_lang_dir = str()
        self._xml_names = []

        self._open()

    def _open(self):
        if not os.path.isdir(self.path):
            self._decompile()
        (self._values_dir,
         self._dest_lang_dir,
         self._xml_names) = getAPKLang(self.path, self.target_lang_code)
        self._open_dir()

    def _decompile(self):
        ret, out, dest = decompileAPK(self.path, frameworks=self.frameworks)
        assert ret == 0, f'Could not decompile {self.path}\n reason: {out.decode()}\n'
        self.path, self.dest = dest, self.path

    def _open_dir(self):
        self.add_children(self._xml_names)

    def add_children(self, names):
        for name in names:
            self.add_child(name)

    def add_child(self, name):
        if name in self.get_children():
            return
        origin_xml = os.path.join(self._values_dir, name)
        dest_xml = os.path.join(self._dest_lang_dir, name)
        xml = Xml(
            path=origin_xml,
            dest=dest_xml,
            target_lang=self.target_lang,
        )
        self.children.append(xml)

    def build(self):
        print(self.path)
        ret, out, outpath = recompileAPK(self.path, os.path.dirname(self.dest), self.frameworks)
        assert ret == 0, f'Could not rrecompile {self.path}\n reason: {out.decode()}\n'

    @staticmethod
    def is_decompiled_apk(path):
        return 'apktool.yml' in os.listdir(path)

class Rom(_BaseTree):
    """
    Description for Rom.
    """

    def __init__(self, *args, **kwargs):
        super(Rom, self).__init__(*args, **kwargs)
        assert os.path.isdir(self.path), 'Rom path must be a directory (got a file).'
        self._open()

    def _open(self):
        frameworks = findFile(frameworkFileName, self.path)
        self.frameworks += frameworks
        apks = findFile('*.apk', self.path) + findFile(f'*.apk{DECOMPILED_SUFFIX}', self.path)
        for apk in apks:
            self.add_child(apk)

    def add_child(self, path):
        self.children.append(Apk(
            path=path,
            target_lang=self.target_lang,
            dest=self.dest,
            additional_langs=self.additional_langs,
            frameworks=self.frameworks,
        ))

    def build(self):
        for apk in self.get_children():
            apk.build()

def findFile(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

