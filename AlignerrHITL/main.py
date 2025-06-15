import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore    import QObject, QThread, pyqtSignal

from hitl_app_copy_ui import Ui_BehaviorAnalysis
from hitl_runner      import HITLRunner

def run_hitl_analysis(video_url,
                    progress_callback=None,
                    status_callback=None):
    return HITLRunner().run_analysis(
        video_url,
        progress_callback,
        status_callback
    )

class Worker(QObject):
    status            = pyqtSignal(str)
    progress          = pyqtSignal(int)
    result_ready      = pyqtSignal(str)
    finished          = pyqtSignal(str)
    error             = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            transcript = run_hitl_analysis(
                self.url,
                progress_callback=self.progress.emit,
                status_callback=self.status.emit
            )
        except Exception as e:
            self.error.emit(str(e))
            return

        # emit final transcript
        self.result_ready.emit(transcript or "[no transcript]")
        self.finished.emit(transcript or "")

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_BehaviorAnalysis()
        self.ui.setupUi(self)
        self.ui.btn_run.clicked.connect(self.start_analysis)

    def start_analysis(self):
        url = self.ui.lineEdit_url.text().strip()
        if not url:
            self.ui.statusbar.showMessage("Enter a valid URL.")
            return

        self.ui.result_box.clear()
        self.ui.progressBar.setValue(0)
        self.ui.statusbar.showMessage("Starting analysis")

        self.thread = QThread()
        self.worker = Worker(url)
        self.worker.moveToThread(self.thread)

        # connect signals
        self.worker.progress.connect(self.ui.progressBar.setValue)
        self.worker.status.connect(self.append_status)
        self.worker.result_ready.connect(self.append_result)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def append_status(self, msg):
        self.ui.statusbar.showMessage(msg)
        self.ui.result_box.append(msg)

    def append_result(self, text):
        self.ui.result_box.append(text)

    def on_finished(self, _):
        self.ui.progressBar.setValue(100)
        self.ui.statusbar.showMessage("Analysis complete")

    def on_error(self, message):
        self.ui.progressBar.setValue(0)
        self.ui.statusbar.showMessage("Error: " + message)

def main():
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
