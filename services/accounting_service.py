from utils.date_utils import today_str


class AccountingService:

    def __init__(self, db):
        self.db = db

    # =====================================================
    # INVENTORY MOVEMENT HELPER
    # =====================================================

    def add_inventory_movement(
        self, trx_date, product_id, movement_type, qty_in, qty_out, ref_no, notes
    ):

        self.db.execute(
            """
            INSERT INTO inventory_movements
            (trx_date,product_id,movement_type,qty_in,qty_out,ref_no,notes)
            VALUES (?,?,?,?,?,?,?)
            """,
            (trx_date, product_id, movement_type, qty_in, qty_out, ref_no, notes),
            commit=True,
        )

        # hitung ulang stok
        self.db.update_product_stock(product_id)

    # =====================================================
    # HITUNG MOVING AVERAGE
    # =====================================================

    def calculate_moving_average(self, product_id, qty_in, price):

        product = self.db.execute(
            "SELECT stock, cost_price FROM products WHERE id=?", (product_id,)
        ).fetchone()

        old_stock = product["stock"] or 0
        old_cost = product["cost_price"] or 0

        if old_stock <= 0:
            return price

        new_avg = ((old_stock * old_cost) + (qty_in * price)) / (old_stock + qty_in)

        return new_avg

    # =====================================================
    # UTILITAS
    # =====================================================

    def delete_journal_by_ref(self, ref_no):

        journal = self.db.execute(
            "SELECT id FROM journal_entries WHERE ref_no=?", (ref_no,)
        ).fetchone()

        if journal:

            self.db.execute(
                "DELETE FROM journal_details WHERE journal_id=?",
                (journal["id"],),
                commit=True,
            )

            self.db.execute(
                "DELETE FROM journal_entries WHERE id=?", (journal["id"],), commit=True
            )

    # =====================================================
    # PENJUALAN
    # =====================================================

    def create_sales_invoice(
        self, trx_date, customer_id, product_id, qty, unit_price=None, discount=0
    ):

        product = self.db.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()

        if not product:
            raise ValueError("Produk tidak ditemukan.")

        if qty <= 0:
            raise ValueError("Qty harus lebih dari 0.")

        if product["stock"] < qty:
            raise ValueError(f"Stok tidak cukup. Stok tersedia: {product['stock']}")

        if unit_price is None:
            unit_price = product["sell_price"]

        if unit_price < 0 or discount < 0:
            raise ValueError("Harga dan diskon tidak boleh negatif.")

        # ===============================
        # PERHITUNGAN
        # ===============================

        subtotal = qty * unit_price
        total_discount = discount * qty
        total = subtotal - total_discount

        if total < 0:
            raise ValueError("Diskon terlalu besar.")

        invoice_no = self.db.get_next_number("SI", trx_date)

        cur = self.db.execute(
            """
        INSERT INTO sales_invoices
        (invoice_no,trx_date,customer_id,subtotal,discount,tax,total,paid,status,notes)
        VALUES (?,?,?,?,?,0,?,0,'UNPAID','')
        """,
            (invoice_no, trx_date, customer_id, subtotal, total_discount, total),
            commit=True,
        )

        sales_id = cur.lastrowid

        self.db.execute(
            """
        INSERT INTO sales_invoice_items
        (sales_invoice_id,product_id,qty,unit_price,price,discount,total)
        VALUES (?,?,?,?,?,?,?)
        """,
            (sales_id, product_id, qty, unit_price, unit_price, total_discount, total),
            commit=True,
        )

        # ===============================
        # INVENTORY
        # ===============================

        self.add_inventory_movement(
            trx_date, product_id, "SALE", 0, qty, invoice_no, f"Penjualan {invoice_no}"
        )

        # ===============================
        # HPP
        # ===============================

        hpp_total = qty * product["cost_price"]

        # ===============================
        # JURNAL
        # ===============================

        self.db.add_journal(
            trx_date,
            invoice_no,
            f"Penjualan {invoice_no}",
            [
                ("1101", total, 0),
                ("4001", 0, total),
                ("5001", hpp_total, 0),
                ("1201", 0, hpp_total),
            ],
        )

        return invoice_no

    # =====================================================
    # UPDATE PENJUALAN (EDIT FAKTUR)
    # =====================================================

    def update_sales_invoice_multi(
        self, invoice_no, trx_date, customer_id, items, notes=""
    ):

        inv = self.db.execute(
            "SELECT id FROM sales_invoices WHERE invoice_no=?", (invoice_no,)
        ).fetchone()

        if not inv:
            raise ValueError("Invoice tidak ditemukan")

        sales_id = inv["id"]

        # ===============================
        # KEMBALIKAN STOK LAMA
        # ===============================

        old_items = self.db.execute(
            """
            SELECT product_id, qty
            FROM sales_invoice_items
            WHERE sales_invoice_id=?
            """,
            (sales_id,),
        ).fetchall()

        for r in old_items:

            self.db.execute(
                """
                INSERT INTO inventory_movements
                (trx_date,product_id,movement_type,qty_in,qty_out,ref_no,notes)
                VALUES (?,?, 'SALE-EDIT',?,0,?,?)
                """,
                (
                    trx_date,
                    r["product_id"],
                    r["qty"],
                    invoice_no,
                    f"Rollback {invoice_no}",
                ),
                commit=True,
            )

            self.db.update_product_stock(r["product_id"])

        # ===============================
        # HAPUS ITEM LAMA
        # ===============================

        self.db.execute(
            "DELETE FROM sales_invoice_items WHERE sales_invoice_id=?",
            (sales_id,),
            commit=True,
        )

        # hapus movement lama
        self.db.execute(
            "DELETE FROM inventory_movements WHERE ref_no=?",
            (invoice_no,),
            commit=True,
        )

        subtotal = 0
        total_discount = 0
        total_hpp = 0

        # ===============================
        # INSERT ITEM BARU
        # ===============================

        for item in items:

            product = self.db.execute(
                "SELECT * FROM products WHERE id=?", (item["product_id"],)
            ).fetchone()

            if not product:
                raise ValueError("Produk tidak ditemukan")

            qty = item["qty"]
            price = item["price"]
            disc = item["discount"]

            if product["stock"] < qty:
                raise ValueError(
                    f"Stok tidak cukup untuk {product['name']} "
                    f"(Stok tersedia {product['stock']})"
                )

            sub = qty * price
            disc_total = disc * qty
            total = sub - disc_total

            subtotal += sub
            total_discount += disc_total

            # simpan item
            self.db.execute(
                """
                INSERT INTO sales_invoice_items
                (sales_invoice_id,product_id,qty,unit_price,price,discount,total)
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    sales_id,
                    item["product_id"],
                    qty,
                    price,
                    price,
                    disc_total,
                    total,
                ),
                commit=True,
            )

            # inventory out
            self.db.execute(
                """
                INSERT INTO inventory_movements
                (trx_date,product_id,movement_type,qty_in,qty_out,ref_no,notes)
                VALUES (?,?, 'SALE',0,?,?,?)
                """,
                (
                    trx_date,
                    item["product_id"],
                    qty,
                    invoice_no,
                    f"Penjualan {invoice_no}",
                ),
                commit=True,
            )

            self.db.update_product_stock(item["product_id"])

            total_hpp += qty * product["cost_price"]

        grand_total = subtotal - total_discount

        # ===============================
        # UPDATE HEADER
        # ===============================

        self.db.execute(
            """
            UPDATE sales_invoices
            SET trx_date=?,customer_id=?,subtotal=?,discount=?,total=?,notes=?
            WHERE id=?
            """,
            (
                trx_date,
                customer_id,
                subtotal,
                total_discount,
                grand_total,
                notes,
                sales_id,
            ),
            commit=True,
        )

        return invoice_no

    # =====================================================
    # DELETE PENJUALAN
    # =====================================================

    def delete_sales_invoice(self, invoice_no):

        inv = self.db.execute(
            "SELECT * FROM sales_invoices WHERE invoice_no=?", (invoice_no,)
        ).fetchone()

        if not inv:
            raise ValueError("Faktur tidak ditemukan.")

        items = self.db.execute(
            "SELECT product_id FROM sales_invoice_items WHERE sales_invoice_id=?",
            (inv["id"],),
        ).fetchall()

        # hapus jurnal
        self.delete_journal_by_ref(invoice_no)

        # hapus movement lama
        self.db.execute(
            "DELETE FROM inventory_movements WHERE ref_no=? AND movement_type='SALE'",
            (invoice_no,),
            commit=True,
        )

        # hapus item
        self.db.execute(
            "DELETE FROM sales_invoice_items WHERE sales_invoice_id=?",
            (inv["id"],),
            commit=True,
        )

        # hapus invoice
        self.db.execute(
            "DELETE FROM sales_invoices WHERE id=?", (inv["id"],), commit=True
        )

        for item in items:
            self.db.update_product_stock(item["product_id"])

    # =====================================================
    # PEMBAYARAN PENJUALAN
    # =====================================================

    def receive_sales_payment(
        self, invoice_no, amount, account_name, account_code, method
    ):

        inv = self.db.execute(
            "SELECT * FROM sales_invoices WHERE invoice_no=?", (invoice_no,)
        ).fetchone()

        if not inv:
            raise ValueError("Invoice tidak ditemukan.")

        # ===============================
        # HITUNG RETUR
        # ===============================

        ret = self.db.execute(
            """
            SELECT COALESCE(SUM(total),0) t
            FROM sales_returns
            WHERE invoice_no=?
            """,
            (invoice_no,),
        ).fetchone()

        return_total = ret["t"]

        net_total = inv["total"] - return_total

        remaining = net_total - inv["paid"]

        if amount > remaining:
            raise ValueError("Pembayaran melebihi sisa tagihan.")

        new_paid = inv["paid"] + amount

        status = "PAID" if new_paid >= net_total else "PARTIAL"

        self.db.execute(
            "UPDATE sales_invoices SET paid=?,status=? WHERE id=?",
            (new_paid, status, inv["id"]),
            commit=True,
        )

        ref = self.db.get_next_number("RCV", today_str())

        # simpan kas bank
        self.db.execute(
            """
        INSERT INTO cash_bank_transactions
        (trx_date,trx_type,account_name,account_code,amount,discount,ref_no,notes)
        VALUES (?, 'IN', ?, ?, ?,0,?,?)
        """,
            (
                today_str(),
                account_name,
                account_code,
                amount,
                ref,
                f"{method} {invoice_no}",
            ),
            commit=True,
        )

        # jurnal
        self.db.add_journal(
            today_str(),
            ref,
            f"Pembayaran {invoice_no}",
            [(account_code, amount, 0), ("1101", 0, amount)],
        )

    # =====================================================
    # DELETE CASHBANK
    # =====================================================

    def delete_cashbank(self, trx_id):

        row = self.db.execute(
            "SELECT ref_no FROM cash_bank_transactions WHERE id=?", (trx_id,)
        ).fetchone()

        if row:
            self.delete_journal_by_ref(row["ref_no"])

        self.db.execute(
            "DELETE FROM cash_bank_transactions WHERE id=?", (trx_id,), commit=True
        )

    def save_cashbank(
        self, trx_date, trx_type, account_name, account_code, amount, discount, notes
    ):

        if amount <= 0:
            raise ValueError("Jumlah harus lebih dari 0")

        ref = self.db.get_next_number("CB", trx_date)

        self.db.execute(
            """
        INSERT INTO cash_bank_transactions
        (trx_date,trx_type,account_name,account_code,amount,discount,ref_no,notes)
        VALUES (?,?,?,?,?,?,?,?)
        """,
            (
                trx_date,
                trx_type,
                account_name,
                account_code,
                amount,
                discount,
                ref,
                notes,
            ),
            commit=True,
        )

        net = amount - discount

        # =========================
        # JURNAL
        # =========================

        if trx_type == "IN":

            self.db.add_journal(
                trx_date,
                ref,
                notes or "Kas/Bank Masuk",
                [(account_code, net, 0), ("3001", 0, net)],
            )

        elif trx_type == "OUT":

            self.db.add_journal(
                trx_date,
                ref,
                notes or "Kas/Bank Keluar",
                [("6001", net, 0), (account_code, 0, net)],
            )

    # =====================================================
    # UPDATE CASH BANK
    # =====================================================

    def update_cashbank(
        self,
        trx_id,
        trx_date,
        trx_type,
        account_name,
        account_code,
        amount,
        discount,
        notes,
    ):

        row = self.db.execute(
            "SELECT ref_no FROM cash_bank_transactions WHERE id=?", (trx_id,)
        ).fetchone()

        if not row:
            raise ValueError("Transaksi tidak ditemukan")

        ref = row["ref_no"]

        # hapus jurnal lama
        self.delete_journal_by_ref(ref)

        # update transaksi
        self.db.execute(
            """
        UPDATE cash_bank_transactions
        SET trx_date=?,trx_type=?,account_name=?,account_code=?,
            amount=?,discount=?,notes=?
        WHERE id=?
        """,
            (
                trx_date,
                trx_type,
                account_name,
                account_code,
                amount,
                discount,
                notes,
                trx_id,
            ),
            commit=True,
        )

        net = amount - discount

        # buat jurnal baru
        if trx_type == "IN":

            self.db.add_journal(
                trx_date,
                ref,
                notes or "Kas Masuk",
                [("1001", net, 0), (account_code, 0, net)],
            )

        elif trx_type == "OUT":

            self.db.add_journal(
                trx_date,
                ref,
                notes or "Kas Keluar",
                [(account_code, net, 0), ("1001", 0, net)],
            )

    # =====================================================
    # PEMBELIAN
    # =====================================================

    def create_purchase_invoice(
        self, trx_date, supplier_id, product_id, qty, price=None, discount=0
    ):

        product = self.db.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()

        if not product:
            raise ValueError("Produk tidak ditemukan.")

        if qty <= 0:
            raise ValueError("Qty harus lebih dari 0.")

        if price is None:
            price = product["cost_price"]

        if price < 0 or discount < 0:
            raise ValueError("Harga dan diskon tidak boleh negatif.")

        # ===============================
        # PERHITUNGAN
        # ===============================

        subtotal = qty * price
        total_discount = discount * qty
        total = subtotal - total_discount

        if total < 0:
            raise ValueError("Diskon terlalu besar.")

        invoice_no = self.db.get_next_number("PI", trx_date)

        cur = self.db.execute(
            """
        INSERT INTO purchase_invoices
        (invoice_no,trx_date,supplier_id,subtotal,discount,tax,total,paid,status,notes)
        VALUES (?,?,?,?,?,0,?,0,'UNPAID','')
        """,
            (invoice_no, trx_date, supplier_id, subtotal, total_discount, total),
            commit=True,
        )

        purchase_id = cur.lastrowid

        self.db.execute(
            """
        INSERT INTO purchase_invoice_items
        (purchase_invoice_id,product_id,qty,price,total)
        VALUES (?,?,?,?,?)
        """,
            (purchase_id, product_id, qty, price, subtotal),
            commit=True,
        )

        # ===============================
        # UPDATE MOVING AVERAGE COST
        # ===============================

        net_price = price - discount

        new_avg = self.calculate_moving_average(product_id, qty, net_price)

        self.db.execute(
            "UPDATE products SET cost_price=? WHERE id=?",
            (new_avg, product_id),
            commit=True,
        )

        # ===============================
        # INVENTORY MASUK
        # ===============================

        self.db.execute(
            """
        INSERT INTO inventory_movements
        (trx_date,product_id,movement_type,qty_in,qty_out,ref_no,notes)
        VALUES (?,?, 'PURCHASE',?,0,?,?)
        """,
            (trx_date, product_id, qty, invoice_no, f"Pembelian {invoice_no}"),
            commit=True,
        )

        self.db.update_product_stock(product_id)

        # ===============================
        # JURNAL PEMBELIAN
        # ===============================

        self.db.add_journal(
            trx_date,
            invoice_no,
            f"Pembelian {invoice_no}",
            [("1201", total, 0), ("2101", 0, total)],
        )

        return invoice_no

    # =====================================================
    # UPDATE PEMBELIAN
    # =====================================================

    def update_purchase_invoice(
        self, invoice_no, trx_date, supplier_id, product_id, qty, price, discount
    ):

        inv = self.db.execute(
            "SELECT * FROM purchase_invoices WHERE invoice_no=?", (invoice_no,)
        ).fetchone()

        if not inv:
            raise ValueError("Faktur tidak ditemukan.")

        item = self.db.execute(
            "SELECT * FROM purchase_invoice_items WHERE purchase_invoice_id=?",
            (inv["id"],),
        ).fetchone()

        old_product = item["product_id"]
        old_qty = item["qty"]

        # ===============================
        # HAPUS DATA LAMA
        # ===============================

        self.delete_journal_by_ref(invoice_no)

        self.db.execute(
            "DELETE FROM inventory_movements WHERE ref_no=? AND movement_type='PURCHASE'",
            (invoice_no,),
            commit=True,
        )

        # ===============================
        # PERHITUNGAN BARU
        # ===============================

        subtotal = qty * price
        total_discount = discount * qty
        total = subtotal - total_discount

        if total < 0:
            raise ValueError("Diskon terlalu besar.")

        # ===============================
        # UPDATE MOVING AVERAGE COST
        # ===============================

        new_avg = self.calculate_moving_average(product_id, qty, price)

        self.db.execute(
            "UPDATE products SET cost_price=? WHERE id=?",
            (new_avg, product_id),
            commit=True,
        )

        # ===============================
        # UPDATE INVOICE
        # ===============================

        self.db.execute(
            """
        UPDATE purchase_invoices
        SET trx_date=?,supplier_id=?,subtotal=?,discount=?,total=?
        WHERE invoice_no=?
        """,
            (trx_date, supplier_id, subtotal, total_discount, total, invoice_no),
            commit=True,
        )

        self.db.execute(
            """
        UPDATE purchase_invoice_items
        SET product_id=?,qty=?,price=?,total=?
        WHERE purchase_invoice_id=?
        """,
            (product_id, qty, price, subtotal, inv["id"]),
            commit=True,
        )

        # ===============================
        # INVENTORY MASUK
        # ===============================

        self.db.execute(
            """
        INSERT INTO inventory_movements
        (trx_date,product_id,movement_type,qty_in,qty_out,ref_no,notes)
        VALUES (?,?, 'PURCHASE',?,0,?,?)
        """,
            (trx_date, product_id, qty, invoice_no, f"Pembelian {invoice_no}"),
            commit=True,
        )

        self.db.update_product_stock(product_id)

        if old_product != product_id:
            self.db.update_product_stock(old_product)

        # ===============================
        # JURNAL BARU
        # ===============================

        self.db.add_journal(
            trx_date,
            invoice_no,
            f"Pembelian {invoice_no}",
            [("1201", total, 0), ("2101", 0, total)],
        )

    # =====================================================
    # DELETE PEMBELIAN
    # =====================================================

    def delete_purchase_invoice(self, invoice_no):

        inv = self.db.execute(
            "SELECT * FROM purchase_invoices WHERE invoice_no=?", (invoice_no,)
        ).fetchone()

        if not inv:
            raise ValueError("Faktur tidak ditemukan.")

        items = self.db.execute(
            "SELECT product_id FROM purchase_invoice_items WHERE purchase_invoice_id=?",
            (inv["id"],),
        ).fetchall()

        # hapus jurnal
        self.delete_journal_by_ref(invoice_no)

        # hapus stok
        self.db.execute(
            "DELETE FROM inventory_movements WHERE ref_no=? AND movement_type='PURCHASE'",
            (invoice_no,),
            commit=True,
        )

        # hapus item
        self.db.execute(
            "DELETE FROM purchase_invoice_items WHERE purchase_invoice_id=?",
            (inv["id"],),
            commit=True,
        )

        # hapus invoice
        self.db.execute(
            "DELETE FROM purchase_invoices WHERE id=?", (inv["id"],), commit=True
        )

        for item in items:
            self.db.update_product_stock(item["product_id"])

    # =====================================================
    # BAYAR PEMBELIAN
    # =====================================================

    def pay_purchase_invoice(
        self, invoice_no, amount, account_name, account_code, method
    ):

        inv = self.db.execute(
            "SELECT * FROM purchase_invoices WHERE invoice_no=?", (invoice_no,)
        ).fetchone()

        if not inv:
            raise ValueError("Invoice tidak ditemukan.")

        remaining = inv["total"] - inv["paid"]

        if amount > remaining:
            raise ValueError("Pembayaran melebihi sisa tagihan.")

        new_paid = inv["paid"] + amount
        status = "PAID" if new_paid >= inv["total"] else "PARTIAL"

        self.db.execute(
            "UPDATE purchase_invoices SET paid=?,status=? WHERE id=?",
            (new_paid, status, inv["id"]),
            commit=True,
        )

        ref = self.db.get_next_number("PAY", today_str())

        # simpan kas / bank
        self.db.execute(
            """
        INSERT INTO cash_bank_transactions
        (trx_date,trx_type,account_name,account_code,amount,discount,ref_no,notes)
        VALUES (?, 'OUT', ?, ?, ?,0,?,?)
        """,
            (
                today_str(),
                account_name,
                account_code,
                amount,
                ref,
                f"{method} {invoice_no}",
            ),
            commit=True,
        )

        # jurnal otomatis
        self.db.add_journal(
            today_str(),
            ref,
            f"Pembayaran {invoice_no}",
            [("2101", amount, 0), (account_code, 0, amount)],
        )

    # =====================================================
    # PENJUALAN MULTI ITEM
    # =====================================================

    def create_sales_invoice_multi(self, trx_date, customer_id, items, notes=""):

        if not items:
            raise ValueError("Tidak ada item.")

        invoice_no = self.db.get_next_number("SI", trx_date)
        sj_no = self.db.get_next_number("DO", trx_date)

        subtotal = 0
        total_discount = 0

        # ===============================
        # CEK STOK DULU
        # ===============================

        for item in items:

            product = self.db.execute(
                "SELECT name,stock FROM products WHERE id=?", (item["product_id"],)
            ).fetchone()

            if not product:
                raise ValueError("Produk tidak ditemukan")

            if product["stock"] < item["qty"]:
                raise ValueError(
                    f"Stok tidak cukup untuk {product['name']} "
                    f"(Stok tersedia {product['stock']})"
                )

        # ===============================
        # CREATE INVOICE HEADER
        # ===============================

        cur = self.db.execute(
            """
        INSERT INTO sales_invoices
        (invoice_no,sj_no,trx_date,customer_id,subtotal,discount,tax,total,paid,status,notes)
        VALUES (?,?,?,?,?,?,0,?,0,'UNPAID',?)
        """,
            (invoice_no, sj_no, trx_date, customer_id, 0, 0, 0, notes),
            commit=True,
        )

        sales_id = cur.lastrowid

        # ===============================
        # LOOP ITEMS
        # ===============================

        total_hpp = 0

        for item in items:

            product = self.db.execute(
                "SELECT * FROM products WHERE id=?", (item["product_id"],)
            ).fetchone()

            if not product:
                raise ValueError("Produk tidak ditemukan")

            qty = item["qty"]
            price = item["price"]
            disc = item["discount"]

            stock = product["stock"]

            # =========================
            # CEK STOK
            # =========================
            if stock < qty:
                raise ValueError(
                    f"Stok tidak cukup untuk {product['name']} "
                    f"(Stok tersedia: {stock})"
                )

            sub = qty * price
            disc_total = disc * qty
            total = sub - disc_total

            subtotal += sub
            total_discount += disc_total

            # ===============================
            # INSERT ITEM
            # ===============================

            self.db.execute(
                """
            INSERT INTO sales_invoice_items
            (sales_invoice_id,product_id,qty,unit_price,price,discount,total)
            VALUES (?,?,?,?,?,?,?)
            """,
                (sales_id, item["product_id"], qty, price, price, disc_total, total),
                commit=True,
            )

            # ===============================
            # INVENTORY OUT
            # ===============================

            self.db.execute(
                """
            INSERT INTO inventory_movements
            (trx_date,product_id,movement_type,qty_in,qty_out,ref_no,notes)
            VALUES (?,?, 'SALE',0,?,?,?)
            """,
                (
                    trx_date,
                    item["product_id"],
                    qty,
                    invoice_no,
                    f"Penjualan {invoice_no}",
                ),
                commit=True,
            )

            self.db.update_product_stock(item["product_id"])

            # ===============================
            # HPP
            # ===============================

            total_hpp += qty * product["cost_price"]

        grand_total = subtotal - total_discount

        # ===============================
        # UPDATE HEADER TOTAL
        # ===============================

        self.db.execute(
            """
        UPDATE sales_invoices
        SET subtotal=?,discount=?,total=?
        WHERE id=?
        """,
            (subtotal, total_discount, grand_total, sales_id),
            commit=True,
        )

        # ===============================
        # JURNAL
        # ===============================

        self.db.add_journal(
            trx_date,
            invoice_no,
            f"Penjualan {invoice_no}",
            [
                ("1101", grand_total, 0),
                ("4001", 0, grand_total),
                ("5001", total_hpp, 0),
                ("1201", 0, total_hpp),
            ],
        )

        return invoice_no

    # =====================================================
    # PEMBELIAN MULTI ITEM
    # =====================================================

    def create_purchase_invoice_multi(self, trx_date, supplier_id, items, notes=""):

        if not items:
            raise ValueError("Tidak ada item.")

        invoice_no = self.db.get_next_number("PI", trx_date)

        subtotal = 0
        total_discount = 0
        grand_total = 0

        for item in items:
            qty = item["qty"]
            price = item["price"]
            discount = item["discount"]

            total = (qty * price) - (discount * qty)

            grand_total += total

        # ===============================
        # CREATE HEADER
        # ===============================

        cur = self.db.execute(
            """
        INSERT INTO purchase_invoices
        (invoice_no,trx_date,supplier_id,total,status,paid,notes)
        VALUES(?,?,?,?,?,?,?)
        """,
            (
            invoice_no,
            trx_date,
            supplier_id,
            grand_total,
            "UNPAID",
            0,
            notes
        ),
            commit=True,
        )

        purchase_id = cur.lastrowid

        # ===============================
        # LOOP ITEMS
        # ===============================

        for item in items:

            product = self.db.execute(
                "SELECT * FROM products WHERE id=?", (item["product_id"],)
            ).fetchone()

            if not product:
                raise ValueError("Produk tidak ditemukan")

            qty = item["qty"]
            price = item["price"]
            disc = item["discount"]

            sub = qty * price
            disc_total = disc * qty
            total = sub - disc_total

            subtotal += sub
            total_discount += disc_total

            # ===============================
            # INSERT ITEM
            # ===============================

            self.db.execute(
                """
            INSERT INTO purchase_invoice_items
            (purchase_invoice_id,product_id,qty,price,total)
            VALUES (?,?,?,?,?)
            """,
                (purchase_id, item["product_id"], qty, price, sub),
                commit=True,
            )

            # ===============================
            # MOVING AVERAGE COST
            # ===============================

            net_price = price - disc

            new_avg = self.calculate_moving_average(item["product_id"], qty, net_price)

            self.db.execute(
                "UPDATE products SET cost_price=? WHERE id=?",
                (new_avg, item["product_id"]),
                commit=True,
            )

            # ===============================
            # INVENTORY IN
            # ===============================

            self.db.execute(
                """
            INSERT INTO inventory_movements
            (trx_date,product_id,movement_type,qty_in,qty_out,ref_no,notes)
            VALUES (?,?, 'PURCHASE',?,0,?,?)
            """,
                (
                    trx_date,
                    item["product_id"],
                    qty,
                    invoice_no,
                    f"Pembelian {invoice_no}",
                ),
                commit=True,
            )

            self.db.update_product_stock(item["product_id"])

        grand_total = subtotal - total_discount

        # ===============================
        # UPDATE HEADER
        # ===============================

        self.db.execute(
            """
        UPDATE purchase_invoices
        SET subtotal=?,discount=?,total=?
        WHERE id=?
        """,
            (subtotal, total_discount, grand_total, purchase_id),
            commit=True,
        )

        # ===============================
        # JURNAL
        # ===============================

        self.db.add_journal(
            trx_date,
            invoice_no,
            f"Pembelian {invoice_no}",
            [("1201", grand_total, 0), ("2101", 0, grand_total)],
        )

        return invoice_no

    def create_sales_return(self, trx_date, invoice_no, customer_id, items):

        # ===============================
        # VALIDASI INVOICE
        # ===============================

        inv = self.db.execute(
            "SELECT * FROM sales_invoices WHERE invoice_no=?", (invoice_no,)
        ).fetchone()

        if not inv:
            raise ValueError("Invoice tidak ditemukan")

        # ===============================
        # GENERATE NOMOR RETUR
        # ===============================

        row = self.db.execute("SELECT COUNT(*) c FROM sales_returns").fetchone()

        num = (row["c"] or 0) + 1
        return_no = f"RET-SLS-{str(num).zfill(5)}"

        self.db.execute(
            """
            INSERT INTO sales_returns(return_no,trx_date,invoice_no,customer_id)
            VALUES(?,?,?,?)
            """,
            (return_no, trx_date, invoice_no, customer_id),
            commit=True,
        )

        return_id = self.db.execute(
            "SELECT id FROM sales_returns WHERE return_no=?",
            (return_no,),
        ).fetchone()["id"]

        total_return = 0
        total_hpp = 0

        # ===============================
        # PROSES ITEM
        # ===============================

        for item in items:

            product_id = int(item["product_id"])
            qty = float(item["qty"])
            price = float(item["price"])

            if qty <= 0:
                continue

            # ===============================
            # CEK QTY TERJUAL
            # ===============================

            sold = (
                self.db.execute(
                    """
                SELECT SUM(qty) q
                FROM sales_invoice_items
                WHERE sales_invoice_id =
                    (SELECT id FROM sales_invoices WHERE invoice_no=?)
                AND product_id=?
                """,
                    (invoice_no, product_id),
                ).fetchone()["q"]
                or 0
            )

            # ===============================
            # CEK QTY SUDAH DIRETUR
            # ===============================

            returned = (
                self.db.execute(
                    """
                SELECT SUM(qty) q
                FROM sales_return_items sri
                JOIN sales_returns sr ON sr.id=sri.sales_return_id
                WHERE sr.invoice_no=? AND sri.product_id=?
                """,
                    (invoice_no, product_id),
                ).fetchone()["q"]
                or 0
            )

            if qty + returned > sold:
                raise ValueError("Qty retur melebihi qty yang dijual")

            # ===============================
            # HITUNG TOTAL
            # ===============================

            line_total = qty * price
            total_return += line_total

            product = self.db.execute(
                "SELECT cost_price FROM products WHERE id=?", (product_id,)
            ).fetchone()

            hpp = product["cost_price"] * qty
            total_hpp += hpp

            # ===============================
            # SIMPAN ITEM RETUR
            # ===============================

            self.db.execute(
                """
                INSERT INTO sales_return_items
                (sales_return_id,product_id,qty,price,total)
                VALUES(?,?,?,?,?)
                """,
                (return_id, product_id, qty, price, line_total),
                commit=True,
            )

            # ===============================
            # INVENTORY MOVEMENT
            # ===============================

            self.db.execute(
                """
                INSERT INTO inventory_movements
                (trx_date,product_id,movement_type,qty_in,qty_out,ref_no,notes)
                VALUES (?,?, 'SALE-RETURN',?,0,?,?)
                """,
                (
                    trx_date,
                    product_id,
                    qty,
                    return_no,
                    f"Retur {invoice_no}",
                ),
                commit=True,
            )

            self.db.update_product_stock(product_id)

        # ===============================
        # UPDATE TOTAL RETUR
        # ===============================

        self.db.execute(
            "UPDATE sales_returns SET total=? WHERE id=?",
            (total_return, return_id),
            commit=True,
        )

        # ===============================
        # JURNAL AKUNTANSI
        # ===============================

        self.db.add_journal(
            trx_date,
            return_no,
            f"Retur Penjualan {invoice_no}",
            [
                ("4002", total_return, 0),  # Retur Penjualan
                ("1101", 0, total_return),  # Piutang
                ("1201", total_hpp, 0),  # Persediaan
                ("5001", 0, total_hpp),  # HPP
            ],
        )

        return return_no

    # =====================================================
    # RETUR PENJUALAN MANUAL
    # =====================================================

    def create_sales_return_manual(self, trx_date, customer_id, items):

        if not items:
            raise ValueError("Tidak ada item retur.")

        return_no = self.db.get_next_number("SR", trx_date)

        cur = self.db.execute(
            """
            INSERT INTO sales_returns
            (return_no,trx_date,invoice_no,customer_id,total)
            VALUES (?,?,?,?,0)
            """,
            (return_no, trx_date, "", customer_id),
            commit=True,
        )

        return_id = cur.lastrowid

        total = 0
        total_hpp = 0

        for item in items:

            product_id = item["product_id"]
            qty = item["qty"]
            price = item["price"]

            line_total = qty * price
            total += line_total

            product = self.db.execute(
                "SELECT cost_price FROM products WHERE id=?", (product_id,)
            ).fetchone()

            hpp = product["cost_price"] * qty
            total_hpp += hpp

            # simpan item retur
            self.db.execute(
                """
            INSERT INTO sales_return_items
            (sales_return_id,product_id,qty,price,total)
            VALUES(?,?,?,?,?)
            """,
                (return_id, product_id, qty, price, line_total),
                commit=True,
            )

            # TAMBAH STOK
            self.add_inventory_movement(
                trx_date, product_id, "SALE-RETURN", qty, 0, return_no, "Retur Manual"
            )

        # update total retur
        self.db.execute(
            "UPDATE sales_returns SET total=? WHERE id=?",
            (total, return_id),
            commit=True,
        )

        # jurnal otomatis
        self.db.add_journal(
            trx_date,
            return_no,
            "Retur Penjualan Manual",
            [
                ("4002", total, 0),
                ("1101", 0, total),
                ("1201", total_hpp, 0),
                ("5001", 0, total_hpp),
            ],
        )

        return return_no

    def update_sales_invoice_after_return(self, invoice_no):

        inv = self.db.execute(
            "SELECT * FROM sales_invoices WHERE invoice_no=?", (invoice_no,)
        ).fetchone()

        if not inv:
            return

        # =========================
        # HITUNG TOTAL RETUR
        # =========================

        row = self.db.execute(
            """
            SELECT COALESCE(SUM(total),0) total
            FROM sales_returns
            WHERE invoice_no=?
            """,
            (invoice_no,),
        ).fetchone()

        return_total = row["total"] or 0

        net_total = inv["total"] - return_total

        # =========================
        # HITUNG STATUS
        # =========================

        paid = inv["paid"]

        if paid >= net_total:
            status = "PAID"
        elif paid == 0:
            status = "UNPAID"
        else:
            status = "PARTIAL"

        # =========================
        # UPDATE INVOICE
        # =========================

        self.db.execute(
            """
            UPDATE sales_invoices
            SET status=?
            WHERE id=?
            """,
            (status, inv["id"]),
            commit=True,
        )

    # =====================================================
    # PURCHASE RETURN
    # =====================================================

    def create_purchase_return(
        self,
        trx_date,
        invoice_no,
        supplier_id,
        items,
    ):

        return_no = self.generate_number("PR")

        total_return = 0

        for item in items:

            total_return += (
                item["qty"] * item["price"]
            )

        self.db.execute(
            """
            INSERT INTO purchase_returns
            (
                return_no,
                trx_date,
                invoice_no,
                supplier_id,
                total
            )
            VALUES (?,?,?,?,?)
            """,
            (
                return_no,
                trx_date,
                invoice_no,
                supplier_id,
                total_return,
            ),
            commit=True,
        )

        ret = self.db.execute(
            """
            SELECT id
            FROM purchase_returns
            WHERE return_no=?
            """,
            (return_no,),
        ).fetchone()

        return_id = ret["id"]

        for item in items:

            product_id = item["product_id"]

            qty = item["qty"]

            price = item["price"]

            total = qty * price

            # simpan item retur
            self.db.execute(
                """
                INSERT INTO purchase_return_items
                (
                    purchase_return_id,
                    product_id,
                    qty,
                    price,
                    total
                )
                VALUES (?,?,?,?,?)
                """,
                (
                    return_id,
                    product_id,
                    qty,
                    price,
                    total,
                ),
                commit=True,
            )

            # stok berkurang lagi
            self.db.execute(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE id=?
                """,
                (
                    qty,
                    product_id,
                ),
                commit=True,
            )

            # inventory movement
            self.db.execute(
                """
                INSERT INTO inventory_movements
                (
                    trx_date,
                    product_id,
                    movement_type,
                    qty,
                    ref_no,
                    notes
                )
                VALUES (?,?,?,?,?,?)
                """,
                (
                    trx_date,
                    product_id,
                    "OUT",
                    qty,
                    return_no,
                    "Retur Pembelian",
                ),
                commit=True,
            )

        # update paid purchase invoice
        self.db.execute(
            """
            UPDATE purchase_invoices
            SET paid = paid - ?
            WHERE invoice_no=?
            """,
            (
                total_return,
                invoice_no,
            ),
            commit=True,
        )

        return return_no
    
    def update_purchase_invoice_multi(
        self,
        invoice_no,
        trx_date,
        supplier_id,
        items,
        notes=""
    ):

        inv = self.db.execute(
            """
            SELECT id
            FROM purchase_invoices
            WHERE invoice_no=?
            """,
            (invoice_no,),
        ).fetchone()

        if not inv:
            raise Exception("Invoice tidak ditemukan")

        invoice_id = inv["id"]

        # =====================================
        # KEMBALIKAN STOK LAMA
        # =====================================

        old_items = self.db.execute(
            """
            SELECT product_id, qty
            FROM purchase_invoice_items
            WHERE purchase_invoice_id=?
            """,
            (invoice_id,),
        ).fetchall()

        for item in old_items:

            self.db.execute(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE id=?
                """,
                (item["qty"], item["product_id"]),
                commit=True,
            )

        # =====================================
        # HAPUS ITEM LAMA
        # =====================================

        self.db.execute(
            """
            DELETE FROM purchase_invoice_items
            WHERE purchase_invoice_id=?
            """,
            (invoice_id,),
            commit=True,
        )

        subtotal = 0

        # =====================================
        # INSERT ITEM BARU
        # =====================================

        for item in items:

            qty = item["qty"]
            price = item["price"]
            discount = item.get("discount", 0)

            total = (qty * price) - (qty * discount)

            subtotal += total

            self.db.execute(
                """
                INSERT INTO purchase_invoice_items
                (
                    purchase_invoice_id,
                    product_id,
                    qty,
                    price,
                    total
                )
                VALUES(?,?,?,?,?)
                """,
                (
                    invoice_id,
                    item["product_id"],
                    qty,
                    price,
                    total,
                ),
                commit=True,
            )

            # tambah stok baru
            self.db.execute(
                """
                UPDATE products
                SET stock = stock + ?
                WHERE id=?
                """,
                (qty, item["product_id"]),
                commit=True,
            )

        # =====================================
        # UPDATE HEADER
        # =====================================

        self.db.execute(
            """
            UPDATE purchase_invoices
            SET
                trx_date=?,
                supplier_id=?,
                total=?,
                notes=?
            WHERE id=?
            """,
            (
                trx_date,
                supplier_id,
                subtotal,
                notes,
                invoice_id,
            ),
            commit=True,
        )

        return invoice_no