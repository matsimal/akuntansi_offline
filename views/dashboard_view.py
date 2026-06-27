import tkinter as tk
from utils import rupiah

from services.dashboard_service import DashboardService

from views.dashboard.header import HeaderFrame
from views.dashboard.kpi_cards import KPICards


class DashboardView(tk.Frame):

    def __init__(self, parent, db):

        super().__init__(parent, bg="#f9fafb")

        self.db = db

        # Buat service SATU KALI
        self.dashboard_service = DashboardService(self.db)

        self.build_ui()

    def build_ui(self):

        self.header = HeaderFrame(
            self,
            self.db
        )

        self.header.pack(
            fill="x",
            padx=15,
            pady=15,
        )

        # Kirim service, bukan database
        self.kpis = KPICards(
            self,
            self.dashboard_service
        )

        self.kpis.pack(
            fill="x",
            padx=15
        )

    def refresh(self):

        data = self.service.get_kpi()

        self.kpi[0].set_value(rupiah(data["sales"]))
        self.kpi[1].set_value(rupiah(data["purchase"]))
        self.kpi[2].set_value(rupiah(data["profit"]))
        self.kpi[3].set_value(rupiah(data["cash"]))
        self.kpi[4].set_value(rupiah(data["receivable"]))
        self.kpi[5].set_value(rupiah(data["payable"]))