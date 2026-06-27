import tkinter as tk
from tkinter import ttk

class JournalView(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg="#f9fafb")
        self.db = db
        self.journals = {}
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="Akuntansi / Jurnal Umum", font=("Segoe UI", 16, "bold"), bg="#f9fafb").pack(anchor="w", pady=(0, 10))

        self.tree = ttk.Treeview(self, columns=("date", "ref", "desc"), show="headings", height=10)
        for c, h, w in [
            ("date", "Tanggal", 120),
            ("ref", "Ref No", 120),
            ("desc", "Deskripsi", 500),
        ]:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        self.tree.pack(fill="x", pady=10)

        self.detail_tree = ttk.Treeview(self, columns=("acc", "name", "debit", "credit"), show="headings", height=12)
        for c, h, w in [
            ("acc", "Kode Akun", 120),
            ("name", "Nama Akun", 260),
            ("debit", "Debit", 120),
            ("credit", "Kredit", 120),
        ]:
            self.detail_tree.heading(c, text=h)
            self.detail_tree.column(c, width=w)
        self.detail_tree.pack(fill="both", expand=True, pady=10)

        self.load_data()
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self.db.execute("""
            SELECT * FROM journal_entries
            ORDER BY id DESC
        """).fetchall()

        for r in rows:
            iid = self.tree.insert("", "end", values=(r["trx_date"], r["ref_no"], r["description"]))
            self.journals[iid] = r["id"]

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        journal_id = self.journals[selected[0]]

        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)

        details = self.db.execute("""
            SELECT a.code, a.name, jd.debit, jd.credit
            FROM journal_details jd
            JOIN accounts a ON a.id = jd.account_id
            WHERE jd.journal_id=?
        """, (journal_id,)).fetchall()

        for d in details:
            self.detail_tree.insert("", "end", values=(d["code"], d["name"], d["debit"], d["credit"]))
