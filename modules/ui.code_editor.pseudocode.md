# Code Editor Widget Pseudocode

## Initialization
1. INHERIT from QPlainTextEdit
2. SET monospace font
3. CREATE LineNumberArea widget
4. CONNECT signals:
   - blockCountChanged -> update_line_number_area_width
   - updateRequest -> update_line_number_area
5. INITIALIZE line number area

## Line Number Area
1. CREATE custom QWidget
2. OVERRIDE paintEvent:
   - GET first visible block
   - FOR each visible block:
     - DRAW line number
     - MOVE to next block
3. OVERRIDE sizeHint:
   - CALCULATE width based on digit count

## Methods

### update_line_number_area_width
1. CALCULATE required width:
   - GET max line count
   - COUNT digits
   - ADD padding
2. SET viewport margins

### update_line_number_area
1. IF scroll delta provided:
   - SCROLL line number area
2. ELSE:
   - UPDATE line number area
3. IF viewport rect contains update rect:
   - UPDATE line number area width

### line_number_area_paint_event
1. CREATE painter for line number area
2. FILL background with alternate base color
3. GET first visible block
4. WHILE block is valid and within paint rect:
   - IF block is visible:
     - DRAW line number
   - MOVE to next block