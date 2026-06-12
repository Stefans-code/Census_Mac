"""Import da CSV / Excel con wizard di mappatura colonne (stile Invoicex).

Uso:
    fields = [("code", "Codice", True), ("description", "Descrizione", False), ...]
    ImportWizard(parent, "Importa Articoli", fields, on_import=callback)
    # callback(rows: list[dict]) -> str  (messaggio di report)
"""
import csv
import os
import re
import unicodedata
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from utils import theme

# Sinonimi per l'auto-associazione delle colonne del file ai campi target
SYNONYMS = {
    'code':            ['codice', 'cod', 'code', 'sku', 'codice articolo', 'cod art', 'codart'],
    'barcode':         ['barcode', 'ean', 'ean13', 'codice a barre', 'cod barre', 'codbarre'],
    'description':     ['descrizione', 'desc', 'description', 'articolo', 'nome', 'denominazione'],
    'unit':            ['um', 'u m', 'unita', 'unita di misura', 'unit'],
    'price_base':      ['prezzo', 'prezzo vendita', 'prezzo di vendita', 'listino', 'price', 'prezzo base'],
    'cost_last':       ['costo', 'prezzo acquisto', "prezzo d'acquisto", 'cost', 'costo acquisto'],
    'vat_rate':        ['iva', 'aliquota', 'aliquota iva', 'vat', '% iva', 'iva %'],
    'stock_quantity':  ['giacenza', 'quantita', 'qta', 'stock', 'esistenza', 'disponibilita'],
    'min_stock':       ['scorta', 'scorta minima', 'scorta min', 'min stock'],
    'supplier_code':   ['codice fornitore', 'cod fornitore', 'cod forn'],
    'warehouse_location': ['posizione', 'ubicazione', 'posizione magazzino', 'scaffale'],
    'ragione_sociale': ['ragione sociale', 'denominazione', 'nome', 'cliente', 'fornitore', 'azienda', 'ditta'],
    'address':         ['indirizzo', 'via', 'address'],
    'cap':             ['cap', 'codice postale', 'zip'],
    'city':            ['citta', 'comune', 'localita', 'city'],
    'province':        ['provincia', 'prov', 'pr'],
    'phone':           ['telefono', 'tel', 'phone'],
    'mobile':          ['cellulare', 'cell', 'mobile'],
    'email':           ['email', 'e mail', 'mail'],
    'pec':             ['pec', 'posta certificata'],
    'vat_number':      ['partita iva', 'p iva', 'piva', 'vat number', 'p iva cf'],
    'tax_code':        ['codice fiscale', 'cod fiscale', 'cf', 'codfisc'],
    'sdi_code':        ['sdi', 'codice sdi', 'codice destinatario', 'codice univoco'],
    'type':            ['tipo', 'tipologia', 'type'],
    'qty':             ['qta', 'quantita', 'qty', 'q ta', 'pezzi'],
    'price':           ['prezzo', 'prezzo unitario', 'price', 'importo unitario'],
    'vat':             ['iva', 'aliquota', 'aliquota iva', '% iva'],
    'disc1':           ['sconto', 'sconto 1', 'sconto1', 'sc1', 'sc 1'],
    'disc2':           ['sconto 2', 'sconto2', 'sc2', 'sc 2'],
}

NESSUNA = "— nessuna —"


def _norm(s):
    """Normalizza un'intestazione per il confronto: minuscole, niente accenti/punteggiatura."""
    s = str(s or '').strip().lower()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()


def read_table(path):
    """Legge un file CSV o Excel. Ritorna (headers, rows) come liste di stringhe."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xlsx', '.xlsm', '.xls'):
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError("Per i file Excel serve il pacchetto 'openpyxl' (pip install openpyxl).")
        if ext == '.xls':
            raise RuntimeError("Il vecchio formato .xls non è supportato: salva il file come .xlsx.")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        data = []
        for row in ws.iter_rows(values_only=True):
            vals = ["" if v is None else str(v).strip() for v in row]
            if any(vals):
                data.append(vals)
        wb.close()
    else:
        # CSV: rileva il delimitatore (; , o tab) e l'encoding più comune
        raw = None
        for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
            try:
                with open(path, encoding=enc, newline='') as f:
                    raw = f.read()
                break
            except UnicodeDecodeError:
                continue
        if raw is None:
            raise RuntimeError("Impossibile leggere il file (encoding non riconosciuto).")
        sample = raw[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
        except csv.Error:
            class dialect:  # fallback: punto e virgola (standard italiano)
                delimiter = ';'
        data = []
        for row in csv.reader(raw.splitlines(), delimiter=dialect.delimiter):
            vals = [str(v).strip() for v in row]
            if any(vals):
                data.append(vals)

    if not data:
        raise RuntimeError("Il file è vuoto.")
    headers = [h if h else f"Colonna {i+1}" for i, h in enumerate(data[0])]
    width = len(headers)
    rows = [(r + [""] * width)[:width] for r in data[1:]]
    return headers, rows


def auto_match(field_key, headers):
    """Trova l'intestazione del file che meglio corrisponde al campo target."""
    return auto_match_all([field_key], headers).get(field_key)


