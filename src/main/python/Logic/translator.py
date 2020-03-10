import os
import translators as ts
import fnmatch
from typing import Union

from .languages import langs
from .APKUtils import *

frameworkDirNames = {'framework', 'system-framework', 'priv-app', 'app'}
frameworkFileName = 'framework-res.apk'


class DataKeys:
    TRANSLATION = 'Translation'
    ORIGIN = 'Origin'
    KEEP = 'keep'
    ELEMENT = 'element'

# class CustomList(list):
#     def __getitem__(self, item):
#         return self.__getitem__(item)
#
#     def __setitem__(self, key, value):
#         return self.__setitem__(key, value)
#
#     def __len__(self):
#         return self.__len__()
#


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
                 parent_el=None,
                 **kwargs,
                 ):
        """

        :param path: The path.
        :param target_lang: Target language for translation.
        :param *args: additional argument to pass on.
        :param dest: Destination path.
        :param additional_langs: additional languages to parse (except for the default).
        :param parent_el: The parent translation element of the object (if exists)
        :param kwargs: additional keyword args
        """
        super(_BaseData, self).__init__(*args, **kwargs)
        assert os.path.exists(path), f'The path: {path} does not exists.'
        self.path = os.path.abspath(os.path.normpath(path))
        self.dest = dest
        self.target_lang = target_lang
        self.additional_langs = additional_langs
        self._data = []

        self.parent_el = None
        self.name = os.path.basename(path)
        self._set_parent(parent_el) if parent_el else None


        self._open()

    def _set_parent(self, parent):
        if not isinstance(parent, _BaseTree):
            raise TypeError(f'Trying to set parent of type {type(parent)}')
        self.parent_el.remove_child(self) if self.parent_el else None
        self.parent_el = parent
        self.parent_el.children.append(self)

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

    def auto_translate_item(self, item: Union[dict, int]):
        item = self.data[item] if type(item) is int else item
        if not self.item_is_translatable(item):
            return
        if item[DataKeys.ORIGIN]:
            item[DataKeys.TRANSLATION] = self._auto_translate(item[DataKeys.ORIGIN])
            item[DataKeys.KEEP] = False
        else:
            item[DataKeys.TRANSLATION] = None
            item[DataKeys.KEEP] = False

    def keep_item(self, item: Union[dict, int]):
        item = self.data[item] if type(item) is int else item
        item[DataKeys.KEEP] = True
        item[DataKeys.TRANSLATION] = None

    def set_item_untraslatable(self, item: Union[dict, int]):
        item = self.data[item] if type(item) is int else item
        element = item['element']
        element.attrib['translatable'] = 'false'

    def set_item_translatable(self, item: Union[dict, int]):
        item = self.data[item] if type(item) is int else item
        element = item['element']
        element.attrib['translatable'] = 'true'

    def item_is_translatable(self, item: Union[dict, int]):
        item = self.data[item] if type(item) is int else item
        element = item['element']
        return 'translatable' not in element.attrib or element.attrib['translatable'] == 'true'

    def _data_changed(self):
        self.parent_el._child_data_changed(self) if self.parent_el else None
        
    @property
    def target_lang_code(self):
        return langs[self.target_lang]

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
        self._data_changed()

    def iter_data(self):
        for i in self._data:
            yield i


class _BaseTree(_BaseData):
    """
    A basic tree of translation data (may be an apk or a rom).
    """
    CHILD_TYPE = _BaseData

    def __init__(self, *args, frameworks=None, **kwargs):
        self.children = []
        self.frameworks = frameworks if frameworks else []
        super(_BaseTree, self).__init__(*args, **kwargs)

    def get_children(self):
        return self.children

    def add_child(self, path, *args, **kwargs):
        child = self.CHILD_TYPE(
            *args,
            path=path,
            target_lang=self.target_lang,
            additional_langs=self.additional_langs,
            parent_el=self,
            **kwargs,
        )
        return child

    def remove_child(self, child):
        assert child in self.get_children(), 'Trying to remove child that not exists'
        self.children.remove(child)

    def build(self):
        pass

    def save(self):
        for child in self.get_children():
            child.save()

    def _child_data_changed(self, *args, **kwargs):
        self.data = list(self.iter_data())

    def iter_data(self):
        for child in self.get_children():
            for i in child.iter_data():
                yield i


