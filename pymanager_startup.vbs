Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "Y:\PyManager"
' Le 0 a la fin signifie "cacher la fenetre", False signifie "ne pas attendre la fin"
WshShell.Run "Y:\PyManager\.venv\Scripts\python.exe main.py", 0, False
