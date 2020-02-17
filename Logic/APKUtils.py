import os
import xml.etree.ElementTree as ET


DECOMPILED_SUFFIX = '-decompiled'
APKTOOL = 'C:\\Users\\shmbi\\Documents\\Translate_Qin1SPlus\\resources\\apktool_2.4.1.jar'
APKSIGNER = 'C:\\Users\\shmbi\\Downloads\\apk-editor-studio_win32_1.3.1\\APK Editor Studio v1.3.1\\tools\\apksigner.jar'
keystore = ''
JAVA = '"C:\\Program Files (x86)\\Common Files\\Oracle\\Java\\javapath\\java"'


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
            l += list(item)
    return [i for i in l if isElementTranslatable(i)]

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

def decompileAPK(path, outdir='', framework=''):

    # Dest path
    newDirName = os.path.basename(path) + DECOMPILED_SUFFIX
    destPath = os.path.join(outdir, newDirName) if outdir else path + DECOMPILED_SUFFIX

    # Temporary change framework resourceses apk name
    if framework:
        fwPath = os.path.dirname(framework)
        tmpFw = os.path.join(fwPath, '1.apk')
        os.rename(framework, tmpFw)

    # Run
    cmd = f'{JAVA} -jar {APKTOOL} d {path} -f -o {destPath}{f" -p {fwPath}" if framework else ""}'
    ret = os.system(cmd)

    # Restore previouse resourceses apk name
    if framework:
        os.rename(tmpFw, framework)

    # return
    return ret, destPath

def recompileAPK(path, outdir='', framework=''):

    # Dest path
    apkName = os.path.basename(path)[:-len(DECOMPILED_SUFFIX)]
    destPath = os.path.join(outdir, apkName) if outdir else apkName

    # Temporary change framework resourceses apk name
    if framework:
        fwPath = os.path.dirname(framework)
        tmpFw = os.path.join(fwPath, '1.apk')
        os.rename(framework, tmpFw)

    # Run
    cmd = f'{JAVA} -jar {APKTOOL} b {path} -o {destPath}{f" -p {fwPath}" if framework else ""}'
    ret = os.system(cmd)

    # Restore previouse resourceses apk name
    if framework:
        os.rename(tmpFw, framework)

    # return
    return ret, destPath
