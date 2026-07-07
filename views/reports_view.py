from datetime import date
import tkinter as tk
from utils.currency_utils import rupiah


class ReportsView(tk.Frame):

    def __init__(self, parent, db):
        super().__init__(parent, bg="#f9fafb")

        self.db = db

        self.build_ui()

    def build_ui(self):

        for w in self.winfo_children():
            w.destroy()

        tk.Label(
            self, text="Laporan Keuangan", font=("Segoe UI", 16, "bold"), bg="#f9fafb"
        ).pack(anchor="w", pady=(0, 10))

        filter_frame = tk.Frame(self, bg="#f9fafb")
        filter_frame.pack(fill="x")

        tk.Label(filter_frame, text="Tahun:", bg="#f9fafb").pack(side="left")

        current_year = date.today().year

        self.year_entry = tk.Entry(filter_frame, width=10)
        self.year_entry.insert(0, str(current_year))
        self.year_entry.pack(side="left", padx=5)

        tk.Button(
            filter_frame,
            text="Tampilkan",
            command=self.load_report,
            bg="#2563eb",
            fg="white",
        ).pack(side="left", padx=5)

        self.text = tk.Text(self, font=("Consolas", 11))
        self.text.pack(fill="both", expand=True, pady=10)

        self.load_report()

    def refresh(self):

        # hapus semua widget lama
        for widget in self.winfo_children():
            widget.destroy()

        # bangun ulang UI
        self.build_ui()

    def load_report(self):

        year = self.year_entry.get()

        sales = self.db.execute(
            """
        SELECT COALESCE(SUM(total),0) t
        FROM sales_invoices
        WHERE substr(trx_date,7,4)=?
        """,
            (year,),
        ).fetchone()["t"]

        purchase = self.db.execute(
            """
        SELECT COALESCE(SUM(total),0) t
        FROM purchase_invoices
        WHERE substr(trx_date,7,4)=?
        """,
            (year,),
        ).fetchone()["t"]

        cogs = self.db.execute(
            """
        SELECT COALESCE(SUM(jd.debit-jd.credit),0) t
        FROM journal_details jd
        JOIN accounts a ON a.id=jd.account_id
        WHERE a.code='5001'
        """
        ).fetchone()["t"]

        expense = self.db.execute(
            """
        SELECT COALESCE(SUM(jd.debit-jd.credit),0)
        FROM journal_details jd
        JOIN accounts a ON a.id=jd.account_id
        WHERE a.type='Expense'
        """
        ).fetchone()[0]

        profit = sales - cogs - expense

        # PIUTANG
        receivable = self.db.execute(
            """
        SELECT COALESCE(SUM(total-paid),0)
        FROM sales_invoices
        WHERE status!='PAID'
        """
        ).fetchone()[0]

        # HUTANG
        payable = self.db.execute(
            """
        SELECT COALESCE(SUM(total-paid),0)
        FROM purchase_invoices
        WHERE status!='PAID'
        """
        ).fetchone()[0]

        lines = []

        lines.append("========= LAPORAN KEUANGAN =========")
        lines.append("")
        lines.append(f"Tahun : {year}")
        lines.append("")

        lines.append("===== LABA RUGI =====")
        lines.append("Penjualan       : " + rupiah(sales))
        lines.append("HPP             : " + rupiah(cogs))
        lines.append("Pengeluaran     : " + rupiah(expense))
        lines.append("-------------------------------")
        lines.append("LABA BERSIH     : " + rupiah(profit))
        lines.append("")

        lines.append("===== POSISI KEUANGAN =====")
        lines.append("Piutang Usaha   : " + rupiah(receivable))
        lines.append("Hutang Usaha    : " + rupiah(payable))
        lines.append("")

        lines.append("===== PRODUK STOK MINIMUM =====")

        rows = self.db.execute(
            """
        SELECT sku,name,stock,min_stock
        FROM products
        WHERE stock < min_stock
        """
        ).fetchall()

        for r in rows:
            lines.append(
                f"{r['sku']} | {r['name']} | stok:{r['stock']} min:{r['min_stock']}"
            )

        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.config(state="disabled")
