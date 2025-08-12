# Main Window Pseudocode

## Initialization
1. CREATE QApplication instance
2. INITIALIZE ThemeManager
3. INITIALIZE StateManager
4. CREATE MainWindow instance
5. SETUP UI:
   - CREATE central widget
   - CREATE toolbar
   - CREATE content area (3-panel splitter)
   - CONNECT all signals
6. RESTORE saved state
7. SHOW window
8. START event loop

## Toolbar Setup
1. CREATE horizontal layout
2. ADD buttons:
   - Open File button
   - Open Folder button
   - Open Diff button
   - Apply Patch button
   - Save As button
3. ADD checkboxes:
   - Create backups
   - Live preview
4. CONNECT button clicks to handlers

## Content Area Setup
1. CREATE horizontal splitter
2. CREATE left panel:
   - QLabel "Files"
   - QListWidget for file list
3. CREATE middle panel:
   - QLabel "Original"
   - CodeEditor widget
4. CREATE right panel:
   - QTabWidget
   - ADD tabs:
     - Diff editor
     - Preview editor
     - Navigation widget
5. SET splitter sizes [200, 600, 800]

## Event Handlers

### on_open_file
1. OPEN file dialog
2. IF file selected:
   - SET current_file
   - SET root_folder = None
   - LOAD file content into original editor
   - CLEAR file list
   - CLEAR preview

### on_open_folder
1. OPEN folder dialog
2. IF folder selected:
   - SET root_folder
   - SET current_file = None
   - CLEAR editors
   - SCAN folder for files

### on_open_diff
1. OPEN file dialog for diff
2. IF file selected:
   - LOAD diff content into diff editor
   - PARSE diff using DiffParser
   - UPDATE file list
   - SELECT first file

### on_diff_changed
1. GET diff content
2. IF empty:
   - CLEAR file list
   - RETURN
3. TRY:
   - PARSE diff using DiffParser
   - UPDATE file list
   - IF files exist:
     - SELECT first file
4. CATCH ParseError:
   - SHOW warning dialog

### on_file_selected
1. GET selected patch from list item
2. IF no patch:
   - RETURN
3. LOAD original content:
   - TRY relative to root folder
   - TRY absolute path
4. IF loaded:
   - SET original editor content
   - APPLY patch using DiffApplier
   - UPDATE preview editor
   - UPDATE navigation

## State Management

### save_state
1. CREATE state dict:
   - window_size
   - window_position
   - root_folder
   - current_file
   - splitter_sizes
2. CALL StateManager.save(state)

### restore_state
1. CALL StateManager.load()
2. IF state exists:
   - RESTORE window size
   - RESTORE window position
   - RESTORE splitter sizes