import tkinter as tk
from tkinter import ttk


class SmartBiteApp(tk.Tk):
    """ Main window. Holds the engine and swaps between screens (frames). """

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.title("SmartBite")
        self.geometry("900x650")
        self.minsize(760, 560)
        ttk.Style(self).theme_use("clam")