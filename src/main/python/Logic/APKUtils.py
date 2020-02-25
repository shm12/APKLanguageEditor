import os
import random
import string
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
    return [i for i in l if isElementTranslatable(i) and i.tag in ('item', 'string')]

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

def decompileAPK(path, outdir='', frameworks=[]):

    # Dest path
    newDirName = os.path.basename(path) + DECOMPILED_SUFFIX
    destPath = os.path.join(outdir, newDirName) if outdir else path + DECOMPILED_SUFFIX
    installFrameworks(frameworks)  

    # Run
    cmd = f'{JAVA} -jar {APKTOOL} d {path} -f -o {destPath}'
    ret = os.system(cmd)
    # return
    return ret, destPath

def installFrameworks(frameworks):
    for f in frameworks:
        os.system(f'{JAVA} -jar {APKTOOL} if {f}')

def recompileAPK(path, outdir='', frameworks=[]):

    # Dest path
    path = os.path.normpath(path)
    apkName = os.path.basename(path)[:-len(DECOMPILED_SUFFIX)]
    destPath = os.path.join(outdir, apkName) if outdir else apkName
    destPath = outdir
    installFrameworks(frameworks)  

    # Run
    cmd = f'{JAVA} -jar {APKTOOL} b {path} -o {destPath}'
    ret = os.system(cmd)

    # return
    return ret, destPath

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