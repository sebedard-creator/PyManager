@echo off
echo =======================================
echo     Arret de PyManager en cours...
echo =======================================
echo.
echo Demande d'arret gracieux envoyee (Fermeture des sous-services...)
curl -X POST http://127.0.0.1:8000/api/shutdown >nul 2>&1
echo.
echo PyManager et tous ses sous-services ont ete arretes avec succes !
echo.
timeout /t 3
