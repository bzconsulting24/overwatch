import sys
import io
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore    import QObject, QThread, pyqtSignal
from hitl_app        import Ui_BehaviorAnalysis   # your UI class
from hitl_runner     import run_hitl_analysis     # your existing logic

class EmittingStream(io.TextIOBase):
    def __init__(self, write_fn, orig_stream):
        super().__init__()
        self.write_fn    = write_fn
        self.orig_stream = orig_stream

    def write(self, text):
        # print to real console
        self.orig_stream.write(text)
        self.orig_stream.flush()
        # append to GUI text box
        self.write_fn(text)

    def flush(self):
        self.orig_stream.flush()

class Worker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error    = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            self.progress.emit(0)
            print("Starting analysis...")
            run_hitl_analysis(self.url)
            self.progress.emit(100)
            print("Analysis complete.")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_BehaviorAnalysis()
        self.ui.setupUi(self)

        # redirect stdout/stderr to both console and GUI
        orig_out = sys.stdout
        orig_err = sys.stderr
        sys.stdout = EmittingStream(self.ui.result_box.append, orig_out)
        sys.stderr = EmittingStream(self.ui.result_box.append, orig_err)

        self.ui.btn_run.clicked.connect(self.run_from_gui)

    def run_from_gui(self):
        self.ui.result_box.clear()
        self.ui.progressBar.setValue(0)

        url = self.ui.lineEdit_url.text().strip()
        if not url:
            print("Please enter a URL or file path.")
            return

        self.thread = QThread()
        self.worker = Worker(url)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.ui.progressBar.setValue)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def show_error(self, message):
        print(f"Error: {message}")
        self.ui.progressBar.setValue(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
