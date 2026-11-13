import tkinter as tk
from tkinter import ttk

from gui.popups import show_error
from gui.questions_dialog import QuestionsDialog

VERDICT_COLOURS = {"OK": "#3ba776", "CAUTION": "#f2b134", "AVOID": "#E5534B", "UNDETERMINED": "#8a9099"} # same as progress/chart.py
VERDICT_MEANING = {"OK": "Okay to eat", "CAUTION": "Eat with caution", "AVOID": "Best to avoid", "UNDETERMINED": "Could not decide"}


class HomeFrame(ttk.Frame):
    """ Main screen: type a food (+ optional barcode) -> check_food -> maybe follow-up questions -> show Outcome. """

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app

        # ---- top bar ----
        top = ttk.Frame(self)
        top.pack(fill="x")
        self.welcome = ttk.Label(top, font=("Helvetica", 18, "bold"))
        self.welcome.pack(side="left")
        self.nav_buttons = [
        ttk.Button(top, text="Log out", command=app.logout),
        ttk.Button(top, text="My progress", command=lambda: app.show("dashboard")),
        ]
        for button in self.nav_buttons:
            button.pack(side="right", padx=(8, 0))

        # ---- input ----
        form = ttk.LabelFrame(self, text="Check a food", padding=12)
        form.pack(fill="x", pady=16)
        ttk.Label(form, text="Food name").grid(row=0, column=0, sticky="w")
        self.food = ttk.Entry(form, width=40)
        self.food.grid(row=0, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(form, text="Barcode (optional)").grid(row=1, column=0, sticky="w")
        self.barcode = ttk.Entry(form, width=20)
        self.barcode.grid(row=1, column=1, sticky="w", padx=8, pady=4)
        self.check_button = ttk.Button(form, text="Check", command=self._start_check)
        self.check_button.grid(row=0, column=2, rowspan=2, padx=8)
        self.food.bind("<Return>", lambda _event: self._start_check())
        self.status = ttk.Label(form, foreground="#8a9099")
        self.status.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # ---- result ----
    # ---- result ----
        self.verdict = tk.Label(self, font=("Helvetica", 22, "bold"), fg="white", padx=14, pady=6)
        self.result = tk.Text(self, wrap="word", height=16, relief="flat", font=("Helvetica", 12), padx=10, pady=10)

    def on_show(self): # runs every time this screen opens, so nothing carries over from the last user
        profile = self.app.engine.profile
        self.welcome.config(text=f"Hi, {profile.username}" if profile else "")
        self.food.delete(0, "end")
        self.barcode.delete(0, "end")
        self.verdict.pack_forget()
        self.result.pack_forget()
        self.status.config(text="")

    # =========== Food Check Flow ===========
    def _start_check(self):
        food, barcode = self.food.get(), self.barcode.get()
        self._busy("Checking with SmartBite AI...")
        self.app.run_in_background(lambda: self.app.engine.check_food(food, barcode), self._handle_step)

    def _handle_step(self, step): # step is a FoodCheckStep, or None if an error popup was shown
        self._busy(None)
        if step is None:
            return
        if step.needs_answers:
            dialog = QuestionsDialog(self, step.questions)
            self.wait_window(dialog)
            if dialog.answers is None:
                self.app.engine.cancel_food_check()
                self.status.config(text="Check cancelled.")
                return
            self._busy("Thinking about your answers...")
            self.app.run_in_background(lambda: self.app.engine.answer_questions(dialog.answers), self._handle_step)
            return
        self._show_outcome(step.outcome)        

    def _busy(self, message): # while a check runs, nothing can log out or leave this screen
        state = "disabled" if message else "normal"
        self.status.config(text=message or "")
        self.check_button.config(state=state)
        for button in self.nav_buttons:
            button.config(state=state)

    
    # =========== Showing the Outcome ===========
    def _show_outcome(self, outcome):
        headline = outcome.headline
        self.verdict.config(text=f"{headline} – {VERDICT_MEANING.get(headline, '')}", bg=VERDICT_COLOURS.get(headline, "#8a9099"))
        self.verdict.pack(anchor="w")
        self.result.pack(fill="both", expand=True, pady=(10, 0))

        details = outcome.details()
        self.result.config(state="normal")
        self.result.delete("1.0", "end")
        if outcome.severity is None: # RecommendationOutcome (fallback)
            self.result.insert("end", details["message"] + "\n\nYou could try instead:\n")
            for item in details.get("recommendations", []):
                self.result.insert("end", f"  • {item.get('food', '')}: {item.get('reason', '')}\n")
        else: # AssessmentOutcome
            self.result.insert("end", details["reason"] + "\n")
            if details["allergens_found"]:
                self.result.insert("end", "\nAllergens found:\n")
                for category, words in details["allergens_found"].items():
                    self.result.insert("end", f"  • {category.replace('_', ' ')}: {', '.join(words)}\n")
            if details["flags"]:
                self.result.insert("end", "\nFlagged nutrients:\n")
                for flag in details["flags"]:
                    self.result.insert("end", f"  • {flag['nutrient']}: {flag['value']} ({flag['level']})\n")
            if details["nutrients"]:
                self.result.insert("end", f"\nNutrients per {details['portion_g']} g:\n")
                for nutrient, value in details["nutrients"].items():
                    self.result.insert("end", f"  • {nutrient}: {value}\n")
            self.result.insert("end", f"\nAI confidence: {details['confidence']}/10")
        self.result.config(state="disabled") # read only