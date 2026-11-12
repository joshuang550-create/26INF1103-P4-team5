from tkinter import ttk
from models.errors import InvalidInputError


class RegisterFrame(ttk.Frame):
    """ Sign-up form. Turns the text boxes into the types AppEngine.register expects
    (age -> int, height/weight -> float, conditions -> list), then lets the engine validate. """

    def __init__(self, parent, app):
        super().__init__(parent, padding=30)
        self.app = app
        self.fields = {}

        ttk.Label(self, text="Create your health profile", font=("Helvetica", 20, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))

        rows = [
            ("username", "Username"),
            ("password", "Password"),
            ("gender", "Gender"),
            ("age", "Age"),
            ("height", "Height (cm)"),
            ("weight", "Weight (kg)"),
            ("country", "Country"),
            ("ethnicity", "Ethnicity"),
            ("conditions", "Medical conditions / allergies\n(comma separated, optional)"),
        ]
        for row, (key, label) in enumerate(rows, start=1):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 12))
            if key == "gender":
                widget = ttk.Combobox(self, values=["male", "female"], state="readonly", width=33)
            else:
                widget = ttk.Entry(self, width=36, show="•" if key == "password" else "")
            widget.grid(row=row, column=1, sticky="w", pady=4)
            self.fields[key] = widget
        
        buttons = ttk.Frame(self)
        buttons.grid(row=len(rows) + 1, column=0, columnspan=3, sticky="w", pady=(20, 0))
        ttk.Button(buttons, text="Create account").pack(side="left")
        ttk.Button(buttons, text="Back to login", command=lambda: app.show("login")).pack(side="left", padx=8)