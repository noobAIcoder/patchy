# Application Entry Point Pseudocode

## main()
1. CREATE QApplication
2. SET application metadata:
   - Name: "Patchy"
   - Version: "2.0.0"
   - Organization: "Patchy Project"
3. INITIALIZE exception handler
4. CREATE MainWindow
5. HANDLE command line arguments:
   - IF file path provided:
     - LOAD file
   - IF diff path provided:
     - LOAD diff
6. SHOW main window
7. START event loop
8. ON exit:
   - SAVE state
   - CLEANUP resources

## Exception Handler
1. SET global exception handler
2. ON unhandled exception:
   - LOG to console
   - SHOW error dialog
   - SAVE crash report
   - GRACEFUL exit

## CLI Arguments
1. PARSE arguments:
   - --file: Open specific file
   - --diff: Open specific diff
   - --folder: Open specific folder
   - --theme: Force theme (light/dark)
   - --debug: Enable debug mode
2. APPLY parsed arguments