import tkinter as tk


class KPICard(tk.Frame):

    def __init__(
        self,
        parent,
        title,
        value,
        subtitle="",
        color="#2563eb",
        icon="●"
    ):

        super().__init__(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )

        self.configure(
            padx=15,
            pady=15
        )

        self.build_ui(
            title,
            value,
            subtitle,
            color,
            icon
        )

    # ===================================
    # UI
    # ===================================

    def build_ui(
        self,
        title,
        value,
        subtitle,
        color,
        icon
    ):

        top = tk.Frame(
            self,
            bg="white"
        )

        top.pack(fill="x")

        tk.Label(
            top,
            text=icon,
            fg=color,
            bg="white",
            font=("Segoe UI Emoji", 18),
        ).pack(side="left")

        tk.Label(
            top,
            text=title,
            bg="white",
            fg="#6b7280",
            font=("Segoe UI", 10, "bold"),
        ).pack(
            side="left",
            padx=8
        )

        self.value_label = tk.Label(
            self,
            text=value,
            bg="white",
            fg="#111827",
            font=("Segoe UI", 18, "bold"),
        )

        self.value_label.pack(
            anchor="w",
            pady=(12, 4)
        )

        self.subtitle_label = tk.Label(
            self,
            text=subtitle,
            bg="white",
            fg="#9ca3af",
            font=("Segoe UI", 9),
        )

        self.subtitle_label.pack(
            anchor="w"
        )

    # ===================================
    # UPDATE VALUE
    # ===================================

    def set_value(
        self,
        value,
        subtitle=None
    ):

        self.value_label.config(
            text=value
        )

        if subtitle is not None:

            self.subtitle_label.config(
                text=subtitle
            )