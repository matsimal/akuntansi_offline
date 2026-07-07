import tkinter as tk
from tkinter import ttk, messagebox

from utils.number_utils import format_number


class AccountsView(tk.Frame):

    def __init__(self, parent, db):
        super().__init__(parent, bg="#f9fafb")

        self.db = db
        self.selected_code = None

        self.build_ui()

    def build_ui(self):

        tk.Label(
            self, text="COA / Daftar Akun", font=("Segoe UI", 16, "bold"), bg="#f9fafb"
        ).pack(anchor="w", pady=(0, 10))

        tk.Button(
            self, text="🔄 Refresh", command=self.load_data, bg="#2563eb", fg="white"
        ).pack(anchor="e", pady=(0, 10))

        form = tk.Frame(self, bg="white", bd=1, relief="solid")
        form.pack(fill="x", pady=5)

        tk.Label(form, text="Kode", bg="white").grid(
            row=0, column=0, padx=10, pady=(10, 2)
        )
        tk.Label(form, text="Nama Akun", bg="white").grid(
            row=0, column=1, padx=10, pady=(10, 2)
        )
        tk.Label(form, text="Tipe", bg="white").grid(
            row=0, column=2, padx=10, pady=(10, 2)
        )

        self.code_entry = tk.Entry(form)
        self.name_entry = tk.Entry(form)

        self.type_combo = ttk.Combobox(
            form,
            values=["Asset", "Liability", "Equity", "Revenue", "Expense"],
            state="readonly",
        )

        self.code_entry.grid(row=1, column=0, padx=10, pady=(0, 10))
        self.name_entry.grid(row=1, column=1, padx=10, pady=(0, 10))
        self.type_combo.grid(row=1, column=2, padx=10, pady=(0, 10))

        btn = tk.Frame(form, bg="white")
        btn.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="w")

        tk.Button(
            btn, text="Tambah", command=self.add_account, bg="#2563eb", fg="white"
        ).pack(side="left", padx=5)

        tk.Button(
            btn, text="Update", command=self.update_account, bg="#f59e0b", fg="white"
        ).pack(side="left", padx=5)

        tk.Button(
            btn, text="Hapus", command=self.delete_account, bg="#dc2626", fg="white"
        ).pack(side="left", padx=5)

        self.tree = ttk.Treeview(
            self,
            columns=("code", "name", "type", "balance"),
            show="headings",
            height=20,
        )

        headers = [
            ("code", "Kode", 120),
            ("name", "Nama", 300),
            ("type", "Tipe", 120),
            ("balance", "Saldo", 150),
        ]

        for c, h, w in headers:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)

        self.tree.pack(fill="both", expand=True, pady=10)

        self.tree.tag_configure("minus", foreground="red")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.load_data()

    def load_data(self):

        for i in self.tree.get_children():
            self.tree.delete(i)

        rows = self.db.execute(
            """
        SELECT
        a.code,
        a.name,
        a.type,
        CASE
        WHEN a.type IN ('Asset','Expense')
        THEN COALESCE(SUM(jd.debit - jd.credit),0)
        ELSE COALESCE(SUM(jd.credit - jd.debit),0)
        END balance
        FROM accounts a
        LEFT JOIN journal_details jd
        ON jd.account_id=a.id
        GROUP BY a.id
        ORDER BY a.code
        """
        ).fetchall()

        for r in rows:

            tag = "minus" if r["balance"] < 0 else ""

            self.tree.insert(
                "",
                "end",
                values=(r["code"], r["name"], r["type"], format_number(r["balance"])),
                tags=(tag,),
            )

    def on_select(self, event):

        s = self.tree.selection()

        if not s:
            return

        vals = self.tree.item(s[0], "values")

        self.selected_code = vals[0]

        self.code_entry.delete(0, "end")
        self.code_entry.insert(0, vals[0])

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, vals[1])

        self.type_combo.set(vals[2])

    def add_account(self):

        code = self.code_entry.get()
        name = self.name_entry.get()
        typ = self.type_combo.get()

        self.db.execute(
            "INSERT INTO accounts(code,name,type) VALUES(?,?,?)",
            (code, name, typ),
            commit=True,
        )

        self.load_data()

    def update_account(self):

        if not self.selected_code:
            return

        name = self.name_entry.get()
        typ = self.type_combo.get()

        self.db.execute(
            "UPDATE accounts SET name=?,type=? WHERE code=?",
            (name, typ, self.selected_code),
            commit=True,
        )

        self.load_data()

    def delete_account(self):

        if not self.selected_code:
            return

        self.db.execute(
            "DELETE FROM accounts WHERE code=?", (self.selected_code,), commit=True
        )

        self.load_data()
