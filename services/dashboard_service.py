from datetime import date
from utils import rupiah

class DashboardService:

    def __init__(self, db):

        self.db = db

    def get_kpi(self):

        year = str(date.today().year)

        sales = self.db.execute(
            """
            SELECT COALESCE(SUM(total),0)
            FROM sales_invoices
            WHERE substr(trx_date,7,4)=?
            """,
            (year,)
        ).fetchone()[0]

        purchase = self.db.execute(
            """
            SELECT COALESCE(SUM(total),0)
            FROM purchase_invoices
            WHERE substr(trx_date,7,4)=?
            """,
            (year,)
        ).fetchone()[0]

        receivable = self.db.execute(
            """
            SELECT COALESCE(SUM(total-paid),0)
            FROM sales_invoices
            WHERE status!='PAID'
            """
        ).fetchone()[0]

        payable = self.db.execute(
            """
            SELECT COALESCE(SUM(total-paid),0)
            FROM purchase_invoices
            WHERE status!='PAID'
            """
        ).fetchone()[0]

        cash = self.db.execute(
            """
            SELECT COALESCE(SUM(balance),0)
            FROM accounts
            WHERE type='Asset'
            """
        ).fetchone()[0]

        profit = sales - purchase

        return {

            "sales": sales,

            "purchase": purchase,

            "profit": profit,

            "cash": cash,

            "receivable": receivable,

            "payable": payable,
        }