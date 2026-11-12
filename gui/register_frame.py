from tkinter import ttk
from models.errors import InvalidInputError
from gui.popups import show_error


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
        
                # live validation hints, uses the engine's is_valid_* helpers
        self.hints = {key: ttk.Label(self, foreground="#E5534B") for key in ("username", "country", "ethnicity", "conditions")}
        for key, hint in self.hints.items():
            hint.grid(row=[r[0] for r in rows].index(key) + 1, column=2, sticky="w", padx=8)
            self.fields[key].bind("<FocusOut>", lambda _event, k=key: self._check_field(k))

        buttons = ttk.Frame(self)
        buttons.grid(row=len(rows) + 1, column=0, columnspan=3, sticky="w", pady=(20, 0))
        ttk.Button(buttons, text="Create account", command=self._register).pack(side="left")
        ttk.Button(buttons, text="Back to login", command=lambda: app.show("login")).pack(side="left", padx=8)


    def on_show(self):
        for widget in self.fields.values():
            if isinstance(widget, ttk.Combobox):
                widget.set("") # readonly combobox can't use delete()
            else:
                widget.delete(0, "end")
        for hint in self.hints.values():
            hint.config(text="")


    # =========== Live Validation ===========
    def _check_field(self, key):
        value = self.fields[key].get().strip()
        engine = self.app.engine
        message = ""
        if key == "username" and value and engine.is_username_taken(value):
            message = "Username taken"
        elif key == "country" and value and not engine.is_valid_country(value):
            message = "Not a recognised country"
        elif key == "ethnicity" and value and not engine.is_valid_ethnicity(value):
            message = "Not a recognised ethnicity"
        elif key == "conditions":
            unknown = [c for c in self._conditions() if not engine.is_valid_condition(c)]
            message = f"Not recognised: {', '.join(unknown)}" if unknown else ""
        self.hints[key].config(text=message)

    # =========== Submit ===========
    def _conditions(self):
        return [part.strip() for part in self.fields["conditions"].get().split(",") if part.strip()]

    @staticmethod
    def _number(text, label, kind):
        try:
            return kind(text.strip())
        except ValueError:
            raise InvalidInputError(f"{label} must be a number.") from None

    
    def _register(self):
        get = lambda key: self.fields[key].get() # noqa: E731
        try:
            self.app.engine.register(
                username=get("username"),
                plain_password=get("password"),
                gender=get("gender"),
                age=self._number(get("age"), "Age", int),
                ethnicity=get("ethnicity"),
                country=get("country"),
                height=self._number(get("height"), "Height", float),
                weight=self._number(get("weight"), "Weight", float),
                medical_conditions=self._conditions() or None,
            )
        except Exception as error: # noqa: BLE001
            show_error(error, self)
            return
        self.app.show("home") # register() also logs the user in