class Xml(_BaseData):
    """
    Description for Xml.
    """
    def __init__(self, *args, **kwargs):
        super(Xml, self).__init__(*args, **kwargs)
        self.untranslatables = []

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
            entry['Translation'] = entry['Translation'].text if entry['Translation'] is not None else None
            entry['keep'] = entry['Translation'] is None
            l.append(entry)
        self.data = l

    def save(self):
        if not self.data:
            return

        # Initialize
        xml = self.data[0]['element'].getroottree()

        # Save untranslatables
        untranslatable_tree_items = {}
        untranslatable_items = []
        for i in self.data:
            el = i['element']
            if 'translatable' in el.attrib and el.attrib['translatable'] == 'false':
                parent = el.getparent()
                if el.tag == 'item':
                    # This is a plural or a string-array. We save them for later care.
                    if parent in untranslatable_tree_items:
                        untranslatable_tree_items[parent] += [el]
                    else:
                        untranslatable_tree_items[parent] = [el]
                else:
                    untranslatable_items.append(el)

                self.data.remove(i)

        # Now we take care of plurals and string-arrays
        for parent, items in untranslatable_tree_items.items():
            if len(items) == len(parent.items()[0]):
                untranslatable_items.append(parent)

        xml.write(self.path, xml_declaration=True, encoding="UTF-8")

        # Clear untranslatables from dest
        for element in untranslatable_items:
            element.getparent().remove(element)

        # Clear apktool dummy items
        for i in xml.findall('//item'):
            if 'name' in i.attrib and i.attrib['name'].startswith('APKTOOL_DUMMY'):
                i.getparent().remove(i)

        # Save to dest
        tree_items = {}
        for i in self.data:
            el = i['element']
            if i['keep'] or i['Translation'] is None:
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

        # Reload data (for the xml elements)
        self._open()


class Apk(_BaseTree):
    """
    Description for Apk.
    """
    CHILD_TYPE = Xml

    def __init__(self, *args, **kwargs):
        super(Apk, self).__init__(*args, **kwargs)
        self.name = self.name[:-len(DECOMPILED_SUFFIX)] if self.name[-len(DECOMPILED_SUFFIX):] == DECOMPILED_SUFFIX else self.name

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
            self.add_child(name=name)

    def add_child(self, name, *args, **kwargs):
        if name in [i.name for i in self.get_children()]:
            return
        origin_xml = os.path.join(self._values_dir, name)
        dest_xml = os.path.join(self._dest_lang_dir, name)
        return super(Apk, self).add_child(
            *args,
            path=origin_xml,
            dest=dest_xml,
            **kwargs
        )

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
    CHILD_TYPE = Apk

    def __init__(self, *args, **kwargs):
        super(Rom, self).__init__(*args, **kwargs)
        assert os.path.isdir(self.path), 'Rom path must be a directory (got a file).'

    def _open(self):
        frameworks = findFile(frameworkFileName, self.path)
        self.frameworks += frameworks
        apks = findFile('*.apk', self.path)
        decompiled = findFile(f'*.apk{DECOMPILED_SUFFIX}', self.path)
        apks = apks + [apk for apk in decompiled if apk[:-len(DECOMPILED_SUFFIX)] not in apks]
        for apk in apks:
            self.add_child(apk)

    def add_child(self, path, *args, **kwargs):
        return super(Rom, self).add_child(
            *args,
            path=path,
            frameworks=self.frameworks,
            **kwargs
        )

    def build(self):
        for apk in self.get_children():
            apk.build()


def findFile(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files + dirs:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

