import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from utils import (
    current_date,
    bind_number_entry,
    parse_number,
    format_number,
)


class PurchaseView(tk.Frame):

    def __init__(self, parent, db, service, refresh_callback=None):
        super().__init__(parent, bg="#f9fafb")

        self.db = db
        self.service = service
        self.refresh_callback = refresh_callback

        self.selected_invoice = None

        self.build_ui()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):

        # =========================================================
        # HEADER
        # =========================================================

        header = tk.Frame(self, bg="#f9fafb")
        header.pack(fill="x", pady=5)

        tk.Label(
            header,
            text="Pembelian",
            font=("Segoe UI", 20, "bold"),
            bg="#f9fafb",
        ).pack(side="left", padx=10)

        btn_frame = tk.Frame(header, bg="#f9fafb")
        btn_frame.pack(side="right", padx=10)

        tk.Button(
            btn_frame,
            text="Buat\nFaktur",
            bg="#22c55e",
            width=12,
            command=self.create_invoice,
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame,
            text="Cetak\nPO",
            bg="#fde047",
            width=12,
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame,
            text="Cetak\nFaktur",
            bg="#d1d5db",
            width=12,
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame,
            text="Edit\nFaktur",
            bg="#facc15",
            width=12,
            command=self.edit_invoice,
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame,
            text="Hapus\nFaktur",
            bg="#ef4444",
            fg="white",
            width=12,
            command=self.delete_invoice,
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame,
            text="Retur\nFaktur",
            bg="#fb923c",
            fg="white",
            width=12,
            command=self.return_invoice,
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame,
            text="Bayar\nFaktur",
            bg="#22c55e",
            width=12,
            command=self.pay_invoice,
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame,
            text="Refresh",
            bg="#3b82f6",
            fg="white",
            width=12,
            command=self.load_data,
        ).pack(side="left", padx=3)

        # =========================================================
        # SEARCH
        # =========================================================

        search_frame = tk.Frame(self, bg="#f9fafb")
        search_frame.pack(fill="x", padx=10, pady=(5, 0))

        self.selected_invoices = set()

        self.select_all_var = tk.BooleanVar()

        def toggle_select_all():

            checked = self.select_all_var.get()

            self.selected_invoices.clear()

            if checked:

                for item in self.tree.get_children():

                    vals = self.tree.item(item, "values")

                    if vals:
                        invoice = vals[4]
                        self.selected_invoices.add(invoice)

            self.refresh_checkboxes()

        tk.Checkbutton(
            search_frame,
            variable=self.select_all_var,
            command=toggle_select_all,
            bg="#f9fafb",
        ).pack(side="left", padx=(5, 5))

        tk.Label(
            search_frame,
            text="Cari Faktur:",
            bg="#f9fafb",
        ).pack(side="left")

        self.search_entry = tk.Entry(search_frame, width=30)

        self.search_entry.pack(side="left", padx=5)

        self.search_entry.bind(
            "<KeyRelease>",
            lambda e: self.load_data(),
        )

        tk.Label(
            search_frame,
            text="Status:",
            bg="#f9fafb",
        ).pack(side="left", padx=(10, 2))

        self.status_filter = ttk.Combobox(
            search_frame,
            values=["SEMUA", "PAID", "UNPAID", "PARTIAL"],
            state="readonly",
            width=15,
        )

        self.status_filter.set("SEMUA")

        self.status_filter.pack(side="left")

        self.status_filter.bind(
            "<<ComboboxSelected>>",
            lambda e: self.load_data(),
        )

        # =========================================================
        # TABLE
        # =========================================================

        table_frame = tk.Frame(
            self,
            bg="white",
            bd=1,
            relief="solid",
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        cols = (
            "check",
            "view1",
            "view2",
            "po",
            "invoice",
            "date",
            "supplier",
            "total",
            "return",
            "net",
            "paid",
            "status",
        )

        style = ttk.Style()

        style.configure("Treeview", rowheight=22)

        self.tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
        )

        headers = [
            ("check", "", 20),
            ("view1", "Lihat PO", 40),
            ("view2", "Lihat Faktur", 40),
            ("po", "No PO", 150),
            ("invoice", "No Faktur", 150),
            ("date", "Tanggal", 120),
            ("supplier", "Pemasok", 220),
            ("total", "Total", 120),
            ("return", "Retur", 120),
            ("net", "Net", 120),
            ("paid", "Dibayar", 120),
            ("status", "Status", 110),
        ]

        for c, h, w in headers:

            self.tree.heading(c, text=h)

            self.tree.column(
                c,
                width=w,
                anchor="center",
            )

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Button-1>", self.tree_click)

        self.tree.bind("<Double-1>", self.open_preview)

        self.load_data()

    # =========================================================
    # TREE CLICK
    # =========================================================

    def tree_click(self, event):

        region = self.tree.identify("region", event.x, event.y)

        if region != "cell":
            return

        column = self.tree.identify_column(event.x)

        row = self.tree.identify_row(event.y)

        if not row:
            return

        vals = self.tree.item(row, "values")

        # checkbox
        if column == "#1":
            self.toggle_checkbox(event)
            return

        # preview PO
        if column == "#2":

            invoice_no = vals[4]

            self.preview_purchase_order(invoice_no)

            return

        # preview faktur
        if column == "#3":

            invoice_no = vals[4]

            self.preview_faktur(invoice_no)

            return

    # =========================================================
    # CHECKBOX
    # =========================================================

    def toggle_checkbox(self, event):

        region = self.tree.identify("region", event.x, event.y)

        if region != "cell":
            return

        column = self.tree.identify_column(event.x)

        item = self.tree.identify_row(event.y)

        if not item:
            return

        vals = list(self.tree.item(item, "values"))

        if column == "#1":

            invoice = vals[4]

            if invoice in self.selected_invoices:

                self.selected_invoices.remove(invoice)

                vals[0] = "☐"

            else:

                self.selected_invoices.add(invoice)

                vals[0] = "☑"

            self.tree.item(item, values=vals)

    def refresh_checkboxes(self):

        for item in self.tree.get_children():

            vals = list(self.tree.item(item, "values"))

            invoice = vals[4]

            if invoice in self.selected_invoices:
                vals[0] = "☑"
            else:
                vals[0] = "☐"

            self.tree.item(item, values=vals)

    # =========================================================
    # LOAD DATA
    # =========================================================

    def load_data(self):

        for i in self.tree.get_children():
            self.tree.delete(i)

        keyword = ""
        status_filter = "SEMUA"

        if hasattr(self, "search_entry"):
            keyword = self.search_entry.get().lower()

        if hasattr(self, "status_filter"):
            status_filter = self.status_filter.get()

        rows = self.db.execute(
            """
            SELECT
                p.invoice_no,
                p.trx_date,
                s.name supplier,
                p.total,
                p.paid,
                p.status,

                COALESCE((
                    SELECT SUM(qty * price)
                    FROM purchase_return_items pri
                    JOIN purchase_returns pr
                    ON pr.id = pri.purchase_return_id
                    WHERE pr.invoice_no = p.invoice_no
                ),0) AS return_total

            FROM purchase_invoices p

            LEFT JOIN suppliers s
            ON s.id = p.supplier_id

            ORDER BY p.id DESC
            """
        ).fetchall()

        for r in rows:

            invoice = r["invoice_no"]

            supplier = (r["supplier"] or "").lower()

            status = r["status"]

            if keyword:

                if keyword not in invoice.lower() and keyword not in supplier:
                    continue

            if status_filter != "SEMUA":

                if status != status_filter:
                    continue

            total = r["total"]

            retur = r["return_total"]

            net = total - retur

            self.tree.insert(
                "",
                "end",
                values=(
                    "☐",
                    "👁",
                    "👁",
                    "-",                 # No PO
                    invoice,             # No Faktur
                    r["trx_date"],
                    r["supplier"],
                    format_number(total),
                    format_number(retur),
                    format_number(net),
                    format_number(r["paid"]),
                    status,
                ),
            )

    # =========================================================
    # PAY INVOICE
    # =========================================================

    def pay_invoice(self):

        sel = self.tree.selection()

        if not sel:

            messagebox.showerror(
                "Error",
                "Pilih faktur",
            )

            return

        vals = self.tree.item(sel[0], "values")

        invoice_no = vals[4]

        self.popup_payment(invoice_no)

    # =========================================================
    # POPUP PAYMENT
    # =========================================================

    def popup_payment(self, invoice_no):

        win = tk.Toplevel(self)

        win.title("Pembayaran Hutang")

        win.geometry("350x260")

        tk.Label(
            win,
            text=f"Invoice : {invoice_no}",
        ).pack(pady=5)

        tk.Label(
            win,
            text="Metode Pembayaran",
        ).pack()

        method_combo = ttk.Combobox(
            win,
            values=["Cash", "Transfer", "Giro", "QRIS"],
            state="readonly",
        )

        method_combo.pack()

        tk.Label(
            win,
            text="Akun Bank",
        ).pack()

        accounts = self.db.execute(
            """
            SELECT code,name
            FROM accounts
            WHERE type='Asset'
            """
        ).fetchall()

        acc_map = {
            f"{r['code']} - {r['name']}": r["code"]
            for r in accounts
        }

        acc_combo = ttk.Combobox(
            win,
            values=list(acc_map.keys()),
            state="readonly",
        )

        acc_combo.pack()

        tk.Label(
            win,
            text="Jumlah Bayar",
        ).pack()

        amount_entry = tk.Entry(win)

        amount_entry.pack()

        bind_number_entry(amount_entry)

        def save():

            method = method_combo.get()

            acc = acc_combo.get()

            if not method:

                messagebox.showerror(
                    "Error",
                    "Pilih metode pembayaran",
                )

                return

            if not acc:

                messagebox.showerror(
                    "Error",
                    "Pilih akun kas/bank",
                )

                return

            amount = parse_number(amount_entry.get())

            if amount <= 0:

                messagebox.showerror(
                    "Error",
                    "Jumlah pembayaran tidak valid",
                )

                return

            code = acc_map[acc]

            try:

                self.service.pay_purchase_invoice(
                    invoice_no,
                    amount,
                    acc,
                    code,
                    method,
                )

                messagebox.showinfo(
                    "Sukses",
                    "Pembayaran berhasil disimpan",
                )

                win.destroy()

                self.load_data()

            except Exception as e:

                messagebox.showerror(
                    "Error",
                    str(e),
                )

        tk.Button(
            win,
            text="Simpan",
            command=save,
            bg="#16a34a",
            fg="white",
        ).pack(pady=10)

    # =========================================================
    # DELETE INVOICE
    # =========================================================

    def delete_invoice(self):

        if self.selected_invoices:

            targets = list(self.selected_invoices)

        else:

            sel = self.tree.selection()

            if not sel:

                messagebox.showerror(
                    "Error",
                    "Pilih faktur terlebih dahulu",
                )

                return

            vals = self.tree.item(sel[0], "values")

            targets = [vals[4]]

        if not messagebox.askyesno(
            "Konfirmasi",
            "Hapus faktur yang dipilih?",
        ):
            return

        try:

            for invoice_no in targets:

                inv = self.db.execute(
                    """
                    SELECT id
                    FROM purchase_invoices
                    WHERE invoice_no=?
                    """,
                    (invoice_no,),
                ).fetchone()

                if not inv:
                    continue

                invoice_id = inv["id"]

                items = self.db.execute(
                    """
                    SELECT product_id, qty
                    FROM purchase_invoice_items
                    WHERE purchase_invoice_id=?
                    """,
                    (invoice_id,),
                ).fetchall()

                for item in items:

                    product_id = item["product_id"]

                    qty = item["qty"]

                    # kurangi stok kembali
                    self.db.execute(
                        """
                        UPDATE products
                        SET stock = stock - ?
                        WHERE id=?
                        """,
                        (qty, product_id),
                        commit=True,
                    )

                self.db.execute(
                    """
                    DELETE FROM inventory_movements
                    WHERE ref_no=?
                    """,
                    (invoice_no,),
                    commit=True,
                )

                self.db.execute(
                    """
                    DELETE FROM purchase_invoice_items
                    WHERE purchase_invoice_id=?
                    """,
                    (invoice_id,),
                    commit=True,
                )

                self.db.execute(
                    """
                    DELETE FROM purchase_invoices
                    WHERE id=?
                    """,
                    (invoice_id,),
                    commit=True,
                )

            self.selected_invoices.clear()

            messagebox.showinfo(
                "Sukses",
                "Faktur berhasil dihapus",
            )

            self.load_data()

        except Exception as e:

            messagebox.showerror(
                "Error",
                str(e),
            )

    # =========================================================
    # EDIT INVOICE
    # =========================================================

    def edit_invoice(self):

        sel = self.tree.selection()

        if not sel:

            messagebox.showerror(
                "Error",
                "Pilih faktur",
            )

            return

        vals = self.tree.item(sel[0], "values")

        invoice_no = vals[4]

        self.selected_invoice = invoice_no

        inv = self.db.execute(
            """
            SELECT
                p.invoice_no,
                p.trx_date,
                s.name supplier

            FROM purchase_invoices p

            LEFT JOIN suppliers s
            ON s.id = p.supplier_id

            WHERE p.invoice_no=?
            """,
            (invoice_no,),
        ).fetchone()

        if not inv:

            messagebox.showerror(
                "Error",
                "Invoice tidak ditemukan",
            )

            return

        items = self.db.execute(
            """
            SELECT
                pii.product_id,
                pr.name,
                pii.qty,
                pii.price,
                0 as discount,
                pii.total

            FROM purchase_invoice_items pii

            JOIN products pr
            ON pr.id = pii.product_id

            JOIN purchase_invoices p
            ON p.id = pii.purchase_invoice_id

            WHERE p.invoice_no=?
            """,
            (invoice_no,),
        ).fetchall()

        self.old_qty_map = {}

        for item in items:

            self.old_qty_map[item["product_id"]] = item["qty"]

        win = self.create_invoice()

        win.date_entry.set(inv["trx_date"])

        win.supp_combo.set(inv["supplier"])

        for item in items:

            disc_per_qty = (
                item["discount"] / item["qty"]
                if item["qty"]
                else 0
            )

            win.item_tree.insert(
                "",
                "end",
                values=(
                    item["name"],
                    format_number(item["qty"]),
                    format_number(item["price"]),
                    format_number(disc_per_qty),
                    format_number(item["total"]),
                ),
            )

        win.calculate_totals()

        win.invoice_no = invoice_no

    # =========================================================
    # CREATE INVOICE
    # =========================================================

    def create_invoice(self):

        win = tk.Toplevel(self)

        win.title("Faktur Pembelian")

        win.geometry("1200x650")

        # center
        win.update_idletasks()

        w = 1200
        h = 650

        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)

        win.geometry(f"{w}x{h}+{x}+{y}")

        main = tk.Frame(win)

        main.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=15,
        )

        for i in range(6):
            main.grid_columnconfigure(i, weight=1)

        main.grid_rowconfigure(5, weight=1)

        # =========================================================
        # HEADER
        # =========================================================

        tk.Label(main, text="Tanggal").grid(
            row=1,
            column=0,
            sticky="w",
        )

        tk.Label(main, text="Supplier").grid(
            row=1,
            column=1,
            sticky="w",
        )

        tk.Label(main, text="No Faktur").grid(
            row=1,
            column=2,
            sticky="w",
        )

        from datepicker import DatePicker

        date_entry = DatePicker(main, width=10)

        date_entry.grid(
            row=2,
            column=0,
            padx=5,
            pady=5,
            sticky="we",
        )

        supp_combo = ttk.Combobox(main, width=30)

        supp_combo.grid(
            row=2,
            column=1,
            padx=5,
            pady=5,
            sticky="we",
        )

        suppliers = self.db.execute(
            """
            SELECT id,name
            FROM suppliers
            ORDER BY name
            """
        ).fetchall()

        self.supplier_map = {
            s["name"]: s["id"]
            for s in suppliers
        }

        supp_combo["values"] = list(self.supplier_map.keys())

        invoice_entry = tk.Entry(main, width=28)

        invoice_entry.grid(
            row=2,
            column=2,
            padx=5,
            pady=5,
            sticky="we",
        )

        # =========================================================
        # RIGHT BUTTONS
        # =========================================================

        btn_frame = tk.Frame(main)

        btn_frame.grid(
            row=1,
            column=3,
            rowspan=2,
            columnspan=3,
            sticky="e",
        )

        tk.Button(
            btn_frame,
            text="Simpan &\nCetak PO",
            bg="#facc15",
            width=18,
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Simpan &\nCetak Faktur",
            bg="#d1d5db",
            width=18,
        ).pack(side="left", padx=5)

        # =========================================================
        # SAVE INVOICE
        # =========================================================

        def save_invoice():

            supp = supp_combo.get()

            trx_date = date_entry.get().replace("-", "/")

            notes = notes_entry.get().strip()

            if not supp:

                messagebox.showerror(
                    "Error",
                    "Pilih supplier",
                )

                return

            items = []

            for row in item_tree.get_children():

                vals = item_tree.item(row, "values")

                prod = vals[0]

                qty = parse_number(vals[1])

                price = parse_number(vals[2])

                disc = parse_number(vals[3])

                items.append(
                    {
                        "product_id": self.product_map[prod][0],
                        "qty": qty,
                        "price": price,
                        "discount": disc,
                    }
                )

            if not items:

                messagebox.showerror(
                    "Error",
                    "Belum ada item",
                )

                return

            try:

                if self.selected_invoice:

                    invoice_no = self.service.update_purchase_invoice_multi(
                        self.selected_invoice,
                        trx_date,
                        self.supplier_map[supp],
                        items,
                        notes,
                    )

                else:

                    invoice_no = self.service.create_purchase_invoice_multi(
                        trx_date,
                        self.supplier_map[supp],
                        items,
                        notes,
                    )

                messagebox.showinfo(
                    "Sukses",
                    f"Faktur {invoice_no} berhasil dibuat",
                )

                # =========================
                # WARNING STOK MINUS
                # =========================
                minus_products = self.db.execute(
                    """
                    SELECT name, stock
                    FROM products
                    WHERE stock < 0
                    """
                ).fetchall()

                if minus_products:

                    warning_text = "Produk berikut masih stok minus:\n\n"

                    for p in minus_products:
                        warning_text += (
                            f"- {p['name']} : "
                            f"{format_number(p['stock'])}\n"
                        )

                    messagebox.showwarning(
                        "Warning Stok Minus",
                        warning_text
                    )

                win.destroy()

                self.load_data()

            except Exception as e:

                messagebox.showerror(
                    "Error",
                    str(e),
                )

        tk.Button(
            btn_frame,
            text="Simpan\nFaktur",
            bg="#22d3ee",
            width=12,
            command=save_invoice,
        ).pack(side="left", padx=5)

        # =========================================================
        # ITEM INPUT
        # =========================================================

        tk.Label(main, text="Produk").grid(
            row=3,
            column=0,
            padx=5,
            sticky="w",
        )

        tk.Label(main, text="Qty").grid(
            row=3,
            column=1,
            padx=5,
            sticky="w",
        )

        tk.Label(main, text="Harga").grid(
            row=3,
            column=2,
            padx=5,
            sticky="w",
        )

        tk.Label(main, text="Diskon / Qty").grid(
            row=3,
            column=3,
            padx=5,
            sticky="w",
        )

        prod_combo = ttk.Combobox(main)

        prod_combo.grid(
            row=4,
            column=0,
            padx=5,
            pady=5,
            sticky="we",
        )

        # =========================================================
        # LOAD PRODUCT
        # =========================================================

        products = self.db.execute(
            """
            SELECT
                id,
                name,
                cost_price,
                stock,
                is_active

            FROM products

            ORDER BY name
            """
        ).fetchall()

        self.product_map = {
            p["name"]: (
                p["id"],
                p["cost_price"],
                p["stock"],
                p["is_active"],
            )
            for p in products
        }

        prod_combo["values"] = list(self.product_map.keys())

        def on_product_select(event):

            prod = prod_combo.get()

            if prod in self.product_map:

                price = self.product_map[prod][1]

                price_entry.delete(0, "end")

                price_entry.insert(
                    0,
                    format_number(price),
                )

        prod_combo.bind(
            "<<ComboboxSelected>>",
            on_product_select,
        )

        qty_entry = tk.Entry(main)

        qty_entry.grid(
            row=4,
            column=1,
            padx=5,
            pady=5,
            sticky="we",
        )

        price_entry = tk.Entry(main)

        price_entry.grid(
            row=4,
            column=2,
            padx=5,
            pady=5,
            sticky="we",
        )

        disc_entry = tk.Entry(main)

        disc_entry.grid(
            row=4,
            column=3,
            padx=5,
            pady=5,
            sticky="we",
        )

        bind_number_entry(qty_entry)
        bind_number_entry(price_entry)
        bind_number_entry(disc_entry)

        btn_item = tk.Frame(main)

        btn_item.grid(
            row=4,
            column=5,
        )

        # =========================================================
        # TABLE ITEM
        # =========================================================

        table_frame = tk.Frame(
            main,
            bd=1,
            relief="solid",
        )

        table_frame.grid(
            row=5,
            column=0,
            columnspan=6,
            pady=10,
            sticky="nsew",
        )

        cols = (
            "produk",
            "qty",
            "harga",
            "diskon",
            "total",
        )

        item_tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            height=15,
        )

        headers = [
            ("produk", "Produk", 350),
            ("qty", "Qty", 100),
            ("harga", "Harga", 150),
            ("diskon", "Diskon", 150),
            ("total", "Total", 150),
        ]

        for c, h, w in headers:

            item_tree.heading(c, text=h)

            item_tree.column(c, width=w)

        item_tree.pack(fill="both", expand=True)

        # =========================================================
        # ITEM FUNCTIONS
        # =========================================================

        def add_item():

            prod = prod_combo.get()

            qty = parse_number(qty_entry.get())

            price = parse_number(price_entry.get())

            disc = parse_number(disc_entry.get())

            if prod not in self.product_map:

                messagebox.showerror(
                    "Error",
                    "Produk tidak ditemukan",
                )

                return

            product_id, cost_price, stock, is_active = self.product_map[prod]

            if is_active == 0:

                messagebox.showerror(
                    "Produk Nonaktif",
                    "Produk sudah dinonaktifkan",
                )

                return

            if qty <= 0:

                messagebox.showerror(
                    "Error",
                    "Qty harus lebih dari 0",
                )

                return

            total = (qty * price) - (disc * qty)

            sel = item_tree.selection()

            if sel:

                item_tree.item(
                    sel[0],
                    values=(
                        prod,
                        format_number(qty),
                        format_number(price),
                        format_number(disc),
                        format_number(total),
                    ),
                )

            else:

                item_tree.insert(
                    "",
                    "end",
                    values=(
                        prod,
                        format_number(qty),
                        format_number(price),
                        format_number(disc),
                        format_number(total),
                    ),
                )

            calculate_totals()

        def edit_item():

            sel = item_tree.selection()

            if not sel:

                messagebox.showerror(
                    "Error",
                    "Pilih item",
                )

                return

            vals = item_tree.item(sel[0], "values")

            prod_combo.set(vals[0])

            qty_entry.delete(0, "end")
            qty_entry.insert(0, vals[1])

            price_entry.delete(0, "end")
            price_entry.insert(0, vals[2])

            disc_entry.delete(0, "end")
            disc_entry.insert(0, vals[3])

        def delete_item():

            sel = item_tree.selection()

            if sel:

                item_tree.delete(sel[0])

            calculate_totals()

        def calculate_totals():

            subtotal = 0
            total_discount = 0
            grand_total = 0

            for row in item_tree.get_children():

                vals = item_tree.item(row, "values")

                qty = parse_number(vals[1])

                price = parse_number(vals[2])

                disc = parse_number(vals[3])

                subtotal += qty * price

                total_discount += disc * qty

                grand_total += (
                    (qty * price) - (disc * qty)
                )

            subtotal_entry.delete(0, "end")
            subtotal_entry.insert(
                0,
                format_number(subtotal),
            )

            disc_total_entry.delete(0, "end")
            disc_total_entry.insert(
                0,
                format_number(total_discount),
            )

            grand_total_entry.delete(0, "end")
            grand_total_entry.insert(
                0,
                format_number(grand_total),
            )

        tk.Button(
            btn_item,
            text="Tambah Item",
            bg="#22c55e",
            command=add_item,
        ).pack(side="left", padx=5)

        tk.Button(
            btn_item,
            text="Edit Item",
            bg="#facc15",
            command=edit_item,
        ).pack(side="left", padx=5)

        tk.Button(
            btn_item,
            text="Hapus Item",
            bg="#ef4444",
            command=delete_item,
        ).pack(side="left", padx=5)

        # =========================================================
        # FOOTER
        # =========================================================

        footer = tk.Frame(main)

        footer.grid(
            row=6,
            column=0,
            columnspan=6,
            sticky="we",
            pady=10,
        )

        footer.grid_columnconfigure(0, weight=1)

        left_footer = tk.Frame(footer)

        left_footer.grid(
            row=0,
            column=0,
            sticky="w",
        )

        tk.Label(
            left_footer,
            text="Keterangan:",
        ).grid(row=0, column=0, sticky="w")

        notes_entry = tk.Entry(
            left_footer,
            width=60,
        )

        notes_entry.grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
        )

        # =========================================================
        # TOTAL
        # =========================================================

        right_footer = tk.Frame(footer)

        right_footer.grid(
            row=0,
            column=1,
            sticky="e",
        )

        tk.Label(
            right_footer,
            text="Subtotal",
        ).grid(row=0, column=0, sticky="e")

        subtotal_entry = tk.Entry(
            right_footer,
            width=20,
            justify="right",
        )

        subtotal_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=2,
        )

        tk.Label(
            right_footer,
            text="Total Diskon",
        ).grid(row=1, column=0, sticky="e")

        disc_total_entry = tk.Entry(
            right_footer,
            width=20,
            justify="right",
        )

        disc_total_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=2,
        )

        tk.Label(
            right_footer,
            text="Grand Total",
        ).grid(row=2, column=0, sticky="e")

        grand_total_entry = tk.Entry(
            right_footer,
            width=20,
            justify="right",
        )

        grand_total_entry.grid(
            row=2,
            column=1,
            padx=5,
            pady=2,
        )

        # =========================================================
        # EXPORT WINDOW ATTR
        # =========================================================

        win.date_entry = date_entry
        win.supp_combo = supp_combo
        win.item_tree = item_tree
        win.calculate_totals = calculate_totals

        return win

    # =========================================================
    # RETURN INVOICE
    # =========================================================

    def return_invoice(self):

        sel = self.tree.selection()

        if not sel:

            messagebox.showerror(
                "Error",
                "Pilih faktur",
            )

            return

        vals = self.tree.item(sel[0], "values")

        invoice_no = vals[4]

        rows = self.db.execute(
            """
            SELECT
                pii.product_id,
                p.name,
                pii.qty,
                pii.unit_price,

                COALESCE((
                    SELECT SUM(qty)
                    FROM purchase_return_items pri
                    JOIN purchase_returns pr
                    ON pr.id = pri.purchase_return_id
                    WHERE pr.invoice_no = pi.invoice_no
                    AND pri.product_id = pii.product_id
                ),0) AS returned

            FROM purchase_invoice_items pii

            JOIN products p
            ON p.id = pii.product_id

            JOIN purchase_invoices pi
            ON pi.id = pii.purchase_invoice_id

            WHERE pi.invoice_no=?
            """,
            (invoice_no,),
        ).fetchall()

        win = tk.Toplevel(self)

        win.title("Retur Pembelian")

        win.geometry("700x400")

        tree = ttk.Treeview(
            win,
            columns=(
                "produk",
                "qty_beli",
                "qty_retur",
                "harga",
            ),
            show="headings",
        )

        headers = [
            ("produk", "Produk", 250),
            ("qty_beli", "Qty Beli", 100),
            ("qty_retur", "Qty Retur", 100),
            ("harga", "Harga", 120),
        ]

        for c, h, w in headers:

            tree.heading(c, text=h)

            tree.column(c, width=w)

        tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        form = tk.Frame(win)

        form.pack(pady=5)

        tk.Label(form, text="Produk").grid(
            row=0,
            column=0,
            padx=5,
        )

        tk.Label(form, text="Qty Retur").grid(
            row=0,
            column=1,
            padx=5,
        )

        product_label = tk.Label(
            form,
            text="-",
            width=25,
            anchor="w",
        )

        product_label.grid(
            row=1,
            column=0,
            padx=5,
        )

        qty_entry = tk.Entry(
            form,
            width=10,
        )

        qty_entry.grid(
            row=1,
            column=1,
            padx=5,
        )

        def select_item(event):

            item = tree.selection()

            if not item:
                return

            item = item[0]

            vals = tree.item(item, "values")

            product_label.config(text=vals[0])

            qty_entry.delete(0, "end")

            qty_entry.insert(0, vals[2])

        tree.bind(
            "<<TreeviewSelect>>",
            select_item,
        )

        def set_qty():

            item = tree.selection()

            if not item:

                messagebox.showerror(
                    "Error",
                    "Pilih produk dulu",
                )

                return

            item = item[0]

            vals = list(tree.item(item, "values"))

            qty = parse_number(qty_entry.get())

            qty_beli = parse_number(vals[1])

            qty_returned = parse_number(vals[2])

            if qty > (qty_beli - qty_returned):

                messagebox.showerror(
                    "Error",
                    f"Qty retur melebihi sisa ({qty_beli - qty_returned})",
                )

                return

            vals[2] = qty

            tree.item(item, values=vals)

        tk.Button(
            form,
            text="Set Retur",
            bg="#f59e0b",
            command=set_qty,
        ).grid(
            row=1,
            column=2,
            padx=10,
        )

        for r in rows:

            tree.insert(
                "",
                "end",
                values=(
                    r["name"],
                    r["qty"],
                    r["returned"],
                    r["unit_price"],
                ),
                tags=(r["product_id"],),
            )

        def save():

            items = []

            for item in tree.get_children():

                vals = tree.item(item, "values")

                qty_return = parse_number(vals[2])

                qty_beli = parse_number(vals[1])

                if qty_return > qty_beli:

                    messagebox.showerror(
                        "Error",
                        "Qty retur melebihi qty beli",
                    )

                    return

                if qty_return <= 0:
                    continue

                items.append(
                    {
                        "product_id": tree.item(item, "tags")[0],
                        "qty": qty_return,
                        "price": vals[3],
                    }
                )

            if not items:

                messagebox.showerror(
                    "Error",
                    "Tidak ada retur",
                )

                return

            inv = self.db.execute(
                """
                SELECT supplier_id
                FROM purchase_invoices
                WHERE invoice_no=?
                """,
                (invoice_no,),
            ).fetchone()

            return_no = self.service.create_purchase_return(
                current_date(),
                invoice_no,
                inv["supplier_id"],
                items,
            )

            messagebox.showinfo(
                "Sukses",
                f"Retur {return_no} berhasil",
            )

            win.destroy()

            self.load_data()

        tk.Button(
            win,
            text="Simpan Retur",
            bg="#22c55e",
            command=save,
        ).pack(pady=10)

    # =========================================================
    # PREVIEW
    # =========================================================

    def open_preview(self, event):

        region = self.tree.identify(
            "region",
            event.x,
            event.y,
        )

        if region != "cell":
            return

        column = self.tree.identify_column(event.x)

        item = self.tree.identify_row(event.y)

        if not item:
            return

        vals = self.tree.item(item, "values")

        invoice_no = vals[4]

        if column == "#2":

            self.preview_purchase_order(invoice_no)

        elif column == "#3":

            self.preview_faktur(invoice_no)

    # =========================================================
    # PREVIEW PO
    # =========================================================

    def preview_purchase_order(self, invoice_no):

        messagebox.showinfo(
            "Preview PO",
            f"Preview Purchase Order\n{invoice_no}",
        )

    # =========================================================
    # PREVIEW FAKTUR
    # =========================================================

    def preview_faktur(self, invoice_no):

        messagebox.showinfo(
            "Preview Faktur",
            f"Preview Faktur Pembelian\n{invoice_no}",
        )