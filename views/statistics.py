"""Statistiche (OBF, totale fatture, chi/cosa) e Registro IVA."""
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime
import database
from utils import theme

MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


def _years_available():
    """Anni presenti nei documenti (più l'anno corrente)."""
    conn = database.sqlite3.connect(database.DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT strftime('%Y', date) FROM documents WHERE date IS NOT NULL ORDER BY 1 DESC")
        years = [r[0] for r in cur.fetchall() if r[0]]
    except Exception:
        years = []
    conn.close()
    current = str(datetime.now().year)
    if current not in years:
        years.insert(0, current)
    return years


def _make_tree(parent, cols, widths, anchors=None):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    for i, c in enumerate(cols):
        tree.heading(c, text=c)
        anchor = (anchors or {}).get(c, "e" if i else "w")
        tree.column(c, width=widths[i], anchor=anchor)
    tree.grid(row=0, column=0, sticky="nsew")
    sb = ctk.CTkScrollbar(frame, command=tree.yview)
    sb.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=sb.set)
    return frame, tree


class StatisticsWindow(ctk.CTkFrame):
    def __init__(self, parent, start_tab=None):
        super().__init__(parent, fg_color=theme.BG)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(head, text="Statistiche", font=theme.font(22, bold=True),
                     text_color=theme.TEXT).pack(side="left")

        ctk.CTkLabel(head, text="Anno:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(24, 6))
        self.combo_year = ctk.CTkOptionMenu(head, values=_years_available(), width=90,
                                            command=lambda x: self.refresh())
        self.combo_year.pack(side="left")

        self.tabs = ctk.CTkTabview(self, fg_color=theme.SURFACE,
                                   segmented_button_selected_color=theme.ACCENT)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.tabs.add("Ordinato / Bollettato / Fatturato")
        self.tabs.add("Totale Fatture")
        self.tabs.add("Chi / Cosa")

        # --- TAB OBF ---
        t1 = self.tabs.tab("Ordinato / Bollettato / Fatturato")
        f1, self.tree_obf = _make_tree(t1, ("Mese", "Ordinato", "Bollettato", "Fatturato"),
                                       (160, 140, 140, 140))
        f1.pack(fill="both", expand=True, padx=8, pady=8)

        # --- TAB FATTURE ---
        t2 = self.tabs.tab("Totale Fatture")
        bar2 = ctk.CTkFrame(t2, fg_color="transparent")
        bar2.pack(fill="x", padx=8, pady=(8, 0))
        self.combo_ftype = ctk.CTkOptionMenu(bar2, values=["Vendite", "Acquisti"], width=110,
                                             command=lambda x: self.refresh())
        self.combo_ftype.pack(side="left")
        f2, self.tree_fatt = _make_tree(t2, ("Mese", "N. Fatture", "Imponibile", "IVA", "Totale"),
                                        (160, 90, 130, 130, 130))
        f2.pack(fill="both", expand=True, padx=8, pady=8)

        # --- TAB CHI/COSA ---
        t3 = self.tabs.tab("Chi / Cosa")
        t3.grid_columnconfigure((0, 1), weight=1, uniform="cc")
        t3.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(t3, text="👥 Top Clienti", font=theme.font(13, bold=True),
                     text_color=theme.TEXT).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(t3, text="📦 Top Articoli", font=theme.font(13, bold=True),
                     text_color=theme.TEXT).grid(row=0, column=1, sticky="w", padx=10, pady=(8, 2))
        fc, self.tree_clients = _make_tree(t3, ("Cliente", "N. Fatt.", "Totale"), (220, 70, 120))
        fc.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))
        fp, self.tree_products = _make_tree(t3, ("Codice", "Descrizione", "Qtà", "Importo"),
                                            (90, 220, 80, 110))
        fp.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))

        if start_tab == "fatture":
            self.tabs.set("Totale Fatture")
        elif start_tab == "chicosa":
            self.tabs.set("Chi / Cosa")

        self.refresh()

    def refresh(self):
        year = self.combo_year.get()

        # OBF
        for x in self.tree_obf.get_children():
            self.tree_obf.delete(x)
        data = database.get_stats_obf(year)
        tot = {'ordinato': 0.0, 'bollettato': 0.0, 'fatturato': 0.0}
        for m in range(1, 13):
            v = data[f"{m:02d}"]
            for k in tot:
                tot[k] += v[k]
            self.tree_obf.insert("", "end", values=(
                MESI[m - 1], theme.euro(v['ordinato']), theme.euro(v['bollettato']),
                theme.euro(v['fatturato'])))
        self.tree_obf.insert("", "end", values=(
            "TOTALE", theme.euro(tot['ordinato']), theme.euro(tot['bollettato']),
            theme.euro(tot['fatturato'])), tags=("green",))
        theme.stripe(self.tree_obf)

        # Totale fatture
        for x in self.tree_fatt.get_children():
            self.tree_fatt.delete(x)
        rows = database.get_invoice_totals(year, purchases=(self.combo_ftype.get() == "Acquisti"))
        tn = tv = tg = 0.0
        tc = 0
        by_month = {r[0]: r for r in rows}
        for m in range(1, 13):
            r = by_month.get(f"{m:02d}")
            if r:
                tc += r[1]; tn += r[2] or 0; tv += r[3] or 0; tg += r[4] or 0
                self.tree_fatt.insert("", "end", values=(
                    MESI[m - 1], r[1], theme.euro(r[2]), theme.euro(r[3]), theme.euro(r[4])))
            else:
                self.tree_fatt.insert("", "end", values=(MESI[m - 1], 0, "-", "-", "-"),
                                      tags=("dim",))
        self.tree_fatt.insert("", "end", values=(
            "TOTALE", tc, theme.euro(tn), theme.euro(tv), theme.euro(tg)), tags=("green",))
        theme.stripe(self.tree_fatt)

        # Chi / Cosa
        for x in self.tree_clients.get_children():
            self.tree_clients.delete(x)
        for r in database.get_top_clients(year):
            self.tree_clients.insert("", "end", values=(r[0], r[1], theme.euro(r[2])))
        theme.stripe(self.tree_clients)

        for x in self.tree_products.get_children():
            self.tree_products.delete(x)
        for r in database.get_top_products(year):
            self.tree_products.insert("", "end", values=(r[0], r[1], f"{r[2]:g}", theme.euro(r[3])))
        theme.stripe(self.tree_products)


