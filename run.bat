@echo off
echo ========================================
echo   Medical Agent Ollama
echo ========================================
echo.
echo Starting Ollama server...
start /B ollama serve
timeout /t 3
echo.
echo Starting Medical Agent on D:\medical-agent-ollama...
echo.
streamlit run app.py
pause