import tkinter as tk

from config import SIDEBAR_BG


class Sidebar(tk.Frame):

    def __init__(self, parent, db, callback):

        super().__init__(
            parent,
            bg=SIDEBAR_BG,
            width=300
        )

        self.db = db
        self.callback = callback

        self.configure(width=300)
        self.pack_propagate(False)

        self.menu_buttons = {}

        self.build_header()

        self.create_scroll()

        self.build_menu()

        # Paksa Tkinter menghitung ukuran seluruh isi sidebar
        self.scroll_frame.update_idletasks()

        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    # ==========================================================
    # HEADER (FIXED)
    # ==========================================================

    def build_header(self):

        self.header = tk.Frame(
            self,
            bg=SIDEBAR_BG,
            height=230
        )

        self.header.pack(
            fill="x"
        )

        self.header.pack_propagate(False)

        self.build_logo(self.header)

        tk.Label(
            self.header,
            text="© 2026 dibuat oleh Thio Charlie",
            bg=SIDEBAR_BG,
            fg="#9ca3af",
            font=("Segoe UI",9)
        ).pack(
            pady=(8,10)
        )

    # ==========================================================
    # SCROLL
    # ==========================================================

    def create_scroll(self):

        self.canvas = tk.Canvas(
            self,
            bg=SIDEBAR_BG,
            highlightthickness=0
        )

        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scroll_frame = tk.Frame(
            self.canvas,
            bg=SIDEBAR_BG
        )

        # Frame di dalam Canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scroll_frame,
            anchor="nw"
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        # ==============================
        # Update scrollregion
        # ==============================
        def on_frame_configure(event):
            self.canvas.update_idletasks()
            self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )

        self.scroll_frame.bind(
            "<Configure>",
            on_frame_configure
        )

        # ==============================
        # Lebar frame mengikuti canvas
        # ==============================
        def on_canvas_configure(event):
            self.canvas.itemconfig(
                self.canvas_window,
                width=event.width
            )

        self.canvas.bind(
            "<Configure>",
            on_canvas_configure
        )

        # ==============================
        # Mouse Wheel
        # ==============================
        def _on_mousewheel(event):

            # Windows
            if event.delta:
                self.canvas.yview_scroll(
                    -int(event.delta / 120),
                    "units"
                )

            # Linux
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")

            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

        def _bind_mousewheel(event):

            self.canvas.bind_all(
                "<MouseWheel>",
                _on_mousewheel
            )

            self.canvas.bind_all(
                "<Button-4>",
                _on_mousewheel
            )

            self.canvas.bind_all(
                "<Button-5>",
                _on_mousewheel
            )

        def _unbind_mousewheel(event):

            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

        self.canvas.bind(
            "<Enter>",
            _bind_mousewheel
        )

        self.canvas.bind(
            "<Leave>",
            _unbind_mousewheel
        )

    # ==========================================================
    # LOGO
    # ==========================================================

    def build_logo(self, parent):

        frame = tk.Frame(
            parent,
            bg=SIDEBAR_BG
        )

        frame.pack(
            fill="x",
            padx=20,
            pady=20
        )

        try:

            from PIL import Image
            from PIL import ImageTk

            profile = self.db.execute("""
                SELECT logo
                FROM company_profile
                LIMIT 1
            """).fetchone()

            if profile and profile["logo"]:

                img = Image.open(profile["logo"])
                img.thumbnail((180, 120))

                photo = ImageTk.PhotoImage(img)

                lbl = tk.Label(
                    frame,
                    image=photo,
                    bg=SIDEBAR_BG
                )

                lbl.image = photo
                lbl.pack(anchor="center")

        except:
            pass

    # ==========================================================
    # MENU
    # ==========================================================

    def build_menu(self):

        MENU = [

            ("DASHBOARD", None),
 
            ("🤖 AI Assistant", "ai"),
            ("🏠 Dasbor", "dashboard"),

            ("MASTER", None),

            ("📦 Produk", "product"),
            ("👤 Pelanggan", "customer"),
            ("🏢 Pemasok", "supplier"),

            ("TRANSAKSI", None),

            ("💰 Penjualan", "sales"),
            ("🛒 Pembelian", "purchase"),
            ("📋 Persediaan", "inventory"),

            ("AKUNTANSI", None),

            ("💵 Kas & Bank", "cashbank"),
            ("📒 Jurnal Umum", "journal"),
            ("📑 Akun Perkiraan", "account"),

            ("LAPORAN", None),

            ("📊 Laporan", "report"),

            ("SYSTEM", None),

            ("⚙ Pengaturan", "setting"),
        ]

        for text, page in MENU:

            if page is None:

                self.add_heading(text)

            else:

                self.add_button(text, page)

    # ==========================================================
    # HEADING
    # ==========================================================

    def add_heading(self, text):

        tk.Label(
            self.scroll_frame,
            text=text,
            bg=SIDEBAR_BG,
            fg="#94a3b8",
            anchor="w",
            padx=25,
            pady=8,
            font=("Segoe UI", 9, "bold")
        ).pack(fill="x")

    # ==========================================================
    # BUTTON
    # ==========================================================

    def add_button(self, text, page):

        btn = tk.Label(

            self.scroll_frame,

            text=text,

            bg="#b91c1c",

            fg="white",

            padx=28,

            pady=13,

            anchor="w",

            cursor="hand2",

            font=("Segoe UI", 11, "bold")
        )

        btn.pack(
            fill="x",
            padx=18,
            pady=4
        )

        btn.bind(
            "<Button-1>",
            lambda e:
            self.menu_click(page)
        )

        btn.bind(
            "<Enter>",
            lambda e,
            b=btn:
            self.hover(b)
        )

        btn.bind(
            "<Leave>",
            lambda e,
            b=btn:
            self.leave(b)
        )

        self.menu_buttons[page] = btn

    # ==========================================================
    # MENU CLICK
    # ==========================================================

    def menu_click(self, page):

        for key, btn in self.menu_buttons.items():

            if key == page:

                btn.config(
                    bg="#2563eb",
                    fg="white"
                )

            else:

                btn.config(
                    fg="white",
                    bg="#b91c1c"
                )

        self.callback(page)

    # ==========================================================
    # HOVER
    # ==========================================================

    def hover(self, btn):

        if btn.cget("bg") == "#2563eb":
            return

        btn.config(bg="#374151")

    def leave(self, btn):

        if btn.cget("bg") == "#2563eb":
            return

        btn.config(bg="#b91c1c")

    # ==========================================================
    # ACTIVE
    # ==========================================================

    def set_active(self, page):

        self.menu_click(page)