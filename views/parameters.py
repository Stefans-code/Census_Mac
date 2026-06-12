import customtkinter as ctk
from tkinter import ttk, messagebox, Toplevel
import database

# Re-using TabbedMasterDataEditor pattern but often customized
# We will create specific keys for these tables.

class VatRatesEditor(ctk.CTkFrame):
    def __init__(self, parent, table_name=None, title=None):
        super().__init__(parent)
        self.parent = parent
        self.title_text = title
        self.current_id = None
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Toolbar
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkButton(toolbar, text="Nuovo", command=self.clear_form, width=80).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="Elimina", command=self.delete_item, width=80, fg_color="red").pack(side="left", padx=2)
        
        # Tabs
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.tabs.add("Dati")
        self.tabs.add("Elenco")
        
        # Form
        t_dati = self.tabs.tab("Dati")
        self.entries = {}
        
        def row(lbl, key, r, c=0, w=200):
            ctk.CTkLabel(t_dati, text=lbl, anchor="e").grid(row=r, column=c, padx=5, pady=5, sticky="e")
            e = ctk.CTkEntry(t_dati, width=w)
            e.grid(row=r, column=c+1, padx=5, pady=5, sticky="w")
            self.entries[key] = e
            
        row("Codice", "code", 0, w=100)
        row("Perc. IVA %", "rate", 1, w=100)
        row("Descrizione", "description", 2, w=400)
        row("Natura", "nature", 3, w=400)
        row("Codice esterno", "external_code", 4, w=150)
        
        # Save Button
        ctk.CTkButton(t_dati, text="Salva", command=self.save, fg_color="green").grid(row=5, column=1, pady=20, sticky="w")
        
        # List
        t_list = self.tabs.tab("Elenco")
        cols = ("Codice", "Perc", "Descrizione")
        self.tree = ttk.Treeview(t_list, columns=cols, show="headings")
        self.tree.heading("Codice", text="Codice")
        self.tree.heading("Perc", text="%")
        self.tree.heading("Descrizione", text="Descrizione")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        self.refresh_list()
        
    def refresh_list(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        conn = database.sqlite3.connect(database.DB_NAME)
        curr = conn.cursor()
        curr.execute("SELECT id, code, rate, description FROM vat_rates")
        for r in curr.fetchall():
            self.tree.insert("", "end", values=(r[1], r[2], r[3]), tags=(str(r[0]),))
        conn.close()
            
    def save(self):
        data = {k: v.get() for k,v in self.entries.items()}
        try:
            conn = database.sqlite3.connect(database.DB_NAME)
            curr = conn.cursor()
            if self.current_id:
                curr.execute("UPDATE vat_rates SET code=?, rate=?, description=?, nature=?, external_code=? WHERE id=?", 
                             (data['code'], data['rate'], data['description'], data['nature'], data['external_code'], self.current_id))
            else:
                curr.execute("INSERT INTO vat_rates (code, rate, description, nature, external_code) VALUES (?,?,?,?,?)",
                             (data['code'], data['rate'], data['description'], data['nature'], data['external_code']))
            conn.commit()
            conn.close()
            messagebox.showinfo("Info", "Salvato")
            self.refresh_list()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            
    def on_double_click(self, e):
        sel = self.tree.selection()
        if sel:
            self.current_id = self.tree.item(sel[0])['tags'][0]
            self.load_item(self.current_id)
            self.tabs.set("Dati")
            
    def load_item(self, iid):
        conn = database.sqlite3.connect(database.DB_NAME)
        curr = conn.cursor()
        curr.execute("SELECT * FROM vat_rates WHERE id=?", (iid,))
        r = curr.fetchone() # returns tuple (id, code, desc, rate, nature, ext) or similar order
        # Need to map logic if row_factory not set, but let's assume standard order or use keys if Row
        # DB schema: id, code, description, rate, nature, external_code
        if r:
            # Check dictionary vs tuple
             # Schema: id(0), code(1), description(2), rate(3), nature(4), external_code(5)
             # Wait, schema creation order: code, description, rate
             # Updated migration: nature, external_code appended
             # So indices: 0:id, 1:code, 2:description, 3:rate, 4:nature, 5:external_code
             pass
        conn.row_factory = database.sqlite3.Row
        curr = conn.cursor()
        curr.execute("SELECT * FROM vat_rates WHERE id=?", (iid,))
        r = curr.fetchone()
        conn.close()
        
        if r:
            self.entries['code'].delete(0,"end"); self.entries['code'].insert(0, r['code'] or "")
            self.entries['rate'].delete(0,"end"); self.entries['rate'].insert(0, str(r['rate'] or 0))
            self.entries['description'].delete(0,"end"); self.entries['description'].insert(0, r['description'] or "")
            self.entries['nature'].delete(0,"end"); self.entries['nature'].insert(0, r['nature'] or "")
            self.entries['external_code'].delete(0,"end"); self.entries['external_code'].insert(0, r['external_code'] or "")

    def clear_form(self):
        self.current_id = None
        for e in self.entries.values(): e.delete(0, "end")
        self.tabs.set("Dati")
        
    def delete_item(self):
        if not self.current_id: return
        if messagebox.askyesno("Confirm", "Delete"):
            conn = database.sqlite3.connect(database.DB_NAME)
            conn.execute("DELETE FROM vat_rates WHERE id=?", (self.current_id,))
            conn.commit()
            conn.close()
            self.refresh_list()
            self.clear_form()

# --- BANKS ---
class BanksEditor(ctk.CTkFrame):
    def __init__(self, parent, table_name=None, title=None):
        super().__init__(parent)
        self.parent = parent
        
        # Simple list + form on top
        self.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=10)
        
        self.entries = {}
        ctk.CTkLabel(top, text="ABI").pack(side="left")
        self.entries['abi'] = ctk.CTkEntry(top, width=80); self.entries['abi'].pack(side="left", padx=5)
        
        ctk.CTkLabel(top, text="Nome Banca").pack(side="left")
        self.entries['name'] = ctk.CTkEntry(top, width=300); self.entries['name'].pack(side="left", padx=5)
        
        ctk.CTkButton(top, text="Aggiungi", command=self.add).pack(side="left", padx=10)
        ctk.CTkButton(top, text="Elimina", fg_color="red", command=self.delete_item).pack(side="right", padx=10)
        
        self.tree = ttk.Treeview(self, columns=("ABI", "Nome"), show="headings")
        self.tree.heading("ABI", text="ABI")
        self.tree.heading("Nome", text="Nome Banca")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh()
        
    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, abi, name FROM banks ORDER BY name")
        for r in cur.fetchall():
            self.tree.insert("", "end", values=(r[1], r[2]), tags=(str(r[0]),))
        conn.close()
            
    def add(self):
        abi = self.entries['abi'].get()
        name = self.entries['name'].get()
        if not name: return
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.execute("INSERT INTO banks (abi, name) VALUES (?,?)", (abi, name))
        conn.commit()
        conn.close()
        self.entries['abi'].delete(0,"end"); self.entries['name'].delete(0,"end")
        self.refresh()
        
    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.execute("DELETE FROM banks WHERE id=?", (iid,))
        conn.commit()
        conn.close()
        self.refresh()

