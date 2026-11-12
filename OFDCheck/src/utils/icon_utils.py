# Установить иконку
import tkinter as tk
from pathlib import Path

def set_icon(root: tk.Tk):
    icon_image = tk.PhotoImage(file= Path(__file__).resolve().parent.parent.parent / "assets/favicon.png")
    root.iconphoto(False, icon_image) # Иконка
