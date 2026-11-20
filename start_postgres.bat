@echo off
echo ========================================================
echo   AuctionHub - Lokal PostgreSQL Serveri Basladilir...
echo ========================================================
"C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D "c:\Users\AliAL\OneDrive\Desktop\Commerce\pg_data" -l "c:\Users\AliAL\OneDrive\Desktop\Commerce\scratch\pg_local.log" start
echo.
echo Server ugurla ise salindi: 127.0.0.1:5433 (commerce_db)
echo.
pause
