import tkinter as tk
from tkinter import ttk, messagebox

from utils import treeview_sort_column
from utils import current_date, bind_number_entry, parse_number, format_number


class CashBankView(tk.Frame):

    def __init__(self, parent, service, db, refresh_callback=None):
        super().__init__(parent, bg="#f9fafb")

        self.service = service
        self.db = db
        self.refresh_callback = refresh_callback
        self.selected_id = None

        self.build_ui()

    def build_ui(self):

        tk.Label(
            self, text="Kas & Bank", font=("Segoe UI", 16, "bold"), bg="#f9fafb"
        ).pack(anchor="w", pady=(0, 10))

        form = tk.Frame(self, bg="white", bd=1, relief="solid")
        form.pack(fill="x", pady=5)

        account_rows = self.db.execute(
            "SELECT code,name FROM accounts ORDER BY code"
        ).fetchall()

        self.account_map = {
            f"{r['code']} - {r['name']}": r["code"] for r in account_rows
        }

        self.cashbank_map = {"Kas": "1001", "Bank": "1002"}

        labels = [
            "Tanggal",
            "Jenis",
            "Kas/Bank",
            "Akun Lawan",
            "Jumlah",
            "Diskon",
            "Catatan",
        ]

        for i, lbl in enumerate(labels):
            tk.Label(form, text=lbl, bg="white").grid(
                row=0, column=i, padx=10, pady=(10, 2), sticky="w"
            )

        from datepicker import DatePicker

        self.date_entry = DatePicker(form)

        self.date_entry.grid(row=1, column=0, padx=10, pady=(0, 10))

        self.type_combo = ttk.Combobox(
            form, values=["IN", "OUT", "TRANSFER"], state="readonly"
        )

        self.acc_combo = ttk.Combobox(form, values=["Kas", "Bank"], state="readonly")

        self.account_combo = ttk.Combobox(
            form, values=list(self.account_map.keys()), state="readonly"
        )

        self.amount_entry = tk.Entry(form)
        self.discount_entry = tk.Entry(form)
        self.notes_entry = tk.Entry(form)

        self.date_entry.grid(row=1, column=0, padx=10, pady=(0, 10))
        self.type_combo.grid(row=1, column=1, padx=10, pady=(0, 10))
        self.acc_combo.grid(row=1, column=2, padx=10, pady=(0, 10))
        self.account_combo.grid(row=1, column=3, padx=10, pady=(0, 10))
        self.amount_entry.grid(row=1, column=4, padx=10, pady=(0, 10))
        self.discount_entry.grid(row=1, column=5, padx=10, pady=(0, 10))
        self.notes_entry.grid(row=1, column=6, padx=10, pady=(0, 10))

        for i in range(7):
            form.grid_columnconfigure(i, weight=1)

        # format angka otomatis
        bind_number_entry(self.amount_entry)
        bind_number_entry(self.discount_entry)

        btn = tk.Frame(form, bg="white")
        btn.grid(row=2, column=0, columnspan=7, sticky="w", padx=10, pady=(0, 10))

        tk.Button(
            btn, text="Simpan", command=self.save_cashbank, bg="#2563eb", fg="white"
        ).pack(side="left", padx=5)

        tk.Button(
            btn, text="Update", command=self.update_cashbank, bg="#f59e0b", fg="white"
        ).pack(side="left", padx=5)

        tk.Button(
            btn, text="Hapus", command=self.delete_cashbank, bg="#dc2626", fg="white"
        ).pack(side="left", padx=5)

        self.tree = ttk.Treeview(
            self,
            columns=(
                "id",
                "date",
                "type",
                "acc",
                "account",
                "amount",
                "discount",
                "ref",
                "notes",
            ),
            show="headings",
            height=18,
        )

        headers = [
            ("id", "ID", 50, True),
            ("date", "Tanggal", 100, False),
            ("type", "Jenis", 100, False),
            ("acc", "Kas/Bank", 100, False),
            ("account", "Akun Lawan", 120, False),
            ("amount", "Jumlah", 120, True),
            ("discount", "Diskon", 100, True),
            ("ref", "Ref", 120, False),
            ("notes", "Catatan", 260, False),
        ]

        for c, h, w, num in headers:
            self.tree.heading(
                c,
                text=h,
                command=lambda col=c, numeric=num: treeview_sort_column(
                    self.tree, col, False, numeric
                ),
            )
            self.tree.column(c, width=w)

        self.tree.pack(fill="both", expand=True, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.load_data()

    def load_data(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self.db.execute(
            """
        SELECT
        id,trx_date,trx_type,account_name,
        account_code,amount,discount,ref_no,notes
        FROM cash_bank_transactions
        ORDER BY id DESC
        """
        ).fetchall()

        for r in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    r["id"],
                    r["trx_date"],
                    r["trx_type"],
                    r["account_name"],
                    r["account_code"],
                    format_number(r["amount"]),
                    format_number(r["discount"]),
                    r["ref_no"],
                    r["notes"],
                ),
            )

    def on_select(self, event=None):

        s = self.tree.selection()

        if not s:
            return

        vals = self.tree.item(s[0], "values")

        self.selected_id = vals[0]

        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, vals[1])

        self.type_combo.set(vals[2])
        self.acc_combo.set(vals[3])

        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, vals[5])

        self.discount_entry.delete(0, "end")
        self.discount_entry.insert(0, vals[6])

        self.notes_entry.delete(0, "end")
        self.notes_entry.insert(0, vals[8])

    def save_cashbank(self):

        trx_date = self.date_entry.get().strip()
        trx_type = self.type_combo.get().strip()
        account_name = self.acc_combo.get().strip()

        account_code = self.cashbank_map.get(account_name, "1001")

        amount = parse_number(self.amount_entry.get())
        discount = parse_number(self.discount_entry.get())

        notes = self.notes_entry.get().strip()

        self.service.save_cashbank(
            trx_date, trx_type, account_name, account_code, amount, discount, notes
        )

        self.load_data()

        messagebox.showinfo("Sukses", "Transaksi disimpan")

    def update_cashbank(self):

        if not self.selected_id:
            return

        trx_date = self.date_entry.get()
        trx_type = self.type_combo.get()
        account_name = self.acc_combo.get()

        account_code = self.account_map.get(self.account_combo.get(), "")

        amount = parse_number(self.amount_entry.get())
        discount = parse_number(self.discount_entry.get())

        notes = self.notes_entry.get()

        self.service.update_cashbank(
            self.selected_id,
            trx_date,
            trx_type,
            account_name,
            account_code,
            amount,
            discount,
            notes,
        )

        self.load_data()

    def delete_cashbank(self):

        if not self.selected_id:
            return

        self.service.delete_cashbank(self.selected_id)

        self.load_data()
