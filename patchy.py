#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt6 UI for Patchy, using patchy_core.py.

New in this version:
- 'File diff' tab: per-file diff next to the full unified diff
- Prev / Next change navigation (Original ↔ Preview)
- Optional sync scroll between Original and Preview
- Collapsible unchanged blocks in Preview (folded mode with placeholders)
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, Tuple, Dict

from PyQt6.QtCore import Qt, QRect, QSize, QTimer
from PyQt6.QtGui import (
    QColor, QPainter, QPalette, QFont, QSyntaxHighlighter, QTextCharFormat
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSplitter, QMessageBox,
    QCheckBox, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QFrame, QTabWidget
)

from patchy_core import (
    UnifiedDiffParser, DiffApplier, FilePatch, PatchParseError, PatchApplyError,
    summarize_patch, ApplyResult, format_file_diff
)

# ---------------- Logging ----------------

def log(msg: str):
    print(msg, flush=True)

# ---------------- Theme helpers ----------------

def is_windows_dark() -> Optional[bool]:
    if sys.platform.startswith('win'):
        try:
            from PyQt6.QtCore import QSettings
            s = QSettings('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize',
                          QSettings.Format.NativeFormat)
            val = s.value('AppsUseLightTheme', None)
            if val is None:
                return None
            return str(val) == '0'  # 0 means dark
        except Exception:
            return None
    return None

def palette_is_dark(pal: QPalette) -> bool:
    c = pal.window().color()
    l = 0.2126 * c.redF() + 0.7152 * c.greenF() + 0.0722 * c.blueF()
    return l < 0.5

def make_dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    p.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    return p

# ---------------- Code editor with line numbers ----------------

class LineNumberArea(QWidget):
    def __init__(self, editor: 'CodeEditor'):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

        mono = QFont("Consolas" if sys.platform.startswith("win") else "Monospace")
        mono.setStyleHint(QFont.StyleHint.TypeWriter)
        self.setFont(mono)

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space + 6

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(),
                                                 self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        pal = self.palette()
        painter.fillRect(event.rect(), pal.alternateBase())
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(pal.mid().color())
                fm = self.fontMetrics()
                painter.drawText(0, top, self._line_number_area.width()-4, fm.height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

# ---------------- Highlighters ----------------

def _colors_for_palette(pal: QPalette) -> Tuple[QColor, QColor, QColor, QColor]:
    """Return (green_add, red_del, header, added_bg)."""
    dark = palette_is_dark(pal)
    if dark:
        green = QColor(80, 200, 120)
        red = QColor(255, 110, 110)
        header = QColor(120, 170, 255)
        added_bg = QColor(30, 70, 30); added_bg.setAlpha(110)
    else:
        green = QColor(0, 128, 0)
        red = QColor(200, 0, 0)
        header = QColor(0, 70, 170)
        added_bg = QColor(173, 255, 173); added_bg.setAlpha(120)
    return green, red, header, added_bg

class UnifiedDiffHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, palette: QPalette):
        super().__init__(doc)
        g, r, hdr, _ = _colors_for_palette(palette)
        self.f_add = QTextCharFormat();  self.f_add.setForeground(g)
        self.f_del = QTextCharFormat();  self.f_del.setForeground(r)
        self.f_hdr = QTextCharFormat();  self.f_hdr.setForeground(hdr)

    def highlightBlock(self, text: str):
        if text.startswith('@@') or text.startswith('+++') or text.startswith('---'):
            self.setFormat(0, len(text), self.f_hdr)
            return
        if not text:
            return
        ch = text[0]
        if ch == '+':
            self.setFormat(0, len(text), self.f_add)
        elif ch == '-':
            self.setFormat(0, len(text), self.f_del)

class PatchedHighlighter(QSyntaxHighlighter):
    """Highlights added lines in Preview (indices are for the displayed text)."""
    def __init__(self, doc, palette: QPalette):
        super().__init__(doc)
        *_, added_bg = _colors_for_palette(palette)
        self._added_lines: set[int] = set()
        self.f_added = QTextCharFormat()
        self.f_added.setBackground(added_bg)

    def set_added_lines(self, indices: List[int]):
        self._added_lines = set(indices)
        self.rehighlight()

    def highlightBlock(self, text: str):
        ln = self.currentBlock().blockNumber()
        if ln in self._added_lines:
            self.setFormat(0, len(text), self.f_added)

