import tkinter as tk
from tkinter import ttk, messagebox

from utils import current_date
from utils import treeview_sort_column


class InventoryView(tk.Frame):

    def __init__(self, parent, db, service, refresh_callback=None):

        super().__init__(parent, bg="#f9fafb")

        self.db = db
        self.service = service
        self.refresh_callback = refresh_callback

        self.build_ui()

    def build_ui(self):

        tk.Label(
            self,
            text="Persediaan / Gudang",
            font=("Segoe UI", 16, "bold"),
            bg="#f9fafb",
        ).pack(anchor="w", pady=(0, 10))

        tk.Button(
            self, text="🔄 Refresh", command=self.load_data, bg="#2563eb", fg="white"
        ).pack(anchor="e", pady=(0, 10))

        # ==============================
        # FORM PENYESUAIAN STOK
        # ==============================

        form = tk.Frame(self, bg="white", bd=1, relief="solid")
        form.pack(fill="x", pady=5)

        products = self.db.execute(
            "SELECT id, name FROM products ORDER BY name"
        ).fetchall()

        self.product_map = {r["name"]: r["id"] for r in products}

        tk.Label(form, text="Tanggal", bg="white").grid(
            row=0, column=0, padx=10, pady=(10, 2), sticky="w"
        )
        tk.Label(form, text="Produk", bg="white").grid(
            row=0, column=1, padx=10, pady=(10, 2), sticky="w"
        )
        tk.Label(form, text="Jenis", bg="white").grid(
            row=0, column=2, padx=10, pady=(10, 2), sticky="w"
        )
        tk.Label(form, text="Qty", bg="white").grid(
            row=0, column=3, padx=10, pady=(10, 2), sticky="w"
        )

        from datepicker import DatePicker

        self.date_entry = DatePicker(form)
        self.date_entry.set(current_date())

        self.prod_combo = ttk.Combobox(
            form, values=list(self.product_map.keys()), state="readonly"
        )

        self.type_combo = ttk.Combobox(
            form, values=["ADJUST_IN", "ADJUST_OUT"], state="readonly"
        )

        self.qty_entry = tk.Entry(form)

        self.date_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="we")
        self.prod_combo.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="we")
        self.type_combo.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="we")
        self.qty_entry.grid(row=1, column=3, padx=10, pady=(0, 10), sticky="we")

        for i in range(4):
            form.grid_columnconfigure(i, weight=1)

        tk.Button(
            form,
            text="Simpan Penyesuaian",
            command=self.adjust_stock,
            bg="#2563eb",
            fg="white",
        ).grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")

        # ==============================
        # TABEL STOK
        # ==============================

        self.tree_stock = ttk.Treeview(
            self, columns=("sku", "name", "stock", "min"), show="headings", height=8
        )

        headers = [
            ("sku", "SKU", 120, False),
            ("name", "Nama Produk", 220, False),
            ("stock", "Stok", 120, True),
            ("min", "Min Stok", 120, True),
        ]

        for c, h, w, num in headers:
            self.tree_stock.heading(
                c,
                text=h,
                command=lambda col=c, numeric=num: treeview_sort_column(
                    self.tree_stock, col, False, numeric
                ),
            )
            self.tree_stock.column(c, width=w)

        self.tree_stock.pack(fill="x", pady=10)

        # style warning
        self.tree_stock.tag_configure("lowstock", foreground="red")

        # ==============================
        # TABEL MUTASI STOK
        # ==============================

        self.tree_move = ttk.Treeview(
            self,
            columns=("date", "product", "type", "in", "out", "ref", "notes"),
            show="headings",
            height=12,
        )

        headers = [
            ("date", "Tanggal", 100, False),
            ("product", "Produk", 200, False),
            ("type", "Jenis", 120, False),
            ("in", "Masuk", 80, True),
            ("out", "Keluar", 80, True),
            ("ref", "Ref", 120, False),
            ("notes", "Catatan", 260, False),
        ]

        for c, h, w, num in headers:
            self.tree_move.heading(
                c,
                text=h,
                command=lambda col=c, numeric=num: treeview_sort_column(
                    self.tree_move, col, False, numeric
                ),
            )
            self.tree_move.column(c, width=w)

        self.tree_move.pack(fill="both", expand=True, pady=10)

        self.load_data()

    # =================================
    # LOAD DATA
    # =================================

    def load_data(self):

        for item in self.tree_stock.get_children():
            self.tree_stock.delete(item)

        for item in self.tree_move.get_children():
            self.tree_move.delete(item)

        rows = self.db.execute(
            """
        SELECT sku, name, stock, min_stock
        FROM products
        ORDER BY name
        """
        ).fetchall()

        for r in rows:

            tag = ""

            if r["stock"] < r["min_stock"]:
                tag = "lowstock"

            self.tree_stock.insert(
                "",
                "end",
                values=(r["sku"], r["name"], r["stock"], r["min_stock"]),
                tags=(tag,),
            )

        moves = self.db.execute(
            """
        SELECT
        im.trx_date,
        p.name product,
        im.movement_type,
        im.qty_in,
        im.qty_out,
        im.ref_no,
        im.notes
        FROM inventory_movements im
        JOIN products p ON p.id=im.product_id
        ORDER BY im.id DESC
        """
        ).fetchall()

        for m in moves:

            self.tree_move.insert(
                "",
                "end",
                values=(
                    m["trx_date"],
                    m["product"],
                    m["movement_type"],
                    m["qty_in"],
                    m["qty_out"],
                    m["ref_no"],
                    m["notes"],
                ),
            )

    # =================================
    # ADJUST STOK
    # =================================

    def adjust_stock(self):

        try:

            trx_date = self.date_entry.get().strip()
            prod = self.prod_combo.get().strip()
            mov_type = self.type_combo.get().strip()
            qty = float(self.qty_entry.get() or 0)

            if not prod or not mov_type or qty <= 0:
                messagebox.showerror("Error", "Lengkapi data penyesuaian.")
                return

            self.service.adjust_stock(trx_date, self.product_map[prod], mov_type, qty)

            self.load_data()

            if self.refresh_callback:
                self.refresh_callback()

            messagebox.showinfo("Sukses", "Penyesuaian stok berhasil.")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
