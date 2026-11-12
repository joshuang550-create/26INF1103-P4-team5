from tkinter import ttk


class LoginFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=40)
        self.app = app

        box = ttk.Frame(self)
        box.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(box, text="SmartBite", font=("Helvetica", 26, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 4))
        ttk.Label(box, text="Check if a food suits your health profile").grid(row=1, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(box, text="Username").grid(row=2, column=0, sticky="w", pady=4)
        self.username = ttk.Entry(box, width=28)
        self.username.grid(row=2, column=1, pady=4)

        ttk.Label(box, text="Password").grid(row=3, column=0, sticky="w", pady=4)
        self.password = ttk.Entry(box, width=28, show="•")
        self.password.grid(row=3, column=1, pady=4)