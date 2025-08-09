# Patchy — A Friendly Patch Applier with Live Preview

Patchy is a **PyQt6-based GUI tool** for applying unified diff/patch files to source code or text files.  
It’s designed for clarity and safety, with **live previews**, **color-coded changes**, and **per-file navigation**.

---

## ✨ Features

- **Unified Diff Parsing**  
  Robust parser for `.diff` / `.patch` files with tolerant handling of context lines and blank-line quirks.

- **Safe, Flexible Patch Application**  
  - Per-file previews before applying changes  
  - In-place save with optional `.bak` backup  
  - Batch "Apply all to folder" mode

- **Rich Visual Interface**  
  - Side-by-side **Original**, **Unified Diff**, and **Preview** panes  
  - Per-file diff view in its own tab  
  - **Line number gutters** in all editors  
  - Color-coded additions (green) and deletions (red)  
  - Summary bar showing `+adds / -dels / #hunks`

- **Quality-of-Life Controls**  
  - Live preview with debounce & scroll preservation  
  - Sync scroll toggle (Original ↔ Preview)  
  - Prev/Next change navigation  
  - Optional folding of unchanged lines around edits  
  - Dark/light theme auto-detection on Windows

---

## 📸 UI Layout

```

[ Files in diff ] | [ Original file ] | [ Diff / File diff tab ]
|                   | [ Preview pane ]

````

---

## 🚀 Getting Started

### Requirements
- Python 3.9+
- [PyQt6](https://pypi.org/project/PyQt6/)

Install dependencies:
```bash
pip install PyQt6
````

### Run Patchy

```bash
python patchy.py
```

---

## 🛠 How to Use

1. **Load context**

   * *Single file mode*: Open File → choose file to patch
   * *Folder mode*: Open Folder → base path for relative patch paths

2. **Load a diff**

   * Paste unified diff into the **Unified diff** tab
   * Or `Open Diff` to load a `.patch`/`.diff` file

3. **Preview changes**

   * Select a file in the left panel
   * View unified diff or file-specific diff in top-right tab
   * Compare **Original** vs **Preview** side-by-side

4. **Apply changes**

   * `Save Selected As` — write patched file to a chosen location
   * `Save Selected In Place` — overwrite original (optionally with `.bak` backup)
   * `Apply All to Folder` — batch apply to all files in a folder context

---

## ⚙️ Core Architecture

* **patchy_core.py**
  Handles diff parsing (`UnifiedDiffParser`) and patch application (`DiffApplier`) with robust anchoring.
  Produces `ApplyResult` objects with both patched text and change line indices.

* **patchy.py**
  Implements the PyQt6 UI: file list, multi-pane editors, highlighters, navigation, folding, theme handling.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

## 💡 Tips

* Folding unchanged lines is great for large diffs — toggle with *Fold unchanged* checkbox above Preview.
* Sync scroll keeps your eyes on corresponding lines in both Original and Preview.
* Navigation buttons jump quickly between change blocks.

---

## 🖼 Future Ideas

* Inline hunk comments
* Patch creation from file comparisons
* Configurable color themes and fonts

---

**Happy patching!**