class RemovedHighlighter(QSyntaxHighlighter):
    """Highlights deleted lines (by original indices) in the Original pane."""
    def __init__(self, doc, palette: QPalette):
        super().__init__(doc)
        _, red, _, _ = _colors_for_palette(palette)
        self._removed_lines: set[int] = set()
        self.f_removed = QTextCharFormat()
        bg = QColor(red); bg.setAlpha(60)
        self.f_removed.setBackground(bg)

    def set_removed_lines(self, original_indices: List[int]):
        self._removed_lines = set(original_indices)
        self.rehighlight()

    def highlightBlock(self, text: str):
        ln = self.currentBlock().blockNumber()
        if ln in self._removed_lines:
            self.setFormat(0, len(text), self.f_removed)

# ---------------- Main Window ----------------

class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.setWindowTitle("Patchy — patch applier")
        self.resize(1500, 950)

        # state
        self.original_path: Optional[str] = None
        self.root_folder: Optional[str] = None
        self.file_patches: List[FilePatch] = []
        self.applier = DiffApplier()

        # preview state helpers
        self.fold_context = 3
        self.fold_enabled = False
        self.sync_scroll_enabled = False
        self._display_line_map: List[Optional[int]] = []  # displayed line -> real preview line (None for placeholders)
        self._added_blocks: List[int] = []
        self._removed_blocks: List[int] = []

        # Actions / controls
        self.open_file_btn = QPushButton("Open File")
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_diff_btn = QPushButton("Open Diff")
        self.preview_btn = QPushButton("Preview Selected")
        self.save_as_btn = QPushButton("Save Selected As")
        self.save_inplace_btn = QPushButton("Save Selected In Place")
        self.apply_all_btn = QPushButton("Apply All to Folder")
        self.backup_checkbox = QCheckBox("Create .bak on in-place writes"); self.backup_checkbox.setChecked(True)
        self.live_checkbox = QCheckBox("Live Preview"); self.live_checkbox.setChecked(True)

        # Path indicator
        self.path_line = QLineEdit(); self.path_line.setReadOnly(True); self.path_line.setPlaceholderText("No context")

        # Summary + controls row for preview
        self.summary_label = QLabel("(no diff)")
        self.fold_checkbox = QCheckBox("Fold unchanged")
        self.fold_checkbox.stateChanged.connect(self._on_fold_toggled)
        self.sync_checkbox = QCheckBox("Sync scroll")
        self.sync_checkbox.stateChanged.connect(self._on_sync_toggled)
        self.prev_btn = QPushButton("Prev change")
        self.next_btn = QPushButton("Next change")
        self.prev_btn.clicked.connect(self.on_prev_change)
        self.next_btn.clicked.connect(self.on_next_change)

        # Layout top
        row1 = QHBoxLayout()
        for w in (self.open_file_btn, self.open_folder_btn, self.open_diff_btn,
                  self.preview_btn, self.save_as_btn, self.save_inplace_btn, self.apply_all_btn,
                  self.backup_checkbox, self.live_checkbox):
            row1.addWidget(w)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Context:"))
        row2.addWidget(self.path_line)

        # Sidebar: file list
        self.files_list = QListWidget()
        self.files_list.setSelectionMode(self.files_list.SelectionMode.SingleSelection)

        # Editors
        self.original_edit = CodeEditor()
        self.original_edit.setPlaceholderText("Original content here")

        # Right: tabs for unified diff + file diff
        self.diff_edit = CodeEditor()
        self.diff_edit.setPlaceholderText("Paste unified diff here or use Open Diff")
        self.file_diff_edit = CodeEditor()
        self.file_diff_edit.setPlaceholderText("Per-file diff will appear here")
        self.file_diff_edit.setReadOnly(True)

        # Preview
        self.patched_edit = CodeEditor()
        self.patched_edit.setPlaceholderText("Patched preview will appear here")
        self.patched_edit.setReadOnly(True)

        # Highlighters
        self.diff_highlighter = UnifiedDiffHighlighter(self.diff_edit.document(), self.app.palette())
        self.file_diff_highlighter = UnifiedDiffHighlighter(self.file_diff_edit.document(), self.app.palette())
        self.patch_highlighter = PatchedHighlighter(self.patched_edit.document(), self.app.palette())
        self.removed_highlighter = RemovedHighlighter(self.original_edit.document(), self.app.palette())

        # Right panel (diff tabs + preview)
        right_split = QSplitter(Qt.Orientation.Vertical)
        rtop = QWidget(); rtop_v = QVBoxLayout(rtop)
        rtop_tabs = QTabWidget()
        rtop_tabs.addTab(self.diff_edit, "Unified diff")
        rtop_tabs.addTab(self.file_diff_edit, "File diff")
        rtop_v.addWidget(rtop_tabs)

        rbot = QWidget(); rbot_v = QVBoxLayout(rbot)
        header = QHBoxLayout()
        header.addWidget(QLabel("Preview"))
        header.addStretch(1)
        header.addWidget(self.prev_btn)
        header.addWidget(self.next_btn)
        header.addSpacing(12)
        header.addWidget(self.sync_checkbox)
        header.addWidget(self.fold_checkbox)
        header.addSpacing(12)
        header.addWidget(self.summary_label)
        rbot_v.addLayout(header)
        rbot_v.addWidget(self.patched_edit)

        right_split.addWidget(rtop); right_split.addWidget(rbot)
        right_split.setSizes([450, 500])

        # Middle panel (original)
        middle_panel = QWidget(); mpv = QVBoxLayout(middle_panel)
        mpv.addWidget(QLabel("Original"))
        mpv.addWidget(self.original_edit)

        # Left panel (files)
        left_panel = QWidget(); lpv = QVBoxLayout(left_panel)
        lpv.addWidget(QLabel("Files in diff"))
        lpv.addWidget(self.files_list)

        left_split = QSplitter(Qt.Orientation.Vertical)
        left_split.addWidget(left_panel)

        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.addWidget(left_split)
        main_split.addWidget(middle_panel)
        main_split.addWidget(right_split)
        main_split.setSizes([260, 560, 680])

        # Central
        root = QWidget(); rv = QVBoxLayout(root)
        rv.addLayout(row1)
        rv.addLayout(row2)
        rv.addWidget(main_split)
        self.setCentralWidget(root)

        # Signals
        self.open_file_btn.clicked.connect(self.on_open_file)
        self.open_folder_btn.clicked.connect(self.on_open_folder)
        self.open_diff_btn.clicked.connect(self.on_open_diff)
        self.preview_btn.clicked.connect(self.on_preview_selected)
        self.save_as_btn.clicked.connect(self.on_save_selected_as)
        self.save_inplace_btn.clicked.connect(self.on_save_selected_in_place)
        self.apply_all_btn.clicked.connect(self.on_apply_all_to_folder)
        self.files_list.currentItemChanged.connect(self.on_file_selected)

        # Debouncers
        self.preview_timer = QTimer(self); self.preview_timer.setSingleShot(True); self.preview_timer.setInterval(350)
        self.preview_timer.timeout.connect(self._refresh_preview)

        self.reparse_timer = QTimer(self); self.reparse_timer.setSingleShot(True); self.reparse_timer.setInterval(400)
        self.reparse_timer.timeout.connect(self._reparse_diff_from_editor)

        self.original_edit.textChanged.connect(self._maybe_preview_after_edit)
        self.diff_edit.textChanged.connect(self._maybe_reparse_and_preview)

        # Theme watcher
        self._last_dark = palette_is_dark(self.app.palette())
        self.theme_timer = QTimer(self); self.theme_timer.setInterval(30000)
        self.theme_timer.timeout.connect(self._check_theme_change); self.theme_timer.start()

        # Sync scroll signals (enable/disable via checkbox)
        self.original_edit.verticalScrollBar().valueChanged.connect(self._on_orig_scroll)
        self.patched_edit.verticalScrollBar().valueChanged.connect(self._on_patch_scroll)
        self._guard_sync = False

        self.update_buttons()

    # ---- UI helpers ----

    def update_buttons(self):
        in_folder = self.root_folder is not None
        has_diff = len(self.file_patches) > 0
        has_selection = self.files_list.currentItem() is not None
        self.apply_all_btn.setEnabled(in_folder and has_diff)
        self.save_inplace_btn.setEnabled(has_selection and (in_folder or self.original_path is not None))
        self.save_as_btn.setEnabled(has_selection and self.patched_edit.toPlainText() != "")
        self.preview_btn.setEnabled(has_selection)
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)

    def set_context_label(self):
        if self.root_folder:
            self.path_line.setText(f"Folder: {self.root_folder}")
        elif self.original_path:
            self.path_line.setText(f"File: {self.original_path}")
        else:
            self.path_line.setText("No context")

    def populate_files_list(self):
        current = self.current_file_patch()
        current_path = (current.new_path or current.old_path) if current else None
        self.files_list.clear()
        for fp in self.file_patches:
            display = fp.new_path or fp.old_path or "<unknown>"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, fp)
            self.files_list.addItem(item)
        # restore selection
        if current_path:
            for i in range(self.files_list.count()):
                it = self.files_list.item(i)
                fp = it.data(Qt.ItemDataRole.UserRole)
                if (fp.new_path or fp.old_path) == current_path:
                    self.files_list.setCurrentRow(i)
                    break
        elif self.files_list.count() > 0:
            self.files_list.setCurrentRow(0)

    def current_file_patch(self) -> Optional[FilePatch]:
        it = self.files_list.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def load_original_for_patch(self, fp: FilePatch) -> str:
        candidates = [p for p in [fp.new_path, fp.old_path] if p]
        for rel in candidates:
            if self.root_folder:
                path = os.path.join(self.root_folder, rel)
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        txt = f.read()
                    self.original_path = path
                    return txt
            if rel and os.path.isfile(rel):
                with open(rel, 'r', encoding='utf-8') as f:
                    txt = f.read()
                self.original_path = os.path.abspath(rel)
                return txt
        return self.original_edit.toPlainText()

    # ---- Theme watcher ----

    def _save_scroll_positions(self):
        return {
            'orig': self.original_edit.verticalScrollBar().value(),
            'diff': self.diff_edit.verticalScrollBar().value(),
            'filediff': self.file_diff_edit.verticalScrollBar().value(),
            'patch': self.patched_edit.verticalScrollBar().value(),
        }

    def _restore_scroll_positions(self, st: Dict[str, int]):
        self.original_edit.verticalScrollBar().setValue(st['orig'])
        self.diff_edit.verticalScrollBar().setValue(st['diff'])
        self.file_diff_edit.verticalScrollBar().setValue(st['filediff'])
        self.patched_edit.verticalScrollBar().setValue(st['patch'])

    def _check_theme_change(self):
        win_dark = is_windows_dark()
        current_is_dark = palette_is_dark(self.app.palette())
        target_dark = (True if win_dark is True else False if win_dark is False else current_is_dark)
        if target_dark == self._last_dark:
            return

        scroll = self._save_scroll_positions()
        if target_dark:
            self.app.setStyle('Fusion')
            self.app.setPalette(make_dark_palette())
            log('Theme watcher: applied dark')
        else:
            self.app.setPalette(QApplication.style().standardPalette())
            log('Theme watcher: reverted to light')

        self._last_dark = target_dark
        self.diff_highlighter.rehighlight()
        self.file_diff_highlighter.rehighlight()
        self.patch_highlighter.rehighlight()
        self.removed_highlighter.rehighlight()
        self._restore_scroll_positions(scroll)

    # ---- Live preview plumbing ----

    def _maybe_preview_after_edit(self):
        if self.live_checkbox.isChecked():
            self.preview_timer.start()

    def _maybe_reparse_and_preview(self):
        if self.live_checkbox.isChecked():
            self.reparse_timer.start()

    def _reparse_diff_from_editor(self):
        txt = self.diff_edit.toPlainText()
        if not txt.strip():
            self.file_patches = []
            self.populate_files_list()
            self.patched_edit.clear()
            self.file_diff_edit.clear()
            self.patch_highlighter.set_added_lines([])
            self.removed_highlighter.set_removed_lines([])
            self.summary_label.setText("(no diff)")
            self.update_buttons()
            return
        try:
            parser = UnifiedDiffParser()
            patches = parser.parse(txt)
            self.file_patches = patches
            self.populate_files_list()
            self._refresh_preview()
            log(f"Reparsed diff: {len(patches)} file(s)")
        except PatchParseError as e:
            log(f"Diff parse error (live): {e}")

    # ---- Slots ----

    def on_open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All files (*.*)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                txt = f.read()
            self.original_path = path
            self.root_folder = None
            self.original_edit.setPlainText(txt)
            self.set_context_label()
            log(f"Opened file: {path}")
            self.update_buttons()
            self._refresh_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
            log(f"ERROR opening file: {e}")

    def on_open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open folder", "")
        if not folder:
            return
        self.root_folder = folder
        self.original_path = None
        self.original_edit.clear()
        self.patched_edit.clear()
        self.file_diff_edit.clear()
        self.patch_highlighter.set_added_lines([])
        self.removed_highlighter.set_removed_lines([])
        self.set_context_label()
        log(f"Opened folder: {folder}")
        self.update_buttons()
        self._refresh_preview()

    def on_open_diff(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open diff", "", "Patch files (*.patch *.diff);;All files (*.*)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                txt = f.read()
            self.diff_edit.setPlainText(txt)
            parser = UnifiedDiffParser()
            self.file_patches = parser.parse(txt)
            self.populate_files_list()
            if self.files_list.count() > 0:
                self.files_list.setCurrentRow(0)
            log(f"Loaded diff: {path} with {len(self.file_patches)} file(s)")
            self.update_buttons()
            self._refresh_preview()
        except PatchParseError as e:
            QMessageBox.critical(self, "Parse error", f"Failed to parse diff:\n{e}")
            log(f"ERROR parsing diff: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open diff: {e}")
            log(f"ERROR opening diff: {e}")

    def on_file_selected(self, _cur: QListWidgetItem, _prev: QListWidgetItem):
        fp = self.current_file_patch()
        if not fp:
            return
        txt = self.load_original_for_patch(fp)
        if txt:
            self.original_edit.setPlainText(txt)
        self.patched_edit.clear()
        self.file_diff_edit.clear()
        self.patch_highlighter.set_added_lines([])
        self.removed_highlighter.set_removed_lines([])
        self.update_buttons()
        self._refresh_preview()

    def on_preview_selected(self):
        fp = self.current_file_patch()
        if not fp:
            QMessageBox.information(self, "No selection", "Select a file from the diff list.")
            return
        if self.original_edit.toPlainText() == "":
            txt = self.load_original_for_patch(fp)
            if txt:
                self.original_edit.setPlainText(txt)
        try:
            self._refresh_preview()
        except PatchApplyError as e:
            QMessageBox.critical(self, "Apply error", f"Failed to apply patch:\n{e}")
            log(f"ERROR applying patch: {e}")

    def on_save_selected_as(self):
        if self.patched_edit.toPlainText() == "":
            QMessageBox.information(self, "Nothing to save", "Generate a preview first.")
            return
        suggested = self._suggest_output_path()
        path, _ = QFileDialog.getSaveFileName(self, "Save patched file", suggested, "All files (*.*)")
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.patched_edit.toPlainText())
            QMessageBox.information(self, "Saved", f"Patched file saved to:\n{path}")
            log(f"Saved patched file: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Failed to save: {e}")
            log(f"ERROR saving file: {e}")

    def on_save_selected_in_place(self):
        fp = self.current_file_patch()
        if not fp:
            QMessageBox.information(self, "No selection", "Select a file from the diff list.")
            return
        if self.patched_edit.toPlainText() == "":
            QMessageBox.information(self, "Nothing to save", "Generate a preview first.")
            return
        target = None
        for rel in [fp.new_path, fp.old_path]:
            if not rel:
                continue
            if self.root_folder:
                cand = os.path.join(self.root_folder, rel)
                if os.path.isdir(os.path.dirname(cand)):
                    target = cand
                    break
            elif self.original_path:
                target = self.original_path
                break
        if not target:
            QMessageBox.warning(self, "No target path", "Cannot resolve target path to save.")
            return

        try:
            if self.backup_checkbox.isChecked() and os.path.isfile(target):
                with open(target + ".bak", 'w', encoding='utf-8') as f:
                    f.write(self.original_edit.toPlainText())
                log(f"Backup written: {target}.bak")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(self.patched_edit.toPlainText())
            QMessageBox.information(self, "Saved", f"Patched file written in place:\n{target}")
            log(f"Patched file saved in place: {target}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Failed to write in place: {e}")
            log(f"ERROR saving in place: {e}")

    def on_apply_all_to_folder(self):
        if not self.root_folder:
            QMessageBox.warning(self, "No folder", "Open a folder first.")
            return
        if not self.file_patches:
            QMessageBox.information(self, "No diff", "Open a unified diff first.")
            return

        failures: List[str] = []
        successes: List[str] = []
        for fp in self.file_patches:
            rel = fp.new_path or fp.old_path or "<unknown>"
            try:
                src_text = self.load_original_for_patch(fp)
                if src_text == "":
                    raise PatchApplyError("Source empty or not found")
                res = self.applier.apply(src_text, fp)
                target = os.path.join(self.root_folder, rel)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                if self.backup_checkbox.isChecked() and os.path.isfile(target):
                    with open(target + ".bak", 'w', encoding='utf-8') as f:
                        f.write(src_text)
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(res.text)
                successes.append(rel)
            except Exception as e:
                failures.append(f"{rel}: {e}")

        msg = f"Applied: {len(successes)} file(s)\n"
        if failures:
            msg += f"Failed: {len(failures)}\n\n" + "\n".join(failures[:10])
            if len(failures) > 10:
                msg += f"\n... and {len(failures) - 10} more"
        QMessageBox.information(self, "Apply All", msg)
        log(msg)

    # ---- Core preview ----

    def _refresh_preview(self):
        fp = self.current_file_patch()
        if not fp:
            self.summary_label.setText("(no file selected)")
            return

        # ensure original text loaded
        if self.original_edit.toPlainText() == "":
            txt = self.load_original_for_patch(fp)
            if txt:
                self.original_edit.setPlainText(txt)

        # update file-diff tab
        try:
            self.file_diff_edit.setPlainText(format_file_diff(fp))
        except Exception:
            self.file_diff_edit.clear()

        # compute & render
        try:
            res: ApplyResult = self.applier.apply(self.original_edit.toPlainText(), fp)

            # Prepare either full or folded preview content + line map
            if self.fold_enabled:
                display_text, line_map = self._render_folded_preview(res)
            else:
                display_text = res.text
                # identity map for each displayed line -> same index
                line_map = list(range(len(res.text.splitlines())))

            # Save preview scroll, update text, restore scroll
            patch_scroll = self.patched_edit.verticalScrollBar().value()
            self.patched_edit.setPlainText(display_text)
            self.patched_edit.verticalScrollBar().setValue(patch_scroll)

            # Highlight adds in Preview (translate res.added_lines into displayed indices)
            display_added = self._map_added_to_display(res.added_lines, line_map)
            self.patch_highlighter.set_added_lines(display_added)

            # Highlight deletions in Original by original indices
            self.removed_highlighter.set_removed_lines(res.removed_lines_original)

            # Update summary bar
            adds, dels, hunks = summarize_patch(fp)
            self.summary_label.setText(f"<b>+{adds}</b> / <b>-{dels}</b> across {hunks} hunks")

            # Cache for navigation + sync scroll
            self._display_line_map = line_map
            self._added_blocks = _contiguous_blocks(display_added)
            self._removed_blocks = _contiguous_blocks(res.removed_lines_original)

            log("Live preview refreshed")
            self.update_buttons()
        except PatchApplyError as e:
            log(f"Live preview apply error: {e}")

    # ---- Folding / mapping helpers ----

    def _render_folded_preview(self, res: ApplyResult) -> Tuple[str, List[Optional[int]]]:
        """
        Build folded preview text showing +/- fold_context lines around changes,
        replacing gaps with a placeholder line.
        Returns (display_text, display_line_map).
        """
        lines = res.text.splitlines()
        L = len(lines)
        # Build set of interesting lines to keep: added lines expanded by context
        keep = set()
        for idx in res.added_lines:
            for k in range(max(0, idx - self.fold_context), min(L, idx + self.fold_context + 1)):
                keep.add(k)
        # Always keep file top/bottom small context
        for k in range(min(L, self.fold_context)):
            keep.add(k)
        for k in range(max(0, L - self.fold_context), L):
            keep.add(k)

        # Sort and coalesce into ranges
        keep_sorted = sorted(keep)
        ranges: List[Tuple[int, int]] = []
        if keep_sorted:
            s = e = keep_sorted[0]
            for v in keep_sorted[1:]:
                if v == e + 1:
                    e = v
                else:
                    ranges.append((s, e))
                    s = e = v
            ranges.append((s, e))

        display_lines: List[str] = []
        line_map: List[Optional[int]] = []
        cur = 0
        for (s, e) in ranges:
            if s > cur:
                skipped = s - cur
                display_lines.append(f"... {skipped} unchanged lines ...")
                line_map.append(None)  # placeholder
            for idx in range(s, e + 1):
                display_lines.append(lines[idx])
                line_map.append(idx)
            cur = e + 1
        if cur < L:
            skipped = L - cur
            display_lines.append(f"... {skipped} unchanged lines ...")
            line_map.append(None)

        return "\n".join(display_lines), line_map

    def _map_added_to_display(self, added_real: List[int], line_map: List[Optional[int]]) -> List[int]:
        real_to_display: Dict[int, int] = {}
        for i, r in enumerate(line_map):
            if r is not None and r not in real_to_display:
                real_to_display[r] = i
        out: List[int] = []
        for r in added_real:
            d = real_to_display.get(r)
            if d is not None:
                out.append(d)
        return out

    # ---- Navigation ----

    def on_prev_change(self):
        self._jump_change(prev=True)

    def on_next_change(self):
        self._jump_change(prev=False)

    def _jump_change(self, prev: bool):
        # decide which list to use based on focus: if preview has focus -> added blocks, else original -> removed
        use_preview = self.patched_edit.hasFocus() or not self.original_edit.hasFocus()
        blocks = self._added_blocks if use_preview else self._removed_blocks
        if not blocks:
            return
        editor = self.patched_edit if use_preview else self.original_edit
        current_line = editor.textCursor().blockNumber()
        # find nearest block start before/after current
        target = None
        if prev:
            for b in reversed(blocks):
                if b < current_line:
                    target = b
                    break
            if target is None:
                target = blocks[-1]
        else:
            for b in blocks:
                if b > current_line:
                    target = b
                    break
            if target is None:
                target = blocks[0]

        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, target)
        editor.setTextCursor(cursor)

    # ---- Sync scroll ----

    def _on_sync_toggled(self, state: int):
        self.sync_scroll_enabled = state == Qt.CheckState.Checked.value

    def _on_fold_toggled(self, state: int):
        self.fold_enabled = state == Qt.CheckState.Checked.value
        self._refresh_preview()

    def _on_orig_scroll(self, value: int):
        if not self.sync_scroll_enabled or self._guard_sync:
            return
        try:
            self._guard_sync = True
            self._sync_scroll(self.original_edit, self.patched_edit)
        finally:
            self._guard_sync = False

    def _on_patch_scroll(self, value: int):
        if not self.sync_scroll_enabled or self._guard_sync:
            return
        try:
            self._guard_sync = True
            self._sync_scroll(self.patched_edit, self.original_edit)
        finally:
            self._guard_sync = False

    def _sync_scroll(self, src: QPlainTextEdit, dst: QPlainTextEdit):
        sb_src = src.verticalScrollBar()
        sb_dst = dst.verticalScrollBar()
        # proportional sync - simple and robust; works fine even in folded mode
        if sb_src.maximum() > 0:
            ratio = sb_src.value() / sb_src.maximum()
            sb_dst.setValue(int(ratio * sb_dst.maximum()))

    # ---- Utils ----

    def _suggest_output_path(self) -> str:
        fp = self.current_file_patch()
        if fp:
            rel = fp.new_path or fp.old_path or "patched_output.txt"
            base = os.path.basename(rel)
            root, ext = os.path.splitext(base)
            return os.path.join(os.getcwd(), f"{root}.patched{ext if ext else '.txt'}")
        if self.original_path:
            root, ext = os.path.splitext(self.original_path)
            return f"{root}.patched{ext if ext else '.txt'}"
        return os.path.join(os.getcwd(), "patched_output.txt")

# ---- Helpers ----

def _contiguous_blocks(indices: List[int]) -> List[int]:
    """Return the start line of each contiguous block from a sorted list of indices."""
    if not indices:
        return []
    sorted_idx = sorted(indices)
    blocks = [sorted_idx[0]]
    for i in range(1, len(sorted_idx)):
        if sorted_idx[i] != sorted_idx[i-1] + 1:
            blocks.append(sorted_idx[i])
    return blocks

# ---------------- Entry ----------------

def main():
    app = QApplication(sys.argv)
    # Follow OS theme if already dark; don't force frequent repaint
    if is_windows_dark() is True and not palette_is_dark(app.palette()):
        app.setStyle('Fusion'); app.setPalette(make_dark_palette())

    w = MainWindow(app)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
