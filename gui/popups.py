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