# --- COMPANY ACCOUNTS ---
class CompanyAccountsEditor(ctk.CTkFrame):
    def __init__(self, parent, table_name=None, title=None):
        super().__init__(parent)
        self.current_id = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Nuovo", command=self.clear, width=80).pack(side="left")
        ctk.CTkButton(toolbar, text="Elimina", command=self.delete, width=80, fg_color="red").pack(side="left", padx=5)
        
        f = ctk.CTkFrame(self)
        f.grid(row=1, column=0, fill="x", padx=10, pady=10)
        
        self.entries = {}
        def row(lbl, key, r, c, w=200):
            ctk.CTkLabel(f, text=lbl, anchor="e").grid(row=r, column=c, padx=5, pady=5, sticky="e")
            e = ctk.CTkEntry(f, width=w)
            e.grid(row=r, column=c+1, padx=5, pady=5, sticky="w")
            self.entries[key] = e
            
        row("IBAN", "iban", 0, 0, 300)
        row("ABI", "abi", 1, 0, 80)
        row("CAB", "cab", 2, 0, 80)
        row("Numero Conto", "account_number", 3, 0, 150)
        
        ctk.CTkLabel(f, text="Note").grid(row=4, column=0)
        self.entries['notes'] = ctk.CTkEntry(f, width=300)
        self.entries['notes'].grid(row=4, column=1)
        
        ctk.CTkButton(f, text="Salva", command=self.save, fg_color="green").grid(row=5, column=1, pady=10)
        
        self.tree = ttk.Treeview(self, columns=("IBAN", "Banca", "Conto"), show="headings")
        self.tree.heading("IBAN", text="IBAN")
        self.tree.heading("Banca", text="ABI/CAB")
        self.tree.heading("Conto", text="Conto")
        self.tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.tree.bind("<Double-1>", self.load)
        
        self.refresh()
        
    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM company_accounts")
        for r in cur.fetchall():
            # r: 0:id, 1:iban, 2:abi, 3:cab, 4:acc, 5:notes
            self.tree.insert("", "end", values=(r[1], f"{r[2]}/{r[3]}", r[4]), tags=(str(r[0]),))
        conn.close()
        
    def save(self):
        d = {k: v.get() for k,v in self.entries.items()}
        conn = database.sqlite3.connect(database.DB_NAME)
        if self.current_id:
             conn.execute("UPDATE company_accounts SET iban=?, abi=?, cab=?, account_number=?, notes=? WHERE id=?", 
                          (d['iban'], d['abi'], d['cab'], d['account_number'], d['notes'], self.current_id))
        else:
            conn.execute("INSERT INTO company_accounts (iban, abi, cab, account_number, notes) VALUES (?,?,?,?,?)",
                         (d['iban'], d['abi'], d['cab'], d['account_number'], d['notes']))
        conn.commit(); conn.close()
        self.refresh(); self.clear()

    def load(self, e):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        self.current_id = iid
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.row_factory = database.sqlite3.Row
        r = conn.execute("SELECT * FROM company_accounts WHERE id=?",(iid,)).fetchone()
        conn.close()
        if r:
            self.entries['iban'].delete(0,"end"); self.entries['iban'].insert(0, r['iban'] or "")
            self.entries['abi'].delete(0,"end"); self.entries['abi'].insert(0, r['abi'] or "")
            self.entries['cab'].delete(0,"end"); self.entries['cab'].insert(0, r['cab'] or "")
            self.entries['account_number'].delete(0,"end"); self.entries['account_number'].insert(0, r['account_number'] or "")
            self.entries['notes'].delete(0,"end"); self.entries['notes'].insert(0, r['notes'] or "")

    def clear(self):
        self.current_id = None
        for e in self.entries.values(): e.delete(0,"end")
        
    def delete(self):
        if self.current_id and messagebox.askyesno("Confirm", "Delete?"):
            conn = database.sqlite3.connect(database.DB_NAME)
            conn.execute("DELETE FROM company_accounts WHERE id=?", (self.current_id,))
            conn.commit(); conn.close()
            self.refresh(); self.clear()

