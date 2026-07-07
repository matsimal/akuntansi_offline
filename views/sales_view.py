import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from utils.date_utils import today_str, start_of_month, end_of_month, start_of_year, end_of_year
from utils.widget_utils import bind_number_entry
from utils.number_utils import format_number , parse_number

from widgets.date_picker import DatePicker

class SalesView(tk.Frame):

    def __init__(self, parent, db, service, refresh_callback=None):
        super().__init__(parent, bg="#f9fafb")

        self.db = db
        self.service = service
        self.refresh_callback = refresh_callback

        self.selected_invoice = None

        self.build_ui()

    # ==========================================
    # UI
    # ==========================================

    def build_ui(self):

        # ==========================================
        # HEADER
        # ==========================================

        header = tk.Frame(self, bg="#f9fafb")
        header.pack(fill="x", pady=5)

        tk.Label(
            header, text="Penjualan", font=("Segoe UI", 20, "bold"), bg="#f9fafb"
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

        tk.Button(btn_frame, text="Cetak\nSurat Jalan", bg="#fde047", width=12).pack(
            side="left", padx=3
        )

        tk.Button(btn_frame, text="Cetak\nFaktur", bg="#d1d5db", width=12).pack(
            side="left", padx=3
        )

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
            text="Retur\nManual",
            bg="#f97316",
            fg="white",
            width=12,
            command=self.return_manual,
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

        # ==========================================
        # SEARCH & FILTER
        # ==========================================

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

        tk.Label(search_frame, text="Cari Faktur:", bg="#f9fafb").pack(side="left")

        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_data())

        tk.Label(search_frame, text="Status:", bg="#f9fafb").pack(
            side="left", padx=(10, 2)
        )

        self.status_filter = ttk.Combobox(
            search_frame,
            values=["SEMUA", "PAID", "UNPAID", "PARTIAL"],
            state="readonly",
            width=15,
        )

        self.status_filter.set("SEMUA")
        self.status_filter.pack(side="left")
        self.status_filter.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        # ==========================================
        # TABLE INVOICE
        # ==========================================

        table_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("check", "invoice", "date", "customer", "total", "paid", "status")

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        cols = (
            "check",
            "view1",
            "view2",
            "sj",
            "invoice",
            "date",
            "customer",
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
            ("view1", "Lihat DO", 40),
            ("view2", "Lihat Faktur", 40),
            ("sj", "No DO", 150),
            ("invoice", "No Faktur", 150),
            ("date", "Tanggal", 120),
            ("customer", "Pelanggan", 220),
            ("total", "Total", 120),
            ("return", "Retur", 120),
            ("net", "Net", 120),
            ("paid", "Dibayar", 120),
            ("status", "Status", 110),
        ]

        for c, h, w in headers:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Button-1>", self.tree_click)
        self.tree.bind("<Double-1>", self.open_preview)

        self.load_data()

    def tree_click(self, event):

        region = self.tree.identify("region", event.x, event.y)

        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)

        if not row:
            return

        vals = self.tree.item(row, "values")

        # kolom pertama checkbox
        if column == "#1":
            self.toggle_checkbox(event)
            return

        # kolom view surat jalan
        if column == "#2":
            invoice_no = vals[4]
            self.preview_surat_jalan(invoice_no)
            return

        # kolom view faktur
        if column == "#3":
            invoice_no = vals[4]
            self.preview_faktur(invoice_no)
            return

    # ==========================================
    # ITEM FUNCTIONS
    # ==========================================

    def add_item(self):

        prod = self.prod_combo.get()
        qty = parse_number(self.qty_entry.get())
        price = parse_number(self.price_entry.get())
        disc = parse_number(self.discount_entry.get())

        # cek produk aktif
        prod_data = self.product_map.get(prod)

        if not prod_data:
            messagebox.showerror("Error", "Produk tidak ditemukan")
            return

        product_id, sell_price, is_active = prod_data

        if is_active == 0:
            messagebox.showerror(
                "Produk Nonaktif",
                "Produk ini sudah dinonaktifkan dan tidak bisa dijual.",
            )
            return

        if not prod or qty <= 0:
            messagebox.showerror("Error", "Isi produk dan qty")
            return

        total = (qty * price) - (disc * qty)

        self.item_tree.insert(
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

    def delete_item(self):

        s = self.item_tree.selection()

        if not s:
            return

        self.item_tree.delete(s[0])

    def pay_invoice(self):

        sel = self.tree.selection()

        if not sel:
            messagebox.showerror("Error", "Pilih faktur")
            return

        vals = self.tree.item(sel[0], "values")

        invoice_no = vals[4]

        # gunakan popup pembayaran saja
        self.popup_payment(invoice_no)

    def edit_invoice(self):

        sel = self.tree.selection()

        if not sel:
            messagebox.showerror("Error", "Pilih faktur")
            return

        vals = self.tree.item(sel[0], "values")
        invoice_no = vals[4]
        self.selected_invoice = invoice_no

        inv = self.db.execute(
            """
            SELECT
                s.invoice_no,
                s.trx_date,
                c.name customer
            FROM sales_invoices s
            LEFT JOIN customers c ON c.id=s.customer_id
            WHERE s.invoice_no=?
            """,
            (invoice_no,),
        ).fetchone()

        if not inv:
            messagebox.showerror("Error", "Invoice tidak ditemukan")
            return

        # ambil semua item
        items = self.db.execute(
            """
            SELECT
                sii.product_id,
                p.name,
                sii.qty,
                sii.unit_price,
                sii.discount,
                sii.total
            FROM sales_invoice_items sii
            JOIN products p ON p.id=sii.product_id
            JOIN sales_invoices s ON s.id=sii.sales_invoice_id
            WHERE s.invoice_no=?
            """,
            (invoice_no,),
        ).fetchall()

        self.old_qty_map = {}

        for item in items:
            self.old_qty_map[item["product_id"]] = item["qty"]

        # buka popup faktur
        win = self.create_invoice()

        # isi data header
        win.date_entry.set(inv["trx_date"])
        win.cust_combo.set(inv["customer"])

        # isi item
        for item in items:

            disc_per_qty = item["discount"] / item["qty"] if item["qty"] else 0

            win.item_tree.insert(
                "",
                "end",
                values=(
                    item["name"],
                    format_number(item["qty"]),
                    format_number(item["unit_price"]),
                    format_number(disc_per_qty),
                    format_number(item["total"]),
                ),
            )

        win.calculate_totals()

        win.invoice_no = invoice_no

    def delete_invoice(self):

        if self.selected_invoices:
            targets = list(self.selected_invoices)
        else:

            sel = self.tree.selection()

            if not sel:
                messagebox.showerror("Error", "Pilih faktur terlebih dahulu")
                return

            vals = self.tree.item(sel[0], "values")
            targets = [vals[4]]

        if not messagebox.askyesno("Konfirmasi", "Hapus faktur yang dipilih?"):
            return

        try:

            for invoice_no in targets:

                inv = self.db.execute(
                    "SELECT id FROM sales_invoices WHERE invoice_no=?",
                    (invoice_no,),
                ).fetchone()

                if not inv:
                    continue

                invoice_id = inv["id"]

                # ambil item faktur
                items = self.db.execute(
                    """
                    SELECT product_id, qty
                    FROM sales_invoice_items
                    WHERE sales_invoice_id=?
                    """,
                    (invoice_id,),
                ).fetchall()

                for item in items:

                    product_id = item["product_id"]
                    qty = item["qty"]

                    # kembalikan stok
                    self.db.execute(
                        """
                        UPDATE products
                        SET stock = stock + ?
                        WHERE id=?
                        """,
                        (qty, product_id),
                        commit=True,
                    )

                # hapus inventory movement
                self.db.execute(
                    "DELETE FROM inventory_movements WHERE ref_no=?",
                    (invoice_no,),
                    commit=True,
                )

                # hapus detail item
                self.db.execute(
                    "DELETE FROM sales_invoice_items WHERE sales_invoice_id=?",
                    (invoice_id,),
                    commit=True,
                )

                # hapus invoice
                self.db.execute(
                    "DELETE FROM sales_invoices WHERE id=?",
                    (invoice_id,),
                    commit=True,
                )

            self.selected_invoices.clear()

            messagebox.showinfo("Sukses", "Faktur berhasil dihapus")

            self.load_data()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def popup_payment(self, invoice_no):

        win = tk.Toplevel(self)
        win.title("Pembayaran Faktur")
        win.geometry("350x260")

        tk.Label(win, text=f"Invoice : {invoice_no}").pack(pady=5)

        tk.Label(win, text="Metode Pembayaran").pack()

        method_combo = ttk.Combobox(
            win,
            values=["Cash", "Transfer", "Giro", "QRIS"],
            state="readonly",
        )
        method_combo.pack()

        tk.Label(win, text="Akun Bank").pack()

        accounts = self.db.execute(
            "SELECT code,name FROM accounts WHERE type='Asset'"
        ).fetchall()

        acc_map = {f"{r['code']} - {r['name']}": r["code"] for r in accounts}

        acc_combo = ttk.Combobox(win, values=list(acc_map.keys()), state="readonly")
        acc_combo.pack()

        tk.Label(win, text="Jumlah Bayar").pack()

        amount_entry = tk.Entry(win)
        amount_entry.pack()

        bind_number_entry(amount_entry)

        def save():

            method = method_combo.get()
            acc = acc_combo.get()

            if not method:
                messagebox.showerror("Error", "Pilih metode pembayaran")
                return

            if not acc:
                messagebox.showerror("Error", "Pilih akun bank/kas")
                return

            amount = parse_number(amount_entry.get())

            if amount <= 0:
                messagebox.showerror("Error", "Jumlah pembayaran tidak valid")
                return

            code = acc_map[acc]

            try:

                self.service.receive_sales_payment(
                    invoice_no, amount, acc, code, method
                )

                messagebox.showinfo("Sukses", "Pembayaran berhasil disimpan")

                win.destroy()

                self.load_data()

            except Exception as e:

                messagebox.showerror("Error", str(e))

        tk.Button(win, text="Simpan", command=save, bg="#16a34a", fg="white").pack(
            pady=10
        )

    # ==========================================
    # CREATE INVOICE
    # ==========================================

    def create_invoice(self):

        win = tk.Toplevel(self)
        win.title("Faktur Penjualan")
        win.geometry("1200x650")

        # center screen
        win.update_idletasks()
        w = 1200
        h = 650
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

        main = tk.Frame(win)
        main.pack(fill="both", expand=True, padx=20, pady=15)

        # buat layout responsive
        for i in range(6):
            main.grid_columnconfigure(i, weight=1)

        main.grid_rowconfigure(5, weight=1)

        # ==========================
        # HEADER FORM
        # ==========================
        tk.Label(main, text="Tanggal").grid(row=1, column=0, sticky="w")
        tk.Label(main, text="Pelanggan").grid(row=1, column=1, sticky="w")
        tk.Label(main, text="No. Faktur").grid(row=1, column=2, sticky="w")

        date_entry = DatePicker(main, width=10)
        date_entry.grid(row=2, column=0, padx=5, pady=5, sticky="we")

        cust_combo = ttk.Combobox(main, width=30)
        cust_combo.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        # load customer
        customers = self.db.execute(
            "SELECT id,name FROM customers ORDER BY name"
        ).fetchall()

        self.customer_map = {c["name"]: c["id"] for c in customers}

        cust_combo["values"] = list(self.customer_map.keys())

        invoice_entry = tk.Entry(main, width=28)
        invoice_entry.grid(row=2, column=2, padx=5, pady=5, sticky="we")

        # ==========================
        # RIGHT BUTTONS
        # ==========================
        btn_frame = tk.Frame(main)
        btn_frame.grid(row=1, column=3, rowspan=2, columnspan=3, sticky="e")

        tk.Button(
            btn_frame, text="Simpan &\nCetak Surat Jalan", bg="#facc15", width=18
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Simpan &\nCetak Faktur", bg="#d1d5db", width=18
        ).pack(side="left", padx=5)

        def save_invoice():

            cust = cust_combo.get()
            trx_date = date_entry.get().replace("-", "/")
            notes = notes_entry.get().strip()

            if not cust:
                messagebox.showerror("Error", "Pilih pelanggan")
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
                messagebox.showerror("Error", "Belum ada item")
                return

            try:

                if self.selected_invoice:

                    invoice_no = self.service.update_sales_invoice_multi(
                        self.selected_invoice,
                        trx_date,
                        self.customer_map[cust],
                        items,
                        notes,
                    )

                else:

                    invoice_no = self.service.create_sales_invoice_multi(
                        trx_date, self.customer_map[cust], items, notes
                    )

                messagebox.showinfo("Sukses", f"Faktur {invoice_no} berhasil dibuat")
                minus_products = self.db.execute(
                    """
                    SELECT name, stock
                    FROM products
                    WHERE stock < 0
                    """
                ).fetchall()

                if minus_products:

                    warning_text = "Produk berikut mengalami stok minus:\n\n"

                    for p in minus_products:
                        warning_text += f"- {p['name']} : {format_number(p['stock'])}\n"

                    messagebox.showwarning(
                        "Warning Stok Minus",
                        warning_text
                    )

                win.destroy()
                self.load_data()

            except Exception as e:

                messagebox.showerror("Error", str(e))

        tk.Button(
            btn_frame,
            text="Simpan\nFaktur",
            bg="#22d3ee",
            width=12,
            command=save_invoice,
        ).pack(side="left", padx=5)

        # ==========================================
        # ITEM INPUT
        # ==========================================

        # header
        tk.Label(main, text="Produk").grid(row=3, column=0, padx=5, sticky="w")
        tk.Label(main, text="Qty").grid(row=3, column=1, padx=5, sticky="w")
        tk.Label(main, text="Harga").grid(row=3, column=2, padx=5, sticky="w")
        tk.Label(main, text="Diskon / Qty").grid(row=3, column=3, padx=5, sticky="w")

        # input
        prod_combo = ttk.Combobox(main)
        prod_combo.grid(row=4, column=0, padx=5, pady=5, sticky="we")

        def on_product_select(event):

            prod = prod_combo.get()

            if prod in self.product_map:

                price = self.product_map[prod][1]

                price_entry.delete(0, "end")
                price_entry.insert(0, format_number(price))

        prod_combo.bind("<<ComboboxSelected>>", on_product_select)

        # load produk
        products = self.db.execute(
            "SELECT id,name,sell_price,stock,is_active FROM products ORDER BY name"
        ).fetchall()

        self.product_map = {
            p["name"]: (p["id"], p["sell_price"], p["stock"], p["is_active"])
            for p in products
        }

        prod_combo["values"] = list(self.product_map.keys())

        qty_entry = tk.Entry(main)
        qty_entry.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        price_entry = tk.Entry(main)
        price_entry.grid(row=4, column=2, padx=5, pady=5, sticky="we")

        disc_entry = tk.Entry(main)
        disc_entry.grid(row=4, column=3, padx=5, pady=5, sticky="we")

        btn_item = tk.Frame(main)
        btn_item.grid(row=4, column=4, padx=5)

        # format angka otomatis
        bind_number_entry(qty_entry)
        bind_number_entry(price_entry)
        bind_number_entry(disc_entry)

        btn_item = tk.Frame(main)
        btn_item.grid(row=4, column=5)

        # ==========================
        # TABLE ITEM
        # ==========================
        table_frame = tk.Frame(main, bd=1, relief="solid")
        table_frame.grid(row=5, column=0, columnspan=6, pady=10, sticky="nsew")

        cols = ("produk", "qty", "harga", "diskon", "total")

        item_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)

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

        # ==========================
        # ITEM FUNCTIONS
        # ==========================
        def add_item():

            prod = prod_combo.get()
            qty = parse_number(qty_entry.get())
            price = parse_number(price_entry.get())
            disc = parse_number(disc_entry.get())

            if prod not in self.product_map:
                messagebox.showerror("Error", "Produk tidak ditemukan")
                return

            product_id, sell_price, _, is_active = self.product_map[prod]

            # ambil stok terbaru dari database
            row = self.db.execute(
                "SELECT stock FROM products WHERE id=?", (product_id,)
            ).fetchone()

            stock = row["stock"] if row else 0

            old_qty = 0

            if hasattr(self, "old_qty_map"):
                old_qty = self.old_qty_map.get(product_id, 0)

            available_stock = stock + old_qty

            if qty > available_stock:

                result = messagebox.askyesno(
                    "Peringatan Stok Minus",
                    f"Stok tersedia hanya {format_number(available_stock)}.\n\n"
                    f"Jika dilanjutkan stok akan minus.\n\n"
                    f"Lanjutkan transaksi?"
                )

                if not result:
                    return

            # cek produk aktif
            if is_active == 0:
                messagebox.showerror(
                    "Produk Nonaktif",
                    "Produk ini sudah dinonaktifkan dan tidak bisa dijual.",
                )
                return

            if qty <= 0:
                messagebox.showerror("Error", "Qty harus lebih dari 0")
                return

            # =========================
            # CEK STOK
            # =========================

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

        def delete_item():

            sel = item_tree.selection()
            if sel:
                item_tree.delete(sel[0])

            calculate_totals()

        def edit_item():

            sel = item_tree.selection()

            if not sel:
                messagebox.showerror("Error", "Pilih item yang ingin diedit")
                return

            vals = item_tree.item(sel[0], "values")

            prod = vals[0]
            qty = vals[1]
            price = vals[2]
            disc = vals[3]

            prod_combo.set(prod)

            qty_entry.delete(0, "end")
            qty_entry.insert(0, qty)

            price_entry.delete(0, "end")
            price_entry.insert(0, price)

            disc_entry.delete(0, "end")
            disc_entry.insert(0, disc)

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
                grand_total += (qty * price) - (disc * qty)

            subtotal_entry.delete(0, "end")
            subtotal_entry.insert(0, format_number(subtotal))

            disc_total_entry.delete(0, "end")
            disc_total_entry.insert(0, format_number(total_discount))

            grand_total_entry.delete(0, "end")
            grand_total_entry.insert(0, format_number(grand_total))

        tk.Button(btn_item, text="Tambah Item", bg="#22c55e", command=add_item).pack(
            side="left", padx=5
        )

        tk.Button(btn_item, text="Edit Item", bg="#facc15", command=edit_item).pack(
            side="left", padx=5
        )

        tk.Button(btn_item, text="Hapus Item", bg="#ef4444", command=delete_item).pack(
            side="left", padx=5
        )

        footer = tk.Frame(main)
        footer.grid(row=6, column=0, columnspan=6, sticky="we", pady=10)

        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=0)

        # ==========================
        # KETERANGAN (KIRI)
        # ==========================
        left_footer = tk.Frame(footer)
        left_footer.grid(row=0, column=0, sticky="w")

        tk.Label(left_footer, text="Keterangan:").grid(row=0, column=0, sticky="w")

        notes_entry = tk.Entry(left_footer, width=60)
        notes_entry.grid(row=1, column=0, padx=5, pady=5)

        # ==========================
        # TOTAL (KANAN)
        # ==========================
        right_footer = tk.Frame(footer)
        right_footer.grid(row=0, column=1, sticky="e")

        tk.Label(right_footer, text="Subtotal").grid(row=0, column=0, sticky="e")
        subtotal_entry = tk.Entry(right_footer, width=20, justify="right")
        subtotal_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(right_footer, text="Total Diskon").grid(row=1, column=0, sticky="e")
        disc_total_entry = tk.Entry(right_footer, width=20, justify="right")
        disc_total_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(right_footer, text="Grand Total").grid(row=2, column=0, sticky="e")
        grand_total_entry = tk.Entry(right_footer, width=20, justify="right")
        grand_total_entry.grid(row=2, column=1, padx=5, pady=2)

        win.date_entry = date_entry
        win.cust_combo = cust_combo
        win.item_tree = item_tree

        win.calculate_totals = calculate_totals

        return win

    def update_invoice(self):

        if not self.selected_invoice:
            messagebox.showerror("Error", "Tidak ada faktur yang sedang diedit")
            return

        cust = self.cust_combo.get()
        trx_date = self.date_entry.get()

        if not cust:
            messagebox.showerror("Error", "Pilih pelanggan")
            return

        items = []

        for row in self.item_tree.get_children():

            vals = self.item_tree.item(row, "values")

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
            messagebox.showerror("Error", "Belum ada item")
            return

        item = items[0]

        try:

            self.service.update_sales_invoice(
                self.selected_invoice,
                trx_date,
                self.customer_map[cust],
                item["product_id"],
                item["qty"],
                item["price"],
                item["discount"],
            )

            messagebox.showinfo("Sukses", "Faktur berhasil diupdate")

            self.selected_invoice = None

            for i in self.item_tree.get_children():
                self.item_tree.delete(i)

            self.load_data()

        except Exception as e:

            messagebox.showerror("Error", str(e))

    # ==========================================
    # LOAD DATA
    # ==========================================

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
        s.sj_no,
        s.invoice_no,
        s.trx_date,
        c.name customer,
        s.total,
        s.paid,
        s.status,
        COALESCE((
            SELECT SUM(qty * price)
            FROM sales_return_items sri
            JOIN sales_returns sr ON sr.id=sri.sales_return_id
            WHERE sr.invoice_no = s.invoice_no
        ),0) AS return_total
        FROM sales_invoices s
        LEFT JOIN customers c ON c.id=s.customer_id
        ORDER BY s.id DESC
        """
        ).fetchall()

        for r in rows:

            invoice = r["invoice_no"]
            customer = (r["customer"] or "").lower()
            status = r["status"]

            if keyword:
                if keyword not in invoice.lower() and keyword not in customer:
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
                    r["sj_no"],
                    invoice,
                    r["trx_date"],
                    r["customer"],
                    format_number(total),
                    format_number(retur),
                    format_number(net),
                    format_number(r["paid"]),
                    status,
                ),
            )

    def save_invoice(self):

        cust = self.cust_combo.get()
        trx_date = self.date_entry.get()

        if not cust:
            messagebox.showerror("Error", "Pilih pelanggan")
            return

        items = []

        for row in self.item_tree.get_children():

            vals = self.item_tree.item(row, "values")

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
            messagebox.showerror("Error", "Belum ada item")
            return

        try:

            if self.selected_invoice:

                self.service.update_sales_invoice_multi(
                    self.selected_invoice, trx_date, self.customer_map[cust], items
                )

                messagebox.showinfo("Sukses", "Faktur berhasil diupdate")

                self.selected_invoice = None

            else:

                invoice = self.service.create_sales_invoice_multi(
                    trx_date, self.customer_map[cust], items
                )

                messagebox.showinfo("Sukses", f"Invoice {invoice} dibuat")

            for i in self.item_tree.get_children():
                self.item_tree.delete(i)

            self.load_data()

        except Exception as e:
            messagebox.showerror("Error", str(e))

        for item in items:

            row = self.db.execute(
                "SELECT stock FROM products WHERE id=?", (item["product_id"],)
            ).fetchone()

            stock = row["stock"] if row else 0

            if item["qty"] > stock:
                raise Exception(f"Stok produk tidak cukup. Tersedia: {stock}")

    def toggle_checkbox(self, event):

        region = self.tree.identify("region", event.x, event.y)

        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)

        if not item:
            return

        vals = list(self.tree.item(item, "values"))

        # checkbox
        if column == "#1":
            invoice = vals[4]

            if invoice in self.selected_invoices:
                self.selected_invoices.remove(invoice)
                vals[0] = "☐"
            else:
                self.selected_invoices.add(invoice)
                vals[0] = "☑"

            self.tree.item(item, values=vals)

        # mata kuning
        elif column == "#2":
            invoice = vals[4]
            messagebox.showinfo("Preview Faktur", f"Lihat faktur {invoice}")

        # mata abu
        elif column == "#3":
            invoice = vals[4]
            messagebox.showinfo("Detail Faktur", f"Detail faktur {invoice}")

    def refresh_checkboxes(self):

        for item in self.tree.get_children():

            vals = list(self.tree.item(item, "values"))
            invoice = vals[4]

            if invoice in self.selected_invoices:
                vals[0] = "☑"
            else:
                vals[0] = "☐"

            self.tree.item(item, values=vals)

    def return_invoice(self):

        sel = self.tree.selection()

        if not sel:
            messagebox.showerror("Error", "Pilih faktur")
            return

        vals = self.tree.item(sel[0], "values")

        invoice_no = vals[4]

        rows = self.db.execute(
            """
        SELECT
            sii.product_id,
            p.name,
            sii.qty,
            sii.unit_price,
            COALESCE((
                SELECT SUM(qty)
                FROM sales_return_items sri
                JOIN sales_returns sr ON sr.id=sri.sales_return_id
                WHERE sr.invoice_no=s.invoice_no
                AND sri.product_id=sii.product_id
            ),0) AS returned
        FROM sales_invoice_items sii
        JOIN products p ON p.id=sii.product_id
        JOIN sales_invoices s ON s.id=sii.sales_invoice_id
        WHERE s.invoice_no=?
        """,
            (invoice_no,),
        ).fetchall()

        win = tk.Toplevel(self)
        win.title("Retur Penjualan")
        win.geometry("700x400")

        tree = ttk.Treeview(
            win, columns=("produk", "qty_jual", "qty_retur", "harga"), show="headings"
        )

        headers = [
            ("produk", "Produk", 250),
            ("qty_jual", "Qty Jual", 100),
            ("qty_retur", "Qty Retur", 100),
            ("harga", "Harga", 120),
        ]

        for c, h, w in headers:
            tree.heading(c, text=h)
            tree.column(c, width=w)

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        form = tk.Frame(win)
        form.pack(pady=5)

        tk.Label(form, text="Produk").grid(row=0, column=0, padx=5)
        tk.Label(form, text="Qty Retur").grid(row=0, column=1, padx=5)

        product_label = tk.Label(form, text="-", width=25, anchor="w")
        product_label.grid(row=1, column=0, padx=5)

        qty_entry = tk.Entry(form, width=10)
        qty_entry.grid(row=1, column=1, padx=5)

        def select_item(event):

            item = tree.selection()
            if not item:
                return

            item = item[0]
            vals = tree.item(item, "values")

            product_label.config(text=vals[0])

            qty_entry.delete(0, "end")
            qty_entry.insert(0, vals[2])

        tree.bind("<<TreeviewSelect>>", select_item)

        def set_qty():

            item = tree.selection()
            if not item:
                messagebox.showerror("Error", "Pilih produk dulu")
                return

            item = item[0]
            vals = list(tree.item(item, "values"))

            try:
                qty = float(qty_entry.get())
            except:
                messagebox.showerror("Error", "Qty tidak valid")
                return

            qty_sold = float(vals[1])
            qty_returned = float(vals[2])

            if qty > (qty_sold - qty_returned):
                messagebox.showerror(
                    "Error",
                    f"Qty retur melebihi sisa yang bisa diretur ({qty_sold - qty_returned})",
                )
                return

            vals[2] = qty
            tree.item(item, values=vals)

        tk.Button(form, text="Set Retur", bg="#f59e0b", command=set_qty).grid(
            row=1, column=2, padx=10
        )

        for r in rows:

            tree.insert(
                "",
                "end",
                values=(r["name"], r["qty"], r["returned"], r["unit_price"]),
                tags=(r["product_id"],),
            )

        def save():

            items = []

            for item in tree.get_children():

                vals = tree.item(item, "values")

                qty_return = float(vals[2])
                qty_sold = float(vals[1])

                if qty_return > qty_sold:
                    messagebox.showerror(
                        "Error",
                        f"Qty retur tidak boleh lebih dari qty jual ({qty_sold})",
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
                messagebox.showerror("Error", "Tidak ada retur")
                return

            inv = self.db.execute(
                "SELECT customer_id FROM sales_invoices WHERE invoice_no=?",
                (invoice_no,),
            ).fetchone()

            return_no = self.service.create_sales_return(
                today_str(), invoice_no, inv["customer_id"], items
            )

            messagebox.showinfo("Sukses", f"Retur {return_no} berhasil")

            win.destroy()

            self.load_data()

        tk.Button(win, text="Simpan Retur", bg="#22c55e", command=save).pack(pady=10)

    def return_manual(self):

        win = tk.Toplevel(self)
        win.title("Retur Penjualan Manual")
        win.geometry("600x400")

        tk.Label(win, text="Customer").pack()

        customers = self.db.execute(
            "SELECT id,name FROM customers ORDER BY name"
        ).fetchall()

        cust_map = {c["name"]: c["id"] for c in customers}

        cust_combo = ttk.Combobox(win, values=list(cust_map.keys()))
        cust_combo.pack()

        tk.Label(win, text="Produk").pack()

        products = self.db.execute(
            "SELECT id,name,sell_price FROM products ORDER BY name"
        ).fetchall()

        prod_map = {p["name"]: (p["id"], p["sell_price"]) for p in products}

        prod_combo = ttk.Combobox(win, values=list(prod_map.keys()))
        prod_combo.pack()

        tk.Label(win, text="Qty").pack()
        qty_entry = tk.Entry(win)
        qty_entry.pack()

        tk.Label(win, text="Harga").pack()
        price_entry = tk.Entry(win)
        price_entry.pack()

        items = []

        def add_item():

            prod = prod_combo.get()
            qty = parse_number(qty_entry.get())
            price = parse_number(price_entry.get())

            if qty <= 0:
                messagebox.showerror("Error", "Qty harus lebih dari 0")
                return

            if prod not in prod_map:
                messagebox.showerror("Error", "Produk tidak valid")
                return

            items.append(
                {
                    "product_id": prod_map[prod][0],
                    "qty": qty,
                    "price": price,
                }
            )

            messagebox.showinfo("Item", "Item retur ditambahkan")

        tk.Button(win, text="Tambah Item", command=add_item).pack(pady=5)

        def save():

            cust = cust_combo.get()

            if not cust:
                messagebox.showerror("Error", "Pilih customer")
                return

            if not items:
                messagebox.showerror("Error", "Belum ada item")
                return

            return_no = self.service.create_sales_return_manual(
                today_str(),
                cust_map[cust],
                items,
            )

            messagebox.showinfo("Sukses", f"Retur {return_no} berhasil")

            win.destroy()
            self.load_data()

        tk.Button(win, text="Simpan Retur", bg="#22c55e", command=save).pack(pady=10)

    def open_preview(self, event):

        region = self.tree.identify("region", event.x, event.y)

        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)

        if not item:
            return

        vals = self.tree.item(item, "values")

        invoice_no = vals[4]

        # kolom view1 = #2
        if column == "#2":
            self.preview_surat_jalan(invoice_no)

    def preview_surat_jalan(self, invoice_no):

        # ================= DATA =================
        header = self.db.execute(
            """
            SELECT
            s.sj_no,
            s.trx_date,
            c.name customer,
            c.address customer_address,
            s.notes
            FROM sales_invoices s
            LEFT JOIN customers c ON c.id=s.customer_id
            WHERE s.invoice_no=?
        """,
            (invoice_no,),
        ).fetchone()

        items = self.db.execute(
            """
            SELECT
            p.name,
            sii.qty
            FROM sales_invoice_items sii
            JOIN products p ON p.id=sii.product_id
            JOIN sales_invoices s ON s.id=sii.sales_invoice_id
            WHERE s.invoice_no=?
        """,
            (invoice_no,),
        ).fetchall()

        profile = self.db.execute(
            """
            SELECT * FROM company_profile LIMIT 1
        """
        ).fetchone()

        # ================= WINDOW =================
        win = tk.Toplevel(self)
        win.title("Preview Surat Jalan")
        win.geometry("900x700")

        main = tk.Frame(win, bg="white")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # ================= ROW 1 =================
        row1 = tk.Frame(main, bg="white")
        row1.pack(fill="x")

        tk.Label(
            row1, text="SURAT JALAN", font=("Segoe UI", 16, "bold"), bg="white"
        ).pack()

        # ================= ROW 2 =================
        row2 = tk.Frame(main, bg="white")
        row2.pack(fill="x", pady=10)

        row2.grid_columnconfigure(0, weight=0)
        row2.grid_columnconfigure(1, weight=1)
        row2.grid_columnconfigure(2, weight=1)

        # ================= LOGO =================
        logo_frame = tk.Frame(row2, width=120, height=100, bg="white")
        logo_frame.grid(row=0, column=0, padx=5)
        logo_frame.pack_propagate(False)

        try:
            from PIL import Image, ImageTk

            if profile["logo"]:
                img = Image.open(profile["logo"])
                img = img.resize((120, 100))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(logo_frame, image=photo, bg="white")
                lbl.image = photo
                lbl.pack(expand=True)
            else:
                tk.Label(logo_frame, text="LOGO", bg="white").pack(expand=True)
        except:
            tk.Label(logo_frame, text="LOGO", bg="white").pack(expand=True)

        # ================= PERUSAHAAN =================
        company = tk.Frame(row2, bg="white")
        company.grid(row=0, column=1, sticky="w")

        tk.Label(company, text=profile["address"] or "-", bg="white").pack(anchor="w")
        tk.Label(company, text=profile["phone"] or "-", bg="white").pack(anchor="w")
        tk.Label(company, text="Rekening perusahaan", bg="white").pack(anchor="w")
        tk.Label(company, text="Rekening perusahaan #2", bg="white").pack(anchor="w")

        # ================= TRANSAKSI =================
        trx = tk.Frame(row2, bg="white")
        trx.grid(row=0, column=2, sticky="e")

        def trx_row(label, value):
            row = tk.Frame(trx, bg="white")
            row.pack(anchor="e")

            # kolom 1 (label align kanan)
            tk.Label(row, text=label, width=18, anchor="e", bg="white").pack(
                side="left"
            )

            tk.Label(row, text=" : ", bg="white").pack(side="left")

            # kolom 2 (value)
            tk.Label(row, text=value, anchor="w", bg="white").pack(side="left")

        trx_row("Tanggal", header["trx_date"])
        trx_row("No. Surat Jalan", header["sj_no"])
        trx_row("Pelanggan", header["customer"])
        trx_row("Alamat", header["customer_address"] or "-")

        # ================= ROW 3 (TABEL) =================
        row3 = tk.Frame(main, bg="white")
        row3.pack(fill="both", expand=True, pady=10)

        cols = ("no", "name", "qty")

        tree = ttk.Treeview(row3, columns=cols, show="headings")

        tree.heading("no", text="No")
        tree.heading("name", text="Nama Barang")
        tree.heading("qty", text="Qty")

        tree.column("no", width=50, anchor="center")
        tree.column("name", width=600)
        tree.column("qty", width=100, anchor="center")

        tree.pack(fill="both", expand=True)

        for i, item in enumerate(items, start=1):
            tree.insert("", "end", values=(i, item["name"], item["qty"]))

        # ================= ROW 4 =================
        row4 = tk.Frame(main, bg="white")
        row4.pack(fill="x", pady=10)

        row4.grid_columnconfigure(0, weight=1)
        row4.grid_columnconfigure(1, weight=1)

        # KETERANGAN
        notes_frame = tk.Frame(row4, bg="white")
        notes_frame.grid(row=0, column=0, sticky="w")

        tk.Label(notes_frame, text="Keterangan:", bg="white").pack(anchor="w")

        notes_box = tk.Text(notes_frame, height=4, width=50)
        notes_box.pack()
        notes_box.insert("1.0", header["notes"] or "")

        # TTD
        sign_frame = tk.Frame(row4, bg="white")
        sign_frame.grid(row=0, column=1, sticky="e")

        for label in ["Finance", "Supir", "Penerima"]:
            box = tk.Frame(
                sign_frame, width=100, height=80, bd=1, relief="solid", bg="white"
            )
            box.pack(side="left", padx=10)
            box.pack_propagate(False)

            tk.Label(box, text=label, bg="white").pack(side="bottom", pady=5)

    def preview_faktur(self, invoice_no):

        header = self.db.execute(
            """
            SELECT
            s.invoice_no,
            s.trx_date,
            c.name customer,
            s.total,
            s.notes
            FROM sales_invoices s
            LEFT JOIN customers c ON c.id=s.customer_id
            WHERE s.invoice_no=?
            """,
            (invoice_no,),
        ).fetchone()

        items = self.db.execute(
            """
            SELECT
            p.name,
            sii.qty,
            sii.price,
            sii.discount,
            sii.total,
            u.name unit
            FROM sales_invoice_items sii
            JOIN products p ON p.id=sii.product_id
            JOIN sales_invoices s ON s.id=sii.sales_invoice_id
            WHERE s.invoice_no=?
            """,
            (invoice_no,),
        ).fetchall()

        self.show_invoice_window(header, items)

    def show_sj_window(self, header, items):

        win = tk.Toplevel(self)
        win.title("Preview Surat Jalan")

        # ukuran A5 landscape (pixel kira2)
        width = 842
        height = 595

        win.geometry(f"{width}x{height}")

        canvas = tk.Canvas(win, bg="white", width=width, height=height)
        canvas.pack(fill="both", expand=True)

        center_x = width / 2

        # =========================
        # LOAD PROFIL PERUSAHAAN
        # =========================
        profile = self.db.execute(
            "SELECT company_name,address,description,logo FROM company_profile LIMIT 1"
        ).fetchone()

        company = profile["company_name"] if profile else ""
        address = profile["address"] if profile else ""
        desc = profile["description"] if profile else ""
        logo = profile["logo"] if profile else ""
        notes = header["notes"] if header["notes"] else ""

        # =========================
        # LOGO
        # =========================
        if logo:
            try:
                from PIL import Image, ImageTk

                img = Image.open(logo)
                img = img.resize((170, 130))
                photo = ImageTk.PhotoImage(img)

                canvas.logo = photo
                canvas.create_image(150, 100, image=photo)
            except:
                pass

        # =========================
        # TITLE
        # =========================
        canvas.create_text(center_x, 40, text="SURAT JALAN", font=("Arial", 18, "bold"))

        # =========================
        # COMPANY INFO (CENTER)
        # =========================
        canvas.create_text(
            275,
            70,
            text=company,
            font=("Arial", 14, "bold"),
            width=250,
            anchor="w",
            justify="left",
        )

        canvas.create_text(
            275,
            105,
            text=address,
            font=("Arial", 8),
            width=250,
            anchor="w",
            justify="left",
        )

        canvas.create_text(
            275,
            145,
            text=desc,
            font=("Arial", 8),
            width=250,
            anchor="w",
            justify="left",
        )

        # =========================
        # INFO BOX
        # =========================
        start_x = width - 300
        start_y = 60
        row_h = 28

        rows = [
            ("Tanggal", header["trx_date"]),
            ("No SJ", header["sj_no"]),
            ("Pelanggan", header["customer"]),
        ]

        for i, (label, value) in enumerate(rows):

            y = start_y + (i * row_h)

            canvas.create_rectangle(start_x, y, start_x + 110, y + row_h)
            canvas.create_rectangle(start_x + 110, y, start_x + 260, y + row_h)

            canvas.create_text(
                start_x + 5,
                y + row_h / 2,
                text=label,
                anchor="w",
                font=("Arial", 10, "bold"),
            )

            canvas.create_text(
                start_x + 115,
                y + row_h / 2,
                text=value,
                anchor="w",
                width=140,
                font=("Arial", 10),
            )

        # =========================
        # TABEL BARANG
        # =========================
        table_x = 60
        table_y = 200
        row_h = 28

        col_no = 50
        col_name = 472
        col_qty = 100
        col_unit = 120

        total_w = col_no + col_name + col_qty + col_unit

        # header
        canvas.create_rectangle(table_x, table_y, table_x + total_w, table_y + row_h)

        canvas.create_text(
            table_x + col_no / 2, table_y + 14, text="No", font=("Arial", 10, "bold")
        )
        canvas.create_text(
            table_x + col_no + col_name / 2,
            table_y + 14,
            text="Nama Barang",
            font=("Arial", 10, "bold"),
        )
        canvas.create_text(
            table_x + col_no + col_name + col_qty / 2,
            table_y + 14,
            text="Qty",
            font=("Arial", 10, "bold"),
        )
        canvas.create_text(
            table_x + col_no + col_name + col_qty + col_unit / 2,
            table_y + 14,
            text="Satuan",
            font=("Arial", 10, "bold"),
        )

        # garis vertikal kolom
        canvas.create_line(
            table_x + col_no,
            table_y,
            table_x + col_no,
            table_y + row_h * (len(items) + 1),
        )

        canvas.create_line(
            table_x + col_no + col_name,
            table_y,
            table_x + col_no + col_name,
            table_y + row_h * (len(items) + 1),
        )

        canvas.create_line(
            table_x + col_no + col_name + col_qty,
            table_y,
            table_x + col_no + col_name + col_qty,
            table_y + row_h * (len(items) + 1),
        )

        # isi tabel
        for i, item in enumerate(items):

            y = table_y + (i + 1) * row_h

            canvas.create_rectangle(table_x, y, table_x + total_w, y + row_h)

            canvas.create_text(table_x + col_no / 2, y + 14, text=i + 1)
            canvas.create_text(
                table_x + col_no + 5,
                y + 14,
                text=item["name"],
                anchor="w",
                width=col_name - 10,
            )
            canvas.create_text(
                table_x + col_no + col_name + col_qty / 2, y + 14, text=item["qty"]
            )
            canvas.create_text(
                table_x + col_no + col_name + col_qty + col_unit / 2,
                y + 14,
                text=item["unit"],
            )

        # =========================
        # AREA BAWAH (KETERANGAN + TTD)
        # =========================

        bottom_y = table_y + (len(items) + 2) * row_h

        # -------- KETERANGAN --------
        gap = 10

        table_width = total_w

        # lebar area keterangan (sekitar 50% tabel)
        ket_x = table_x
        ket_w = int(table_width * 0.5)
        ket_h = 80

        canvas.create_rectangle(ket_x, bottom_y, ket_x + ket_w, bottom_y + ket_h)

        canvas.create_text(
            ket_x + 5,
            bottom_y + 10,
            text="Keterangan:",
            anchor="nw",
            font=("Arial", 10, "bold"),
        )

        canvas.create_text(
            ket_x + 10,
            bottom_y + 35,
            text=notes,
            anchor="nw",
            width=ket_w - 20,
            font=("Arial", 9),
        )

        # -------- TANDA TANGAN --------

        # sisa lebar untuk tanda tangan
        remaining_w = table_width - ket_w - gap

        # bagi 3 tanda tangan
        box_w = int((remaining_w - (2 * gap)) / 3)
        box_h = 80

        ttd_x = ket_x + ket_w + gap

        labels = ["Finance", "Gudang", "Penerima"]

        for i, name in enumerate(labels):

            x1 = ttd_x + (i * (box_w + gap))

            canvas.create_rectangle(x1, bottom_y, x1 + box_w, bottom_y + box_h)

            canvas.create_text(
                x1 + box_w / 2,
                bottom_y + 15,
                text=name,
                font=("Arial", 9, "bold"),
            )

    def show_invoice_window(self, header, items):

        win = tk.Toplevel(self)
        win.title("Preview Faktur")

        width = 842
        height = 595

        win.geometry(f"{width}x{height}")

        canvas = tk.Canvas(win, bg="white", width=width, height=height)
        canvas.pack(fill="both", expand=True)

        center_x = width / 2

        profile = self.db.execute(
            "SELECT company_name,address,description,logo FROM company_profile LIMIT 1"
        ).fetchone()

        company = profile["company_name"] if profile else ""
        address = profile["address"] if profile else ""
        desc = profile["description"] if profile else ""
        logo = profile["logo"] if profile else ""
        notes = header["notes"] if header["notes"] else ""

        # =========================
        # LOGO
        # =========================
        if logo:
            try:
                from PIL import Image, ImageTk

                img = Image.open(logo)
                img = img.resize((170, 130))
                photo = ImageTk.PhotoImage(img)

                canvas.logo = photo
                canvas.create_image(150, 100, image=photo)
            except:
                pass

        # =========================
        # TITLE
        # =========================
        canvas.create_text(
            center_x, 40, text="FAKTUR PENJUALAN", font=("Arial", 18, "bold")
        )

        # =========================
        # COMPANY INFO
        # =========================
        canvas.create_text(
            275, 70, text=company, font=("Arial", 14, "bold"), anchor="w", width=250
        )
        canvas.create_text(
            275, 105, text=address, font=("Arial", 8), anchor="w", width=250
        )
        canvas.create_text(
            275, 145, text=desc, font=("Arial", 8), anchor="w", width=250
        )

        # =========================
        # INFO BOX
        # =========================
        start_x = width - 300
        start_y = 60
        row_h = 28

        rows = [
            ("Tanggal", header["trx_date"]),
            ("No Faktur", header["invoice_no"]),
            ("Pelanggan", header["customer"]),
        ]

        for i, (label, value) in enumerate(rows):

            y = start_y + (i * row_h)

            canvas.create_rectangle(start_x, y, start_x + 110, y + row_h)
            canvas.create_rectangle(start_x + 110, y, start_x + 260, y + row_h)

            canvas.create_text(
                start_x + 5,
                y + row_h / 2,
                text=label,
                anchor="w",
                font=("Arial", 10, "bold"),
            )

            canvas.create_text(
                start_x + 115,
                y + row_h / 2,
                text=value,
                anchor="w",
                width=140,
                font=("Arial", 10),
            )

        # =========================
        # TABEL BARANG
        # =========================
        table_x = 40
        table_y = 200
        row_h = 28

        col_no = 40
        col_name = 270
        col_qty = 60
        col_unit = 80
        col_price = 110
        col_disc = 90
        col_total = 120

        total_w = (
            col_no + col_name + col_qty + col_unit + col_price + col_disc + col_total
        )

        # HEADER
        canvas.create_rectangle(table_x, table_y, table_x + total_w, table_y + row_h)

        headers = [
            "No",
            "Nama Barang",
            "Qty",
            "Satuan",
            "Harga",
            "Diskon/QTY",
            "Total Harga",
        ]
        cols = [col_no, col_name, col_qty, col_unit, col_price, col_disc, col_total]

        x = table_x

        for i, h in enumerate(headers):

            canvas.create_text(
                x + cols[i] / 2, table_y + 14, text=h, font=("Arial", 10, "bold")
            )

            if i > 0:
                canvas.create_line(x, table_y, x, table_y + row_h * (len(items) + 1))

            x += cols[i]

        # isi tabel
        subtotal = 0
        total_discount = 0

        for i, item in enumerate(items):

            y = table_y + (i + 1) * row_h

            canvas.create_rectangle(table_x, y, table_x + total_w, y + row_h)

            subtotal += item["price"] * item["qty"]
            total_discount += item["discount"] * item["qty"]

            canvas.create_text(table_x + col_no / 2, y + 14, text=i + 1)

            canvas.create_text(
                table_x + col_no + 5,
                y + 14,
                text=item["name"],
                anchor="w",
                width=col_name - 10,
            )

            canvas.create_text(
                table_x + col_no + col_name + col_qty / 2, y + 14, text=item["qty"]
            )

            canvas.create_text(
                table_x + col_no + col_name + col_qty + col_unit / 2,
                y + 14,
                text=item["unit"],
            )

            canvas.create_text(
                table_x + col_no + col_name + col_qty + col_unit + col_price / 2,
                y + 14,
                text=format_number(item["price"]),
            )

            canvas.create_text(
                table_x
                + col_no
                + col_name
                + col_qty
                + col_unit
                + col_price
                + col_disc / 2,
                y + 14,
                text=format_number(item["discount"]),
            )

            canvas.create_text(
                table_x
                + col_no
                + col_name
                + col_qty
                + col_unit
                + col_price
                + col_disc
                + col_total / 2,
                y + 14,
                text=format_number(item["total"]),
            )

        # =========================
        # FOOTER
        # =========================

        bottom_y = table_y + (len(items) + 2) * row_h

        footer_w = total_w

        gap = 10  # jarak antar box

        sign_w = 120
        total_w_box = 170

        ket_w = footer_w - (total_w_box + sign_w * 2 + gap * 3)

        ket_x = table_x
        ket_h = 55

        # ----- KETERANGAN -----
        canvas.create_rectangle(ket_x, bottom_y, ket_x + ket_w, bottom_y + ket_h)

        canvas.create_text(
            ket_x + 5,
            bottom_y + 8,
            text="Keterangan:",
            anchor="nw",
            font=("Arial", 9, "bold"),
        )

        canvas.create_text(
            ket_x + 8,
            bottom_y + 25,
            text=notes,
            anchor="nw",
            width=ket_w - 15,
            font=("Arial", 8),
        )

        # ----- TOTAL BOX -----
        total_x = ket_x + ket_w + gap

        canvas.create_rectangle(
            total_x, bottom_y, total_x + total_w_box, bottom_y + ket_h
        )

        grand_total = subtotal - total_discount

        lines = [
            ("Sub Total", subtotal),
            ("Total Diskon", total_discount),
            ("Grand Total", grand_total),
        ]

        row_h_total = ket_h / len(lines)

        for i, (label, val) in enumerate(lines):

            y = bottom_y + (i * row_h_total)

            # garis pemisah horizontal
            canvas.create_line(
                total_x,
                y,
                total_x + total_w_box,
                y,
            )

            canvas.create_text(
                total_x + 8,
                y + row_h_total / 2,
                text=label,
                anchor="w",
                font=("Arial", 9),
            )

            canvas.create_text(
                total_x + total_w_box - 8,
                y + row_h_total / 2,
                text=format_number(val),
                anchor="e",
                font=("Arial", 9, "bold"),
            )

        # garis bawah terakhir
        canvas.create_line(
            total_x,
            bottom_y + ket_h,
            total_x + total_w_box,
            bottom_y + ket_h,
        )

        # ----- TANDA TANGAN -----
        ttd_x = total_x + total_w_box + gap

        box_w = sign_w
        box_h = ket_h

        labels = ["Penjual", "Penerima"]

        for i, name in enumerate(labels):

            x = ttd_x + (i * (box_w + gap))

            canvas.create_rectangle(x, bottom_y, x + box_w, bottom_y + box_h)

            canvas.create_text(
                x + box_w / 2,
                bottom_y + 12,
                text=name,
                font=("Arial", 9, "bold"),
            )
