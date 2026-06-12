"""Magazzino: movimenti, giacenze, ultimi prezzi."""
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import database
from utils import theme


class MovementsWindow(ctk.CTkFrame):
    """Storico movimenti con carico/scarico manuale (anche da lettore barcode)."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.BG)

        # --- HEADER ---
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(head, text="Movimenti di Magazzino", font=theme.font(22, bold=True),
                     text_color=theme.TEXT).pack(side="left")

        ctk.CTkButton(head, text="➖ Scarico", width=110, fg_color=theme.RED_D,
                      hover_color=theme.darken(theme.RED_D),
                      command=lambda: self.manual_movement("OUT")).pack(side="right", padx=4)
        ctk.CTkButton(head, text="➕ Carico", width=110, fg_color=theme.GREEN_D,
                      hover_color=theme.darken(theme.GREEN_D),
                      command=lambda: self.manual_movement("IN")).pack(side="right", padx=4)

        # --- FILTRI ---
        filt = theme.card(self)
        filt.pack(fill="x", padx=20, pady=(0, 10))
        inner = ctk.CTkFrame(filt, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(inner, text="Cerca articolo:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(0, 6))
        self.ent_search = ctk.CTkEntry(inner, width=220, placeholder_text="codice o descrizione...")
        self.ent_search.pack(side="left", padx=(0, 14))
        self.ent_search.bind("<Return>", lambda e: self.refresh())

        ctk.CTkLabel(inner, text="Direzione:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(0, 6))
        self.combo_dir = ctk.CTkOptionMenu(inner, values=["Tutti", "Carico", "Scarico"],
                                           width=110, command=lambda x: self.refresh())
        self.combo_dir.pack(side="left", padx=(0, 14))

        ctk.CTkButton(inner, text="🔄 Aggiorna", width=100, fg_color=theme.SURFACE_2,
                      hover_color=theme.BORDER, command=self.refresh).pack(side="left")
        ctk.CTkButton(inner, text="📗 Esporta CSV", width=110, fg_color=theme.SURFACE_2,
                      hover_color=theme.BORDER, command=self.export_csv).pack(side="right")

        # --- TABELLA ---
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        cols = ("Data", "Codice", "Articolo", "Qtà", "Direzione", "Causale", "Documento")
        self.tree = ttk.Treeview(body, columns=cols, show="headings")
        widths = {"Data": 130, "Codice": 90, "Articolo": 280, "Qtà": 70,
                  "Direzione": 90, "Causale": 220, "Documento": 140}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="e" if c == "Qtà" else "w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(body, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        self.refresh()

    def refresh(self):
        for x in self.tree.get_children():
            self.tree.delete(x)
        dmap = {"Carico": "IN", "Scarico": "OUT"}
        rows = database.get_movements(search=self.ent_search.get().strip() or None,
                                      direction=dmap.get(self.combo_dir.get()))
        self._rows = rows
        for r in rows:
            # id, date, code, articolo, qty, direction, reason, doc
            arrow = "▲ Carico" if r[5] == "IN" else "▼ Scarico"
            tag = "green" if r[5] == "IN" else "red"
            self.tree.insert("", "end",
                             values=(r[1], r[2], r[3], f"{r[4]:g}", arrow, r[6], r[7]),
                             tags=(tag,))
        theme.stripe(self.tree)

    def manual_movement(self, direction):
        MovementDialog(self, direction)

    def export_csv(self):
        if not getattr(self, "_rows", None):
            messagebox.showinfo("Export", "Nessun movimento da esportare.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="movimenti.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        import csv
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Data", "Codice", "Articolo", "Quantita", "Direzione", "Causale", "Documento"])
            for r in self._rows:
                w.writerow([r[1], r[2], r[3], str(r[4]).replace(".", ","),
                            "Carico" if r[5] == "IN" else "Scarico", r[6], r[7]])
        messagebox.showinfo("Export", f"Esportato:\n{path}")


class MovementDialog(ctk.CTkToplevel):
    """Carico/scarico manuale con supporto lettore di codici a barre."""

    def __init__(self, parent, direction):
        super().__init__(parent)
        self.parent = parent
        self.direction = direction
        is_in = direction == "IN"
        self.title("Carico Magazzino" if is_in else "Scarico Magazzino")
        self.geometry("480x420")
        self.configure(fg_color=theme.BG)
        self.grab_set()

        color = theme.GREEN_D if is_in else theme.RED_D
        ctk.CTkLabel(self, text=("➕ CARICO" if is_in else "➖ SCARICO"),
                     font=theme.font(18, bold=True), text_color=color).pack(pady=(18, 4))

        # Scanner: campo sempre a fuoco, Invio = seleziona articolo
        scan_card = theme.card(self)
        scan_card.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(scan_card, text="📷 Lettore barcode (Invio per confermare)",
                     font=theme.font(10), text_color=theme.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 2))
        self.entry_scan = ctk.CTkEntry(scan_card, placeholder_text="Scansiona codice...")
        self.entry_scan.pack(fill="x", padx=12, pady=(0, 10))
        self.entry_scan.bind("<Return>", self.on_scan)

        # Selezione manuale
        self.products = self._load_products()
        names = list(self.products.keys())
        ctk.CTkLabel(self, text="oppure scegli l'articolo:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(anchor="w", padx=22, pady=(6, 2))
        self.combo_prod = ctk.CTkComboBox(self, values=names, width=420)
        self.combo_prod.pack(padx=20, fill="x")
        self.combo_prod.set("")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(row, text="Quantità:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(2, 6))
        self.entry_qty = ctk.CTkEntry(row, width=90)
        self.entry_qty.insert(0, "1")
        self.entry_qty.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(row, text="Causale:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(0, 6))
        self.entry_reason = ctk.CTkEntry(row, placeholder_text="es. rettifica inventario")
        self.entry_reason.pack(side="left", fill="x", expand=True)

        self.lbl_feedback = ctk.CTkLabel(self, text="", font=theme.font(11), text_color=theme.GREEN)
        self.lbl_feedback.pack(pady=2)

        ctk.CTkButton(self, text="CONFERMA", fg_color=color, hover_color=theme.darken(color),
                      height=38, command=self.confirm).pack(pady=10, padx=20, fill="x")

        self.after(150, self.entry_scan.focus_set)

    def _load_products(self):
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        cur.execute("""SELECT id, COALESCE(code,''), COALESCE(NULLIF(description,''), name)
                       FROM products ORDER BY code""")
        rows = cur.fetchall()
        conn.close()
        return {f"{r[1]} — {r[2]}": r[0] for r in rows}

    def on_scan(self, event=None):
        code = self.entry_scan.get().strip()
        if not code:
            return
        prod = database.get_product_by_code(code)
        if prod:
            label = next((k for k, v in self.products.items() if v == prod['id']), None)
            if label:
                self.combo_prod.set(label)
                self.lbl_feedback.configure(text=f"✔ {prod['desc']}", text_color=theme.GREEN)
        else:
            self.bell()
            self.lbl_feedback.configure(text=f"✖ '{code}' non trovato", text_color=theme.RED)
        self.entry_scan.delete(0, "end")

    def confirm(self):
        pid = self.products.get(self.combo_prod.get())
        if not pid:
            messagebox.showwarning("Articolo", "Seleziona un articolo valido.", parent=self)
            return
        try:
            database.add_manual_movement(pid, self.entry_qty.get(), self.direction,
                                         self.entry_reason.get().strip())
        except ValueError:
            messagebox.showwarning("Quantità", "Inserisci una quantità valida.", parent=self)
            return
        self.parent.refresh()
        self.destroy()


class InventoryWindow(ctk.CTkFrame):
    """Giacenze articoli con valorizzazione e report scorta minima."""

    def __init__(self, parent, only_low=False):
        super().__init__(parent, fg_color=theme.BG)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))
        title = "Report Scorta Minima" if only_low else "Giacenze di Magazzino"
        ctk.CTkLabel(head, text=title, font=theme.font(22, bold=True),
                     text_color=theme.TEXT).pack(side="left")

        self.chk_low = ctk.CTkCheckBox(head, text="Solo sotto scorta", font=theme.font(11),
                                       command=self.refresh)
        if only_low:
            self.chk_low.select()
        self.chk_low.pack(side="right", padx=8)
        ctk.CTkButton(head, text="📗 Esporta CSV", width=110, fg_color=theme.SURFACE_2,
                      hover_color=theme.BORDER, command=self.export_csv).pack(side="right", padx=8)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 4))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        cols = ("Codice", "Descrizione", "UM", "Giacenza", "Scorta min", "Prezzo", "Valore")
        self.tree = ttk.Treeview(body, columns=cols, show="headings")
        widths = {"Codice": 100, "Descrizione": 320, "UM": 50, "Giacenza": 90,
                  "Scorta min": 90, "Prezzo": 100, "Valore": 110}
        for c in cols:
            self.tree.heading(c, text=c)
            anchor = "w" if c in ("Codice", "Descrizione", "UM") else "e"
            self.tree.column(c, width=widths.get(c, 90), anchor=anchor)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(body, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=20, pady=(4, 14))
        self.lbl_total = ctk.CTkLabel(foot, text="", font=theme.font(13, bold=True),
                                      text_color=theme.TEXT)
        self.lbl_total.pack(side="right")

        self.refresh()

    def refresh(self):
        for x in self.tree.get_children():
            self.tree.delete(x)
        rows = database.get_inventory_report(only_low_stock=bool(self.chk_low.get()))
        self._rows = rows
        total_value = 0.0
        low_count = 0
        for r in rows:
            # id, code, desc, um, stock, min, price, value, low
            total_value += r[7]
            tags = ()
            if r[8]:
                tags = ("red",)
                low_count += 1
            self.tree.insert("", "end", values=(
                r[1], r[2], r[3], f"{r[4]:g}", f"{r[5]:g}",
                theme.euro(r[6]), theme.euro(r[7])), tags=tags)
        theme.stripe(self.tree)
        self.lbl_total.configure(
            text=f"⚠ {low_count} sotto scorta      Valore magazzino: {theme.euro(total_value)}")

    def export_csv(self):
        if not getattr(self, "_rows", None):
            messagebox.showinfo("Export", "Nessun dato da esportare.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="giacenze.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        import csv
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Codice", "Descrizione", "UM", "Giacenza", "ScortaMin", "Prezzo", "Valore", "SottoScorta"])
            for r in self._rows:
                w.writerow([r[1], r[2], r[3], str(r[4]).replace(".", ","), str(r[5]).replace(".", ","),
                            str(r[6]).replace(".", ","), str(r[7]).replace(".", ","), "SI" if r[8] else ""])
        messagebox.showinfo("Export", f"Esportato:\n{path}")


class LastPricesWindow(ctk.CTkFrame):
    """Ultimo prezzo praticato per articolo (vendita e acquisto)."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.BG)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(head, text="Ultimi Prezzi", font=theme.font(22, bold=True),
                     text_color=theme.TEXT).pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        cols = ("Codice", "Descrizione", "Data", "Prezzo", "Tipo")
        self.tree = ttk.Treeview(body, columns=cols, show="headings")
        for c, w in zip(cols, (110, 360, 110, 110, 100)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="e" if c == "Prezzo" else "w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(body, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        for r in database.get_last_prices():
            tag = "green" if r[4] == "Vendita" else "red"
            self.tree.insert("", "end", values=(r[0], r[1], r[2], theme.euro(r[3]), r[4]),
                             tags=(tag,))
        theme.stripe(self.tree)
