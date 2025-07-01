from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTimeEdit, QComboBox, QMessageBox
)
from PySide6.QtCore import QTimer, QTime, Qt
from plyer import notification
import sys


class ReminderFeature(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WellHive - Reminders")
        self.setFixedSize(400, 350)

        # Main Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Current Time Display
        self.current_time_label = QLabel()
        self.current_time_label.setAlignment(Qt.AlignCenter)
        self.current_time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333;")
        layout.addWidget(QLabel("Current Time (24-hour format):"))
        layout.addWidget(self.current_time_label)

        # Reminder Dropdown
        self.activity_dropdown = QComboBox()
        self.activity_dropdown.addItems(["Drink Water", "Take a Deep Breath", "Mood Check", "Smile", "Practice Gratitude"])
        layout.addWidget(QLabel("Choose Activity:"))
        layout.addWidget(self.activity_dropdown)

        # Time Picker
        self.time_picker = QTimeEdit()
        self.time_picker.setDisplayFormat("HH:mm")
        layout.addWidget(QLabel("Set Reminder Time (24-hour format):"))
        layout.addWidget(self.time_picker)

        # Set Reminder Button
        self.set_reminder_button = QPushButton("Set Reminder")
        self.set_reminder_button.clicked.connect(self.set_reminder)
        layout.addWidget(self.set_reminder_button)

        # Reminder Storage
        self.reminders = []

        # Timer for Notifications and Current Time Update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.timeout.connect(self.update_current_time)
        self.timer.start(1000)  # Check every second

        self.setLayout(layout)

    def update_current_time(self):
        """Update the current time label."""
        self.current_time_label.setText(QTime.currentTime().toString("HH:mm"))

    def set_reminder(self):
        """Store the reminder and notify the user."""
        activity = self.activity_dropdown.currentText()
        reminder_time = self.time_picker.time()

        if reminder_time < QTime.currentTime():
            QMessageBox.warning(self, "Invalid Time", "You cannot set a reminder for a past time.")
            return

        time_str = reminder_time.toString("HH:mm")
        self.reminders.append((activity, time_str))
        QMessageBox.information(self, "Reminder Set", f"Reminder for '{activity}' set at {time_str}.")

    def check_reminders(self):
        """Check if any reminders match the current time."""
        current_time = QTime.currentTime().toString("HH:mm")
        for activity, time in self.reminders:
            if time == current_time:
                self.trigger_reminder(activity)
                self.reminders.remove((activity, time))  # Remove reminder after triggering

    def trigger_reminder(self, activity):
        """Trigger both a desktop notification and a pop-up notification."""
        # Desktop Notification
        notification.notify(
            title="WellHive Reminder",
            message=f"It's time to {activity}!\nStay consistent for a better you.",
            timeout=10  # Notification duration in seconds
        )
        # Pop-Up Notification
        reminder_popup = QMessageBox(self)
        reminder_popup.setWindowTitle("WellHive Reminder")
        reminder_popup.setText(f"It's time to {activity}!\nStay consistent for a better you.")
        reminder_popup.setIcon(QMessageBox.Information)
        reminder_popup.setStandardButtons(QMessageBox.Ok)
        reminder_popup.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    reminder_window = ReminderFeature()
    reminder_window.show()

    sys.exit(app.exec())
