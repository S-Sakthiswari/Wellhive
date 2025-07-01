from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QPushButton
from PySide6.QtGui import QFont, QPixmap, QColor, QPainter
from PySide6.QtCore import Qt, QPropertyAnimation, QRectF
import subprocess
import mysql.connector

class SelfCareApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Self-Care Space")
        self.setFixedSize(800, 600)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Welcome Container with Animation
        self.welcome_container = self.create_welcome_container()
        self.main_layout.addWidget(self.welcome_container)

        # Tracker Buttons Container
        self.tracker_container = self.create_tracker_container()
        self.main_layout.addWidget(self.tracker_container)

        self.setLayout(self.main_layout)

        # Start Animations
        self.start_welcome_animation()

        # Set up database connection for mood tracker
        try:
            self.db_conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="1234",
                database="wellhive",
            )
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            exit()

    def create_welcome_container(self):
        """Creates the welcome message container."""
        container = QWidget()
        container.setFixedSize(700, 150)
        container.setStyleSheet(
            """
            background-color: rgba(240, 240, 240, 0.5); /* Light gray background */
            border: 2px solid rgba(220, 220, 220, 0.5); /* Light gray border */
            border-radius: 15px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            """
        )

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)

        message = QLabel("Welcome to your Self-Care Space")
        message.setFont(QFont("Arial", 24, QFont.Bold))
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("color: #333333;")  # Dark Gray Text
        layout.addWidget(message)

        # Applying glow effect to the container
        self.apply_glow_effect(container)

        return container

    def create_tracker_container(self):
        """Creates the tracker buttons container."""
        container = QWidget()
        container.setFixedSize(700, 300)
        container.setStyleSheet(
            """
            background-color: rgba(240, 240, 240, 0.5); /* Light gray background */
            border: 2px solid rgba(220, 220, 220, 0.5); /* Light gray border */
            border-radius: 15px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            """
        )
        layout = QHBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        # Add tracker buttons with hover animations
        for text, icon in [
            ("Mood", "C:/kio/145/logo.png"),
            ("Sleep", "C:/kio/145/logo.png"),
            ("Meditation", "C:/kio/145/logo.png"),
            ("Gratitude", "C:/kio/145/logo.png"),
            ("Water", "C:/kio/145/logo.png"),
            ("Reminder", "C:/kio/145/logo.png"),  # New Reminder Button
        ]:
            button = self.create_tracker_button(text, icon)
            layout.addWidget(button)

        # Applying glow effect to the tracker container
        self.apply_glow_effect(container)

        return container

    def create_tracker_button(self, text, icon_path):
        """Creates a tracker button with hover animation."""
        button = QPushButton()
        button.setFixedSize(140, 140)
        button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(240, 240, 240, 0.7); /* Soft gray */
                border: 2px solid rgba(220, 220, 220, 0.8); /* Slightly darker gray border */
                border-radius: 10px;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                color: #333333; /* Dark gray text */
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(240, 240, 240, 0.85); /* Slightly lighter gray on hover */
            }
            """
        )

        layout = QVBoxLayout(button)
        layout.setAlignment(Qt.AlignCenter)

        # Icon
        icon = QLabel()
        pixmap = QPixmap(icon_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Smaller size
        icon.setPixmap(pixmap)
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        # Label
        label = QLabel(text)
        label.setFont(QFont("Arial", 12, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #333333;")  # Dark gray text
        layout.addWidget(label)

        # Hover animation
        button.enterEvent = lambda event: self.animate_button_hover(button, True)
        button.leaveEvent = lambda event: self.animate_button_hover(button, False)

        # Button click logic
        button.clicked.connect(lambda: self.open_tracker(text))

        return button

    def open_tracker(self, tracker_name):
        """Opens the respective tracker by running the appropriate Python script."""
        trackers = {
            "Mood": "mood.py",
            "Sleep": "Sleep.py",
            "Meditation": "med.py",
            "Gratitude": "gra.py",
            "Water": "Water.py",
            "Reminder": "Remender.py"  # New Reminder Script
        }

        script = trackers.get(tracker_name)
        if script:
            subprocess.Popen(["C:/kio/145/.venv/Scripts/python.exe", f"C:/kio/145/{script}"])

    def animate_button_hover(self, button, enlarge):
        """Animates the button on hover."""
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(300)
        rect = button.geometry()
        if enlarge:
            animation.setEndValue(QRectF(rect.x() - 5, rect.y() - 5, rect.width() + 10, rect.height() + 10))
        else:
            animation.setEndValue(QRectF(rect.x() + 5, rect.y() + 5, rect.width() - 10, rect.height() - 10))
        animation.start()

    def start_welcome_animation(self):
        """Animates the welcome container fading in."""
        self.welcome_container.setWindowOpacity(0.0)
        animation = QPropertyAnimation(self.welcome_container, b"windowOpacity")
        animation.setDuration(1000)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.start()

    def apply_glow_effect(self, widget):
        """Applies a glowing light effect to the widget."""
        glow_effect = QGraphicsDropShadowEffect()
        glow_effect.setColor(QColor(220, 220, 220, 255))  # Light gray glow color
        glow_effect.setOffset(0, 0)  # No offset for glow
        glow_effect.setBlurRadius(25)  # Increase blur radius for the glowing effect
        widget.setGraphicsEffect(glow_effect)

    def paintEvent(self, event):
        """Custom paint event to draw a glowing glassmorphism background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the background image
        bg_pixmap = QPixmap("C:/kio/145/hji.png")
        painter.drawPixmap(self.rect(), bg_pixmap)

        # Glassmorphism overlay
        rect = self.rect()

        # Applying a soft glow around the background
        glow_color = QColor(240, 240, 240, 150)  # Soft glow with higher opacity
        painter.setBrush(glow_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 20, 20)


if __name__ == "__main__":
    app = QApplication([])

    window = SelfCareApp()
    window.show()

    app.exec()
