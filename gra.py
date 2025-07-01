import mysql.connector
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit,
    QCalendarWidget, QTabWidget, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont, QPalette, QBrush, QPixmap
from PySide6.QtCore import Qt, QDate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import os


class GratitudeTracker(QWidget):
    def __init__(self, db_conn, background_path=None, parent=None):
        super().__init__(parent)
        self.db_conn = db_conn
        self.setFixedSize(800, 600)
        self.setWindowTitle("Gratitude Tracker")

        # Main Layout
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Gratitude Tracker Tab
        gratitude_tab = QWidget()
        self.gratitude_layout(gratitude_tab, background_path)
        self.tabs.addTab(gratitude_tab, "Gratitude Tracker")

        # Report Tab
        report_tab = QWidget()
        self.report_layout(report_tab)
        self.tabs.addTab(report_tab, "Report")

    def gratitude_layout(self, tab, background_path):
        """This layout is for the Gratitude Tracker tab."""
        layout = QVBoxLayout(tab)

        # Set background
        if background_path:
            self.set_background(tab, background_path)

        # Title
        title = QLabel("Gratitude Tracker")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setSelectedDate(QDate.currentDate())  # Set to current date
        self.calendar.clicked.connect(self.load_day_data)
        layout.addWidget(self.calendar)

        # Gratitude Section
        gratitude_layout = QVBoxLayout()
        gratitude_label = QLabel("What are you grateful for today?")
        gratitude_label.setFont(QFont("Arial", 12))
        self.gratitude_edit = QTextEdit()
        self.gratitude_edit.setPlaceholderText("Write down something you're grateful for...")
        gratitude_layout.addWidget(gratitude_label)
        gratitude_layout.addWidget(self.gratitude_edit)
        layout.addLayout(gratitude_layout)

        # Save Button
        save_button = QPushButton("Save Entry")
        save_button.setStyleSheet(""" 
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        save_button.clicked.connect(self.save_entry)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)

    def report_layout(self, tab):
        """This layout is for the Report tab."""
        layout = QVBoxLayout(tab)

        self.report_box = QTextEdit(self)
        self.report_box.setPlaceholderText("Report will be displayed here...")
        self.report_box.setReadOnly(True)
        layout.addWidget(self.report_box)

        # Generate Report Button
        generate_button = QPushButton("Generate Report")
        generate_button.clicked.connect(self.generate_report)
        layout.addWidget(generate_button, alignment=Qt.AlignCenter)

        # Download Report Button
        pdf_button = QPushButton("Download Report as PDF with Image")
        pdf_button.clicked.connect(self.download_report_pdf_with_image)
        layout.addWidget(pdf_button, alignment=Qt.AlignCenter)

    def set_background(self, widget, background_path):
        """Set the custom background."""
        palette = QPalette()
        pixmap = QPixmap(background_path)
        if not pixmap.isNull():
            palette.setBrush(QPalette.Window, QBrush(pixmap))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

    def load_day_data(self, date):
        """Load data for the selected day."""
        try:
            selected_date = date.toString("yyyy-MM-dd")
            cursor = self.db_conn.cursor()
            query = "SELECT gratitude FROM gratitude_entries WHERE date = %s"
            cursor.execute(query, (selected_date,))
            result = cursor.fetchone()

            if result:
                gratitude = result[0]
                self.gratitude_edit.setPlainText(gratitude)
            else:
                self.gratitude_edit.clear()
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def save_entry(self):
        """Save the current gratitude entry into the database."""
        try:
            date = self.calendar.selectedDate().toString("yyyy-MM-dd")
            gratitude = self.gratitude_edit.toPlainText()

            cursor = self.db_conn.cursor()
            query = "REPLACE INTO gratitude_entries (date, gratitude) VALUES (%s, %s)"
            cursor.execute(query, (date, gratitude))
            self.db_conn.commit()

            QMessageBox.information(self, "Success", f"Entry saved for {date}.")
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to save entry: {e}")

    def generate_report(self):
        """Generate a textual report."""
        try:
            cursor = self.db_conn.cursor()
            end_date = QDate.currentDate().toString("yyyy-MM-dd")
            start_date = QDate.currentDate().addDays(-7).toString("yyyy-MM-dd")

            query = """
                SELECT date, gratitude
                FROM gratitude_entries
                WHERE date BETWEEN %s AND %s;
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            report = f"Report from {start_date} to {end_date}:\n\n"
            for row in results:
                date, gratitude = row
                report += f"Date: {date}\nGratitude: {gratitude}\n\n"

            self.report_box.setPlainText(report)
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def download_report_pdf_with_image(self):
        """Download the gratitude report as a PDF with a background image."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "Gratitude_Report.pdf", "PDF Files (*.pdf)")
            if not file_path:
                return

            cursor = self.db_conn.cursor()
            end_date = QDate.currentDate().toString("yyyy-MM-dd")
            start_date = QDate.currentDate().addDays(-7).toString("yyyy-MM-dd")

            query = """
                SELECT date, gratitude
                FROM gratitude_entries
                WHERE date BETWEEN %s AND %s;
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            pdf = canvas.Canvas(file_path, pagesize=letter)
            width, height = letter

            image_path = r"C:\kio\145\hji.png"  # Add your image path for the PDF background
            if os.path.exists(image_path):
                background = ImageReader(image_path)
                pdf.drawImage(background, 0, 0, width=width, height=height, mask='auto')

            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, height - 50, f"Report from {start_date} to {end_date}")

            y = height - 100
            pdf.setFont("Helvetica", 12)
            for row in results:
                date, gratitude = row
                pdf.drawString(50, y, f"Date: {date} | Gratitude: {gratitude}")
                y -= 20
                if y < 50:
                    pdf.showPage()
                    y = height - 50

            pdf.save()
            QMessageBox.information(self, "Success", "Report saved successfully as PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF: {e}")

# Main Entry
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Database connection
    try:
        db_conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",  # Update your MySQL root password
            database="wellhive"
        )
        cursor = db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gratitude_entries (
                date DATE PRIMARY KEY,
                gratitude TEXT
            );
        """)
        db_conn.commit()
    except mysql.connector.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to connect to database: {e}")
        sys.exit(1)

    # Load the app
    background_path = r"C:\kio\145\hji.png"  # Update to your background image path
    window = GratitudeTracker(db_conn, background_path)
    window.show()

    sys.exit(app.exec())