def auto_match_all(field_keys, headers):
    """Associa più campi alle intestazioni, ognuna usata una sola volta.
    Priorità: match esatto > sinonimo contenuto nel titolo > titolo contenuto nel sinonimo."""
    normed = {h: _norm(h) for h in headers}
    result, used = {}, set()

    def run_pass(match_fn):
        for key in field_keys:
            if key in result:
                continue
            for syn in SYNONYMS.get(key, [key]):
                found = next((h for h in headers
                              if h not in used and match_fn(syn, normed[h])), None)
                if found:
                    result[key] = found
                    used.add(found)
                    break

    run_pass(lambda syn, n: n == syn)
    run_pass(lambda syn, n: syn in n)
    run_pass(lambda syn, n: len(n) >= 3 and n in syn)
    return result


PRODUCT_FIELDS = [
    ("code", "Codice", True),
    ("description", "Descrizione", False),
    ("barcode", "Barcode / EAN", False),
    ("unit", "Unità misura", False),
    ("price_base", "Prezzo vendita", False),
    ("cost_last", "Prezzo acquisto", False),
    ("vat_rate", "IVA %", False),
    ("stock_quantity", "Giacenza", False),
    ("min_stock", "Scorta minima", False),
    ("supplier_code", "Cod. fornitore", False),
    ("warehouse_location", "Posizione", False),
]

CONTACT_FIELDS = [
    ("ragione_sociale", "Ragione sociale", True),
    ("type", "Tipo (cliente/fornitore)", False),
    ("vat_number", "Partita IVA", False),
    ("tax_code", "Codice fiscale", False),
    ("address", "Indirizzo", False),
    ("cap", "CAP", False),
    ("city", "Città", False),
    ("province", "Provincia", False),
    ("phone", "Telefono", False),
    ("mobile", "Cellulare", False),
    ("email", "Email", False),
    ("pec", "PEC", False),
    ("sdi_code", "Codice SDI", False),
    ("code", "Codice esterno", False),
]


def _report(ins, upd, errors, what):
    msg = f"{what} inseriti: {ins}\nAggiornati: {upd}"
    if errors:
        msg += f"\n\nErrori ({len(errors)}):\n" + "\n".join(errors[:10])
        if len(errors) > 10:
            msg += f"\n... e altri {len(errors) - 10}"
    return msg


def open_products_import(parent, on_done=None):
    """Wizard import articoli (upsert per codice)."""
    import database

    def run(records):
        ins, upd, errors = database.import_products(records)
        if on_done:
            on_done()
        return _report(ins, upd, errors, "Articoli")

    ImportWizard(parent, "Importa Articoli da CSV / Excel", PRODUCT_FIELDS, run)


def open_contacts_import(parent, default_type='cliente', on_done=None):
    """Wizard import clienti/fornitori (upsert per P.IVA o ragione sociale)."""
    import database

    def run(records):
        ins, upd, errors = database.import_contacts(records, default_type)
        if on_done:
            on_done()
        return _report(ins, upd, errors, "Clienti/Fornitori")

    ImportWizard(parent, "Importa Clienti/Fornitori da CSV / Excel", CONTACT_FIELDS, run)


