import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore    import QObject, QThread, pyqtSignal
from hitl_app        import Ui_BehaviorAnalysis
from hitl_runner     import run_hitl_analysis

class Worker(QObject):
    status   = pyqtSignal(str)  # “Starting analysis…”, etc
    progress = pyqtSignal(int)  # 0–100
    finished = pyqtSignal(str)  # final transcript text
    error    = pyqtSignal(str)  # any exception message

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        self.status.emit("Starting analysis…")
        self.progress.emit(0)

        try:
            run_hitl_analysis(self.url)
            self.progress.emit(100)
            self.status.emit("Analysis complete.")

            transcript = r"C:\Users\julius\Alignerr_vids\transcript.txt"
            with open(transcript, "r", encoding="utf-8") as f:
                text = f.read()
            self.finished.emit(text)

        except Exception as e:
            self.error.emit(str(e))


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_BehaviorAnalysis()
        self.ui.setupUi(self)
        self.ui.btn_run.clicked.connect(self.run_from_gui)

    def run_from_gui(self):
        # clear old output
        self.ui.result_box.clear()
        self.ui.statusbar.clearMessage()
        # make bar busy
        self.ui.progressBar.setRange(0, 0)

        url = self.ui.lineEdit_url.text().strip()
        if not url:
            self.ui.statusbar.showMessage("Enter a URL or file path.")
            # stop busy mode
            self.ui.progressBar.setRange(0, 100)
            self.ui.progressBar.setValue(0)
            return

        # start background worker
        self.thread = QThread()
        self.worker = Worker(url)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.show_result)
        self.worker.error.connect(self.show_error)

        # clean up later
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()


    def show_result(self, text):
        # stop busy, show 100%
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(100)
        # show transcript
        self.ui.result_box.setPlainText(text)


    def show_error(self, message):
        # stop busy, reset bar
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)
        # display error
        self.ui.statusbar.showMessage(f"Error: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MyApp()
    win.show()
    sys.exit(app.exec_())
