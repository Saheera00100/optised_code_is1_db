import sys
import os
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout,
    QHBoxLayout, QLineEdit, QCheckBox, QMessageBox, QScrollArea,
    QProgressBar, QStackedWidget
)
from PyQt5.QtCore import Qt
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# === SQLAlchemy setup ===
Base = declarative_base()

class Packet(Base):
    __tablename__ = 'packets'
    id = Column(Integer, primary_key=True)
    packet_name = Column(String(255))

def setup_database(destination_folder):
    db_path = os.path.join(destination_folder, "inspire2.db")
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    return engine, Session, session

# === Main App Window ===
class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome to InspireSat-1 Data Tool")
        self.setGeometry(200, 200, 700, 500)

        self.stack = QStackedWidget()
        self.page1 = DataConversionPage(self)
        self.page2 = DataExportPage(self)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Welcome to InspireSat-1 Data Tool")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        subtitle = QLabel("Made by Sheik Saheera — Avionics Branch")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; font-style: italic;")

        btn_page1 = QPushButton("Go to Page 1: Data Conversion into DB")
        btn_page2 = QPushButton("Go to Page 2: Data Export")
        btn_page1.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_page2.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(btn_page1)
        layout.addWidget(btn_page2)
        layout.addStretch()

        home_page = QWidget()
        home_page.setLayout(layout)

        self.stack.addWidget(home_page)
        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.stack)
        self.setLayout(outer_layout)

# === Page 1 ===
class DataConversionPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Data Conversion into DB")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Input folder
        input_layout = QHBoxLayout()
        self.input_path = QLineEdit()
        input_btn = QPushButton("Browse Input Folder")
        input_btn.clicked.connect(self.browse_input)
        input_layout.addWidget(QLabel("Input Folder:"))
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(input_btn)
        layout.addLayout(input_layout)

        # Destination folder
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        output_btn = QPushButton("Browse Destination Folder")
        output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(QLabel("Destination Folder:"))
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_btn)
        layout.addLayout(output_layout)

        # Start button
        self.start_btn = QPushButton("Start Conversion")
        self.start_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.start_btn)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Back
        back_btn = QPushButton("Back to Home")
        back_btn.clicked.connect(lambda: self.parent.stack.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_path.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.output_path.setText(folder)

    def start_conversion(self):
        input_folder = self.input_path.text()
        output_folder = self.output_path.text()

        if not os.path.isdir(input_folder) or not os.path.isdir(output_folder):
            QMessageBox.critical(self, "Error", "Please select valid folders.")
            return

        engine, Session, session = setup_database(output_folder)
        total_files = 0
        all_csv_paths = []

        for root, dirs, files in os.walk(input_folder):
            for file in files:
                if file.endswith(".csv"):
                    all_csv_paths.append((root, file))
        total_files = len(all_csv_paths)

        if total_files == 0:
            QMessageBox.information(self, "No CSVs", "No CSV files found.")
            return

        processed = 0
        for folder, file in all_csv_paths:
            try:
                filepath = os.path.join(folder, file)
                sample = pd.read_csv(filepath, nrows=1)
                header_exists = not all(str(col).isdigit() for col in sample.columns)
                df = pd.read_csv(filepath) if header_exists else pd.read_csv(filepath, header=None)
                if not header_exists:
                    df.columns = [f'val_{i}' for i in range(df.shape[1])]
                foldername = os.path.basename(os.path.dirname(filepath))
                tablename = f"{foldername}_{file.replace('.csv', '')}".replace(" ", "_")
                df.to_sql(name=tablename, con=engine, if_exists='replace', index=False)
                if not session.query(Packet).filter_by(packet_name=file).first():
                    session.add(Packet(packet_name=file))
                    session.commit()
                processed += 1
                self.progress.setValue(int((processed / total_files) * 100))
            except Exception as e:
                print(f"Error: {e}")

        QMessageBox.information(self, "Done", f"Processed {processed} of {total_files} files.")
        self.progress.setValue(100)

# === Page 2 ===
class DataExportPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.column_checkboxes = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Data Export")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # DB input
        db_layout = QHBoxLayout()
        self.db_input = QLineEdit()
        db_browse = QPushButton("Browse")
        db_browse.clicked.connect(self.browse_db)
        db_layout.addWidget(QLabel("Database Input (SQLite3):"))
        db_layout.addWidget(self.db_input)
        db_layout.addWidget(db_browse)
        layout.addLayout(db_layout)

        # Fetch data button
        fetch_btn = QPushButton("Fetch Data")
        fetch_btn.clicked.connect(self.fetch_columns)
        layout.addWidget(fetch_btn)

        # Scroll area for checkboxes
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        # Export button
        export_btn = QPushButton("Export Data as CSV")
        export_btn.clicked.connect(self.export_csv)
        layout.addWidget(export_btn)

        # Back
        back_btn = QPushButton("Back to Home")
        back_btn.clicked.connect(lambda: self.parent.stack.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def browse_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select SQLite DB", "", "Database Files (*.db)")
        if path:
            self.db_input.setText(path)

    def fetch_columns(self):
        db_path = self.db_input.text()
        if not os.path.isfile(db_path):
            QMessageBox.critical(self, "Error", "Invalid database path.")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for cb in self.column_checkboxes:
            cb.setParent(None)
        self.column_checkboxes.clear()

        for (table,) in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            for col in cursor.fetchall():
                cb = QCheckBox(f"{table}.{col[1]}")
                self.scroll_layout.addWidget(cb)
                self.column_checkboxes.append(cb)

        conn.close()

    def export_csv(self):
        selected = [cb.text() for cb in self.column_checkboxes if cb.isChecked()]
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select columns to export.")
            return

        db_path = self.db_input.text()
        table_column_map = {}
        for entry in selected:
            table, column = entry.split(".")
            table_column_map.setdefault(table, []).append(column)

        conn = sqlite3.connect(db_path)
        final_df = pd.DataFrame()
        for table, cols in table_column_map.items():
            df = pd.read_sql_query(f"SELECT {', '.join(cols)} FROM {table}", conn)
            final_df = pd.concat([final_df, df], axis=1)

        conn.close()

        save_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if save_path:
            final_df.to_csv(save_path, index=False)
            QMessageBox.information(self, "Success", f"Data exported to:\n{save_path}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