class VatRegisterWindow(ctk.CTkFrame):
    """Registro IVA vendite/acquisti raggruppato per mese e aliquota."""

    def __init__(self, parent, purchases=False):
        super().__init__(parent, fg_color=theme.BG)
        self.purchases = purchases

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))
        title = "Registro IVA Acquisti" if purchases else "Registro IVA Vendite"
        ctk.CTkLabel(head, text=title, font=theme.font(22, bold=True),
                     text_color=theme.TEXT).pack(side="left")

        ctk.CTkLabel(head, text="Anno:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(24, 6))
        self.combo_year = ctk.CTkOptionMenu(head, values=_years_available(), width=90,
                                            command=lambda x: self.refresh())
        self.combo_year.pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        cols = ("Mese", "Aliquota", "Imponibile", "Imposta", "Totale")
        self.tree = ttk.Treeview(body, columns=cols, show="headings")
        for c, w in zip(cols, (160, 90, 140, 140, 140)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w" if c == "Mese" else "e")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(body, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        self.refresh()

    def refresh(self):
        for x in self.tree.get_children():
            self.tree.delete(x)
        rows = database.get_vat_register(self.combo_year.get(), purchases=self.purchases)
        tot_net = tot_vat = 0.0
        for r in rows:
            # mese, aliquota, imponibile, imposta
            month_name = MESI[int(r[0]) - 1] if r[0] else "-"
            tot_net += r[2] or 0
            tot_vat += r[3] or 0
            self.tree.insert("", "end", values=(
                month_name, f"{r[1]:g}%", theme.euro(r[2]), theme.euro(r[3]),
                theme.euro((r[2] or 0) + (r[3] or 0))))
        self.tree.insert("", "end", values=(
            "TOTALE", "", theme.euro(tot_net), theme.euro(tot_vat),
            theme.euro(tot_net + tot_vat)), tags=("green",))
        theme.stripe(self.tree)
