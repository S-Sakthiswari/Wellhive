import mysql.connector
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QCalendarWidget,
    QTextEdit, QTabWidget, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout, QInputDialog
)
from PySide6.QtGui import QFont, QPalette, QBrush, QPixmap
from PySide6.QtCore import Qt, QDate
from docutils.languages.af import labels
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import os

class SleepTracker(QWidget):
    def __init__(self, db_conn, background_path=None, parent=None):
        super().__init__(parent)
        self.db_conn = db_conn
        self.setFixedSize(800, 600)
        self.setWindowTitle("Sleep Tracker")

        # Main Layout
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Sleep Tracker Tab
        sleep_tab = QWidget()
        self.sleep_layout(sleep_tab, background_path)
        self.tabs.addTab(sleep_tab, "Sleep Tracker")

        # Report Tab
        report_tab = QWidget()
        self.report_layout(report_tab)
        self.tabs.addTab(report_tab, "Report")

    def sleep_layout(self, tab, background_path):
        """This layout is for the Sleep Tracker tab."""
        layout = QVBoxLayout(tab)

        # Set background
        if background_path:
            self.set_background(tab, background_path)

        # Title
        title = QLabel("Sleep Tracker")
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

        # Sleep Duration Section
        sleep_layout = QVBoxLayout()
        sleep_label = QLabel("Enter Sleep Duration (in hours)")
        sleep_label.setFont(QFont("Arial", 12))
        self.sleep_edit = QTextEdit()
        self.sleep_edit.setPlaceholderText("Enter the amount of sleep (in hours)...")
        sleep_layout.addWidget(sleep_label)
        sleep_layout.addWidget(self.sleep_edit)
        layout.addLayout(sleep_layout)

        # Save Button
        save_button = QPushButton("Save Sleep Duration")
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

        # Edit & Delete Layout
        edit_delete_layout = QHBoxLayout()
        self.edit_date_input = QLineEdit()
        self.edit_date_input.setPlaceholderText("Enter Date (yyyy-mm-dd) to Edit/Delete")
        edit_delete_layout.addWidget(self.edit_date_input)

        edit_button = QPushButton("Edit Record")
        edit_button.clicked.connect(self.edit_entry)
        edit_delete_layout.addWidget(edit_button)

        delete_button = QPushButton("Delete Record")
        delete_button.clicked.connect(self.delete_entry)
        edit_delete_layout.addWidget(delete_button)

        layout.addLayout(edit_delete_layout)

        # Generate Report Button
        generate_button = QPushButton("Generate Report")
        generate_button.clicked.connect(self.generate_report)
        layout.addWidget(generate_button, alignment=Qt.AlignCenter)

        # Show Bar Chart Button
        chart_button = QPushButton("Show Statistics (Bar Chart)")
        chart_button.clicked.connect(self.show_statistics)
        layout.addWidget(chart_button, alignment=Qt.AlignCenter)

        # Download Report Button
        pdf_button = QPushButton("Download Report as PDF with Image")
        pdf_button.clicked.connect(self.download_report_pdf_with_image)
        layout.addWidget(pdf_button, alignment=Qt.AlignCenter)

        self.chart_layout = QVBoxLayout()  # Layout for the chart
        layout.addLayout(self.chart_layout)  # Add chart layout to the tab

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
            query = """
                SELECT duration 
                FROM sleep_entries 
                WHERE date = %s
            """
            cursor.execute(query, (selected_date,))
            result = cursor.fetchone()

            if result:
                duration = result[0]
                self.sleep_edit.setPlainText(str(duration))
            else:
                self.sleep_edit.clear()
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def save_entry(self):
        """Save the current entry into the database."""
        try:
            date = self.calendar.selectedDate().toString("yyyy-MM-dd")
            duration = self.sleep_edit.toPlainText()

            if not duration:
                QMessageBox.warning(self, "Input Error", "Please enter the sleep duration value.")
                return

            cursor = self.db_conn.cursor()
            query = """
                REPLACE INTO sleep_entries (date, duration) 
                VALUES (%s, %s)
            """
            cursor.execute(query, (date, duration))
            self.db_conn.commit()

            QMessageBox.information(self, "Success", f"Sleep duration saved for {date}: {duration} hours")
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to save entry: {e}")

    def generate_report(self):
        """Generate a textual report of all sleep entries."""
        try:
            cursor = self.db_conn.cursor()

            # Fetch all sleep entries from the database
            query = """
                SELECT date, duration 
                FROM sleep_entries
                ORDER BY date ASC
            """
            cursor.execute(query)
            results = cursor.fetchall()

            if not results:
                self.report_box.setPlainText("No sleep data available.")
                return

            # Create a report with all records
            report = "Sleep Duration Report (All Records):\n\n"
            for row in results:
                date, duration = row
                report += f"Date: {date} | Sleep Duration: {duration} hours\n"

            self.report_box.setPlainText(report)
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def edit_entry(self):
        """Edit a specific record."""
        date = self.edit_date_input.text()
        duration, ok = QInputDialog.getDouble(self, "Edit Duration", "Enter new sleep duration (hours):", 0, 0, 24, 1)
        if ok and date:
            try:
                cursor = self.db_conn.cursor()
                query = """
                    UPDATE sleep_entries 
                    SET duration = %s 
                    WHERE date = %s
                """
                cursor.execute(query, (duration, date))
                self.db_conn.commit()
                QMessageBox.information(self, "Success", f"Record for {date} updated successfully!")
                self.generate_report()
            except mysql.connector.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to edit record: {e}")

    def delete_entry(self):
        """Delete a specific record."""
        date = self.edit_date_input.text()
        if date:
            try:
                cursor = self.db_conn.cursor()
                query = """
                    DELETE FROM sleep_entries 
                    WHERE date = %s
                """
                cursor.execute(query, (date,))
                self.db_conn.commit()
                QMessageBox.information(self, "Success", f"Record for {date} deleted successfully!")
                self.generate_report()
            except mysql.connector.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to delete record: {e}")

    from PyQt5.QtWidgets import QFileDialog, QPushButton

    def show_statistics(self):
        """Display sleep duration statistics as a pie chart in the tab and add an option to download it."""
        try:
            cursor = self.db_conn.cursor()
            query = "SELECT SUM(duration), date FROM sleep_entries GROUP BY date;"
            cursor.execute(query)
            results = cursor.fetchall()

            # Extract data
            labels = [row[1] for row in results]
            sizes = [row[0] for row in results]

            if not labels or not sizes:
                QMessageBox.warning(self, "No Data", "No data available to display in the chart.")
                return

            # Create pie chart
            fig = Figure()
            ax = fig.add_subplot(111)
            ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99", "#c2c2f0"],
            )
            ax.set_title("Sleep Duration Distribution")

            chart = FigureCanvas(fig)
            chart.setMinimumSize(600, 400)

            # Clear previous charts
            for i in range(self.chart_layout.count()):
                widget = self.chart_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Add the pie chart to the layout
            self.chart_layout.addWidget(chart)

            # Add a "Download" button to allow saving the chart as an image
            download_button = QPushButton("Download Chart", self)
            download_button.clicked.connect(self.download_chart)
            self.chart_layout.addWidget(download_button)

        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to show statistics: {e}")

    def download_chart(self, sizes=None):
        """Save the pie chart as an image (PNG or JPEG)."""
        try:
            # Open file dialog to choose save location
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Chart", "chart.png",
                                                       "PNG Files (*.png);;JPEG Files (*.jpg)")
            if not file_path:
                return  # If the user cancels the save dialog

            # Save the figure as an image
            fig = plt.figure(figsize=(6, 4))
            ax = fig.add_subplot(111)
            ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99", "#c2c2f0"],
            )
            ax.set_title("Sleep Duration Distribution")
            fig.savefig(file_path, bbox_inches='tight')

            QMessageBox.information(self, "Success", "Chart saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save the chart: {e}")

    def download_report_pdf_with_image(self):
        """Download the report as a PDF with a background image for a specific day, week, or month."""
        try:
            # Ask the user for the report period (Day, Week, Month)
            period, ok = QInputDialog.getItem(self, "Select Report Period", "Choose the report period:",
                                              ["Today", "This Week", "This Month"], 0, False)
            if not ok:
                return

            # Get the file path to save the report
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "Sleep_Report.pdf", "PDF Files (*.pdf)")
            if not file_path:
                return

            # Set the date range based on user selection
            cursor = self.db_conn.cursor()
            end_date = QDate.currentDate().toString("yyyy-MM-dd")

            if period == "Today":
                start_date = end_date
            elif period == "This Week":
                start_date = QDate.currentDate().addDays(-7).toString("yyyy-MM-dd")
            elif period == "This Month":
                start_date = QDate.currentDate().addMonths(-1).toString("yyyy-MM-dd")

            # Fetch the sleep entries for the selected date range
            query = """
                SELECT date, duration 
                FROM sleep_entries 
                WHERE date BETWEEN %s AND %s
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            if not results:
                QMessageBox.warning(self, "No Data", "No sleep data available for the selected period.")
                return

            # Create PDF document
            pdf = canvas.Canvas(file_path, pagesize=letter)
            width, height = letter

            # Add background image (optional)
            image_path = r"C:\\path\\to\\background.png"  # Update to your background image path
            if os.path.exists(image_path):
                background = ImageReader(image_path)
                pdf.drawImage(background, 0, 0, width=width, height=height, mask='auto')

            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, height - 50, f"Sleep Duration Report from {start_date} to {end_date}")

            y = height - 100
            pdf.setFont("Helvetica", 12)
            for row in results:
                date, duration = row
                pdf.drawString(50, y, f"Date: {date} | Sleep Duration: {duration} hours")
                y -= 20
                if y < 50:
                    pdf.showPage()
                    y = height - 50

            pdf.save()
            QMessageBox.information(self, "Success", "Report saved successfully as PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF: {e}")


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
          CREATE TABLE IF NOT EXISTS sleep_entries (
              date DATE NOT NULL,
              duration FLOAT NOT NULL,
              PRIMARY KEY (date)
          );
        """)
        db_conn.commit()
    except mysql.connector.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to connect to database: {e}")
        sys.exit(1)

    # Load the app
    background_path = r"C:\kio\145\hji.png"  # Update to your background image path
    window = SleepTracker(db_conn, background_path)
    window.show()
    sys.exit(app.exec())
