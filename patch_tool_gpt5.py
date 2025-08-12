import sys
import re
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QFileDialog, QLabel, QSplitter, QMessageBox, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt

# ---------- Logging ----------
def log(msg: str):
    print(msg, flush=True)

# ---------- Diff model ----------

@dataclass
class HunkLine:
    kind: str  # ' ', '+', '-'
    text: str  # without prefix

@dataclass
class Hunk:
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    lines: List[HunkLine] = field(default_factory=list)

@dataclass
class FilePatch:
    old_path: Optional[str]
    new_path: Optional[str]
    hunks: List[Hunk] = field(default_factory=list)

class PatchParseError(Exception):
    pass

class PatchApplyError(Exception):
    pass

class UnifiedDiffParser:
    RE_FROM = re.compile(r'^---\s+(?P<path>.+)$')
    RE_TO = re.compile(r'^\+\+\+\s+(?P<path>.+)$')
    RE_HUNK = re.compile(
        r'^@@\s*-\s*(?P<o_start>\d+)(?:,(?P<o_len>\d+))?\s+\+\s*(?P<n_start>\d+)(?:,(?P<n_len>\d+))?\s*@@'
    )

    @staticmethod
    def _clean_path(p: str) -> str:
        # Drop leading a/ b/ if present
        p = p.strip()
        if p.startswith("a/") or p.startswith("b/"):
            return p[2:]
        return p

    def parse(self, text: str) -> FilePatch:
        lines = text.splitlines()
        old_path = None
        new_path = None
        hunks: List[Hunk] = []
        cur_hunk: Optional[Hunk] = None

        i = 0
        saw_any_hunk = False
        while i < len(lines):
            line = lines[i]
            if line.startswith('---'):
                m = self.RE_FROM.match(line)
                if not m:
                    raise PatchParseError(f'Bad --- line: {line}')
                old_path = self._clean_path(m.group('path'))
                i += 1
                if i >= len(lines) or not lines[i].startswith('+++'):
                    raise PatchParseError('Expected +++ after ---')
                m2 = self.RE_TO.match(lines[i])
                if not m2:
                    raise PatchParseError(f'Bad +++ line: {lines[i]}')
                new_path = self._clean_path(m2.group('path'))
                i += 1
                continue

            if line.startswith('@@'):
                m = self.RE_HUNK.match(line)
                if not m:
                    raise PatchParseError(f'Bad hunk header: {line}')
                ostart = int(m.group('o_start'))
                olen = int(m.group('o_len') or '0')
                nstart = int(m.group('n_start'))
                nlen = int(m.group('n_len') or '0')
                cur_hunk = Hunk(ostart, olen, nstart, nlen, [])
                hunks.append(cur_hunk)
                saw_any_hunk = True
                i += 1
                # collect hunk lines until next hunk or file header or end
                while i < len(lines):
                    l = lines[i]
                    if l.startswith('@@') or l.startswith('---') or l.startswith('diff '):
                        break
                    if not l:
                        # empty lines are valid context or addition/deletion if prefixed
                        # unified diff lines must start with ' ', '+', '-'
                        # support a corner case where a blank context line is represented as ' ' only
                        cur_hunk.lines.append(HunkLine(' ', ''))  # treat as blank context
                    else:
                        prefix = l[0]
                        if prefix in (' ', '+', '-'):
                            cur_hunk.lines.append(HunkLine(prefix, l[1:]))
                        else:
                            # Some diffs can include '\ No newline at end of file'
                            if l.startswith('\\ No newline at end of file'):
                                pass
                            else:
                                raise PatchParseError(f'Unexpected hunk content line: {l}')
                    i += 1
                continue

            # ignore other leading markers like 'diff --git'
            i += 1

        if not saw_any_hunk:
            raise PatchParseError('No hunks found')
        return FilePatch(old_path=old_path, new_path=new_path, hunks=hunks)

# ---------- Patch applier ----------

