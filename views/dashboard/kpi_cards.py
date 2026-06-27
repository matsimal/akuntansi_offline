import tkinter as tk

from views.dashboard.kpi_card import KPICard


class KPICards(tk.Frame):

    def __init__(self, parent, service):

        super().__init__(
            parent,
            bg="#f9fafb"
        )

        self.service = service

        self.build_ui()

    def build_ui(self):

        for i in range(6):
            self.grid_columnconfigure(
                i,
                weight=1
            )

        cards = [

            ("Penjualan", "Rp0", "Hari Ini", "#16a34a", "💰"),

            ("Pembelian", "Rp0", "Hari Ini", "#2563eb", "🛒"),

            ("Profit", "Rp0", "Tahun Ini", "#9333ea", "📈"),

            ("Kas", "Rp0", "Saldo", "#0891b2", "💵"),

            ("Piutang", "Rp0", "Outstanding", "#ea580c", "📄"),

            ("Hutang", "Rp0", "Outstanding", "#dc2626", "🧾"),
        ]

        self.kpi = []

        for i, card in enumerate(cards):

            widget = KPICard(
                self,
                title=card[0],
                value=card[1],
                subtitle=card[2],
                color=card[3],
                icon=card[4],
            )

            widget.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=5,
                pady=5
            )

            self.kpi.append(widget)