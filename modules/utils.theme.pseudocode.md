# Theme Manager Pseudocode

## ThemeManager Class

### Properties
- app: QApplication reference
- current_theme: 'light' or 'dark'
- timer: QTimer for theme monitoring

### Methods

#### __init__(app)
1. STORE app reference
2. INITIALIZE timer (30s interval)
3. CONNECT timer timeout to check_theme
4. START timer
5. CALL apply_theme

#### detect_system_theme()
1. IF Windows:
   - READ registry key:
     - HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
     - Value: AppsUseLightTheme
   - RETURN 'dark' if value == 0, 'light' otherwise
2. ELSE:
   - CALCULATE palette brightness
   - RETURN 'dark' if brightness < 0.5

#### apply_theme()
1. new_theme = detect_system_theme()
2. IF new_theme == current_theme:
   - RETURN
3. SAVE scroll positions
4. IF dark theme:
   - SET Fusion style
   - APPLY dark palette:
     - Window: dark gray
     - Text: white
     - Base: darker gray
     - Highlight: blue
5. ELSE:
   - RESET to system palette
6. RESTORE scroll positions
7. EMIT theme_changed signal

#### create_dark_palette()
1. CREATE QPalette
2. SET colors:
   - Window: QColor(53, 53, 53)
   - WindowText: white
   - Base: QColor(35, 35, 35)
   - Text: white
   - Button: QColor(53, 53, 53)
   - Highlight: QColor(42, 130, 218)
3. RETURN palette

#### check_theme()
1. new_theme = detect_system_theme()
2. IF new_theme != current_theme:
   - CALL apply_theme()