# --- PRICE LISTS ---
class PriceListsEditor(ctk.CTkFrame):
    def __init__(self, parent, table_name=None, title=None):
        super().__init__(parent)
        # Simplified for brevity, similar structure
        self.current_id = None
        
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.pack(fill="x")
        ctk.CTkButton(toolbar, text="Nuovo", command=self.clear).pack(side="left")
        ctk.CTkButton(toolbar, text="Elimina", command=self.delete, fg_color="red").pack(side="left")
        
        f = ctk.CTkFrame(self); f.pack(fill="x", padx=10, pady=10)
        self.entries = {}
        
        ctk.CTkLabel(f, text="Codice").grid(row=0,column=0)
        self.entries['code'] = ctk.CTkEntry(f); self.entries['code'].grid(row=0, column=1)
        
        ctk.CTkLabel(f, text="Descrizione").grid(row=1,column=0)
        self.entries['description'] = ctk.CTkEntry(f, width=300); self.entries['description'].grid(row=1, column=1)
        
        self.entries['vat_included'] = ctk.CTkCheckBox(f, text="IVA Inclusa")
        self.entries['vat_included'].grid(row=2, column=1, sticky="w")
        
        ctk.CTkLabel(f, text="Ricarico %").grid(row=3, column=0)
        self.entries['markup'] = ctk.CTkEntry(f, width=50); self.entries['markup'].grid(row=3, column=1, sticky="w")
        
        ctk.CTkButton(f, text="Salva", command=self.save, fg_color="green").grid(row=4, column=1)
        
        self.tree = ttk.Treeview(self, columns=("Code", "Desc"), show="headings")
        self.tree.heading("Code", text="Codice")
        self.tree.heading("Desc", text="Descrizione")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.load)
        
        self.refresh()
        
    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        conn = database.sqlite3.connect(database.DB_NAME)
        for r in conn.execute("SELECT id, code, description FROM price_lists"):
            self.tree.insert("", "end", values=(r[1], r[2]), tags=(str(r[0]),))
        conn.close()
        
    def save(self):
        d = {k: v.get() for k,v in self.entries.items()}
        vic = 1 if d['vat_included'] else 0
        conn = database.sqlite3.connect(database.DB_NAME)
        if self.current_id:
             conn.execute("UPDATE price_lists SET code=?, description=?, vat_included=?, markup=? WHERE id=?", 
                          (d['code'], d['description'], vic, d['markup'], self.current_id))
        else:
             conn.execute("INSERT INTO price_lists (code, description, vat_included, markup) VALUES (?,?,?,?)",
                          (d['code'], d['description'], vic, d['markup']))
        conn.commit(); conn.close()
        self.refresh(); self.clear()
        
    def load(self, e):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        self.current_id = iid
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.row_factory = database.sqlite3.Row
        r = conn.execute("SELECT * FROM price_lists WHERE id=?", (iid,)).fetchone()
        conn.close()
        if r:
             self.entries['code'].delete(0,"end"); self.entries['code'].insert(0, r['code'] or "")
             self.entries['description'].delete(0,"end"); self.entries['description'].insert(0, r['description'] or "")
             self.entries['markup'].delete(0,"end"); self.entries['markup'].insert(0, str(r['markup'] or 0))
             if r['vat_included']: self.entries['vat_included'].select()
             else: self.entries['vat_included'].deselect()

    def clear(self):
        self.current_id = None; 
        for k, v in self.entries.items(): 
            if isinstance(v, ctk.CTkEntry): v.delete(0,"end")
            else: v.deselect()
            
    def delete(self):
        if self.current_id:
             conn = database.sqlite3.connect(database.DB_NAME)
             conn.execute("DELETE FROM price_lists WHERE id=?", (self.current_id,))
             conn.commit(); conn.close()
             self.refresh(); self.clear()

