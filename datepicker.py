import tkinter as tk
from datetime import datetime
import calendar


class DatePicker(tk.Frame):

    def __init__(self, parent, width=12):

        super().__init__(parent)

        self.selected_date = datetime.today()

        self.entry = tk.Entry(self, width=width)
        self.entry.pack(side="left")

        self.btn = tk.Button(self, text="📆", width=2, command=self.open_calendar)
        self.btn.pack(side="left")

        self.entry.insert(0, self.selected_date.strftime("%d-%m-%Y"))

    def get(self):
        return self.entry.get()

    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def open_calendar(self):

        if hasattr(self, "popup") and self.popup.winfo_exists():
            return

        self.current_year = self.selected_date.year
        self.current_month = self.selected_date.month

        self.popup = tk.Toplevel(self)
        self.popup.overrideredirect(True)
        self.popup.configure(bg="#e5e7eb")

        # posisi popup di samping tombol
        x = self.btn.winfo_rootx()
        y = self.btn.winfo_rooty() + self.btn.winfo_height()

        self.popup.geometry(f"+{x}+{y}")

        self.popup.bind("<FocusOut>", lambda e: self.popup.destroy())

        self.draw_calendar()

        self.popup.focus_force()

    def draw_calendar(self):

        for w in self.popup.winfo_children():
            w.destroy()

        header = tk.Frame(self.popup, bg="white")
        header.pack(fill="x")

        tk.Button(header, text="←", width=3, command=self.prev_month).pack(
            side="left", padx=5, pady=5
        )

        tk.Label(
            header,
            text=f"{calendar.month_name[self.current_month]} {self.current_year}",
            font=("Segoe UI", 10, "bold"),
            bg="white",
        ).pack(side="left", expand=True)

        tk.Button(header, text="→", width=3, command=self.next_month).pack(
            side="right", padx=5
        )

        body = tk.Frame(self.popup, bg="white")
        body.pack(padx=5, pady=5)

        days = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

        for i, d in enumerate(days):
            tk.Label(
                body, text=d, width=4, bg="white", font=("Segoe UI", 9, "bold")
            ).grid(row=0, column=i)

        cal = calendar.monthcalendar(self.current_year, self.current_month)

        for r, week in enumerate(cal):

            for c, day in enumerate(week):

                if day == 0:

                    tk.Label(body, text="", width=4, bg="white").grid(
                        row=r + 1, column=c
                    )

                else:

                    color = "white"
                    fg = "black"

                    if (
                        day == self.selected_date.day
                        and self.current_month == self.selected_date.month
                        and self.current_year == self.selected_date.year
                    ):
                        color = "#111827"
                        fg = "white"

                    btn = tk.Button(
                        body,
                        text=str(day),
                        width=4,
                        bg=color,
                        fg=fg,
                        relief="flat",
                        command=lambda d=day: self.select_day(d),
                    )

                    btn.grid(row=r + 1, column=c, padx=1, pady=1)

    def select_day(self, day):

        self.selected_date = datetime(self.current_year, self.current_month, day)

        self.entry.delete(0, "end")
        self.entry.insert(0, self.selected_date.strftime("%d-%m-%Y"))

        self.popup.destroy()

    def prev_month(self):

        self.current_month -= 1

        if self.current_month == 0:
            self.current_month = 12
            self.current_year -= 1

        self.draw_calendar()

    def next_month(self):

        self.current_month += 1

        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1

        self.draw_calendar()
