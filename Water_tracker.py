import mysql.connector
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QComboBox,
    QTextEdit, QCalendarWidget, QTabWidget, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout, QInputDialog
)
from PySide6.QtGui import QFont, QPalette, QBrush, QPixmap
from PySide6.QtCore import Qt, QDate
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import os

class WaterTracker(QWidget):
    def __init__(self, db_conn, background_path=None, parent=None):
        super().__init__(parent)
        self.db_conn = db_conn
        self.setFixedSize(800, 600)
        self.setWindowTitle("Water Tracker")

        # Main Layout
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Water Intake Tracker Tab
        water_tab = QWidget()
        self.water_layout(water_tab, background_path)
        self.tabs.addTab(water_tab, "Water Intake Tracker")

        # Report Tab
        report_tab = QWidget()
        self.report_layout(report_tab)
        self.tabs.addTab(report_tab, "Report")

    def water_layout(self, tab, background_path):
        """This layout is for the Water Intake Tracker tab."""
        layout = QVBoxLayout(tab)

        # Set background
        if background_path:
            self.set_background(tab, background_path)

        # Title
        title = QLabel("Water Intake Tracker")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.clicked.connect(self.load_day_data)
        layout.addWidget(self.calendar)

        # Water Intake Section
        intake_layout = QVBoxLayout()
        intake_label = QLabel("Enter Water Intake (in liters)")
        intake_label.setFont(QFont("Arial", 12))
        self.intake_edit = QTextEdit()
        self.intake_edit.setPlaceholderText("Enter the amount of water consumed (in liters)...")
        intake_layout.addWidget(intake_label)
        intake_layout.addWidget(self.intake_edit)
        layout.addLayout(intake_layout)

        # Save Button
        save_button = QPushButton("Save Water Intake")
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
                SELECT intake 
                FROM water_entries 
                WHERE date = %s
            """
            cursor.execute(query, (selected_date,))
            result = cursor.fetchone()

            if result:
                intake = result[0]
                self.intake_edit.setPlainText(str(intake))
            else:
                self.intake_edit.clear()
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def save_entry(self):
        """Save the current entry into the database."""
        try:
            date = self.calendar.selectedDate().toString("yyyy-MM-dd")
            intake = self.intake_edit.toPlainText()

            if not intake:
                QMessageBox.warning(self, "Input Error", "Please enter the water intake value.")
                return

            cursor = self.db_conn.cursor()
            query = """
                 REPLACE INTO water_entries (date, intake) 
                 VALUES (%s, %s)
             """
            cursor.execute(query, (date, intake))
            self.db_conn.commit()

            QMessageBox.information(self, "Success", f"Water intake saved for {date}: {intake} liters")
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to save entry: {e}")

    def generate_report(self):
        """Generate a textual report."""
        try:
            cursor = self.db_conn.cursor()
            end_date = QDate.currentDate().toString("yyyy-MM-dd")
            start_date = QDate.currentDate().addDays(-7).toString("yyyy-MM-dd")

            query = """
                SELECT date, intake 
                FROM water_entries 
                WHERE date BETWEEN %s AND %s
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            report = f"Water Intake Report from {start_date} to {end_date}:\n\n"
            for row in results:
                date, intake = row
                report += f"Date: {date} | Water Intake: {intake} liters\n"

            self.report_box.setPlainText(report)
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def edit_entry(self):
        """Edit a specific record."""
        date = self.edit_date_input.text()
        intake, ok = QInputDialog.getDouble(self, "Edit Intake", "Enter new intake value (liters):", 0, 0, 100, 1)
        if ok and date:
            try:
                cursor = self.db_conn.cursor()
                query = """
                    UPDATE water_entries 
                    SET intake = %s 
                    WHERE date = %s
                """
                cursor.execute(query, (intake, date))
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
                    DELETE FROM water_entries 
                    WHERE date = %s
                """
                cursor.execute(query, (date,))
                self.db_conn.commit()
                QMessageBox.information(self, "Success", f"Record for {date} deleted successfully!")
                self.generate_report()
            except mysql.connector.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to delete record: {e}")

    def show_statistics(self):
        """Display water intake statistics as a bar chart in the tab."""
        try:
            cursor = self.db_conn.cursor()
            query = "SELECT SUM(intake), date FROM water_entries GROUP BY date;"
            cursor.execute(query)
            results = cursor.fetchall()

            dates = [row[1] for row in results]
            intakes = [row[0] for row in results]

            fig = Figure()
            ax = fig.add_subplot(111)
            ax.bar(dates, intakes, color='blue')
            ax.set_title("Water Intake Statistics")
            ax.set_xlabel("Dates")
            ax.set_ylabel("Total Water Intake (liters)")

            chart = FigureCanvas(fig)
            chart.setMinimumSize(600, 400)

            for i in range(self.chart_layout.count()):
                widget = self.chart_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            self.chart_layout.addWidget(chart)
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to show statistics: {e}")

    def download_report_pdf_with_image(self):
        """Download the report as a PDF with a background image."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "Water_Report.pdf", "PDF Files (*.pdf)")
            if not file_path:
                return

            cursor = self.db_conn.cursor()
            end_date = QDate.currentDate().toString("yyyy-MM-dd")
            start_date = QDate.currentDate().addDays(-7).toString("yyyy-MM-dd")

            query = """
                SELECT date, intake 
                FROM water_entries 
                WHERE date BETWEEN %s AND %s;
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            pdf = canvas.Canvas(file_path, pagesize=letter)
            width, height = letter

            image_path = r"C:\\kio\\145\\hji.png"  # Update to your background image path
            if os.path.exists(image_path):
                background = ImageReader(image_path)
                pdf.drawImage(background, 0, 0, width=width, height=height, mask='auto')

            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, height - 50, f"Water Intake Report from {start_date} to {end_date}")

            y = height - 100
            pdf.setFont("Helvetica", 12)
            for row in results:
                date, intake = row
                pdf.drawString(50, y, f"Date: {date} | Water Intake: {intake} liters")
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

    # Database connectionk
    try:
        db_conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",  # Update your MySQL root password
            database="wellhive"
        )
        cursor = db_conn.cursor()
        cursor.execute("""
          CREATE TABLE IF NOT EXISTS water_entries (
              date DATE NOT NULL,
              intake FLOAT NOT NULL,
              PRIMARY KEY (date)
          );
        """)
        db_conn.commit()
    except mysql.connector.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to connect to database: {e}")
        sys.exit(1)

    # Load the app
    background_path = r"C:\\kio\\145\\hji.png"  # Update to your background image path
    window = WaterTracker(db_conn, background_path)
    window.show()
    sys.exit(app.exec())
