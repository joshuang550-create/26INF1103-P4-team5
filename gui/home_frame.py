from tkinter import ttk
from gui.popups import show_error
from gui.questions_dialog import QuestionsDialog


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
        ttk.Button(top, text="Log out", command=app.logout).pack(side="right")
        ttk.Button(top, text="My progress", command=lambda: app.show("dashboard")).pack(side="right", padx=8)

    def on_show(self):
        profile = self.app.engine.profile
        self.welcome.config(text=f"Hi, {profile.username}" if profile else "")
    
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
        self.status.config(text=f"Verdict: {step.outcome.headline}") # proper result display comes next

    def _busy(self, message):
        self.status.config(text=message or "")
        self.check_button.config(state="disabled" if message else "normal")