# --- PAYMENTS ---
class PaymentsEditor(ctk.CTkFrame):
    def __init__(self, parent, table_name=None, title=None):
        super().__init__(parent)
        self.current_id = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Nuovo", command=self.clear).pack(side="left")
        ctk.CTkButton(toolbar, text="Elimina", command=self.delete, fg_color="red").pack(side="left", padx=5)
        
        self.tabs = ctk.CTkTabview(self); self.tabs.grid(row=2, column=0, sticky="nsew")
        self.tabs.add("Dati"); self.tabs.add("Elenco")
        
        t_dati = self.tabs.tab("Dati")
        self.entries = {}
        
        # Simple form matching fields
        def row(lbl, key, r, c):
            ctk.CTkLabel(t_dati, text=lbl).grid(row=r, column=c, padx=5, pady=5, sticky="e")
            e = ctk.CTkEntry(t_dati, width=200)
            e.grid(row=r, column=c+1, padx=5, pady=5, sticky="w")
            self.entries[key] = e
            
        row("Codice", "name", 0, 0) # Mapping 'name' to 'Codice'
        row("Descrizione", "description", 1, 0)
        row("Cod. FE (MP05...)", "fe_code", 2, 0)
        
        self.entries['is_riba'] = ctk.CTkCheckBox(t_dati, text="Ri.Ba.")
        self.entries['is_riba'].grid(row=3, column=1, sticky="w")
        
        self.entries['is_bank_needed'] = ctk.CTkCheckBox(t_dati, text="Banca Necessaria")
        self.entries['is_bank_needed'].grid(row=4, column=1, sticky="w")
        
        ctk.CTkButton(t_dati, text="Salva", command=self.save, fg_color="green").grid(row=10, column=1, pady=20)
        
        t_list = self.tabs.tab("Elenco")
        self.tree = ttk.Treeview(t_list, columns=("Cod", "Desc"), show="headings")
        self.tree.heading("Cod", text="Codice")
        self.tree.heading("Desc", text="Descrizione")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.load)
        
        self.refresh()

    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        conn = database.sqlite3.connect(database.DB_NAME)
        for r in conn.execute("SELECT id, name, description FROM payment_terms"):
             self.tree.insert("", "end", values=(r[1], r[2]), tags=(str(r[0]),))
        conn.close()

    def save(self):
        d = {k: v.get() for k,v in self.entries.items()}
        riba = 1 if d['is_riba'] else 0
        bnk = 1 if d['is_bank_needed'] else 0
        conn = database.sqlite3.connect(database.DB_NAME)
        if self.current_id:
             conn.execute("UPDATE payment_terms SET name=?, description=?, fe_code=?, is_riba=?, is_bank_needed=? WHERE id=?", 
                          (d['name'], d['description'], d['fe_code'], riba, bnk, self.current_id))
        else:
             conn.execute("INSERT INTO payment_terms (name, description, fe_code, is_riba, is_bank_needed) VALUES (?,?,?,?,?)",
                          (d['name'], d['description'], d['fe_code'], riba, bnk))
        conn.commit(); conn.close()
        self.refresh(); self.clear()

    def load(self, e):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        self.current_id = iid
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.row_factory = database.sqlite3.Row
        r = conn.execute("SELECT * FROM payment_terms WHERE id=?", (iid,)).fetchone()
        conn.close()
        if r:
             self.entries['name'].delete(0,"end"); self.entries['name'].insert(0, r['name'] or "")
             self.entries['description'].delete(0,"end"); self.entries['description'].insert(0, r['description'] or "")
             self.entries['fe_code'].delete(0,"end"); self.entries['fe_code'].insert(0, r['fe_code'] or "")
             if r['is_riba']: self.entries['is_riba'].select()
             else: self.entries['is_riba'].deselect()
             if r['is_bank_needed']: self.entries['is_bank_needed'].select()
             else: self.entries['is_bank_needed'].deselect()
             self.tabs.set("Dati")

    def clear(self):
        self.current_id = None
        for k, v in self.entries.items():
             if isinstance(v, ctk.CTkEntry): v.delete(0,"end")
             else: v.deselect()
        self.tabs.set("Dati")
        
    def delete(self):
        if self.current_id:
             conn = database.sqlite3.connect(database.DB_NAME)
             conn.execute("DELETE FROM payment_terms WHERE id=?", (self.current_id,))
             conn.commit(); conn.close()
             self.refresh(); self.clear()

