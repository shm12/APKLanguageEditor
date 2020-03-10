import os
import random
import string
import subprocess
from lxml import etree as ET


DECOMPILED_SUFFIX = '-decompiled'
APKTOOL = 'C:\\Users\\shmbi\\Documents\\Translate_Qin1SPlus\\resources\\apktool_2.4.1.jar'
# APKTOOL = 'apktool_2.4.1.jar'
APKSIGNER = 'C:\\Users\\shmbi\\Downloads\\apk-editor-studio_win32_1.3.1\\APK Editor Studio v1.3.1\\tools\\apksigner.jar'
keystore = ''
JAVA = '"C:\\Program Files (x86)\\Common Files\\Oracle\\Java\\javapath\\java"'
# JAVA = 'java'


def isFileOfType(path, typ):
    fileName = os.path.basename(path)
    splited = fileName.split('.')
    return len(splited) > 1 and \
        splited[-1].lower() == typ.lower()


def isElementTranslatable(element):
    return 'translatable' not in element.attrib \
        or element.attrib['translatable'] == 'true'


def getTranslatableXmls(path):
    l = []

    path = os.path.abspath(path)
    for dirpath, dirs, files in os.walk(path):
        for fil in files:
            filepath = os.path.join(dirpath, fil)
            if (isFileOfType(filepath, 'xml')):
                if getXmlTranslatables(filepath):
                    l.append(filepath)
    
    return l


def getXmlTranslatables(path):
    try:
        xml = ET.parse(path)
    except Exception as e:
        print(e)
        return []
    l = xml.findall('string')
    for typ in ('string-array', 'plurals'):
        for item in xml.findall(typ):
            l += item
    return [i for i in l if i.tag in ('item', 'string')]

def getAPKTranslatableXmls(dpath):
    valuesPath = os.path.join(dpath, 'res', 'values')
    if not os.path.exists(os.path.join(dpath, 'res', 'values')):
        return []
    else:
        return getTranslatableXmls(valuesPath)

def getAPKLang(dpath, lang):
    """
    Returns tuple of (default values path, lang values path, [translatable xmls])
    """
    valuesPath = os.path.join(dpath, 'res', 'values')
    if not os.path.exists(os.path.join(dpath, 'res', 'values')):
        return '', '', []
    
    langPath = f'{valuesPath}-{lang}'
    os.mkdir(langPath) if not os.path.exists(langPath) else None
    return valuesPath, langPath, map(os.path.basename, getTranslatableXmls(valuesPath))


def decompileAPK(path, outdir='', frameworks=None, force=False):

    # Dest path
    newDirName = os.path.basename(path) + DECOMPILED_SUFFIX
    destPath = os.path.join(outdir, newDirName) if outdir else path + DECOMPILED_SUFFIX

    if os.path.exists(destPath) and not force:
        return 0, '', destPath

    install_frameworks(frameworks) if frameworks else None

    # Run
    cmd = f'{JAVA} -jar {APKTOOL} d {path} -f -o {destPath}'
    ret, out = run_cmd(cmd)

    # return
    return ret, out, destPath


def install_frameworks(frameworks):
    finall = []
    for f in frameworks:
        finall.append(run_cmd(f'{JAVA} -jar {APKTOOL} if {f}'))
    return finall


def recompileAPK(path, outdir='', frameworks=None):

    # Dest path
    path = os.path.normpath(path)
    basename = os.path.basename(path)
    apk_name = basename[:-len(DECOMPILED_SUFFIX)] if DECOMPILED_SUFFIX in basename else basename
    apk_name = apk_name + '.apk' if apk_name.split('.')[-1] != 'apk' else apk_name
    dest_path = os.path.join(outdir, apk_name) if outdir else os.path.join(os.path.dirname(path), apk_name)

    install_frameworks(frameworks) if frameworks else None

    # Run
    cmd = f'{JAVA} -jar {APKTOOL} b {path} -o {dest_path}'
    ret, out = run_cmd(cmd)

    # return
    return ret, out, dest_path

def run_cmd(cmd):
    print(cmd)
    ret = 0
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        out = e.output
        ret = e.returncode
    return ret, out

def getRecommendedXMLName(path, langCode):
    xmlDir = os.path.dirname(path)
    newXmlBaseName = '.'.join(os.path.basename(path).split('.')[:-1])
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
    return newXmlPath