class ImportWizard(ctk.CTkToplevel):
    """Finestra di import: scegli file -> mappa colonne -> anteprima -> importa."""

    def __init__(self, parent, title, fields, on_import):
        super().__init__(parent)
        self.title(title)
        self.geometry("860x640")
        self.configure(fg_color=theme.BG)
        self.grab_set()
        self.fields = fields          # [(key, label, required), ...]
        self.on_import = on_import
        self.headers, self.rows = [], []

        ctk.CTkLabel(self, text=title, font=theme.font(18, bold=True),
                     text_color=theme.TEXT).pack(pady=(16, 6))

        # --- Scelta file ---
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20)
        ctk.CTkButton(bar, text="📂 Scegli file CSV / Excel...", width=200,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_H,
                      command=self.pick_file).pack(side="left")
        self.lbl_file = ctk.CTkLabel(bar, text="Nessun file selezionato", font=theme.font(11),
                                     text_color=theme.TEXT_DIM)
        self.lbl_file.pack(side="left", padx=12)

        # --- Mappatura colonne ---
        self.map_card = theme.card(self)
        self.map_card.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.map_card, text="Associa le colonne del file ai campi (• = obbligatorio)",
                     font=theme.font(11), text_color=theme.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.map_inner = ctk.CTkFrame(self.map_card, fg_color="transparent")
        self.map_inner.pack(fill="x", padx=12, pady=(0, 10))
        self.combos = {}

        # --- Anteprima ---
        theme.section_title(self, "Anteprima (prime 30 righe)").pack(anchor="w", padx=20)
        prev = ctk.CTkFrame(self, fg_color="transparent")
        prev.pack(fill="both", expand=True, padx=20, pady=(4, 8))
        prev.grid_columnconfigure(0, weight=1)
        prev.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(prev, columns=(), show="headings", height=8)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sbx = ctk.CTkScrollbar(prev, command=self.tree.xview, orientation="horizontal")
        sbx.grid(row=1, column=0, sticky="ew")
        sby = ctk.CTkScrollbar(prev, command=self.tree.yview)
        sby.grid(row=0, column=1, sticky="ns")
        self.tree.configure(xscrollcommand=sbx.set, yscrollcommand=sby.set)

        # --- Footer ---
        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=20, pady=(0, 16))
        self.btn_import = ctk.CTkButton(foot, text="⬇ IMPORTA", height=38, state="disabled",
                                        fg_color=theme.GREEN_D, hover_color=theme.darken(theme.GREEN_D),
                                        command=self.do_import)
        self.btn_import.pack(side="right")
        self.lbl_count = ctk.CTkLabel(foot, text="", font=theme.font(11), text_color=theme.TEXT_DIM)
        self.lbl_count.pack(side="left")

    def pick_file(self):
        path = filedialog.askopenfilename(
            parent=self, title="Scegli il file da importare",
            filetypes=[("CSV / Excel", "*.csv *.xlsx *.xlsm"), ("CSV", "*.csv"),
                       ("Excel", "*.xlsx *.xlsm"), ("Tutti i file", "*.*")])
        if not path:
            return
        try:
            self.headers, self.rows = read_table(path)
        except Exception as e:
            messagebox.showerror("Import", str(e), parent=self)
            return
        self.lbl_file.configure(text=f"{os.path.basename(path)}  ({len(self.rows)} righe)")
        self.lbl_count.configure(text=f"{len(self.rows)} righe pronte")
        self.build_mapping()
        self.build_preview()
        self.btn_import.configure(state="normal")

    def build_mapping(self):
        for w in self.map_inner.winfo_children():
            w.destroy()
        self.combos = {}
        options = [NESSUNA] + self.headers
        per_row = 3
        guesses = auto_match_all([k for k, _, _ in self.fields], self.headers)
        for i, (key, label, required) in enumerate(self.fields):
            cell = ctk.CTkFrame(self.map_inner, fg_color="transparent")
            cell.grid(row=i // per_row, column=i % per_row, padx=6, pady=4, sticky="w")
            mark = " •" if required else ""
            ctk.CTkLabel(cell, text=label + mark, width=120, anchor="e", font=theme.font(11),
                         text_color=theme.TEXT if required else theme.TEXT_DIM).pack(side="left", padx=(0, 6))
            cb = ctk.CTkComboBox(cell, values=options, width=150, state="readonly")
            cb.set(guesses.get(key) or NESSUNA)
            cb.pack(side="left")
            self.combos[key] = cb

    def build_preview(self):
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=self.headers)
        for h in self.headers:
            self.tree.heading(h, text=h)
            self.tree.column(h, width=110, anchor="w", stretch=False)
        for r in self.rows[:30]:
            self.tree.insert("", "end", values=r)
        theme.stripe(self.tree)

    def do_import(self):
        # Verifica campi obbligatori
        mapping = {k: cb.get() for k, cb in self.combos.items() if cb.get() != NESSUNA}
        missing = [label for key, label, req in self.fields if req and key not in mapping]
        if missing:
            messagebox.showwarning("Import", "Campi obbligatori non associati:\n• " + "\n• ".join(missing),
                                   parent=self)
            return
        idx = {k: self.headers.index(h) for k, h in mapping.items()}
        records = []
        for r in self.rows:
            rec = {k: r[i] for k, i in idx.items()}
            if any(str(v).strip() for v in rec.values()):
                records.append(rec)
        if not records:
            messagebox.showinfo("Import", "Nessuna riga da importare.", parent=self)
            return
        try:
            report = self.on_import(records)
        except Exception as e:
            messagebox.showerror("Import", f"Errore durante l'import:\n{e}", parent=self)
            return
        messagebox.showinfo("Import completato", report, parent=self)
        self.destroy()
