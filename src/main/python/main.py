# from fbs_runtime.application_context.PyQt5 import ApplicationContext
from appctx import ApplicationContext
from PyQt5.QtWidgets import QMainWindow
from Ui.MainWindow import MainWindow

import sys

if __name__ == '__main__':
    app = ApplicationContext       # 1. Instantiate ApplicationContext
    window = MainWindow()
    # window.resize(250, 150)
    window.show()
    exit_code = app.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)