from PyQt5 import QtCore


class Pool(QtCore.QObject):
    tasksFinished = QtCore.pyqtSignal()
    def __init__(self, *args, limit=1, **kwargs):
        super(Pool, self).__init__(*args, **kwargs)
        self._pool = []
        self._running = []
        self.limit = limit
        self._stop = False

    def start(self, thread: QtCore.QThread):
        thread.finished.connect(self._thread_finished)
        self._pool.append(thread)
        self._try_execute()

    def stop_all(self):
        self._stop = True

    def continue_pool(self):
        self._stop = False
        self._try_execute()

    def _try_execute(self):
        while self.limit > len(self._running):
            if self._stop or not len(self._pool):
                self.tasksFinished.emit()
                break
            thread = self._pool[0]
            del self._pool[0]
            self._running.append(thread)
            thread.start()

    @QtCore.pyqtSlot()
    def _thread_finished(self):
        self._running.remove(self.sender())
        self._try_execute()


class Worker(QtCore.QThread):
    exceptionRaised = QtCore.pyqtSignal('PyQt_PyObject', arguments=['Exception'])

    def __init__(self, target, *sargs, args=None, kwargs=None, **skwargs):
        super(Worker, self).__init__(*sargs, **skwargs)
        self.target = target
        self.args = args if args else []
        self.kwarsg = kwargs if kwargs else {}

    def run(self):
        try:
            self.target(*self.args, **self.kwarsg)
        except Exception as e:
            print(e)
            self.exceptionRaised.emit(e)

