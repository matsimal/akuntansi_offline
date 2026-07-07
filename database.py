import sqlite3
from datetime import datetime
from config import DB_NAME


class Database:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.migrate_tables()
        self.seed_defaults()

    def execute(self, query, params=(), commit=False):
        cur = self.conn.cursor()
        cur.execute(query, params)
        if commit:
            self.conn.commit()
        return cur

    def executemany(self, query, seq, commit=False):
        cur = self.conn.cursor()
        cur.executemany(query, seq)
        if commit:
            self.conn.commit()
        return cur

    def table_columns(self, table_name):
        rows = self.execute(f"PRAGMA table_info({table_name})").fetchall()
        return [r["name"] for r in rows]

    def add_column_if_not_exists(self, table_name, column_name, column_def):
        cols = self.table_columns(table_name)
        if column_name not in cols:
            self.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}",
                commit=True,
            )

    def migrate_tables(self):

        self.add_column_if_not_exists("sales_invoices", "discount", "REAL DEFAULT 0")
        self.add_column_if_not_exists(
            "sales_invoice_items", "unit_price", "REAL DEFAULT 0"
        )
        self.add_column_if_not_exists(
            "sales_invoice_items", "discount", "REAL DEFAULT 0"
        )
        self.add_column_if_not_exists("sales_invoices", "sj_no", "TEXT")

        self.add_column_if_not_exists("company_profile", "description", "TEXT")

        self.add_column_if_not_exists("purchase_invoices", "discount", "REAL DEFAULT 0")

        self.add_column_if_not_exists(
            "cash_bank_transactions", "discount", "REAL DEFAULT 0"
        )
        self.add_column_if_not_exists("cash_bank_transactions", "account_code", "TEXT")

        self.add_column_if_not_exists("products", "supplier_id", "INTEGER")
        self.add_column_if_not_exists("products", "is_active", "INTEGER DEFAULT 1")

        # customer
        self.add_column_if_not_exists("customers", "email", "TEXT")
        self.add_column_if_not_exists("customers", "npwp", "TEXT")
        self.add_column_if_not_exists("customers", "credit_limit", "REAL DEFAULT 0")
        self.add_column_if_not_exists("customers", "sales_pic", "TEXT")
        self.add_column_if_not_exists("customers", "domisili", "TEXT")
        self.add_column_if_not_exists("customers", "is_active", "INTEGER DEFAULT 1")

        # supplier (TAMBAHKAN INI)
        self.add_column_if_not_exists("suppliers", "email", "TEXT")
        self.add_column_if_not_exists("suppliers", "npwp", "TEXT")
        self.add_column_if_not_exists("suppliers", "pic", "TEXT")
        self.add_column_if_not_exists("suppliers", "is_active", "INTEGER DEFAULT 1")

        try:
            self.execute(
                """
                CREATE TABLE IF NOT EXISTS app_theme (
                    id INTEGER PRIMARY KEY,
                    background_color TEXT,
                    text_color TEXT,
                    sidebar_color TEXT,
                    sidebar_text_color TEXT,
                    menu_color TEXT,
                    menu_active_color TEXT,
                    menu_text_color TEXT,
                    card_color TEXT,
                    button_color TEXT,
                    button_hover_color TEXT,
                    button_text_color TEXT,
                    button_border_color TEXT
                )
                """,
                commit=True,
            )
        except Exception as e:
            print("Migration Theme :", e)

    def create_tables(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS company_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                address TEXT,
                phone TEXT,
                tax_status TEXT DEFAULT 'NON-PPN'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS numbering_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_type TEXT UNIQUE,
                prefix TEXT,
                current_number INTEGER DEFAULT 0,
                digit_length INTEGER DEFAULT 5,
                date_format TEXT DEFAULT '{YYYY}{MM}'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS app_theme (
                id INTEGER PRIMARY KEY,
                background_color TEXT DEFAULT '#f9fafb',
                text_color TEXT DEFAULT '#1f2937',
                sidebar_color TEXT DEFAULT '#1f2937',
                sidebar_text_color TEXT DEFAULT '#ffffff',
                menu_color TEXT DEFAULT '#374151',
                menu_active_color TEXT DEFAULT '#2563eb',
                menu_text_color TEXT DEFAULT '#ffffff',
                card_color TEXT DEFAULT '#ffffff',
                button_color TEXT DEFAULT '#2563eb',
                button_hover_color TEXT DEFAULT '#1d4ed8',
                button_text_color TEXT DEFAULT '#ffffff',
                button_border_color TEXT DEFAULT '#1e40af'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE,
                name TEXT,
                supplier_id INTEGER,
                category_id INTEGER,
                unit_id INTEGER,
                cost_price REAL DEFAULT 0,
                sell_price REAL DEFAULT 0,
                min_stock REAL DEFAULT 0,
                stock REAL DEFAULT 0,
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY(category_id) REFERENCES categories(id),
                FOREIGN KEY(unit_id) REFERENCES units(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT,
                phone TEXT,
                address TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT,
                phone TEXT,
                address TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT,
                type TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trx_date TEXT,
                ref_no TEXT,
                description TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS journal_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_id INTEGER,
                account_id INTEGER,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                FOREIGN KEY(journal_id) REFERENCES journal_entries(id),
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE,
                trx_date TEXT,
                customer_id INTEGER,
                subtotal REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                total REAL DEFAULT 0,
                paid REAL DEFAULT 0,
                status TEXT DEFAULT 'UNPAID',
                notes TEXT,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales_invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sales_invoice_id INTEGER,
                product_id INTEGER,
                qty REAL DEFAULT 0,
                unit_price REAL DEFAULT 0,
                price REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                total REAL DEFAULT 0,
                FOREIGN KEY(sales_invoice_id) REFERENCES sales_invoices(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS purchase_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE,
                trx_date TEXT,
                supplier_id INTEGER,
                subtotal REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                total REAL DEFAULT 0,
                paid REAL DEFAULT 0,
                status TEXT DEFAULT 'UNPAID',
                notes TEXT,
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS purchase_invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_invoice_id INTEGER,
                product_id INTEGER,
                qty REAL DEFAULT 0,
                price REAL DEFAULT 0,
                total REAL DEFAULT 0,
                FOREIGN KEY(purchase_invoice_id) REFERENCES purchase_invoices(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trx_date TEXT,
                product_id INTEGER,
                movement_type TEXT,
                qty_in REAL DEFAULT 0,
                qty_out REAL DEFAULT 0,
                ref_no TEXT,
                notes TEXT,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cash_bank_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trx_date TEXT,
                trx_type TEXT,
                account_name TEXT,
                account_code TEXT,
                amount REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                ref_no TEXT,
                notes TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS fixed_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_name TEXT,
                acquisition_date TEXT,
                acquisition_cost REAL DEFAULT 0,
                useful_life_years INTEGER DEFAULT 0,
                residual_value REAL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS depreciation_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                dep_date TEXT,
                amount REAL DEFAULT 0,
                FOREIGN KEY(asset_id) REFERENCES fixed_assets(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_no TEXT UNIQUE,
                trx_date TEXT,
                invoice_no TEXT,
                customer_id INTEGER,
                total REAL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales_return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sales_return_id INTEGER,
                product_id INTEGER,
                qty REAL,
                price REAL,
                total REAL,
                FOREIGN KEY(sales_return_id) REFERENCES sales_returns(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """,
                        """
            CREATE TABLE IF NOT EXISTS purchase_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_no TEXT UNIQUE,
                trx_date TEXT,
                invoice_no TEXT,
                supplier_id INTEGER,
                total REAL DEFAULT 0
            )
            """,

            """
            CREATE TABLE IF NOT EXISTS purchase_return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_return_id INTEGER,
                product_id INTEGER,
                qty REAL,
                price REAL,
                total REAL,
                FOREIGN KEY(purchase_return_id)
                    REFERENCES purchase_returns(id),

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
            )
            """,
        ]

        for q in queries:
            self.execute(q, commit=True)

        try:
            self.execute(
                "ALTER TABLE company_profile ADD COLUMN logo TEXT", commit=True
            )
        except:
            pass

        # index untuk mempercepat query customer invoice
        self.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_sales_customer
        ON sales_invoices(customer_id)
        """
        )

        self.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_sales_date
        ON sales_invoices(trx_date)
        """
        )

        self.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_purchase_supplier
        ON purchase_invoices(supplier_id)
        """
        )

        self.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_inventory_product
        ON inventory_movements(product_id)
        """
        )

        self.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_journal_account
        ON journal_details(account_id)
        """
        )

        self.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_purchase_date
        ON purchase_invoices(trx_date)
        """,
            commit=True,
        )

        self.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_sales_invoice_no
        ON sales_invoices(invoice_no);
        """,
            commit=True,
        )

    def seed_defaults(self):
        row = self.execute("SELECT COUNT(*) AS cnt FROM company_profile").fetchone()
        if row["cnt"] == 0:
            self.execute(
                "INSERT INTO company_profile (company_name, address, phone, tax_status) VALUES (?, ?, ?, ?)",
                ("Perusahaan Anda", "", "", "NON-PPN"),
                commit=True,
            )
        
        theme = self.execute(
            "SELECT COUNT(*) AS cnt FROM app_theme"
        ).fetchone()

        if theme["cnt"] == 0:
            self.execute(
                """
                INSERT INTO app_theme(
                    id,
                    background_color,
                    text_color,
                    sidebar_color,
                    sidebar_text_color,
                    menu_color,
                    menu_active_color,
                    menu_text_color,
                    card_color,
                    button_color,
                    button_hover_color,
                    button_text_color,
                    button_border_color
                )
                VALUES(
                    1,
                    '#f9fafb',
                    '#1f2937',
                    '#1f2937',
                    '#ffffff',
                    '#374151',
                    '#2563eb',
                    '#ffffff',
                    '#ffffff',
                    '#2563eb',
                    '#1d4ed8',
                    '#ffffff',
                    '#1e40af'
                )
                """,
                commit=True,
            )

        row = self.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        if row["cnt"] == 0:
            self.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", "admin", "Administrator"),
                commit=True,
            )

        for pm in ["Cash", "Transfer Bank"]:
            try:
                self.execute(
                    "INSERT INTO payment_methods (name) VALUES (?)", (pm,), commit=True
                )
            except sqlite3.IntegrityError:
                pass

        for u in ["sak", "kg", "m3", "batang", "pcs", "unit", "liter"]:
            try:
                self.execute("INSERT INTO units (name) VALUES (?)", (u,), commit=True)
            except sqlite3.IntegrityError:
                pass

        for c in ["Semen", "Besi", "Pasir", "Batu", "Cat", "Lain-lain"]:
            try:
                self.execute(
                    "INSERT INTO categories (name) VALUES (?)", (c,), commit=True
                )
            except sqlite3.IntegrityError:
                pass

        defaults_doc = [
            ("QUO", "QUO-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("SO", "SO-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("DO", "DO-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("SI", "INVJ-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("RCV", "RCV-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("PO", "PO-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("PI", "INVB-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("PAY", "PAY-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("JV", "JV-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("CB", "CB-{YYYY}{MM}-", 0, 5, "{YYYY}{MM}"),
            ("CUST", "CUST-", 0, 5, ""),
        ]

        for doc_type, prefix, current, digit, date_format in defaults_doc:
            existing = self.execute(
                "SELECT id FROM numbering_settings WHERE doc_type=?", (doc_type,)
            ).fetchone()

            if not existing:
                self.execute(
                    """
                    INSERT INTO numbering_settings
                    (doc_type, prefix, current_number, digit_length, date_format)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (doc_type, prefix, current, digit, date_format),
                    commit=True,
                )

        coa_defaults = [
            ("1001", "Kas", "Asset"),
            ("1002", "Bank", "Asset"),
            ("1101", "Piutang Usaha", "Asset"),
            ("1201", "Persediaan Barang", "Asset"),
            ("1501", "Aset Tetap", "Asset"),
            ("2101", "Utang Usaha", "Liability"),
            ("3001", "Modal", "Equity"),
            ("4001", "Penjualan", "Revenue"),
            ("4002", "Retur Penjualan", "Revenue"),
            ("5001", "Harga Pokok Penjualan", "Expense"),
            ("6001", "Biaya Operasional", "Expense"),
            ("6101", "Biaya Penyusutan", "Expense"),
        ]

        for code, name, typ in coa_defaults:
            try:
                self.execute(
                    "INSERT INTO accounts (code, name, type) VALUES (?, ?, ?)",
                    (code, name, typ),
                    commit=True,
                )
            except sqlite3.IntegrityError:
                pass

    def render_number_prefix(self, template, trx_date=None):
        if trx_date:
            dt = datetime.strptime(trx_date, "%d/%m/%Y")
        else:
            dt = datetime.now()

        return (
            template.replace("{YYYY}", dt.strftime("%Y"))
            .replace("{YY}", dt.strftime("%y"))
            .replace("{MM}", dt.strftime("%m"))
            .replace("{DD}", dt.strftime("%d"))
        )

    def get_next_number(self, doc_type, trx_date=None):
        row = self.execute(
            "SELECT * FROM numbering_settings WHERE doc_type=?", (doc_type,)
        ).fetchone()

        if not row:
            return f"{doc_type}-00001"

        next_num = row["current_number"] + 1
        prefix = self.render_number_prefix(row["prefix"], trx_date)
        formatted = f"{prefix}{str(next_num).zfill(row['digit_length'])}"

        self.execute(
            "UPDATE numbering_settings SET current_number=? WHERE doc_type=?",
            (next_num, doc_type),
            commit=True,
        )
        return formatted

    def add_journal(self, trx_date, ref_no, description, lines):
        cur = self.execute(
            "INSERT INTO journal_entries (trx_date, ref_no, description) VALUES (?, ?, ?)",
            (trx_date, ref_no, description),
            commit=True,
        )
        journal_id = cur.lastrowid

        for acc_code, debit, credit in lines:
            acc = self.execute(
                "SELECT id FROM accounts WHERE code=?", (acc_code,)
            ).fetchone()
            if acc:
                self.execute(
                    "INSERT INTO journal_details (journal_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                    (journal_id, acc["id"], debit, credit),
                    commit=True,
                )

    def update_product_stock(self, product_id):
        row = self.execute(
            """
            SELECT COALESCE(SUM(qty_in), 0) - COALESCE(SUM(qty_out), 0) AS stock
            FROM inventory_movements
            WHERE product_id=?
        """,
            (product_id,),
        ).fetchone()

        stock = row["stock"] if row else 0
        self.execute(
            "UPDATE products SET stock=? WHERE id=?", (stock, product_id), commit=True
        )

    def get_theme(self):

        row = self.execute(
            "SELECT * FROM app_theme WHERE id=1"
        ).fetchone()
        return dict(row) if row else None
    
    def save_theme(self, data):
        self.execute(
            """
            UPDATE app_theme
            SET
                background_color=?,
                text_color=?,
                sidebar_color=?,
                sidebar_text_color=?,
                menu_color=?,
                menu_active_color=?,
                menu_text_color=?,
                card_color=?,
                button_color=?,
                button_hover_color=?,
                button_text_color=?,
                button_border_color=?
            WHERE id=1
            """,
            (
                data["background_color"],
                data["text_color"],
                data["sidebar_color"],
                data["sidebar_text_color"],
                data["menu_color"],
                data["menu_active_color"],
                data["menu_text_color"],
                data["card_color"],
                data["button_color"],
                data["button_hover_color"],
                data["button_text_color"],
                data["button_border_color"]
            ),
            commit=True,
        )