@echo off
cd /d "%~dp0"
echo Starting Wise HU RSU Tax Calculator...
echo Press Ctrl+C in this window to stop the app.
python -m streamlit run app.py
pause