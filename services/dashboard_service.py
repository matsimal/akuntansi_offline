from datetime import date

class DashboardService:

    def __init__(self, db):

        self.db = db

    def get_company_profile(self):

        row = self.db.execute("""
            SELECT company_name,
                   address,
                   phone
            FROM company_profile
            LIMIT 1
        """).fetchone()

        return row

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

        cash = 0

        profit = sales - purchase

        return {

            "sales": sales,

            "purchase": purchase,

            "profit": profit,

            "cash": cash,

            "receivable": receivable,

            "payable": payable,
        }
    
    def get_profit_summary(self):

        return {

            "sales":0,

            "cogs":0,

            "expense":0,

            "profit":0,
        }
    
    def get_cash_summary(self):

        return {

            "cash_in":0,

            "cash_out":0,

            "balance":0,
        }
    
    def get_top_customers(self):

        return []
    
    def get_top_suppliers(self):

        return []
    
    def get_stock_warning(self):

        return []
    
    def get_recent_activity(self):

        return []
    
    def get_company_profile(self):

        return self.db.execute("""
            SELECT company_name,
                address,
                phone
            FROM company_profile
            LIMIT 1
        """).fetchone()