# --- CARRIERS (VETTORI) ---
class CarriersEditor(ctk.CTkFrame):
    def __init__(self, parent, table_name=None, title=None):
        super().__init__(parent)
        self.current_id = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Nuovo", command=self.clear).pack(side="left")
        ctk.CTkButton(toolbar, text="Elimina", command=self.delete, fg_color="red").pack(side="left", padx=5)
        
        self.tabs = ctk.CTkTabview(self); self.tabs.grid(row=2, column=0, sticky="nsew")
        self.tabs.add("Dati"); self.tabs.add("Elenco")
        
        t_dati = self.tabs.tab("Dati")
        self.entries = {}
        
        # Form
        ctk.CTkLabel(t_dati, text="Codice").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entries['code'] = ctk.CTkEntry(t_dati, width=100); self.entries['code'].grid(row=0, column=1, sticky="w", padx=5)
        
        ctk.CTkLabel(t_dati, text="Denominazione").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entries['name'] = ctk.CTkEntry(t_dati, width=300); self.entries['name'].grid(row=1, column=1, sticky="w", padx=5)
        
        # P.IVA Group
        f_piva = ctk.CTkFrame(t_dati, fg_color="transparent")
        f_piva.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_piva, text="Partita IVA (Paese").pack(side="left")
        self.entries['vat_country'] = ctk.CTkEntry(f_piva, width=40); self.entries['vat_country'].pack(side="left", padx=2)
        ctk.CTkLabel(f_piva, text=")").pack(side="left")
        self.entries['vat_number'] = ctk.CTkEntry(f_piva, width=200); self.entries['vat_number'].pack(side="left", padx=5)
        
        # Person Group
        ctk.CTkLabel(t_dati, text="Persona fisica").grid(row=3, column=0, sticky="w", padx=5, pady=10)
        
        ctk.CTkLabel(t_dati, text="Nome").grid(row=4, column=0, sticky="e", padx=5)
        self.entries['first_name'] = ctk.CTkEntry(t_dati, width=200); self.entries['first_name'].grid(row=4, column=1, sticky="w", padx=5)
        
        ctk.CTkLabel(t_dati, text="Cognome").grid(row=5, column=0, sticky="e", padx=5)
        self.entries['last_name'] = ctk.CTkEntry(t_dati, width=200); self.entries['last_name'].grid(row=5, column=1, sticky="w", padx=5)
        
        ctk.CTkLabel(t_dati, text="Codice fiscale").grid(row=6, column=0, sticky="e", padx=5)
        self.entries['tax_code'] = ctk.CTkEntry(t_dati, width=200); self.entries['tax_code'].grid(row=6, column=1, sticky="w", padx=5)
        
        ctk.CTkButton(t_dati, text="Salva", command=self.save, fg_color="green").grid(row=7, column=1, pady=20, sticky="w")
        
        # List
        t_list = self.tabs.tab("Elenco")
        self.tree = ttk.Treeview(t_list, columns=("Cod", "Denom", "PIVA"), show="headings")
        self.tree.heading("Cod", text="Codice")
        self.tree.heading("Denom", text="Denominazione")
        self.tree.heading("PIVA", text="Partita IVA")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.load)
        
        self.refresh()
        
    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        conn = database.sqlite3.connect(database.DB_NAME)
        # Select standard fields + custom
        try:
            # Check cols exists or handle error if migration failed (unlikely)
            for r in conn.execute("SELECT id, code, name, vat_country, vat_number FROM vettori"):
                piva = f"{r[3] or ''}{r[4] or ''}"
                self.tree.insert("", "end", values=(r[1], r[2], piva), tags=(str(r[0]),))
        except: pass
        conn.close()

    def save(self):
        d = {k: v.get() for k,v in self.entries.items()}
        conn = database.sqlite3.connect(database.DB_NAME)
        if self.current_id:
             conn.execute("UPDATE vettori SET code=?, name=?, vat_country=?, vat_number=?, first_name=?, last_name=?, tax_code=? WHERE id=?", 
                          (d['code'], d['name'], d['vat_country'], d['vat_number'], d['first_name'], d['last_name'], d['tax_code'], self.current_id))
        else:
             conn.execute("INSERT INTO vettori (code, name, vat_country, vat_number, first_name, last_name, tax_code) VALUES (?,?,?,?,?,?,?)",
                          (d['code'], d['name'], d['vat_country'], d['vat_number'], d['first_name'], d['last_name'], d['tax_code']))
        conn.commit(); conn.close()
        self.refresh(); self.clear()

    def load(self, e):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        self.current_id = iid
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.row_factory = database.sqlite3.Row
        r = conn.execute("SELECT * FROM vettori WHERE id=?", (iid,)).fetchone()
        conn.close()
        if r:
            self.entries['code'].delete(0,"end"); self.entries['code'].insert(0, r['code'] or "")
            self.entries['name'].delete(0,"end"); self.entries['name'].insert(0, r['name'] or "")
            self.entries['vat_country'].delete(0,"end"); self.entries['vat_country'].insert(0, r['vat_country'] or "")
            self.entries['vat_number'].delete(0,"end"); self.entries['vat_number'].insert(0, r['vat_number'] or "")
            self.entries['first_name'].delete(0,"end"); self.entries['first_name'].insert(0, r['first_name'] or "")
            self.entries['last_name'].delete(0,"end"); self.entries['last_name'].insert(0, r['last_name'] or "")
            self.entries['tax_code'].delete(0,"end"); self.entries['tax_code'].insert(0, r['tax_code'] or "")
            self.tabs.set("Dati")

    def clear(self):
        self.current_id = None
        for e in self.entries.values(): e.delete(0,"end")
        self.tabs.set("Dati")
        
    def delete(self):
        if self.current_id:
             conn = database.sqlite3.connect(database.DB_NAME)
             conn.execute("DELETE FROM vettori WHERE id=?", (self.current_id,))
             conn.commit(); conn.close()
             self.refresh(); self.clear()

