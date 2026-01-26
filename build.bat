@echo off
echo ==========================================
echo      CONSTRUCTION DE BURGEAPLY HUB
echo ==========================================
echo.
echo 1. Nettoyage des anciens fichiers...
rmdir /s /q build
rmdir /s /q dist

echo.
echo 2. Lancement de PyInstaller...
python -m PyInstaller Burgeaply.spec

echo.
echo ==========================================
if exist "dist\Burgeaply\Burgeaply.exe" (
    echo [SUCCES] L'executable est pret : dist\Burgeaply\Burgeaply.exe
) else (
    echo [ERREUR] La construction a echoue.
)
echo ==========================================
pause
