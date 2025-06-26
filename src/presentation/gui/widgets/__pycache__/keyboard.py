import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout
from PyQt6.QtCore import Qt
from pynput.keyboard import Controller

class VirtualKeyboard(QWidget):
    def __init__(self):
        super().__init__()
        self.keyboard = Controller()
        self.init_ui()

    def init_ui(self):
        # Flags اختلفوا في PyQt6
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint
        )
        self.setGeometry(100, 500, 800, 300)  # مكان الكيبورد على الشاشة
        self.setStyleSheet("background-color: #f0f0f0;")

        layout = QGridLayout()

        keys = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Backspace'],
            ['Space']
        ]

        for row_idx, row in enumerate(keys):
            for col_idx, key in enumerate(row):
                button = QPushButton(key)
                button.setFixedSize(60, 60)
                button.setStyleSheet("font-size: 20px; background-color: white; border-radius: 10px;")
                button.clicked.connect(lambda checked, k=key: self.key_pressed(k))
                layout.addWidget(button, row_idx, col_idx)

        self.setLayout(layout)

    def key_pressed(self, key):
        if key == 'Space':
            self.keyboard.press(' ')
            self.keyboard.release(' ')
        elif key == 'Backspace':
            self.keyboard.press('\b')
            self.keyboard.release('\b')
        else:
            self.keyboard.press(key.lower())
            self.keyboard.release(key.lower())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    keyboard = VirtualKeyboard()
    keyboard.show()
    sys.exit(app.exec())
