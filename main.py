import os
import tkinter as tk
from database import Database
from services import AccountingService
from config import APP_TITLE, APP_SIZE, THEME_BG, SIDEBAR_BG, BTN_BG, BTN_ACTIVE

from sidebar import Sidebar
from views.ai_chat_view import AIChatView
from views.dashboard_view import DashboardView
from views.master_view import ProductView
from views.customer_view import CustomerView
from views.supplier_view import SupplierView
from views.sales_view import SalesView
from views.purchase_view import PurchaseView
from views.inventory_view import InventoryView
from views.cashbank_view import CashBankView
from views.journal_view import JournalView
from views.accounts_view import AccountsView
from views.reports_view import ReportsView
from views.settings_view import SettingsView


class AccountingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        self.configure(bg=THEME_BG)

        if os.name == "nt":
            try:
                self.state("zoomed")
            except Exception:
                pass

        self.db = Database()
        self.service = AccountingService(self.db)

        self.sidebar = Sidebar(
            self,
            self.db,
            self.show_page
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )
        
        self.content = tk.Frame(self, bg=THEME_BG)
        self.content.pack(side="right", fill="both", expand=True)

        self.current_frame = None

        self.show_page("ai")

    def clear_content(self):
        if self.current_frame:
            self.current_frame.destroy()

    def set_frame(self, frame):
        self.clear_content()
        self.current_frame = frame
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_dashboard(self):
        self.show_dashboard()

    def show_page(self, page):

        pages = {

            "ai": lambda: AIChatView(
                self.content
            ),

            "dashboard": lambda: DashboardView(self.content, self.db),

            "product": lambda: ProductView(
                self.content,
                self.db,
                self.refresh_dashboard
            ),

            "customer": lambda: CustomerView(
                self.content,
                self.db
            ),

            "supplier": lambda: SupplierView(
                self.content,
                self.db
            ),

            "sales": lambda: SalesView(
                self.content,
                self.db,
                self.service,
                self.refresh_dashboard
            ),

            "purchase": lambda: PurchaseView(
                self.content,
                self.db,
                self.service,
                self.refresh_dashboard
            ),

            "inventory": lambda: InventoryView(
                self.content,
                self.db,
                self.service,
                self.refresh_dashboard
            ),

            "cashbank": lambda: CashBankView(
                self.content,
                self.service,
                self.db,
                self.refresh_dashboard
            ),

            "journal": lambda: JournalView(
                self.content,
                self.db
            ),

            "account": lambda: AccountsView(
                self.content,
                self.db
            ),

            "report": lambda: ReportsView(
                self.content,
                self.db
            ),

            "setting": lambda: SettingsView(
                self.content,
                self.db
            )
        }

        if page in pages:
            self.set_frame(pages[page]())

if __name__ == "__main__":
    app = AccountingApp()
    app.mainloop()
