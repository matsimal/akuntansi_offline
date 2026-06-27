import tkinter as tk


class AIChatView(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="#f9fafb")

        self.build_ui()

    def build_ui(self):

        tk.Label(
            self,
            text="AI Assistant",
            font=("Segoe UI", 24, "bold"),
            bg="#f9fafb",
        ).pack(pady=(30, 10))

        tk.Label(
            self,
            text="Coming Soon...",
            font=("Segoe UI", 12),
            bg="#f9fafb",
            fg="#6b7280",
        ).pack()