class DiffApplier:
    def __init__(self, fuzzy_context: int = 3):
        # fuzzy_context controls how much leading context to use when anchoring hunks
        self.fuzzy_context = fuzzy_context

    def apply(self, original_text: str, patch: FilePatch) -> str:
        orig_lines = original_text.splitlines()
        # Work on a mutable list with explicit newlines preserved per line
        # We will rejoin with '\n'. Track content as list of strings without trailing newline tokens.
        out = orig_lines[:]
        line_bias = 0  # tracks net line insertions - deletions up to current hunk

        for hunk in patch.hunks:
            # Build the expected context sequence from ' ' lines at the start of hunk
            context_prefix = []
            for hl in hunk.lines:
                if hl.kind == ' ':
                    context_prefix.append(hl.text)
                else:
                    break
            # Determine an anchor position
            anchor_guess_index = max(hunk.old_start - 1 + line_bias, 0)
            anchor_index = self._find_anchor(out, context_prefix, anchor_guess_index)
            if anchor_index is None:
                # Try globally if local anchor failed
                anchor_index = self._find_anchor(out, context_prefix, None)
            if anchor_index is None:
                raise PatchApplyError(
                    f'Failed to anchor hunk at old_start {hunk.old_start}. '
                    f'Consider increasing context or disabling fuzzy matching.'
                )

            # Now simulate apply at anchor_index
            idx = anchor_index
            # First, verify full sequence while applying modifications
            cur = idx
            for hl in hunk.lines:
                if hl.kind == ' ':
                    if cur >= len(out) or out[cur] != hl.text:
                        raise PatchApplyError(f'Context mismatch near line {cur + 1}')
                    cur += 1
                elif hl.kind == '-':
                    if cur >= len(out) or out[cur] != hl.text:
                        raise PatchApplyError(f'Deletion mismatch near line {cur + 1}')
                    # do not advance cur when deleting
                elif hl.kind == '+':
                    # additions do not consume from out
                    pass

            # Apply for real
            cur = idx
            for hl in hunk.lines:
                if hl.kind == ' ':
                    cur += 1
                elif hl.kind == '-':
                    del out[cur]
                    line_bias -= 1
                elif hl.kind == '+':
                    out.insert(cur, hl.text)
                    cur += 1
                    line_bias += 1

        return '\n'.join(out)

    def _find_anchor(self, lines: List[str], context_prefix: List[str], guess_index: Optional[int]) -> Optional[int]:
        if not context_prefix:
            return guess_index if guess_index is not None else 0
        # Tight search near guess first
        if guess_index is not None:
            start = max(0, guess_index - self.fuzzy_context)
            end = min(len(lines), guess_index + self.fuzzy_context + 1)
            pos = self._search_sequence(lines, context_prefix, start, end)
            if pos is not None:
                return pos
        # Fallback global search
        return self._search_sequence(lines, context_prefix, 0, len(lines))

    @staticmethod
    def _search_sequence(lines: List[str], seq: List[str], start: int, end: int) -> Optional[int]:
        n = len(seq)
        if n == 0:
            return start
        for i in range(start, max(end - n + 1, 0)):
            match = True
            for j in range(n):
                if i + j >= len(lines) or lines[i + j] != seq[j]:
                    match = False
                    break
            if match:
                return i
        return None

