import customtkinter as ctk
from tkinter import ttk, messagebox
import database

class ProductsWindow(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_id = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # --- 1. TOOLBAR ---
        toolbar = ctk.CTkFrame(self, height=40, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkButton(toolbar, text="📄 Nuovo", width=80, fg_color="#3498db", command=self.new_product).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="❌ Elimina", width=80, fg_color="#e74c3c", command=self.delete_product).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="🔍 Trova", width=80, fg_color="#f39c12", command=lambda: self.tabs.set("Elenco")).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="📥 Importa", width=90, fg_color="#16a085", command=self.import_dialog).pack(side="left", padx=2)

        # Search
        ctk.CTkLabel(toolbar, text="Cerca:").pack(side="left", padx=(20, 5))
        self.ent_search = ctk.CTkEntry(toolbar, width=200)
        self.ent_search.pack(side="left", padx=5) 
        self.ent_search.bind("<Return>", lambda e: self.refresh_list())
        ctk.CTkButton(toolbar, text="Cerca", width=60, command=self.refresh_list).pack(side="left", padx=2)
        
        # --- 2. TABS ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.tabs.add("Dati")
        self.tabs.add("Dati F.E.") # Placeholder
        self.tabs.add("Elenco")
        
        # --- TAB ELENCO ---
        t_elenco = self.tabs.tab("Elenco")
        t_elenco.grid_columnconfigure(0, weight=1)
        t_elenco.grid_rowconfigure(0, weight=1)
        
        cols = ("ID", "Codice", "Descrizione", "Prezzo", "Giacenza")
        self.tree = ttk.Treeview(t_elenco, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("ID", width=50)
        self.tree.column("Descrizione", width=300)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(t_elenco, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # --- TAB DATI ---
        t_dati = self.tabs.tab("Dati")
        self.entries = {}
        self.lookups = self.load_lookups()
        
        # Form
        self.form = ctk.CTkFrame(t_dati, fg_color="transparent")
        self.form.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Row 1: Codice, KIT, Obsoleto
        r1 = ctk.CTkFrame(self.form, fg_color="transparent")
        r1.pack(fill="x", pady=2)
        ctk.CTkLabel(r1, text="Codice").pack(side="left", padx=5)
        self.entries['code'] = ctk.CTkEntry(r1, width=150)
        self.entries['code'].pack(side="left", padx=5)
        
        self.entries['is_kit'] = ctk.CTkCheckBox(r1, text="KIT")
        self.entries['is_kit'].pack(side="left", padx=10)
        
        ctk.CTkButton(r1, text="GESTISCI KIT", fg_color="gray", width=100).pack(side="left", padx=5)
        
        # Row 2: Barcode
        r2 = ctk.CTkFrame(self.form, fg_color="transparent")
        r2.pack(fill="x", pady=2)
        ctk.CTkLabel(r2, text="Codice a barre", width=80, anchor="e").pack(side="left", padx=5)
        self.entries['barcode'] = ctk.CTkEntry(r2, width=300)
        self.entries['barcode'].pack(side="left", padx=5)
        
        # Row 3: Categoria, Sottocategoria
        r3 = ctk.CTkFrame(self.form, fg_color="transparent")
        r3.pack(fill="x", pady=2)
        ctk.CTkLabel(r3, text="Categoria", width=80, anchor="e").pack(side="left", padx=5)
        
        # Category Combo - Needs ID mapping
        cat_vals = list(self.lookups['cats'].keys())
        self.entries['category_id'] = ctk.CTkComboBox(r3, values=cat_vals, width=200, command=self.on_cat_change)
        self.entries['category_id'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r3, text="Sotto categoria").pack(side="left", padx=5)
        self.entries['subcategory_id'] = ctk.CTkComboBox(r3, values=[], width=200) # Populated dynamically
        self.entries['subcategory_id'].pack(side="left", padx=5)
        
        self.entries['is_service'] = ctk.CTkCheckBox(r3, text="Servizio")
        self.entries['is_service'].pack(side="left", padx=10)
        
        self.entries['is_description'] = ctk.CTkCheckBox(r3, text="Descrizione")
        self.entries['is_description'].pack(side="left", padx=10)
        
        # Row 4: Descrizione
        r4 = ctk.CTkFrame(self.form, fg_color="transparent")
        r4.pack(fill="x", pady=2)
        ctk.CTkLabel(r4, text="descrizione", width=80, anchor="e").pack(side="left", padx=5)
        self.entries['description'] = ctk.CTkEntry(r4)
        self.entries['description'].pack(side="left", fill="x", expand=True, padx=5)
        
        # Row 5: In Inglese
        r5 = ctk.CTkFrame(self.form, fg_color="transparent")
        r5.pack(fill="x", pady=2)
        ctk.CTkLabel(r5, text="in inglese", width=80, anchor="e").pack(side="left", padx=5)
        self.entries['description_en'] = ctk.CTkEntry(r5)
        self.entries['description_en'].pack(side="left", fill="x", expand=True, padx=5)
        
        # Row 6: IVA, Posizione Magazzino
        r6 = ctk.CTkFrame(self.form, fg_color="transparent")
        r6.pack(fill="x", pady=2)
        ctk.CTkLabel(r6, text="iva", width=80, anchor="e").pack(side="left", padx=5)
        
        vat_vals = list(self.lookups['vat'].keys())
        self.entries['vat_rate_id'] = ctk.CTkComboBox(r6, values=vat_vals, width=100)
        self.entries['vat_rate_id'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r6, text="Posizione magazzino").pack(side="left", padx=10)
        self.entries['warehouse_location'] = ctk.CTkEntry(r6, width=150)
        self.entries['warehouse_location'].pack(side="left", padx=5)
        
        # Row 7: Grid of dims (UM, Peso, ETC)
        r7 = ctk.CTkFrame(self.form, fg_color="transparent")
        r7.pack(fill="x", pady=2)
        
        def add_s(lbl, key, w=80):
            f = ctk.CTkFrame(r7, fg_color="transparent")
            f.pack(side="left", padx=5)
            ctk.CTkLabel(f, text=lbl, width=w, anchor="e").pack(side="left", padx=2)
            e = ctk.CTkEntry(f, width=80)
            e.pack(side="left", padx=2)
            self.entries[key] = e
            
        add_s("unità di misura", "unit", 50)
        add_s("peso", "weight_gross") # Using gross as generic weight
        add_s("quantità per collo", "pieces_per_pack")
        add_s("codice fornitore", "supplier_code")
        
        # Row 8: Scorta Minima, Tipologia
        r8 = ctk.CTkFrame(self.form, fg_color="transparent")
        r8.pack(fill="x", pady=2)
        
        ctk.CTkLabel(r8, text="scorta minima", width=80, anchor="e").pack(side="left", padx=5)
        self.entries['min_stock'] = ctk.CTkEntry(r8, width=80)
        self.entries['min_stock'].pack(side="left", padx=5)
        
        ctk.CTkLabel(r8, text="tipologia").pack(side="left", padx=10)
        self.purchase_type_var = ctk.StringVar(value="Both")
        ctk.CTkRadioButton(r8, text="Acquisto", variable=self.purchase_type_var, value="Purchase").pack(side="left", padx=5)
        ctk.CTkRadioButton(r8, text="Vendita", variable=self.purchase_type_var, value="Sale").pack(side="left", padx=5)
        ctk.CTkRadioButton(r8, text="Entrambi", variable=self.purchase_type_var, value="Both").pack(side="left", padx=5)
        
        # Row 9: Fornitore
        r9 = ctk.CTkFrame(self.form, fg_color="transparent")
        r9.pack(fill="x", pady=2)
        ctk.CTkLabel(r9, text="Fornitore abituale", width=120, anchor="e").pack(side="left", padx=5)
        self.entries['supplier_id'] = ctk.CTkComboBox(r9, values=list(self.lookups['suppliers'].keys()), width=200)
        self.entries['supplier_id'].pack(side="left", padx=5)
        
        # Bottom Split: Prices & Image
        bot = ctk.CTkFrame(self.form)
        bot.pack(fill="both", expand=True, pady=10)
        
        # Prices List
        f_prices = ctk.CTkFrame(bot)
        f_prices.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(f_prices, text="Prezzi listini", font=("Arial", 12, "bold")).pack(anchor="w")
        
        # Simple grid for Base Price (since we only have one really)
        pg = ctk.CTkFrame(f_prices)
        pg.pack(fill="x", pady=5)
        ctk.CTkLabel(pg, text="BASE", width=50).grid(row=0, column=0)
        ctk.CTkLabel(pg, text="LISTINO BASE", width=150).grid(row=0, column=1)
        self.entries['price_base'] = ctk.CTkEntry(pg, width=80)
        self.entries['price_base'].grid(row=0, column=2)
        ctk.CTkLabel(pg, text="€").grid(row=0, column=3)
        
        # Image
        f_img = ctk.CTkFrame(bot, width=200, height=200)
        f_img.pack(side="right", padx=5)
        ctk.CTkLabel(f_img, text="Nessuna immagine").place(relx=0.5, rely=0.5, anchor="center")
        
        # Buttons
        bbar = ctk.CTkFrame(t_dati, height=40, fg_color="transparent")
        bbar.pack(fill="x", side="bottom", pady=10)
        ctk.CTkButton(bbar, text="Annulla", fg_color="gray", command=lambda: self.tabs.set("Elenco")).pack(side="right", padx=10)
        ctk.CTkButton(bbar, text="Salva", fg_color="#27ae60", command=self.save).pack(side="right", padx=10)
        
        self.refresh_list()
        
    def load_lookups(self):
        # Cats, Subcats, Suppliers
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.row_factory = database.sqlite3.Row
        cur = conn.cursor()
        
        def get_kv(tbl):
            try:
                cur.execute(f"SELECT id, name FROM {tbl}")
                return {r['name']: r['id'] for r in cur.fetchall()}
            except: return {}

        cats = get_kv('categories')
        
        # Subcats is special: map ID -> Name, but also need CatID linkage
        cur.execute("SELECT id, name, category_id FROM subcategories")
        subs = cur.fetchall() # list of rows
        
        # Suppliers
        cur.execute("SELECT id, ragione_sociale FROM contacts WHERE type IN ('fornitore', 'both')")
        suppliers = {r['ragione_sociale']: r['id'] for r in cur.fetchall()}
        
        # VAT
        cur.execute("SELECT id, description FROM vat_rates")
        vat = {r['description']: r['id'] for r in cur.fetchall()}
        
        conn.close()
        
        return {
            'cats': cats,
            'subs': subs, # List of Row objects
            'suppliers': suppliers,
            'vat': vat
        }

    def on_cat_change(self, choice):
        # Filter subcats
        cat_id = self.lookups['cats'].get(choice)
        subs = [s['name'] for s in self.lookups['subs'] if s['category_id'] == cat_id]
        self.entries['subcategory_id'].configure(values=subs)
        self.entries['subcategory_id'].set("")

    def refresh_list(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        rows = database.get_products()
        q = self.ent_search.get().lower()
        
        for r in rows:
            # get_products: 0:id, 1:code, 2:name, 3:description, 7:price_base, 9:stock_quantity
            desc = r[3] or r[2] or ""
            code = r[1] or ""
            if q and q not in desc.lower() and q not in code.lower(): continue
            self.tree.insert("", "end", values=(r[0], code, desc, f"€ {(r[7] or 0):.2f}", r[9] or 0), tags=(str(r[0]),))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        self.load_product(iid)
        self.tabs.set("Dati")

    def load_product(self, pid):
        self.current_id = pid
        conn = database.sqlite3.connect(database.DB_NAME)
        conn.row_factory = database.sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE id=?", (pid,))
        row = cur.fetchone()
        conn.close()
        
        if not row: return
        
        # Helper
        def set_val(k, val):
            if k not in self.entries: return
            w = self.entries[k]
            if isinstance(w, ctk.CTkEntry):
                w.delete(0, "end")
                if val is not None: w.insert(0, str(val))
            elif isinstance(w, ctk.CTkCheckBox):
                if val: w.select()
                else: w.deselect()
            elif isinstance(w, ctk.CTkComboBox):
                if val is None: 
                    w.set("")
                    return
                # Reverse Map
                target_map = None
                if k == 'category_id': target_map = self.lookups['cats']
                elif k == 'supplier_id': target_map = self.lookups['suppliers']
                elif k == 'vat_rate_id': target_map = self.lookups['vat']
                
                if target_map:
                     name = next((key for key, v in target_map.items() if v == val), str(val))
                     w.set(name)
                elif k == 'subcategory_id':
                     # Find name in list
                     name = next((s['name'] for s in self.lookups['subs'] if s['id'] == val), "")
                     w.set(name)
                else:
                    w.set(str(val))
        
        for k in row.keys():
            set_val(k, row[k])
            
        # Trigger cat change to populate subcats
        cat_name = self.entries['category_id'].get()
        self.on_cat_change(cat_name)
        # Re-set subcat
        set_val('subcategory_id', row['subcategory_id'])
        
        self.purchase_type_var.set(row['purchase_type'] or "Both")

    def new_product(self):
        self.current_id = None
        for k, w in self.entries.items():
            if isinstance(w, ctk.CTkEntry): w.delete(0, "end")
            elif isinstance(w, ctk.CTkComboBox): w.set("")
            elif isinstance(w, ctk.CTkCheckBox): w.deselect()
        self.tabs.set("Dati")

    def save(self):
        data = {}
        for k, w in self.entries.items():
            if isinstance(w, ctk.CTkEntry): val = w.get()
            elif isinstance(w, ctk.CTkComboBox): val = w.get()
            elif isinstance(w, ctk.CTkCheckBox): val = 1 if w.get() else 0
            
            # Resolve IDs
            if k == 'category_id': val = self.lookups['cats'].get(val)
            elif k == 'supplier_id': val = self.lookups['suppliers'].get(val)
            elif k == 'vat_rate_id': val = self.lookups['vat'].get(val)
            elif k == 'subcategory_id':
                # Find ID from Name
                val = next((s['id'] for s in self.lookups['subs'] if s['name'] == val), None)
            
            data[k] = val

        data['purchase_type'] = self.purchase_type_var.get()

        # La colonna 'name' è NOT NULL: usa la descrizione (o il codice) come nome
        data['name'] = data.get('description') or data.get('code') or "Articolo"

        # Normalizza i campi numerici (virgola -> punto)
        for nk in ('price_base', 'min_stock', 'weight_gross', 'pieces_per_pack'):
            v = data.get(nk)
            if isinstance(v, str):
                v = v.strip().replace(',', '.')
                try: data[nk] = float(v) if v else None
                except ValueError: data[nk] = None

        # Salva anche la percentuale IVA effettiva (usata da documenti/scanner)
        if data.get('vat_rate_id'):
            conn = database.sqlite3.connect(database.DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT rate FROM vat_rates WHERE id=?", (data['vat_rate_id'],))
            r = cur.fetchone()
            conn.close()
            if r and r[0] is not None:
                data['vat_rate'] = r[0]

        try:
            if self.current_id:
                database.update_product_generic(self.current_id, data)
            else:
                conn = database.sqlite3.connect(database.DB_NAME)
                cur = conn.cursor()
                cols = ", ".join(data.keys())
                q = ", ".join(["?"]*len(data))
                cur.execute(f"INSERT INTO products ({cols}) VALUES ({q})", list(data.values()))
                conn.commit()
                conn.close()
                
            messagebox.showinfo("Info", "Articolo salvato")
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            
    def import_dialog(self):
        from utils.importer import open_products_import
        open_products_import(self, on_done=self.refresh_list)

    def delete_product(self):
        if not self.current_id:
             sel = self.tree.selection()
             if sel: self.current_id = self.tree.item(sel[0])['tags'][0]
             else: return
        if messagebox.askyesno("Confirm", "Delete?"):
            database.delete_product(self.current_id)
            self.refresh_list()
            self.new_product()
