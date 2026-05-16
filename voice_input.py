import sys
import os
import json
import ctypes

try:
    import PyQt5
    pyqt5_path = os.path.dirname(PyQt5.__file__)
    plugins_path = os.path.join(pyqt5_path, "Qt5", "plugins", "platforms")
    if os.path.exists(plugins_path):
        ctypes.windll.kernel32.SetDllDirectoryW(plugins_path)
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path
except Exception:
    pass

from PyQt5.QtCore import QThread, pyqtSignal, QEventLoop, Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    import vosk
    HAS_VOSK = True
except ImportError:
    HAS_VOSK = False


def get_default_model_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    model_path = os.path.join(base_path, "models", "vosk-model-small-cn-0.22")

    if not os.path.exists(model_path):
        alt_path = os.path.join(os.path.dirname(base_path), "models", "vosk-model-small-cn-0.22")
        if os.path.exists(alt_path):
            return alt_path

    return model_path


class VoiceRecognitionThread(QThread):
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, model_path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self._is_running = False

    def run(self):
        self._is_running = True

        if not os.path.exists(self.model_path):
            self.error_occurred.emit(f"模型路径不存在: {self.model_path}")
            self.result_ready.emit("")
            return

        import shutil
        import tempfile
        temp_model_dir = os.path.join(tempfile.gettempdir(), "vosk_model_cn")

        try:
            if not os.path.exists(temp_model_dir):
                shutil.copytree(self.model_path, temp_model_dir)

            am_path = os.path.join(temp_model_dir, "am", "final.mdl")
            if not os.path.exists(am_path):
                shutil.rmtree(temp_model_dir, ignore_errors=True)
                shutil.copytree(self.model_path, temp_model_dir)

            model = vosk.Model(temp_model_dir)
        except Exception as e:
            self.error_occurred.emit(f"模型加载失败: {str(e)}")
            self.result_ready.emit("")
            return

        recognizer = vosk.KaldiRecognizer(model, 16000)

        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
        except Exception as e:
            self.error_occurred.emit(f"麦克风初始化失败: {str(e)}")
            self.result_ready.emit("")
            return

        while self._is_running:
            try:
                data = stream.read(4000, exception_on_overflow=False)

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        self.result_ready.emit(text)
                        break

                if not self._is_running:
                    break
            except Exception as e:
                self.error_occurred.emit(f"识别过程出错: {str(e)}")
                break

        try:
            stream.stop_stream()
            stream.close()
            audio.terminate()
        except:
            pass

    def stop(self):
        self._is_running = False
        self.wait()


class VoiceInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("语音输入")
        self.setFixedSize(280, 120)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        self.status_label = QLabel("请开始说话...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; color: #333; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                color: #666;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)

        self.recognized_text = ""

    def on_cancel_clicked(self):
        self.status_label.setText("正在停止...")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("停止中...")
        self.reject()

    def set_cancel_state(self):
        self.status_label.setText("已取消")
        self.cancel_btn.setText("已取消")
        self.cancel_btn.setEnabled(False)

    def set_status(self, text, icon=""):
        self.status_label.setText(text)

    def set_result(self, text):
        self.recognized_text = text
        if text:
            self.set_status("识别完成: " + text)
        else:
            self.set_status("未能识别")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()


def get_voice_input(parent_window=None, model_path=None):
    if model_path is None:
        model_path = get_default_model_path()

    dialog = VoiceInputDialog(parent_window)

    thread = VoiceRecognitionThread(model_path)
    loop = QEventLoop()

    def on_result(text):
        dialog.recognized_text = text
        dialog.set_status("识别完成: " + text if text else "未能识别", "✅" if text else "❌")
        loop.quit()

    def on_error(msg):
        dialog.set_status("错误: " + msg, "❌")
        loop.quit()

    thread.result_ready.connect(on_result)
    thread.error_occurred.connect(on_error)

    thread.start()
    dialog.show()

    from PyQt5.QtCore import QTimer
    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(lambda: (thread.stop(), dialog.reject(), loop.quit()))
    timeout_timer.start(30000)

    loop.exec_()
    timeout_timer.stop()

    if dialog.recognized_text:
        return dialog.recognized_text

    return ""


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    print("模型路径:", get_default_model_path())
    result = get_voice_input()
    print("识别结果:", result)

    sys.exit(0)
