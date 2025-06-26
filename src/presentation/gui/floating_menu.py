from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt
import sys

class FloatingMenu(QWidget):
    def __init__(self, start_tracking_callback, start_voice_callback):
        super().__init__()

        self.setWindowTitle("Control Menu")
        self.setGeometry(100, 100, 200, 300)

        # قائمة الأزرار
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.start_tracking_btn = QPushButton("Start Head Control")
        self.start_tracking_btn.clicked.connect(start_tracking_callback)

        self.voice_cmd_btn = QPushButton("Start Voice Control")
        self.voice_cmd_btn.clicked.connect(start_voice_callback)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.close)

        layout.addWidget(self.start_tracking_btn)
        layout.addWidget(self.voice_cmd_btn)
        layout.addWidget(self.exit_btn)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingMenu(lambda: print("Start Tracking"), lambda: print("Start Voice"))
    window.show()
    sys.exit(app.exec())
