import tkinter as tk
import customtkinter as ctk

from config import THEME


class Sidebar(ctk.CTkFrame):

    def __init__(self, parent, db, callback):

        super().__init__(
            parent,
            fg_color=THEME["sidebar_color"],
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

        self.apply_theme()
        

    # ==========================================================
    # HEADER (FIXED)
    # ==========================================================

    def build_header(self):

        self.header = tk.Frame(
            self,
            bg=THEME["sidebar_color"],
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
            bg=THEME["sidebar_color"],
            fg=THEME["sidebar_text_color"],
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
            bg=THEME["sidebar_color"],
            highlightthickness=0
        )

        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scroll_frame = tk.Frame(
            self.canvas,
            bg=THEME["sidebar_color"]
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
            bg=THEME["sidebar_color"]
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
                    bg=THEME["sidebar_color"]
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

    # Spacer atas
        tk.Frame(
            self.scroll_frame,
            height=30,
            bg=THEME["sidebar_color"]
        ).pack(fill="x")

    # ==========================================================
    # HEADING
    # ==========================================================

    def add_heading(self, text):

        tk.Label(
            self.scroll_frame,
            text=text,
            bg=THEME["sidebar_color"],
            fg=THEME["sidebar_text_color"],
            anchor="w",
            padx=25,
            pady=8,
            font=("Segoe UI", 9, "bold")
        ).pack(fill="x")

    # ==========================================================
    # BUTTON
    # ==========================================================

    def add_button(self, text, page):

        btn = ctk.CTkButton(
            self.scroll_frame,
            text=text,
            corner_radius=10,
            height=42,
            fg_color=THEME["menu_color"],
            hover_color="#323844",
            text_color=THEME["menu_text_color"],
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            command=lambda: self.menu_click(page)
        )

        btn.pack(
            fill="x",
            padx=14,
            pady=3
        )

        self.menu_buttons[page] = btn

    # ==========================================================
    # MENU CLICK
    # ==========================================================

    def menu_click(self, page):

        for key, btn in self.menu_buttons.items():

            if key == page:
                btn.configure(
                    fg_color=THEME["menu_active_color"]
                )

            else:
                btn.configure(
                    fg_color=THEME["menu_color"]
                )

        self.callback(page)

    # ==========================================================
    # HOVER
    # ==========================================================

    def hover(self, btn):

        if btn.cget("fg_color") == THEME["menu_active_color"]:
            return

        btn.configure(fg_color=THEME["menu_color"])

    def leave(self, btn):

        if btn.cget("fg_color") == THEME["menu_active_color"]:
            return

        btn.configure(fg_color=THEME["menu_color"])

    # ==========================================================
    # ACTIVE
    # ==========================================================

    def set_active(self, page):

        self.menu_click(page)

    def refresh_theme(self):

        self.configure(

            fg_color=THEME["sidebar_color"]

        )

        for child in self.winfo_children():

            try:

                child.configure(

                    fg_color=THEME["sidebar_color"]

                )

            except:

                pass

        for btn in self.menu_buttons.values():

            btn.configure(

                fg_color=THEME["menu_color"],

                text_color=THEME["menu_text_color"],

                hover_color=THEME["menu_active_color"],

                text_color_disabled=THEME["menu_text_color"]

            )

    def apply_theme(self):

        self.configure(fg_color=THEME["sidebar_color"])

        if hasattr(self, "logo_frame"):
            self.logo_frame.configure(fg_color=THEME["sidebar_color"])

        if hasattr(self, "title"):
            self.title.configure(
                fg_color=THEME["sidebar_color"],
                text_color=THEME["sidebar_text_color"]
            )

        if hasattr(self, "menu_buttons"):
            for btn in self.menu_buttons.values():
                btn.configure(
                    fg_color=THEME["menu_color"],
                    text_color=THEME["menu_text_color"],
                    hover_color=THEME["menu_active_color"],
                    text_color_disabled=THEME["menu_text_color"]
                )

