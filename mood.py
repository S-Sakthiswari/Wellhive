import mysql.connector
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QCalendarWidget,
    QComboBox, QTabWidget, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout, QInputDialog, QTextEdit
)
from PySide6.QtGui import QFont, QPalette, QBrush, QPixmap
from PySide6.QtCore import Qt, QDate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MoodTracker(QWidget):
    def __init__(self, db_conn, background_path=None, parent=None):
        super().__init__(parent)

        self.db_conn = db_conn
        self.setFixedSize(800, 600)
        self.setWindowTitle("Mood Tracker")

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        mood_tab = QWidget()
        self.mood_layout(mood_tab, background_path)
        self.tabs.addTab(mood_tab, "Mood Tracker")

        report_tab = QWidget()
        self.report_layout(report_tab)
        self.tabs.addTab(report_tab, "Report")

    def mood_layout(self, tab, background_path):
        layout = QVBoxLayout(tab)

        if background_path:
            self.set_background(tab, background_path)

        title = QLabel("Mood Tracker")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.clicked.connect(self.load_day_data)
        layout.addWidget(self.calendar)

        mood_layout = QVBoxLayout()
        mood_label = QLabel("Select Your Mood")
        mood_label.setFont(QFont("Arial", 12))

        self.mood_combobox = QComboBox()
        self.mood_combobox.addItems(["Angry", "Happy", "Sad", "Neutral", "Excited", "Stressed"])

        mood_layout.addWidget(mood_label)
        mood_layout.addWidget(self.mood_combobox)
        layout.addLayout(mood_layout)

        save_button = QPushButton("Save Mood Entry")
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
        layout = QVBoxLayout(tab)

        self.report_box = QTextEdit(self)
        self.report_box.setPlaceholderText("Report will be displayed here...")
        self.report_box.setReadOnly(True)
        layout.addWidget(self.report_box)

        edit_delete_layout = QHBoxLayout()
        self.edit_date_input = QLineEdit()
        self.edit_date_input.setPlaceholderText("Enter Date (yyyy-mm-dd) to Edit/Delete")
        edit_delete_layout.addWidget(self.edit_date_input)

        edit_button = QPushButton("Edit Entry")
        edit_button.clicked.connect(self.edit_entry)
        edit_delete_layout.addWidget(edit_button)

        delete_button = QPushButton("Delete Entry")
        delete_button.clicked.connect(self.delete_entry)
        edit_delete_layout.addWidget(delete_button)

        layout.addLayout(edit_delete_layout)

        generate_button = QPushButton("Generate Report")
        generate_button.clicked.connect(self.generate_report)
        layout.addWidget(generate_button, alignment=Qt.AlignCenter)

        pdf_button = QPushButton("Download Report as PDF")
        pdf_button.clicked.connect(self.download_report_pdf)
        layout.addWidget(pdf_button, alignment=Qt.AlignCenter)

        stats_button = QPushButton("View Statistics")
        stats_button.clicked.connect(self.show_statistics)
        layout.addWidget(stats_button, alignment=Qt.AlignCenter)

    def set_background(self, widget, background_path):
        palette = QPalette()
        pixmap = QPixmap(background_path)
        if not pixmap.isNull():
            palette.setBrush(QPalette.Window, QBrush(pixmap))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

    def load_day_data(self, date):
        try:
            selected_date = date.toString("yyyy-MM-dd")
            cursor = self.db_conn.cursor()
            query = """
                SELECT mood_entry 
                FROM mood_entries 
                WHERE date = %s
            """
            cursor.execute(query, (selected_date,))
            result = cursor.fetchone()

            if result:
                self.mood_combobox.setCurrentText(result[0])
            else:
                self.mood_combobox.setCurrentIndex(0)
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def save_entry(self):
        try:
            date = self.calendar.selectedDate().toString("yyyy-MM-dd")
            mood_entry = self.mood_combobox.currentText()

            if not mood_entry:
                QMessageBox.warning(self, "Input Error", "Please select a mood.")
                return

            cursor = self.db_conn.cursor()
            query = """
                REPLACE INTO mood_entries (date, mood_entry) 
                VALUES (%s, %s)
            """
            cursor.execute(query, (date, mood_entry))
            self.db_conn.commit()

            QMessageBox.information(self, "Success", f"Mood entry saved for {date}")
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to save entry: {e}")

    def generate_report(self):
        try:
            cursor = self.db_conn.cursor()
            end_date = QDate.currentDate().toString("yyyy-MM-dd")
            start_date = QDate.currentDate().addDays(-7).toString("yyyy-MM-dd")

            query = """
                SELECT date, mood_entry 
                FROM mood_entries 
                WHERE date BETWEEN %s AND %s
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            report = f"Mood Entries Report from {start_date} to {end_date}:\n\n"
            for row in results:
                date, mood_entry = row
                report += f"Date: {date} | Mood: {mood_entry}\n"

            self.report_box.setPlainText(report)
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def edit_entry(self):
        date = self.edit_date_input.text()
        mood_entry, ok = QInputDialog.getText(self, "Edit Mood Entry", "Enter new mood entry:")
        if ok and date:
            try:
                cursor = self.db_conn.cursor()
                query = """
                    UPDATE mood_entries 
                    SET mood_entry = %s 
                    WHERE date = %s
                """
                cursor.execute(query, (mood_entry, date))
                self.db_conn.commit()
                QMessageBox.information(self, "Success", f"Record for {date} updated successfully!")
                self.generate_report()
            except mysql.connector.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to edit record: {e}")

    def delete_entry(self):
        date = self.edit_date_input.text()
        if date:
            try:
                cursor = self.db_conn.cursor()
                query = """
                    DELETE FROM mood_entries 
                    WHERE date = %s
                """
                cursor.execute(query, (date,))
                self.db_conn.commit()
                QMessageBox.information(self, "Success", f"Record for {date} deleted successfully!")
                self.generate_report()
            except mysql.connector.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to delete record: {e}")

    def show_statistics(self):
        try:
            cursor = self.db_conn.cursor()
            end_date = QDate.currentDate().toString("yyyy-MM-dd")
            start_date = QDate.currentDate().addDays(-7).toString("yyyy-MM-dd")

            query = """
                SELECT mood_entry, COUNT(*) 
                FROM mood_entries 
                WHERE date BETWEEN %s AND %s
                GROUP BY mood_entry
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            if not results:
                QMessageBox.information(self, "No Data", "No mood entries found for the selected period.")
                return

            # Extract mood entries and their counts
            moods = [row[0] for row in results]
            counts = [row[1] for row in results]

            # Check if a chart window already exists
            if hasattr(self, "chart_window") and self.chart_window is not None:
                self.chart_window.close()

            # Create a new window for the chart
            self.chart_window = QWidget()
            self.chart_window.setWindowTitle("Mood Statistics")
            self.chart_window.setFixedSize(600, 400)

            layout = QVBoxLayout(self.chart_window)

            # Create a matplotlib figure and canvas
            figure = Figure(figsize=(6, 4))
            canvas = FigureCanvas(figure)
            layout.addWidget(canvas)

            # Plot the pie chart
            ax = figure.add_subplot(111)
            ax.pie(
                counts,
                labels=moods,
                autopct="%1.1f%%",
                startangle=140,
                colors=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99", "#c2c2f0", "#ffb3e6"],
            )
            ax.set_title(f"Mood Distribution ({start_date} to {end_date})")

            # Show the chart window and ensure it remains alive
            self.chart_window.show()

        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to generate statistics: {e}")

    def download_report_pdf(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "Mood_Report.pdf", "PDF Files (*.pdf)")
            if not file_path:
                return

            cursor = self.db_conn.cursor()
            end_date = QDate.currentDate().toString("yyyy-MM-dd")
            start_date = QDate.currentDate().addDays(-7).toString("yyyy-MM-dd")

            query = """
                SELECT date, mood_entry 
                FROM mood_entries 
                WHERE date BETWEEN %s AND %s
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            pdf = canvas.Canvas(file_path, pagesize=letter)
            width, height = letter

            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, height - 50, f"Mood Entries Report from {start_date} to {end_date}")

            y = height - 100
            pdf.setFont("Helvetica", 12)
            for row in results:
                date, mood_entry = row
                pdf.drawString(50, y, f"Date: {date} | Mood: {mood_entry}")
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

    try:
        db_conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="wellhive"
        )
        cursor = db_conn.cursor()
        cursor.execute(""" 
          CREATE TABLE IF NOT EXISTS mood_entries (
              date DATE NOT NULL,
              mood_entry VARCHAR(255) NOT NULL,
              PRIMARY KEY (date)
          );
        """)
        db_conn.commit()

    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        sys.exit(1)

    window = MoodTracker(db_conn)
    window.show()
    sys.exit(app.exec())