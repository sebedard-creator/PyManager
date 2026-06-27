import tkinter as tk
from tkinter import filedialog
import threading

def open_dialog():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    res = filedialog.askopenfilename()
    print("Result:", res)
    root.destroy()

t = threading.Thread(target=open_dialog)
t.start()
t.join()
