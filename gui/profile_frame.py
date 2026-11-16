import tkinter as tk
from tkinter import ttk

from gui.popups import show_error, show_info, ask_yes_no
from gui.hint_label import HintLabel


class ProfileFrame(ttk.Frame):
    """ Edit profile: change age, height, weight and country, add or remove medical conditions, delete the account. """

    EDITABLE = (("age", "Age"), ("height", "Height (cm)"), ("weight", "Weight (kg)"), ("country", "Country"))

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.fields = {}
        self._ticks = [] # one tk.BooleanVar per medical condition checkbox

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="My profile", font=("Helvetica", 18, "bold")).pack(side="left")
        ttk.Button(top, text="Back", command=lambda: app.show("home")).pack(side="right")

        # ---- details ----
        details = ttk.LabelFrame(self, text="Details", padding=12)
        details.pack(fill="x", pady=(16, 8))
        self.fixed = ttk.Label(details, foreground="#8a9099") # username, gender and ethnicity can't be changed
        self.fixed.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        for row, (key, label) in enumerate(self.EDITABLE, start=1):
            ttk.Label(details, text=label).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 12))
            self.fields[key] = ttk.Entry(details, width=30)
            self.fields[key].grid(row=row, column=1, sticky="w", pady=3)
        ttk.Button(details, text="Save changes", command=self._save_details).grid(row=len(self.EDITABLE) + 1, column=1, sticky="w", pady=(10, 0))

        self.country_hint = HintLabel(details, on_accept=self._accept_country, wraplength=260)
        self.country_hint.grid(row=len(self.EDITABLE), column=2, sticky="w", padx=8)
        self.country_hint.watch(self.fields["country"], self._check_country)

        # ---- medical conditions ----
        conditions = ttk.LabelFrame(self, text="Medical conditions / allergies", padding=12)
        conditions.pack(fill="x", pady=8)
        self.ticks_box = ttk.Frame(conditions) # checkboxes are rebuilt in on_show
        self.ticks_box.pack(fill="x")
        ttk.Button(conditions, text="Remove ticked", command=self._remove_conditions).pack(anchor="w", pady=(6, 12))

        add_row = ttk.Frame(conditions)
        add_row.pack(fill="x")
        ttk.Label(add_row, text="Add (comma separated)").pack(side="left")
        self.new_conditions = ttk.Entry(add_row, width=36)
        self.new_conditions.pack(side="left", padx=8)
        ttk.Button(add_row, text="Add", command=self._add_conditions).pack(side="left")
        self.conditions_hint = HintLabel(conditions, on_accept=self._accept_conditions, wraplength=600)
        self.conditions_hint.pack(anchor="w", pady=(4, 0))
        self.conditions_hint.watch(self.new_conditions, self._check_conditions)

        # ---- account ----
        ttk.Button(self, text="Delete my account", command=self._delete_account).pack(anchor="w", pady=(12, 0))

    def on_show(self): # fill everything in from the logged-in profile
        profile = self.app.io.profile
        if profile is None:
            return
        self.fixed.config(text=f"{profile.username}  ·  {profile.gender}  ·  {profile.ethnicity}")
        values = {"age": profile.age, "height": profile.height, "weight": profile.weight, "country": profile.country}
        for key, entry in self.fields.items():
            entry.delete(0, "end")
            self.conditions_hint.clear()
            entry.insert(0, str(values[key]))
        self.country_hint.clear()
        self.new_conditions.delete(0, "end")
        self._show_conditions(profile.medical_conditions)

    # =========== Details ===========
    def _save_details(self):
        form = {key: entry.get() for key, entry in self.fields.items()}
        try:
            self.app.io.update_profile(form)
        except Exception as error: # noqa: BLE001
            show_error(error, self)
            return
        show_info("Profile saved", "Your details have been updated.", self)
        self.on_show()

    def _check_country(self):
        self.country_hint.show(self.app.io.check_field("country", self.fields["country"].get()))

    def _accept_country(self, fix):
        self.fields["country"].delete(0, "end")
        self.fields["country"].insert(0, fix)
        self._check_country()

    # =========== Medical Conditions ===========
    def _show_conditions(self, conditions):
        for child in self.ticks_box.winfo_children():
            child.destroy()
        self._ticks = [tk.BooleanVar(value=False) for _ in conditions]
        if not conditions:
            ttk.Label(self.ticks_box, text="None added yet.", foreground="#8a9099").pack(anchor="w")
        for condition, tick in zip(conditions, self._ticks):
            ttk.Checkbutton(self.ticks_box, text=condition.title(), variable=tick).pack(anchor="w")


    def _remove_conditions(self):
        ticked = [i for i, tick in enumerate(self._ticks) if tick.get()]
        try:
            self.app.io.remove_conditions(ticked)
        except Exception as error: # noqa: BLE001
            show_error(error, self)
            return
        self.on_show()

    def _check_conditions(self):
        self.conditions_hint.show(self.app.io.check_field("conditions", self.new_conditions.get()))

    def _accept_conditions(self, fix):
        self.new_conditions.delete(0, "end")
        self.new_conditions.insert(0, fix)
        self._check_conditions()

    def _add_conditions(self):
        try:
            self.app.io.add_conditions(self.new_conditions.get())
        except Exception as error: # noqa: BLE001
            show_error(error, self)
            return
        self.on_show()

    # =========== Account ===========
    def _delete_account(self):
        if not ask_yes_no("Delete account?", "This permanently deletes your profile and food check history. This cannot be undone.", self):
            return
        try:
            self.app.io.delete_account()
        except Exception as error: # noqa: BLE001
            show_error(error, self)
            return
        show_info("Account deleted", "Your account has been deleted.", self)
        self.app.show("login")