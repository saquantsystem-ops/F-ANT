@echo off
REM Pyright LSP WebSocket Bridge (Pyright only - no Ruff bundled)
REM Usage: start.bat --port <PORT> --bot-root <BOT_ROOT> --jesse-root <JESSE_ROOT>

set DIR=%~dp0
"%DIR%node\node.exe" "%DIR%bundle.js" %*
