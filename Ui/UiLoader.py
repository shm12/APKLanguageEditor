from PyQt5 import uic

def getUiClass(uifile):
    Ui, baseClass = uic.loadUiType(uifile)

    # The Ui as sub-Class
    class UiClass(baseClass):
        retranslateUi = Ui.retranslateUi
        def __init__(self, *args, setupUi=True, **kwargs):
            super(UiClass, self).__init__(*args, **kwargs)
            if setupUi:
                self.setupUi()

        def setupUi(self):
            return Ui.setupUi(self, self)
    
    return UiClass
