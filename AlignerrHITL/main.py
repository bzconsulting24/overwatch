import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore    import QObject, QThread, pyqtSignal, QTimer
from hitl_app        import Ui_BehaviorAnalysis
from hitl_runner     import HITLRunner
import os
import time

def run_hitl_analysis(video_url, progress_callback=None, status_callback=None, result_box=None):
    runner = HITLRunner(result_box=result_box)
    return runner.run_analysis(video_url, progress_callback, status_callback)

class Worker(QObject):
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    update_result_box = pyqtSignal(str)  # Signal to update result_box

    def __init__(self, url, result_box):
        super().__init__()
        self.url = url
        self.result_box = result_box
        self.transcript_path = "transcript.txt"
        self.audio_path = "temp_audio.wav"

    def run(self):
        try:
            result = run_hitl_analysis(
                self.url,
                progress_callback=self.progress,
                status_callback=self.status
            )
            self.update_result_box.emit(result)  # Emit signal to update GUI
            self.finished.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

        # Final transcript handling
        if os.path.exists(self.transcript_path):
            with open(self.transcript_path, "r", encoding="utf-8") as f:
                transcript_content = f.read()
            print("--- DEBUG: Final Transcript Content ---")
            print(transcript_content)  # Print to terminal
            self.update_result_box.emit(transcript_content)  # Emit signal to update GUI
        time.sleep(3)
        if os.path.exists(self.transcript_path):
            with open(self.transcript_path, "r", encoding="utf-8") as f:
                transcript_content = f.read()
            if self.result_box:
                self.result_box.setPlainText(transcript_content)
        if os.path.exists(self.transcript_path):
            with open(self.transcript_path, "r", encoding="utf-8") as f:
                transcript_content = f.read()
        if os.path.exists(self.audio_path):
            os.remove(self.audio_path)
        if os.path.exists(self.transcript_path):
            with open(self.transcript_path, "r", encoding="utf-8") as f:
                content = f.read()
                if self.result_box:
                    self.result_box.setPlainText(content)

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_BehaviorAnalysis()
        self.ui.setupUi(self)
        self.ui.btn_run.clicked.connect(self.run_from_gui)

    def run_from_gui(self):
        url = self.ui.lineEdit_url.text().strip()
        if not url:
            self.ui.statusbar.showMessage("Enter a valid URL or file path.")
            return

        self.thread = QThread()
        self.worker = Worker(url, self.ui.result_box)
        self.worker.moveToThread(self.thread)

        self.worker.progress.connect(self.ui.progressBar.setValue)
        self.worker.status.connect(self.append_status)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.started.connect(self.worker.run)

        self.worker.update_result_box.connect(self.update_result_box)

        self.thread.start()

    def _on_finished(self, text):
        self.ui.progressBar.setValue(100)
        self.ui.result_box.setPlainText(text)
        self.ui.statusbar.showMessage("Analysis complete.")

    def _on_error(self, message):
        self.ui.progressBar.setValue(0)
        self.ui.statusbar.showMessage(f"Error: {message}")

    def append_status(self, message):
        self.ui.result_box.insertPlainText(message + "\n")

    def update_result_box(self, text):
        # Append the new text to the result box instead of replacing it
        current_text = self.ui.result_box.toPlainText()
        if current_text:
            self.ui.result_box.setPlainText(current_text + "\n" + text)
        else:
            self.ui.result_box.setPlainText(text)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MyApp()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {e}")
