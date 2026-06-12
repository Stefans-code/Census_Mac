import customtkinter as ctk
from tkinter import ttk, messagebox
import database

class ContactsWindow(ctk.CTkFrame):
    def __init__(self, parent, sub_type=None):
        super().__init__(parent)
        self.parent = parent
        self.sub_type = sub_type # 'cliente', 'fornitore', or None
        self.current_id = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # --- 1. TOOLBAR ---
        toolbar = ctk.CTkFrame(self, height=40, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Icons/Buttons
        ctk.CTkButton(toolbar, text="📄 Nuovo", width=80, fg_color="#3498db", command=self.new_contact).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="❌ Elimina", width=80, fg_color="#e74c3c", command=self.delete_contact).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="🔍 Trova", width=80, fg_color="#f39c12", command=lambda: self.tabs.set("Elenco")).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="📥 Importa", width=90, fg_color="#16a085", command=self.import_dialog).pack(side="left", padx=2)

        # Search Bar
        ctk.CTkLabel(toolbar, text="Cerca:").pack(side="left", padx=(20, 5))
        self.ent_search = ctk.CTkEntry(toolbar, width=200)
        self.ent_search.pack(side="left", padx=5)
        self.ent_search.bind("<Return>", lambda e: self.refresh_list())
        ctk.CTkButton(toolbar, text="Cerca", width=60, command=self.refresh_list).pack(side="left", padx=2)

        # --- 2. MAIN TABS (Dati / Elenco) ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.tabs.add("Dati")
        self.tabs.add("Elenco")
        
        # --- TAB ELENCO ---
        t_elenco = self.tabs.tab("Elenco")
        t_elenco.grid_columnconfigure(0, weight=1)
        t_elenco.grid_rowconfigure(0, weight=1)
        
        cols = ("ID", "Ragione Sociale", "Tipo", "Città", "Telefono")
        self.tree = ttk.Treeview(t_elenco, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
        
        self.tree.column("ID", width=50)
        self.tree.column("Ragione Sociale", width=300)
        self.tree.column("Tipo", width=100)
        self.tree.column("Città", width=150)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(t_elenco, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # --- TAB DATI ---
        t_dati = self.tabs.tab("Dati")
        # Scrollable frame for form? Or just grid.
        # Screenshot shows lots of fields.
        
        self.entries = {}
        self.lookups = self.load_lookups()
        
        # Form Container
        self.form = ctk.CTkFrame(t_dati, fg_color="transparent")
        self.form.pack(fill="both", expand=True, padx=10, pady=10)
        
        # -- Row 1: Codice, Tipo, Categoria, Cod. Est, Obsoleto --
        r1 = ctk.CTkFrame(self.form, fg_color="transparent")
        r1.pack(fill="x", pady=2)
        
        self.lbl_id = ctk.CTkLabel(r1, text="Codice AUTO")
        self.lbl_id.pack(side="left", padx=5)
        
        ctk.CTkLabel(r1, text="Tipo").pack(side="left", padx=5)
        self.entries['type'] = ctk.CTkComboBox(r1, values=["cliente", "fornitore", "both"], width=100)
        self.entries['type'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r1, text="Categoria").pack(side="left", padx=5)
        self.entries['category_id'] = ctk.CTkComboBox(r1, values=list(self.lookups['cats'].keys()), width=150)
        self.entries['category_id'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r1, text="Codice esterno").pack(side="left", padx=5)
        self.entries['external_code'] = ctk.CTkEntry(r1, width=100)
        self.entries['external_code'].pack(side="left", padx=5)
        
        self.entries['is_obsolete'] = ctk.CTkCheckBox(r1, text="Obsoleto ?")
        self.entries['is_obsolete'].pack(side="right", padx=5)
        
        # -- Row 2: Ragione Sociale --
        r2 = ctk.CTkFrame(self.form, fg_color="transparent")
        r2.pack(fill="x", pady=2)
        ctk.CTkLabel(r2, text="Ragione sociale", width=100, anchor="e").pack(side="left", padx=5)
        self.entries['ragione_sociale'] = ctk.CTkEntry(r2)
        self.entries['ragione_sociale'].pack(side="left", fill="x", expand=True, padx=5)
        
        # -- Row 3: Persona Fisica --
        r3 = ctk.CTkFrame(self.form, fg_color="transparent")
        r3.pack(fill="x", pady=2)
        
        self.entries['is_person'] = ctk.CTkCheckBox(r3, text="Persona fisica", width=100)
        self.entries['is_person'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r3, text="Titolo").pack(side="left", padx=5)
        self.entries['title'] = ctk.CTkEntry(r3, width=80)
        self.entries['title'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r3, text="Cognome").pack(side="left", padx=5)
        self.entries['cognome'] = ctk.CTkEntry(r3, width=200)
        self.entries['cognome'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r3, text="Nome").pack(side="left", padx=5)
        self.entries['nome'] = ctk.CTkEntry(r3, width=200)
        self.entries['nome'].pack(side="left", padx=5)
        
        # -- Row 4: P.IVA / CF --
        r4 = ctk.CTkFrame(self.form, fg_color="transparent")
        r4.pack(fill="x", pady=2)
        
        ctk.CTkLabel(r4, text="Partita IVA", width=100, anchor="e").pack(side="left", padx=5)
        self.entries['vat_number'] = ctk.CTkEntry(r4, width=150)
        self.entries['vat_number'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r4, text="Codice Fiscale").pack(side="left", padx=5)
        self.entries['tax_code'] = ctk.CTkEntry(r4, width=150)
        self.entries['tax_code'].pack(side="left", padx=5)
        
        ctk.CTkButton(r4, text="Verifica dati", width=100, fg_color="gray").pack(side="left", padx=20)

        # -- SUB TABS --
        self.subtabs = ctk.CTkTabview(self.form, height=300)
        self.subtabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        t_addr = self.subtabs.add("Indirizzo")
        t_cont = self.subtabs.add("Contatti")
        t_comm = self.subtabs.add("Contabili")
        t_fatt = self.subtabs.add("Fattura Elettronica")
        t_note = self.subtabs.add("Note e Opzioni")
        
        # --- Indirizzo ---
        def add(p, lbl, key, r, c, w=200):
            ctk.CTkLabel(p, text=lbl, anchor="e").grid(row=r, column=c, padx=5, pady=5, sticky="e")
            entry = ctk.CTkEntry(p, width=w)
            entry.grid(row=r, column=c+1, padx=5, pady=5, sticky="w")
            self.entries[key] = entry
        
        add(t_addr, "Via / Piazza / Località", "address", 0, 0, w=400)
        add(t_addr, "CAP", "cap", 1, 0, w=100)
        add(t_addr, "Comune", "city", 2, 0, w=250)
        add(t_addr, "Provincia", "province", 2, 2, w=50) # on same row? grid tricky
        
        ctk.CTkLabel(t_addr, text="Paese").grid(row=3, column=0, sticky="e", padx=5)
        self.entries['country'] = ctk.CTkEntry(t_addr, width=200)
        self.entries['country'].insert(0, "ITALY")
        self.entries['country'].grid(row=3, column=1, sticky="w", padx=5)

        # --- Contatti ---
        add(t_cont, "Telefono", "phone", 0, 0)
        add(t_cont, "Cellulare", "mobile", 1, 0)
        add(t_cont, "Fax", "fax", 2, 0)
        add(t_cont, "Email", "email", 3, 0)
        add(t_cont, "Sito Web", "website", 4, 0)
        add(t_cont, "Persona Rif.", "persona_riferimento", 5, 0)
        
        # --- Contabili ---
        def add_c(p, lbl, key, r, c, vals, w=200):
            ctk.CTkLabel(p, text=lbl, anchor="e").grid(row=r, column=c, padx=5, pady=5, sticky="e")
            combo = ctk.CTkComboBox(p, values=vals, width=w)
            combo.grid(row=r, column=c+1, padx=5, pady=5, sticky="w")
            self.entries[key] = combo
        
        add_c(t_comm, "Listino", "listino_id", 0, 0, list(self.lookups['listini'].keys()))
        add_c(t_comm, "Pagamento", "pagamento_id", 1, 0, list(self.lookups['payments'].keys()))
        add(t_comm, "Banca Appoggio", "banca_nome", 2, 0, w=300)
        add(t_comm, "IBAN", "iban", 3, 0, w=300)
        
        add_c(t_comm, "Agente", "agente_id", 0, 2, list(self.lookups['agents'].keys()))
        add(t_comm, "% Provv.", "provvigione_agente", 1, 2, w=80)
        add(t_comm, "Sconto 1", "sconto1", 2, 2, w=80)
        add(t_comm, "Sconto 2", "sconto2", 3, 2, w=80)

        # --- Fattura Elettronica ---
        add(t_fatt, "Codice Destinatario", "sdi_code", 0, 0)
        add(t_fatt, "PEC", "pec", 1, 0)
        add_c(t_fatt, "Esigibilità IVA", "esigibilita_iva", 2, 0, ["I - Immediata", "D - Differita", "S - Split Payment"])
        
        # --- Note ---
        self.txt_notes = ctk.CTkTextbox(t_note, width=600, height=200)
        self.txt_notes.pack(padx=10, pady=10)
        
        # --- BUTTON BAR BOTTOM ---
        bbar = ctk.CTkFrame(t_dati, height=40, fg_color="transparent")
        bbar.pack(fill="x", side="bottom", pady=10)
        
        ctk.CTkButton(bbar, text="Annulla", fg_color="gray", command=lambda: self.tabs.set("Elenco")).pack(side="right", padx=10)
        ctk.CTkButton(bbar, text="Salva", fg_color="#27ae60", command=self.save).pack(side="right", padx=10)

        self.refresh_list()

    def load_lookups(self):
        # Fetch lookups for combos
        def get_map(tbl):
            conn = database.sqlite3.connect(database.DB_NAME)
            cur = conn.cursor()
            try:
                cur.execute(f"SELECT id, name FROM {tbl}")
                return {r[1]: r[0] for r in cur.fetchall()}
            except: return {}
            finally: conn.close()
            
        return {
            'cats': get_map('client_categories'),
            'payments': get_map('payment_terms'),
            'agents': get_map('agents'),
            'listini': {"Listino Base": 1} # Mock
        }

    def refresh_list(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        res = database.get_contacts() # Assume this returns list of tuples
        
        q = self.ent_search.get().lower()
        if self.sub_type:
            res = [r for r in res if self.sub_type in r[1]] # Filter by type if needed
            
        for r in res:
            # 0:id, 1:type, ... 3:rs ... 5:city ... 
            # Need to match database.get_contacts returns
            # It returns: (id, type, code, rs, cognome, nome, address, cap, city, vat, ...)
            # Let's verify index. 
            # r[3] is RS, r[8] is City, r[11] is Phone
             
             if q and q not in str(r[3]).lower(): continue
             
             self.tree.insert("", "end", values=(r[0], r[3], r[1], r[8], r[11]), tags=(str(r[0]),))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        self.load_contact(iid)
        self.tabs.set("Dati")

    def load_contact(self, cid):
        self.current_id = cid
        self.lbl_id.configure(text=f"Codice: {cid}")
        
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.row_factory = database.sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM contacts WHERE id=?", (cid,))
        row = cur.fetchone()
        conn.close()
        
        if not row: return
        
        # Helper to set Entry
        def set_e(k, val):
            if k in self.entries:
                w = self.entries[k]
                if isinstance(w, ctk.CTkEntry):
                    w.delete(0, "end")
                    if val: w.insert(0, str(val))
                elif isinstance(w, ctk.CTkComboBox):
                    if val is None: 
                        w.set("")
                        return
                    # Reverse Lookup
                    found = False
                    # Check which lookup map belongs to this key
                    target_map = None
                    if k == 'category_id': target_map = self.lookups['cats']
                    elif k == 'pagamento_id': target_map = self.lookups['payments']
                    elif k == 'agente_id': target_map = self.lookups['agents']
                    elif k == 'listino_id': target_map = self.lookups['listini']
                    
                    if target_map:
                         # Find key for value
                         name = next((key for key, v in target_map.items() if v == val), str(val))
                         w.set(name)
                    else:
                        w.set(str(val))
                elif isinstance(w, ctk.CTkCheckBox):
                    if val: w.select()
                    else: w.deselect()

        for k in row.keys():
            set_e(k, row[k])
            
        self.txt_notes.delete("0.0", "end")
        if row['notes']: self.txt_notes.insert("0.0", row['notes'])

    def import_dialog(self):
        from utils.importer import open_contacts_import
        default = self.sub_type if self.sub_type in ('cliente', 'fornitore') else 'cliente'
        open_contacts_import(self, default_type=default, on_done=self.refresh_list)

    def new_contact(self):
        self.current_id = None
        self.lbl_id.configure(text="NUOVO")
        for k, w in self.entries.items():
            if isinstance(w, ctk.CTkEntry): w.delete(0, "end")
            elif isinstance(w, ctk.CTkComboBox): w.set("")
            elif isinstance(w, ctk.CTkCheckBox): w.deselect()
        self.txt_notes.delete("0.0", "end")
        self.tabs.set("Dati")

    def save(self):
        data = {}
        for k, w in self.entries.items():
            if isinstance(w, ctk.CTkEntry): val = w.get()
            elif isinstance(w, ctk.CTkComboBox): val = w.get()
            elif isinstance(w, ctk.CTkCheckBox): val = 1 if w.get() else 0
            
            # Resolve ID for combos
            if k == 'category_id': val = self.lookups['cats'].get(val)
            elif k == 'pagamento_id': val = self.lookups['payments'].get(val)
            elif k == 'agente_id': val = self.lookups['agents'].get(val)
            elif k == 'listino_id': val = self.lookups['listini'].get(val)
            
            data[k] = val
            
        data['notes'] = self.txt_notes.get("0.0", "end")
        
        if not data['ragione_sociale']:
            messagebox.showerror("Errore", "Ragione sociale obbligatoria")
            return

        try:
            if self.current_id:
                database.update_contact_generic(self.current_id, data)
            else:
                database.add_contact(data['type'], data['ragione_sociale'], **data)
            
            messagebox.showinfo("Salvataggio", "Contatto salvato!")
            self.refresh_list()
            # Stay on Dati or switch? Stay is better for editing.
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            
    def delete_contact(self):
        if not self.current_id:
             sel = self.tree.selection()
             if sel: self.current_id = self.tree.item(sel[0])['tags'][0]
             else: return
             
        if messagebox.askyesno("Conferma", "Eliminare contatto?"):
            database.delete_contact(self.current_id, "")
            self.refresh_list()
            self.new_contact()
