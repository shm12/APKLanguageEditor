import sys
from os import path

DIR = path.join(path.dirname(__file__))
sys.path.append(path.join(DIR, '..'))


from PyQt5 import QtCore, QtGui, QtWidgets, uic
import TranslateView
import  LangPicker, PickLanguageDialog
from Logic.translator import Translator
from MainWindow import MainWindow

test_xml = path.join(DIR, '..', 'tmp', 'strings.xml')
test_apk = path.join(DIR, '..', 'tmp', 'Bluetooth.apk')
test_frw = path.join(DIR, '..', 'tmp', 'framework-res.apk')


def run(app, l):
    [i.show() for i in l]
    app.exec_()

def main():
    win_list = []
    # win_list = [TranslateView.TranslateView, LangPicker.LangPicker, PickLanguageDialog.PickLanguageDialog]
    
    win_list.append(MainWindow)
    run(QtWidgets.QApplication([]), [window() for window in win_list])
    # run(QtWidgets.QApplication([]), [Translator(path=test_apk, framework=test_frw)])

if __name__ == "__main__":
    main()