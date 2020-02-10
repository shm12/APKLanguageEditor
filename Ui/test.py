from PyQt5 import QtCore, QtGui, QtWidgets, uic
import TranslateView
import ChooseTargetLocaleDialog

def run(app, l):
    [i.show() for i in l]
    app.exec_()

def main():
    win_list = [TranslateView.TranslateView, ChooseTargetLocaleDialog.ChooseTargetLocaleDialog]
    run(QtWidgets.QApplication([]), [window() for window in win_list])

if __name__ == "__main__":
    main()