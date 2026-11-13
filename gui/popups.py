from tkinter import messagebox

from models.errors import as_app_error


# =========== Error Popups ===========
def show_error(error, parent=None):
    """ Every SmartBiteError has a title and description, so one popup works for all of them.
    Anything unplanned becomes UnexpectedError (default title + description) via as_app_error. """
    problem = as_app_error(error)
    messagebox.showerror(problem.title, problem.description, parent=parent)

def show_info(title, message, parent=None):
    messagebox.showinfo(title, message, parent=parent)

def ask_yes_no(title, message, parent=None):
    return messagebox.askyesno(title, message, parent=parent) # True or False


def center_on_screen(window):
    """ Moves a window to the middle of the screen. Call it after the window's widgets are built. """
    window.update_idletasks() # lets tkinter work out how big the window is first
    width, height = window.winfo_width(), window.winfo_height()
    if width <= 1: # not drawn yet, use the size it asks for
        width, height = window.winfo_reqwidth(), window.winfo_reqheight()
    x = (window.winfo_screenwidth() - width) // 2
    y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"+{x}+{y}")