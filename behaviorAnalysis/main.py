import sys
import os
import vlc
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame
from PyQt5.QtCore    import QObject, QThread, pyqtSignal, QTimer

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
    interrupted       = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        if QThread.currentThread().isInterruptionRequested():
            self.interrupted.emit()
            return
        try:
            transcript = run_hitl_analysis(
                self.url,
                progress_callback=self.progress.emit,
                status_callback=self.status.emit
            )
        except Exception as e:
            if QThread.currentThread().isInterruptionRequested():
                self.interrupted.emit()
                return
            self.error.emit(str(e))
            return

        if QThread.currentThread().isInterruptionRequested():
            self.interrupted.emit()
            return

        self.result_ready.emit(transcript or "[no transcript]")
        self.finished.emit(transcript or "")


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_BehaviorAnalysis()
        self.ui.setupUi(self)
        self.ui.btn_run.clicked.connect(self.start_analysis)
        self.ui.btn_stp.clicked.connect(self.stop_button)
        self.ui.btn_clr.clicked.connect(self.clear_button)
        self.thread = None
        self.worker = None

        # Video playback with audio using VLC
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        # Create a QFrame for VLC to embed into
        self.video_frame = QFrame()

        # Replace the QLabel with QFrame for video display
        old_widget = self.ui.video_display
        parent = old_widget.parent()
        layout = parent.layout()

        # Remove old widget and add new one
        layout.replaceWidget(old_widget, self.video_frame)
        old_widget.deleteLater()

        self.ui.video_display = self.video_frame
        self.ui.video_display.setMinimumSize(640, 480)
        self.ui.video_display.setMaximumSize(800, 600)
        self.ui.video_display.setStyleSheet("""
            QFrame {
                background: #000000;
                border: 2px solid #00ff88;
            }
        """)

        # Set VLC to play in the QFrame
        if sys.platform.startswith('linux'):
            self.media_player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":
            self.media_player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(int(self.video_frame.winId()))

        self.media_player.audio_set_volume(100)

        # Video file monitoring
        self.video_check_timer = QTimer()
        self.video_check_timer.timeout.connect(self.check_for_video)
        self.expected_video_path = None


    def start_analysis(self):
        url = self.ui.lineEdit_url.text().strip()
        if not url:
            self.ui.statusbar.showMessage("Enter a valid URL.")
            return

        # Stop any playing video to release file locks
        self.stop_video()

        self.ui.result_box.clear()
        self.ui.progressBar.setValue(0)
        self.ui.statusbar.showMessage("Starting analysis")

        # Set expected video path to the playback copy (not locked by OpenFace)
        runner = HITLRunner()
        self.expected_video_path = os.path.join(runner.output_dir, "playback.mp4")
        self.video_check_timer.start(500)  # Check every 500ms for video

        self.thread = QThread()
        self.worker = Worker(url)
        self.worker.moveToThread(self.thread)

        # connect signals
        self.worker.progress.connect(self.ui.progressBar.setValue)
        self.worker.status.connect(self.append_status)
        self.worker.result_ready.connect(self.append_result)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.interrupted.connect(self.on_interrupted)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.interrupted.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def append_status(self, msg):
        # Status messages only go to statusbar, not the result box
        self.ui.statusbar.showMessage(msg)

    def append_result(self, text):
        self.ui.result_box.append(text)

    def on_finished(self, _):
        self.ui.progressBar.setValue(100)
        self.ui.statusbar.showMessage("Analysis complete")
        self.video_check_timer.stop()

    def on_error(self, message):
        self.ui.progressBar.setValue(0)
        self.ui.statusbar.showMessage("Error: " + message)
        self.ui.result_box.append(f"\n>>> ERROR: {message}")

    def on_interrupted(self):
        self.ui.progressBar.setValue(0)
        self.ui.statusbar.showMessage("Analysis interrupted by user")
        self.ui.result_box.append("\n>>> ANALYSIS TERMINATED BY USER")
        self.stop_video()

    def start_video(self, video_path):
        """Start playing video with audio using VLC"""
        if os.path.exists(video_path):
            media = self.instance.media_new(os.path.abspath(video_path))
            self.media_player.set_media(media)
            self.media_player.play()
            self.ui.videoTitle.setText("[ LIVE ANALYSIS FEED :: ACTIVE ]")
            print(f"VLC playing: {video_path}")

    def stop_video(self):
        """Stop video playback"""
        self.video_check_timer.stop()
        self.media_player.stop()
        self.ui.videoTitle.setText("[ LIVE ANALYSIS FEED ]")

    def check_for_video(self):
        """Check if video file exists and start playback"""
        if self.expected_video_path and os.path.exists(self.expected_video_path):
            # Check if file size is stable (download complete)
            try:
                size1 = os.path.getsize(self.expected_video_path)
                if size1 > 1024:  # At least 1KB
                    self.video_check_timer.stop()
                    self.start_video(self.expected_video_path)
            except:
                pass

    def clear_button(self):
        self.stop_video()
        self.ui.lineEdit_url.clear()
        self.ui.result_box.clear()
        self.ui.progressBar.setValue(0)
        self.ui.statusbar.showMessage("Ready")

        try:
            runner = HITLRunner()  # use default output_dir
            runner.clear_output_folder()
            self.ui.statusbar.showMessage("Output folder cleared")
        except Exception as e:
            self.ui.statusbar.showMessage(f"Error clearing folder: {e}")
            
    def stop_button(self):
        try:
            if self.thread and self.thread.isRunning():
                self.ui.statusbar.showMessage("Terminating analysis...")
                self.thread.requestInterruption()
                self.thread.quit()

                # Wait for thread to finish (with timeout)
                if not self.thread.wait(3000):  # 3 second timeout
                    self.ui.statusbar.showMessage("Force terminating thread...")
                    self.thread.terminate()
                    self.thread.wait()

                self.ui.progressBar.setValue(0)
                self.ui.statusbar.showMessage("Analysis terminated")
            else:
                self.ui.statusbar.showMessage("No analysis running")
        except Exception as e:
            print(f"Thread stop error: {e}")
            self.ui.statusbar.showMessage(f"Error stopping: {e}")

        


def main():
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
    

if __name__ == "__main__":
    main()
