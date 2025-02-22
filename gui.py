import sys
import os
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit,
    QRadioButton, QComboBox, QCheckBox, QFileDialog, QVBoxLayout, QHBoxLayout,
    QTextEdit, QMessageBox
)
from converter import convert_file

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAD File Converter")
        self.setWindowIcon(QIcon("resources/icon.png"))
        self.resize(650, 500)
        self.init_ui()
    
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Mode selection: Single file vs Folder
        mode_layout = QHBoxLayout()
        self.file_radio = QRadioButton("Single File")
        self.folder_radio = QRadioButton("Folder")
        self.file_radio.setChecked(True)
        mode_layout.addWidget(self.file_radio)
        mode_layout.addWidget(self.folder_radio)
        main_layout.addLayout(mode_layout)
        
        # Input selection
        input_layout = QHBoxLayout()
        self.input_label = QLabel("Input:")
        self.input_line = QLineEdit()
        self.input_button = QPushButton("Select Input")
        self.input_button.clicked.connect(self.select_input)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.input_button)
        main_layout.addLayout(input_layout)
        
        # Output folder selection
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output Folder:")
        self.output_line = QLineEdit()
        self.output_button = QPushButton("Select Output Folder")
        self.output_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_line)
        output_layout.addWidget(self.output_button)
        main_layout.addLayout(output_layout)
        
        # Output format selection (including STL)
        format_layout = QHBoxLayout()
        self.format_label = QLabel("Output Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["step", "iges", "brep", "stl"])
        self.format_combo.currentTextChanged.connect(self.format_changed)
        format_layout.addWidget(self.format_label)
        format_layout.addWidget(self.format_combo)
        main_layout.addLayout(format_layout)
        
        # Sewing (joining) option (for IGES)
        self.sew_checkbox = QCheckBox("Attempt to join IGES surfaces into a solid upon conversion")
        self.sew_checkbox.setEnabled(False)
        main_layout.addWidget(self.sew_checkbox)
        
        # STL deflection input (only enabled for STL)
        stl_layout = QHBoxLayout()
        self.deflection_label = QLabel("STL Deflection:")
        self.deflection_line = QLineEdit("0.1")
        stl_layout.addWidget(self.deflection_label)
        stl_layout.addWidget(self.deflection_line)
        main_layout.addLayout(stl_layout)
        self.deflection_label.setEnabled(False)
        self.deflection_line.setEnabled(False)
        
        # Convert button
        self.convert_button = QPushButton("Convert")
        self.convert_button.clicked.connect(self.convert)
        main_layout.addWidget(self.convert_button)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)
    
    def select_input(self):
        if self.file_radio.isChecked():
            filename, _ = QFileDialog.getOpenFileName(
                self, "Select CAD File", "", "CAD Files (*.iges *.igs *.step *.stp *.brep)"
            )
            if filename:
                self.input_line.setText(filename)
                self.check_sew_option(filename)
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
            if folder:
                self.input_line.setText(folder)
                self.check_sew_option(folder, folder_mode=True)
    
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_line.setText(folder)
    
    def format_changed(self, text):
        if text == "stl":
            self.deflection_label.setEnabled(True)
            self.deflection_line.setEnabled(True)
        else:
            self.deflection_label.setEnabled(False)
            self.deflection_line.setEnabled(False)
    
    def check_sew_option(self, path, folder_mode=False):
        if folder_mode:
            for f in os.listdir(path):
                if f.lower().endswith(('.iges', '.igs')):
                    self.sew_checkbox.setEnabled(True)
                    return
            self.sew_checkbox.setEnabled(False)
        else:
            if path.lower().endswith(('.iges', '.igs')):
                self.sew_checkbox.setEnabled(True)
            else:
                self.sew_checkbox.setEnabled(False)
    
    def convert(self):
        self.log_text.clear()
        mode = "file" if self.file_radio.isChecked() else "folder"
        input_path = self.input_line.text().strip()
        output_folder = self.output_line.text().strip()
        output_format = self.format_combo.currentText().strip().lower()
        sew = self.sew_checkbox.isChecked()
        stl_deflection = None
        if output_format == "stl":
            try:
                stl_deflection = float(self.deflection_line.text().strip())
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for STL deflection.")
                return
        
        if mode == "file":
            if not os.path.isfile(input_path):
                QMessageBox.warning(self, "Invalid Input", "The selected input file does not exist.")
                return
            files = [input_path]
        else:
            if not os.path.isdir(input_path):
                QMessageBox.warning(self, "Invalid Input", "The selected input folder does not exist.")
                return
            files = [os.path.join(input_path, f) for f in os.listdir(input_path)
                     if f.lower().endswith(('.iges', '.igs', '.step', '.stp', '.brep'))]
            if not files:
                QMessageBox.warning(self, "No Files", "No supported CAD files found in the folder.")
                return
        
        total = len(files)
        successes = 0
        skips = 0
        failures = 0
        
        for file in files:
            self.log_text.append(f"Processing file: {file}")
            try:
                result = convert_file(
                    file, output_format, output_folder,
                    sew, batch_mode=(mode=="folder"), stl_deflection=stl_deflection
                )
                if isinstance(result, tuple):
                    status, msg = result
                    if status == "skipped":
                        self.log_text.append(f"  ❗ Skipped conversion (same type): {msg}\n")
                        skips += 1
                    elif status == "message":
                        self.log_text.append(f"  ❗ {msg}\n")
                        skips += 1
                    elif status == "success":
                        self.log_text.append(f"  🎉 Converted to: {msg}\n")
                        successes += 1
                else:
                    self.log_text.append(f"  🎉 Converted to: {result}\n")
                    successes += 1
            except Exception as e:
                self.log_text.append(f"  😔 Failed to convert {file}: {e}\n")
                failures += 1
        
        summary = (f"{'Batch' if mode=='folder' else 'Conversion'} completed.\n"
                   f"Total files processed: {total}\n"
                   f"Successful conversions: {successes}\n"
                   f"Skipped conversions: {skips}\n"
                   f"Failed conversions: {failures}")
        self.log_text.append(summary)
        QMessageBox.information(self, "Conversion Complete", summary)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set Fusion style
    app.setStyle("Fusion")
    
    # Define a dark palette
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
    dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 0, 0))
    app.setPalette(dark_palette)
    
    # Set custom style sheet for a uhhhhhhh modern look
    app.setStyleSheet("""
        QMainWindow {
            background-color: #353535;
        }
        QLabel, QLineEdit, QComboBox, QCheckBox, QRadioButton {
            font-size: 14px;
        }
        QPushButton {
            background-color: #5A5A5A;
            color: white;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #6A6A6A;
        }
        QTextEdit {
            background-color: #2D2D2D;
            color: white;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
