import tkinter as tk

from views.dashboard.header import HeaderFrame
from views.dashboard.kpi_cards import KPICards


class DashboardView(tk.Frame):

    def __init__(self, parent, db):

        super().__init__(parent, bg="#f9fafb")

        self.db = db

        self.build_ui()

    def build_ui(self):

        self.header = HeaderFrame(
            self,
            self.db,
        )

        self.header.pack(
            fill="x",
            padx=15,
            pady=15,
        )

        self.kpis = KPICards(
            self,
            self.db
        )

        self.kpis.pack(
            fill="x",
            padx=15
        )