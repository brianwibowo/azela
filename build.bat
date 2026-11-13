@echo off
echo === Build Azela Bakery SIA (.exe) ===
python -m pip install -r requirements.txt
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

pyinstaller --noconfirm --onefile --windowed ^
  --name "AzelaSIA" ^
  --add-data "web;web" ^
  --hidden-import "openpyxl" ^
  main.py

echo.
echo Selesai! File exe berada di: dist\AzelaSIA.exe
echo Saat AzelaSIA.exe dijalankan, database azela.db otomatis dibuat di folder yang sama.
pause

