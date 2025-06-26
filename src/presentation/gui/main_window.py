from PyQt6.QtWidgets import QMainWindow, QStackedWidget
import sys
from PyQt6.QtCore import QTimer

from presentation.gui.windows.auth.signIn_window import SignInWindow
from presentation.gui.constants import main_page_width, main_page_height, dashboard_page_width, dashboard_page_height
from presentation.gui.windows.dashboard_window import DashboardWindow
from presentation.gui.windows.auth.signup_window import SignUpWindow
from infrastructure.services.voice_service import VoiceService
from presentation.gui.loading_screen import LoadingScreen
from infrastructure.services.Streams.camera_stream import VideoStream


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Virtual Assistant")
        self.setFixedSize(main_page_width, main_page_height)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.voice_service = VoiceService()
        self.voice_service.set_interval(3)

        self.video_stream = VideoStream().start()

        # Start with signup
        self.signup_window = SignUpWindow(self.voice_service, self.video_stream)
        self._connect_signup_signals(self.signup_window)
        self.stacked_widget.addWidget(self.signup_window)
        self.stacked_widget.setCurrentWidget(self.signup_window)

    def _connect_signin_signals(self, window):
        try:
            window.signin_successful.disconnect()
        except TypeError:
            pass
        window.signin_successful.connect(self.handle_signin_successful)

        try:
            window.signup_requested.disconnect()
        except TypeError:
            pass
        window.signup_requested.connect(self.show_signup_window)

    def _connect_signup_signals(self, window):
        try:
            window.signup_successful.disconnect()
        except TypeError:
            pass
        window.signup_successful.connect(self.handle_signup_successful)

        try:
            window.signin_requested.disconnect()
        except TypeError:
            pass
        window.signin_requested.connect(self.show_signin_window)

    def show_signup_window(self):
        self.show_loading_screen("Switching to Sign Up...", duration=2000)
        QTimer.singleShot(2000, self._show_signup_window_actual)

    def _show_signup_window_actual(self):
        self.hide_loading_screen()
        if hasattr(self, 'signin_window'):
            self.signin_window.close()
            self.stacked_widget.removeWidget(self.signin_window)
            self.signin_window.deleteLater()
        self.signup_window = SignUpWindow(self.voice_service, self.video_stream)
        self._connect_signup_signals(self.signup_window)
        self.stacked_widget.addWidget(self.signup_window)
        self.stacked_widget.setCurrentWidget(self.signup_window)

    def show_signin_window(self):
        self.show_loading_screen("Switching to Sign In...", duration=2000)
        QTimer.singleShot(2000, self._show_signin_window_actual)

    def _show_signin_window_actual(self):
        self.hide_loading_screen()
        if hasattr(self, 'signup_window'):
            self.signup_window.close()
            self.stacked_widget.removeWidget(self.signup_window)
            self.signup_window.deleteLater()
        self.signin_window = SignInWindow(self.voice_service, self.video_stream)
        self._connect_signin_signals(self.signin_window)
        self.stacked_widget.addWidget(self.signin_window)
        self.stacked_widget.setCurrentWidget(self.signin_window)

    def show_loading_screen(self, message, duration=2000):
        self.loading_screen = LoadingScreen(message, self, duration=duration)
        self.loading_screen.start()

    def hide_loading_screen(self):
        if hasattr(self, 'loading_screen') and self.loading_screen is not None:
            self.loading_screen.close()
            self.loading_screen = None

    def close_application(self):
        self.video_stream.stop()  # ⛔ مهم جداً
        self.close()
        sys.exit(0)

    def handle_signup_successful(self):
        self.show_loading_screen("Switching to Sign In...", duration=2000)
        QTimer.singleShot(2000, self._handle_signup_successful_actual)

    def _handle_signup_successful_actual(self):
        self.hide_loading_screen()
        if hasattr(self, 'signup_window'):
            self.signup_window.close()
            self.stacked_widget.removeWidget(self.signup_window)
            self.signup_window.deleteLater()
        self.signin_window = SignInWindow(self.voice_service, self.video_stream)
        self._connect_signin_signals(self.signin_window)
        self.stacked_widget.addWidget(self.signin_window)
        self.stacked_widget.setCurrentWidget(self.signin_window)

    def handle_signin_successful(self):
        self.show_loading_screen("Switching to Dashboard...", duration=2000)
        QTimer.singleShot(2000, self._handle_signin_successful_actual)

    def _handle_signin_successful_actual(self):
        self.hide_loading_screen()
        sender = self.sender() if hasattr(self, 'sender') else None
        signin_window = sender if isinstance(sender, SignInWindow) else getattr(self, 'signin_window', None)

        user = getattr(signin_window, 'user', None)
        if hasattr(self, 'signin_window'):
            self.signin_window.close()
            self.stacked_widget.removeWidget(self.signin_window)
            self.signin_window.deleteLater()

        self.dashboard_window = DashboardWindow(self.voice_service, user=user)
        self.dashboard_window.setFixedSize(dashboard_page_width, dashboard_page_height)
        self.setFixedSize(dashboard_page_width, dashboard_page_height)
        self.stacked_widget.addWidget(self.dashboard_window)
        self.stacked_widget.setCurrentWidget(self.dashboard_window)
