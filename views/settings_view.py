import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


class SettingsView(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg="#f9fafb")
        self.db = db
        self.build_ui()

    def build_ui(self):
        header = tk.Frame(self, bg="#f9fafb")
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header, text="Pengaturan", font=("Segoe UI", 16, "bold"), bg="#f9fafb"
        ).pack(side="left")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.build_company_tab(notebook)
        self.build_numbering_tab(notebook)
        self.build_info_tab(notebook)

    def build_company_tab(self, notebook):
        tab = tk.Frame(notebook, bg="white")
        notebook.add(tab, text="Profil Perusahaan")

        profile = self.db.execute("SELECT * FROM company_profile LIMIT 1").fetchone()

        from tkinter import filedialog
        from PIL import Image, ImageTk

        tk.Label(tab, text="Nama Perusahaan", bg="white").grid(
            row=0, column=0, padx=10, pady=(10, 2), sticky="w"
        )

        tk.Label(tab, text="Alamat", bg="white").grid(
            row=1, column=0, padx=10, pady=(10, 2), sticky="w"
        )

        tk.Label(tab, text="Rekening Perusahaan", bg="white").grid(
            row=2, column=0, padx=10, pady=(10, 2), sticky="w"
        )

        tk.Label(tab, text="Rekening Perusahaan #2", bg="white").grid(
            row=3, column=0, padx=10, pady=(10, 2), sticky="w"
        )

        tk.Label(tab, text="Telepon", bg="white").grid(
            row=4, column=0, padx=10, pady=(10, 2), sticky="w"
        )

        tk.Label(tab, text="Status Pajak", bg="white").grid(
            row=5, column=0, padx=10, pady=(10, 2), sticky="w"
        )

        tk.Label(tab, text="Logo Perusahaan 150x110px", bg="white").grid(
            row=6, column=0, padx=10, pady=(10, 2), sticky="w"
        )

        company_entry = tk.Entry(tab, width=50)
        company_entry.insert(0, profile["company_name"] or "")

        addr_entry = tk.Entry(tab, width=50)
        addr_entry.insert(0, profile["address"] or "")

        desc = profile["description"] or ""
        lines = desc.split("\n")

        rekening1 = lines[0] if len(lines) > 0 else ""
        rekening2 = lines[1] if len(lines) > 1 else ""

        # =========================
        # REKENING 1
        # =========================
        rekening_entry = tk.Entry(tab, width=50)
        rekening_entry.grid(row=2, column=1, padx=10, pady=(10, 2), sticky="w")
        rekening_entry.insert(0, rekening1)

        # =========================
        # REKENING 2
        # =========================
        rekening2_entry = tk.Entry(tab, width=50)
        rekening2_entry.grid(row=3, column=1, padx=10, pady=(10, 2), sticky="w")
        rekening2_entry.insert(0, rekening2)

        phone_entry = tk.Entry(tab, width=50)
        phone_entry.insert(0, profile["phone"] or "")

        tax_combo = ttk.Combobox(tab, values=["PPN 11%", "NON-PPN"], state="readonly")
        tax_combo.set(profile["tax_status"] or "NON-PPN")

        logo_path = profile["logo"] if "logo" in profile.keys() else ""

        logo_label = tk.Label(tab, bg="white")

        def load_logo(path):
            try:
                img = Image.open(path)
                img = img.resize((150, 110))
                photo = ImageTk.PhotoImage(img)
                logo_label.image = photo
                logo_label.config(image=photo)
            except:
                logo_label.config(text="Logo tidak ditemukan")

        if logo_path:
            load_logo(logo_path)

        def upload_logo():
            nonlocal logo_path

            file = filedialog.askopenfilename(
                title="Pilih Logo", filetypes=[("Image", "*.png *.jpg *.jpeg")]
            )

            if file:
                logo_path = file
                load_logo(file)

        upload_btn = tk.Button(
            tab, text="Upload Logo", command=upload_logo, bg="#6366f1", fg="white"
        )

        company_entry.grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")
        addr_entry.grid(row=1, column=1, padx=10, pady=(10, 2), sticky="w")
        phone_entry.grid(row=4, column=1, padx=10, pady=(10, 2), sticky="w")
        tax_combo.grid(row=5, column=1, padx=10, pady=(10, 2), sticky="w")

        upload_btn.grid(row=6, column=1, sticky="w", padx=10)
        logo_label.grid(row=7, column=1, padx=10, pady=10, sticky="w")

        def save_profile():

            rekening1 = rekening_entry.get().strip()
            rekening2 = rekening2_entry.get().strip()

            rekening_combined = "\n".join([r for r in [rekening1, rekening2] if r])

            self.db.execute(
                """
                UPDATE company_profile
                SET company_name=?, address=?, phone=?, tax_status=?, logo=?, description=?
                WHERE id=?
                """,
                (
                    company_entry.get().strip(),
                    addr_entry.get().strip(),
                    phone_entry.get().strip(),
                    tax_combo.get().strip(),
                    logo_path,
                    rekening_combined,  # 🔥 gabungan
                    profile["id"],
                ),
                commit=True,
            )

            messagebox.showinfo("Sukses", "Profil perusahaan berhasil disimpan.")

        tk.Button(
            tab,
            text="Simpan Profil",
            command=save_profile,
            bg="#2563eb",
            fg="white",
            padx=15,
        ).grid(row=9, column=1, padx=10, pady=15, sticky="w")

    def build_numbering_tab(self, notebook):
        tab = tk.Frame(notebook, bg="white")
        notebook.add(tab, text="Penomoran Dokumen")

        note = tk.Label(
            tab,
            text="Gunakan placeholder tanggal: {YYYY}, {YY}, {MM}, {DD}\nContoh prefix: INVJ-{YYYY}{MM}- atau PO-{YY}{MM}{DD}-",
            bg="white",
            justify="left",
            fg="#374151",
        )
        note.pack(anchor="w", padx=10, pady=(10, 0))

        tree = ttk.Treeview(
            tab,
            columns=("doc", "prefix", "current", "digit", "date_format"),
            show="headings",
            height=15,
        )
        for c, h, w in [
            ("doc", "Tipe Dokumen", 120),
            ("prefix", "Prefix", 220),
            ("current", "Nomor Saat Ini", 120),
            ("digit", "Digit", 100),
            ("date_format", "Format Tanggal", 140),
        ]:
            tree.heading(c, text=h)
            tree.column(c, width=w)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        rows = self.db.execute(
            "SELECT doc_type, prefix, current_number, digit_length, date_format FROM numbering_settings ORDER BY doc_type"
        ).fetchall()
        for r in rows:
            tree.insert(
                "",
                "end",
                values=(
                    r["doc_type"],
                    r["prefix"],
                    r["current_number"],
                    r["digit_length"],
                    r["date_format"],
                ),
            )

        def edit_numbering():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Pilih data penomoran.")
                return

            vals = tree.item(selected[0], "values")
            doc_type = vals[0]

            prefix = simpledialog.askstring(
                "Edit Prefix", f"Prefix untuk {doc_type}:", initialvalue=vals[1]
            )
            if prefix is None:
                return

            current = simpledialog.askinteger(
                "Edit Nomor Saat Ini",
                f"Nomor saat ini untuk {doc_type}:",
                initialvalue=int(vals[2]),
            )
            if current is None:
                return

            digit = simpledialog.askinteger(
                "Edit Digit", f"Digit untuk {doc_type}:", initialvalue=int(vals[3])
            )
            if digit is None:
                return

            date_format = simpledialog.askstring(
                "Edit Format Tanggal",
                f"Format tanggal untuk {doc_type}:",
                initialvalue=vals[4],
            )
            if date_format is None:
                return

            self.db.execute(
                """
                UPDATE numbering_settings
                SET prefix=?, current_number=?, digit_length=?, date_format=?
                WHERE doc_type=?
            """,
                (prefix, current, digit, date_format, doc_type),
                commit=True,
            )

            # update tampilan treeview
            tree.item(
                selected[0], values=(doc_type, prefix, current, digit, date_format)
            )

            messagebox.showinfo("Sukses", "Penomoran berhasil diperbarui.")

        tk.Button(
            tab,
            text="Edit Penomoran",
            command=edit_numbering,
            bg="#2563eb",
            fg="white",
            relief="flat",
            padx=15,
        ).pack(anchor="w", padx=10, pady=(0, 10))

    def build_info_tab(self, notebook):
        tab = tk.Frame(notebook, bg="white")
        notebook.add(tab, text="Info Pengembangan")

        info_text = tk.Text(tab, wrap="word")
        info_text.pack(fill="both", expand=True, padx=10, pady=10)

        info_text.insert(
            "1.0",
            """
Modul yang sudah ditingkatkan:
- Sort data table
- Edit / hapus master data
- Edit / hapus transaksi tertentu
- Input harga normal dan diskon penjualan
- Pembayaran cicilan / sebagian
- Akun lawan untuk kas & bank
- Diskon pada kas & bank
- Prefix nomor dengan tanggal otomatis
""",
        )
        info_text.config(state="disabled")

    def refresh_self(self):
        self.destroy()
        SettingsView(self.master, self.db).pack(fill="both", expand=True)