# --- CITIES (COMUNI) ---
class CitiesEditor(ctk.CTkFrame):
    def __init__(self, parent, table_name=None, title=None):
        super().__init__(parent)
        self.current_id = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Nuovo", command=self.clear).pack(side="left")
        ctk.CTkButton(toolbar, text="Elimina", command=self.delete, fg_color="red").pack(side="left", padx=5)
        
        self.tabs = ctk.CTkTabview(self); self.tabs.grid(row=2, column=0, sticky="nsew")
        self.tabs.add("Dati"); self.tabs.add("Elenco")
        
        t_dati = self.tabs.tab("Dati")
        self.entries = {}
        
        ctk.CTkLabel(t_dati, text="Codice").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entries['code'] = ctk.CTkEntry(t_dati, width=100); self.entries['code'].grid(row=0, column=1, sticky="w", padx=5)
        
        ctk.CTkLabel(t_dati, text="Comune").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entries['name'] = ctk.CTkEntry(t_dati, width=300); self.entries['name'].grid(row=1, column=1, sticky="w", padx=5)
        
        ctk.CTkLabel(t_dati, text="Provincia").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        # Using entry for now as we don't have a province table
        self.entries['province'] = ctk.CTkComboBox(t_dati, width=100, values=["MI", "RM", "NA", "TO", "PD", "VR", "VI", "TV"]) 
        self.entries['province'].grid(row=2, column=1, sticky="w", padx=5)
        
        ctk.CTkLabel(t_dati, text="Regione").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entries['region'] = ctk.CTkComboBox(t_dati, width=200, values=["Lombardia", "Lazio", "Campania", "Piemonte", "Veneto"])
        self.entries['region'].grid(row=3, column=1, sticky="w", padx=5)
        
        ctk.CTkButton(t_dati, text="Salva", command=self.save, fg_color="green").grid(row=4, column=1, pady=20, sticky="w")
        
        t_list = self.tabs.tab("Elenco")
        self.tree = ttk.Treeview(t_list, columns=("Cod", "Comune", "Prov"), show="headings")
        self.tree.heading("Cod", text="Codice")
        self.tree.heading("Comune", text="Comune")
        self.tree.heading("Prov", text="Pr")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.load)
        
        self.refresh()
        
    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        conn = database.sqlite3.connect(database.DB_NAME)
        for r in conn.execute("SELECT id, code, name, province FROM cities"):
            self.tree.insert("", "end", values=(r[1], r[2], r[3]), tags=(str(r[0]),))
        conn.close()

    def save(self):
        d = {k: v.get() for k,v in self.entries.items()}
        conn = database.sqlite3.connect(database.DB_NAME)
        if self.current_id:
             conn.execute("UPDATE cities SET code=?, name=?, province=?, region=? WHERE id=?", 
                          (d['code'], d['name'], d['province'], d['region'], self.current_id))
        else:
             conn.execute("INSERT INTO cities (code, name, province, region) VALUES (?,?,?,?)",
                          (d['code'], d['name'], d['province'], d['region']))
        conn.commit(); conn.close()
        self.refresh(); self.clear()

    def load(self, e):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        self.current_id = iid
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.row_factory = database.sqlite3.Row
        r = conn.execute("SELECT * FROM cities WHERE id=?", (iid,)).fetchone()
        conn.close()
        if r:
            self.entries['code'].delete(0,"end"); self.entries['code'].insert(0, r['code'] or "")
            self.entries['name'].delete(0,"end"); self.entries['name'].insert(0, r['name'] or "")
            self.entries['province'].set(r['province'] or "")
            self.entries['region'].set(r['region'] or "")
            self.tabs.set("Dati")

    def clear(self):
        self.current_id = None
        for k,v in self.entries.items():
            if isinstance(v, ctk.CTkEntry): v.delete(0,"end")
            else: v.set("")
        self.tabs.set("Dati")
        
    def delete(self):
        if self.current_id:
             conn = database.sqlite3.connect(database.DB_NAME)
             conn.execute("DELETE FROM cities WHERE id=?", (self.current_id,))
             conn.commit(); conn.close()
             self.refresh(); self.clear()
