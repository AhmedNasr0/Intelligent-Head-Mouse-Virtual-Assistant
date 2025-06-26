from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer

class LoadingScreen(QDialog):
    def __init__(self, message="Loading, please wait...", parent=None, duration=20000):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 120)
        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self.duration = duration  # total duration in ms
        self.interval = 100       # ms per update
        self.current_value = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.progress.setValue(0)

    def start(self):
        self.current_value = 0
        self.progress.setValue(0)
        self.timer.start(self.interval)
        self.show()

    def update_progress(self):
        steps = self.duration // self.interval
        increment = 100 / steps
        self.current_value += increment
        if self.current_value >= 100:
            self.current_value = 100
            self.progress.setValue(100)
            self.timer.stop()
        else:
            self.progress.setValue(int(self.current_value)) 