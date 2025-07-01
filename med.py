from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
                               QSpinBox, QHBoxLayout, QSlider)
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt
from PySide6.QtCore import QUrl

class MeditationExercise(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(800, 500)
        self.setWindowTitle("Meditation Exercise")

        # Initialize sound players
        self.breath_in_player = QMediaPlayer()
        self.breath_out_player = QMediaPlayer()

        self.audio_output_in = QAudioOutput()
        self.audio_output_out = QAudioOutput()

        self.breath_in_player.setAudioOutput(self.audio_output_in)
        self.breath_out_player.setAudioOutput(self.audio_output_out)

        # Paths to sound files (update paths accordingly)
        self.breath_in_sound = QUrl.fromLocalFile(r"C:\kio\145\sakisound.mp3")
        self.breath_out_sound = QUrl.fromLocalFile(r"C:\kio\145\sakisound.mp3")
        self.breath_in_player.setSource(self.breath_in_sound)
        self.breath_out_player.setSource(self.breath_out_sound)

        self.sound_timer = QTimer()
        self.sound_timer.timeout.connect(self.play_breathing_cycle)

        # Main Layout
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Title Section
        title = QLabel("Meditation Exercise")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Back Button
        back_button = QPushButton("Back")
        back_button.setIcon(QIcon("icons/back.png"))
        back_button.setFont(QFont("Arial", 16))
        back_button.clicked.connect(self.close)  # Close the widget
        main_layout.addWidget(back_button, alignment=Qt.AlignLeft)

        # Time Settings Section
        time_layout = QVBoxLayout()
        duration_label = QLabel("Set Duration for Breathing Exercise (minutes):")
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 120)
        self.duration_spinbox.setValue(10)

        time_layout.addWidget(duration_label)
        time_layout.addWidget(self.duration_spinbox)

        # Add to main layout
        main_layout.addLayout(time_layout)

        # Breathing Exercise Section
        breath_layout = QVBoxLayout()
        breath_in_label = QLabel("Breath In Duration (seconds):")
        self.breath_in_duration = QSpinBox()
        self.breath_in_duration.setRange(1, 60)
        self.breath_in_duration.setValue(5)

        breath_out_label = QLabel("Breath Out Duration (seconds):")
        self.breath_out_duration = QSpinBox()
        self.breath_out_duration.setRange(1, 60)
        self.breath_out_duration.setValue(5)

        breath_layout.addWidget(breath_in_label)
        breath_layout.addWidget(self.breath_in_duration)
        breath_layout.addWidget(breath_out_label)
        breath_layout.addWidget(self.breath_out_duration)

        # Add to main layout
        main_layout.addLayout(breath_layout)

        # Volume Controls
        volume_layout = QHBoxLayout()
        volume_in_label = QLabel("Breath In Volume:")
        self.volume_in_slider = QSlider(Qt.Horizontal)
        self.volume_in_slider.setRange(0, 100)
        self.volume_in_slider.setValue(50)
        self.volume_in_slider.valueChanged.connect(lambda: self.audio_output_in.setVolume(self.volume_in_slider.value() / 100))

        volume_out_label = QLabel("Breath Out Volume:")
        self.volume_out_slider = QSlider(Qt.Horizontal)
        self.volume_out_slider.setRange(0, 100)
        self.volume_out_slider.setValue(50)
        self.volume_out_slider.valueChanged.connect(lambda: self.audio_output_out.setVolume(self.volume_out_slider.value() / 100))

        volume_layout.addWidget(volume_in_label)
        volume_layout.addWidget(self.volume_in_slider)
        volume_layout.addWidget(volume_out_label)
        volume_layout.addWidget(self.volume_out_slider)

        main_layout.addLayout(volume_layout)

        # Start/Stop Exercise Button
        self.start_button = QPushButton("Start Exercise")
        self.start_button.setIcon(QIcon("icons/start.png"))
        self.start_button.clicked.connect(self.start_breathing_session)
        main_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

        # Breathing Animation Placeholder
        self.animation_label = QLabel("lets get started")
        self.animation_label.setAlignment(Qt.AlignCenter)
        self.animation_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.animation_label.setStyleSheet("border: 2px solid gray; padding: 20px;")
        main_layout.addWidget(self.animation_label)

    def start_breathing_session(self):
        duration = self.duration_spinbox.value() * 60 * 1000  # Convert minutes to milliseconds
        self.sound_timer.start((self.breath_in_duration.value() + self.breath_out_duration.value()) * 1000)
        QTimer.singleShot(duration, self.stop_breathing_session)
        self.animation_label.setText("Exercise Started")
        self.start_button.setText("Stop Exercise")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.stop_breathing_session)

    def stop_breathing_session(self):
        self.sound_timer.stop()
        self.animation_label.setText("Exercise Ended")
        self.start_button.setText("Start Exercise")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.start_breathing_session)

    def play_breathing_cycle(self):
        self.audio_output_in.setVolume(self.volume_in_slider.value() / 100)
        self.breath_in_player.play()
        self.animation_label.setText("Breath In")
        QTimer.singleShot(self.breath_in_duration.value() * 1000, self.play_breath_out_sound)

    def play_breath_out_sound(self):
        self.audio_output_out.setVolume(self.volume_out_slider.value() / 100)
        self.breath_out_player.play()
        self.animation_label.setText("Breath Out")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    exercise = MeditationExercise()
    exercise.show()
    sys.exit(app.exec())
