import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QLabel, QFormLayout
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import patch

# Set an application ID for Windows to show the app icon in the taskbar
try:
    from ctypes import windll
    myappid = 'mycompany.myproduct.subproduct.version'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class PatcherApp(QMainWindow):
    """
    A simple PyQt6 application to apply a .diff or .patch file to a source file.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Patcher Tool")
        self.setFixedSize(500, 220)
        
        # Set the window icon
        # You can replace 'patch_icon.png' with a path to your own icon file
        # For simplicity, we'll try to load it, but it's optional.
        if os.path.exists('patch_icon.png'):
            self.setWindowIcon(QIcon('patch_icon.png'))

        # --- Main Layout and Widgets ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        # --- File Selection Widgets ---
        self.source_file_edit = QLineEdit(self)
        self.source_file_edit.setPlaceholderText("Select the original file...")
        self.select_source_btn = QPushButton("Browse...")
        
        self.patch_file_edit = QLineEdit(self)
        self.patch_file_edit.setPlaceholderText("Select the .patch or .diff file...")
        self.select_patch_btn = QPushButton("Browse...")

        self.output_file_edit = QLineEdit(self)
        self.output_file_edit.setPlaceholderText("Select where to save the patched file...")
        self.select_output_btn = QPushButton("Save As...")

        form_layout.addRow("Source File:", self.source_file_edit)
        form_layout.addRow("", self.select_source_btn)
        form_layout.addRow("Patch File:", self.patch_file_edit)
        form_layout.addRow("", self.select_patch_btn)
        form_layout.addRow("Output File:", self.output_file_edit)
        form_layout.addRow("", self.select_output_btn)

        # --- Action Button and Status Label ---
        self.apply_btn = QPushButton("Apply Patch")
        self.apply_btn.setFixedHeight(40)
        self.status_label = QLabel("Ready. Select files to begin.")
        self.status_label.setStyleSheet("color: grey;")

        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.apply_btn)
        main_layout.addWidget(self.status_label)
        
        # --- Connect Signals to Slots ---
        self.select_source_btn.clicked.connect(self.select_source_file)
        self.select_patch_btn.clicked.connect(self.select_patch_file)
        self.select_output_btn.clicked.connect(self.select_output_file)
        self.apply_btn.clicked.connect(self.apply_patch)

        # Disable the apply button until all fields are filled
        self.source_file_edit.textChanged.connect(self.check_inputs)
        self.patch_file_edit.textChanged.connect(self.check_inputs)
        self.output_file_edit.textChanged.connect(self.check_inputs)
        self.check_inputs() # Initial check

    def check_inputs(self):
        """Enable the 'Apply Patch' button only if all file paths are set."""
        source = self.source_file_edit.text()
        patch_f = self.patch_file_edit.text()
        output = self.output_file_edit.text()
        self.apply_btn.setEnabled(bool(source and patch_f and output))

    def select_source_file(self):
        """Open a dialog to select the source file and suggest an output path."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Source File")
        if file_path:
            self.source_file_edit.setText(file_path)
            # Suggest an output file name
            path, ext = os.path.splitext(file_path)
            self.output_file_edit.setText(f"{path}_patched{ext}")

    def select_patch_file(self):
        """Open a dialog to select the patch file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Patch File", filter="Patch files (*.patch *.diff)")
        if file_path:
            self.patch_file_edit.setText(file_path)

    def select_output_file(self):
        """Open a dialog to set the output file path."""
        suggested_path = self.output_file_edit.text() or self.source_file_edit.text()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Patched File As", suggested_path)
        if file_path:
            self.output_file_edit.setText(file_path)

    def apply_patch(self):
        """Core function to apply the patch."""
        source_path = self.source_file_edit.text()
        patch_path = self.patch_file_edit.text()
        output_path = self.output_file_edit.text()

        try:
            # Read source and patch files in binary mode
            with open(source_path, 'rb') as f_source:
                source_bytes = f_source.read()
            
            with open(patch_path, 'rb') as f_patch:
                patch_bytes = f_patch.read()

            # Create patch set from the patch file content
            patch_set = patch.fromstring(patch_bytes)
            
            # Apply the patch in-memory
            patched_bytes = patch_set.apply(source_bytes)

            if patched_bytes is False:
                # This can happen if a hunk does not apply
                raise RuntimeError("Patch could not be applied cleanly. Check for conflicts.")

            # Write the patched content to the output file
            with open(output_path, 'wb') as f_out:
                f_out.write(patched_bytes)
            
            self.status_label.setText(f"✅ Success! Patched file saved to {os.path.basename(output_path)}")
            self.status_label.setStyleSheet("color: green;")

        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: red;")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PatcherApp()
    window.show()
    sys.exit(app.exec())