# ---------- UI ----------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patchy - simple patch applier")
        self.resize(1200, 800)

        self.original_path: Optional[str] = None
        self.current_patch: Optional[FilePatch] = None

        # Widgets
        self.open_btn = QPushButton("Open file")
        self.load_diff_btn = QPushButton("Open diff")
        self.preview_btn = QPushButton("Preview")
        self.save_as_btn = QPushButton("Save As")
        self.save_inplace_btn = QPushButton("Save in place + .bak")
        self.file_label = QLineEdit()
        self.file_label.setPlaceholderText("No file loaded")
        self.file_label.setReadOnly(True)
        self.backup_checkbox = QCheckBox("Create .bak on Save in place")
        self.backup_checkbox.setChecked(True)

        top_row = QHBoxLayout()
        top_row.addWidget(self.open_btn)
        top_row.addWidget(self.load_diff_btn)
        top_row.addWidget(self.preview_btn)
        top_row.addWidget(self.save_as_btn)
        top_row.addWidget(self.save_inplace_btn)
        top_row.addWidget(self.backup_checkbox)

        top2 = QHBoxLayout()
        top2.addWidget(QLabel("File:"))
        top2.addWidget(self.file_label)

        # Editors
        self.original_edit = QTextEdit()
        self.original_edit.setPlaceholderText("Original file content will appear here")
        self.diff_edit = QTextEdit()
        self.diff_edit.setPlaceholderText("Paste unified diff here or use Open diff")
        self.patched_edit = QTextEdit()
        self.patched_edit.setPlaceholderText("Patched preview will appear here")
        self.patched_edit.setReadOnly(True)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.addWidget(QLabel("Original"))
        lv.addWidget(self.original_edit)

        right = QSplitter(Qt.Orientation.Vertical)
        rtop = QWidget()
        rtv = QVBoxLayout(rtop)
        rtv.addWidget(QLabel("Unified diff"))
        rtv.addWidget(self.diff_edit)
        rbot = QWidget()
        rbv = QVBoxLayout(rbot)
        rbv.addWidget(QLabel("Preview"))
        rbv.addWidget(self.patched_edit)
        right.addWidget(rtop)
        right.addWidget(rbot)
        right.setSizes([400, 400])

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([600, 600])

        root = QWidget()
        rootv = QVBoxLayout(root)
        rootv.addLayout(top_row)
        rootv.addLayout(top2)
        rootv.addWidget(splitter)

        self.setCentralWidget(root)

        # Events
        self.open_btn.clicked.connect(self.on_open_file)
        self.load_diff_btn.clicked.connect(self.on_open_diff)
        self.preview_btn.clicked.connect(self.on_preview)
        self.save_as_btn.clicked.connect(self.on_save_as)
        self.save_inplace_btn.clicked.connect(self.on_save_in_place)

    # ----- UI actions -----

    def on_open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All files (*.*)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                txt = f.read()
            self.original_path = path
            self.file_label.setText(path)
            self.original_edit.setPlainText(txt)
            log(f"Opened file: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
            log(f"ERROR opening file: {e}")

    def on_open_diff(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open diff", "", "Patch files (*.patch *.diff);;All files (*.*)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                txt = f.read()
            self.diff_edit.setPlainText(txt)
            log(f"Loaded diff: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open diff: {e}")
            log(f"ERROR opening diff: {e}")

    def _parse_patch(self) -> Optional[FilePatch]:
        diff_text = self.diff_edit.toPlainText()
        if not diff_text.strip():
            QMessageBox.warning(self, "No diff", "Please paste or open a unified diff.")
            return None
        try:
            parser = UnifiedDiffParser()
            fp = parser.parse(diff_text)
            self.current_patch = fp
            return fp
        except PatchParseError as e:
            QMessageBox.critical(self, "Parse error", f"Failed to parse diff:\n{e}")
            log(f"ERROR parsing diff: {e}")
            return None

    def on_preview(self):
        if not self.original_edit.toPlainText():
            QMessageBox.warning(self, "No file", "Open a file first.")
            return
        patch = self._parse_patch()
        if not patch:
            return
        applier = DiffApplier()
        try:
            result = applier.apply(self.original_edit.toPlainText(), patch)
            self.patched_edit.setPlainText(result)
            log("Preview generated")
        except PatchApplyError as e:
            QMessageBox.critical(self, "Apply error", f"Failed to apply patch:\n{e}")
            log(f"ERROR applying patch: {e}")

    def on_save_as(self):
        if not self.patched_edit.toPlainText():
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

    def on_save_in_place(self):
        if not self.patched_edit.toPlainText():
            QMessageBox.information(self, "Nothing to save", "Generate a preview first.")
            return
        if not self.original_path:
            QMessageBox.warning(self, "No original path", "Open a file so I know where to save in place.")
            return
        path = self.original_path
        try:
            if self.backup_checkbox.isChecked():
                bak = path + ".bak"
                with open(bak, 'w', encoding='utf-8') as f:
                    f.write(self.original_edit.toPlainText())
                log(f"Backup written: {bak}")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.patched_edit.toPlainText())
            QMessageBox.information(self, "Saved", f"Patched file written in place:\n{path}")
            log(f"Patched file saved in place: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Failed to write in place: {e}")
            log(f"ERROR saving in place: {e}")

    def _suggest_output_path(self) -> str:
        if not self.original_path:
            return os.path.join(os.getcwd(), "patched_output.txt")
        root, ext = os.path.splitext(self.original_path)
        return f"{root}.patched{ext if ext else '.txt'}"

# ---------- Entry ----------

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
