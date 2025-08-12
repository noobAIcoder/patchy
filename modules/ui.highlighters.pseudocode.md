# Syntax Highlighters Pseudocode

## DiffHighlighter (QSyntaxHighlighter)
1. INITIALIZE with color palette
2. DEFINE formats:
   - Added lines: green foreground
   - Removed lines: red foreground
   - Headers: blue foreground
3. OVERRIDE highlightBlock:
   - IF line starts with '@@', '+++', '---', or '***':
     - APPLY header format
   - ELIF line starts with '+':
     - APPLY added format
   - ELIF line starts with '-':
     - APPLY removed format

## PatchHighlighter (QSyntaxHighlighter)
1. INITIALIZE with color palette
2. DEFINE format:
   - Added lines: green background
3. METHOD set_added_lines(indices):
   - STORE indices
   - REHIGHLIGHT
4. OVERRIDE highlightBlock:
   - GET current line number
   - IF line in added indices:
     - APPLY added format

## RemovedHighlighter (QSyntaxHighlighter)
1. INITIALIZE with color palette
2. DEFINE format:
   - Removed lines: red background (transparent)
3. METHOD set_removed_lines(indices):
   - STORE indices
   - REHIGHLIGHT
4. OVERRIDE highlightBlock:
   - GET current line number
   - IF line in removed indices:
     - APPLY removed format

## Color Palette Detection
1. DETECT if dark mode:
   - Windows: Check registry
   - Other: Check palette brightness
2. IF dark mode:
   - SET dark color scheme
3. ELSE:
   - SET light color scheme