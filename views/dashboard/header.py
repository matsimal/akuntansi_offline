import tkinter as tk
from datetime import datetime


class HeaderFrame(tk.Frame):

    def __init__(self, parent, service):

        super().__init__(parent, bg="#f9fafb")

        self.service = service

        self.build_ui()

        self.update_clock()

    # =====================================
    # UI
    # =====================================

    def build_ui(self):

        left = tk.Frame(self, bg="#f9fafb")
        left.pack(side="left", fill="x", expand=True)

        right = tk.Frame(self, bg="#f9fafb")
        right.pack(side="right")

        # ----------------------------------

        self.title_label = tk.Label(
            left,
            text="Dashboard",
            font=("Segoe UI", 24, "bold"),
            bg="#f9fafb",
        )

        self.title_label.pack(anchor="w")

        # ----------------------------------

        profile = self.service.get_company_profile()

        company = "Perusahaan"

        if profile:
            company = profile["company_name"]

        self.company_label = tk.Label(
            left,
            text=company,
            font=("Segoe UI", 11),
            fg="#6b7280",
            bg="#f9fafb",
        )

        self.company_label.pack(anchor="w")

        # ----------------------------------

        self.date_label = tk.Label(
            right,
            font=("Segoe UI", 11, "bold"),
            bg="#f9fafb",
        )

        self.date_label.pack(anchor="e")

        self.clock_label = tk.Label(
            right,
            font=("Segoe UI", 11),
            bg="#f9fafb",
        )

        self.clock_label.pack(anchor="e")

    # =====================================
    # CLOCK
    # =====================================

    def update_clock(self):

        hari = [
            "Senin",
            "Selasa",
            "Rabu",
            "Kamis",
            "Jumat",
            "Sabtu",
            "Minggu",
        ]

        bulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]

        now = datetime.now()

        tanggal = f"{hari[now.weekday()]}, {now.day} {bulan[now.month-1]} {now.year}"

        jam = now.strftime("%H:%M:%S")

        self.date_label.config(text=tanggal)

        self.clock_label.config(text=jam)

        self.after(1000, self.update_clock)

    # =====================================
    # REFRESH
    # =====================================

    def refresh(self):
        self.update_clock()