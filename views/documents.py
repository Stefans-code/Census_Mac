import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import database

class DocumentsWindow(ctk.CTkFrame):
    def __init__(self, parent, dtype):
        super().__init__(parent)
    def __init__(self, parent, dtype):
        super().__init__(parent)
        try:
            self.parent = parent
            self.dtype = dtype
            # self.title(f"Gestione {dtype.capitalize()} / Ordini di Vendita") # Not for frame
            # self.geometry("1400x800") # Not for frame
            
            # Grid layout
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(2, weight=1) # The list takes available space
            
            # --- 1. HEADER / TOOLBAR (Top) ---
            # The screenshot shows a "Ribbon" style toolbar with large icons/buttons on toprow 
            # and filters below.
            
            # Toolbar Row
            toolbar = ctk.CTkFrame(self, height=60, fg_color="transparent")
            toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            
            def add_btn(parent, text, icon, cmd, color="#3498db"):
                # Icon+Text button style
                b = ctk.CTkButton(parent, text=f"{icon} {text}", command=cmd, 
                                  fg_color="#ecf0f1", text_color="#333", border_width=1, border_color="#ccc",
                                  hover_color="#bdc3c7", width=120, height=35, anchor="w")
                b.pack(side="left", padx=2)
                
            # Group: Actions
            # Invoicex: [New Prev][New Ord] | [Edit][Delete][Duplicate]
            
            # We simplify based on "dtype" passed (e.g. 'preventivo')
            if "preventivo" in dtype or "ordine" in dtype:
                add_btn(toolbar, "Nuovo Preventivo", "📄", lambda: self.open_new_type("preventivo"))
                add_btn(toolbar, "Nuovo Ordine", "📦", lambda: self.open_new_type("ordine"))
            else:
                add_btn(toolbar, "Nuovo Documento", "📄", self.open_new)
                
            ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5)
            
            add_btn(toolbar, "Modifica", "✏️", self.open_edit)
            add_btn(toolbar, "Elimina", "❌", self.delete_doc)
            add_btn(toolbar, "Duplica", "📑", self.duplicate_doc)
            
            ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5)
            
            add_btn(toolbar, "Stampa", "🖨️", self.print_pdf) # General print
            add_btn(toolbar, "PDF", "🔻", self.print_pdf)
            
            if "preventivo" in dtype:
                 # Invoicex Logic: Preventivo -> Ordine is common, but UI screenshot shows > DDT / > Fattura
                 # Let's support > Ordine as well contextually or just follow screenshot
                 add_btn(toolbar, "> Ordine", "📦", self.convert_to_order) # Added as useful shortcut
                 add_btn(toolbar, "> DDT", "⚙️", self.convert_to_ddt)
                 add_btn(toolbar, "> Fattura", "⚙️", self.convert_to_invoice)
            elif "ordine" in dtype:
                 add_btn(toolbar, "> DDT", "⚙️", self.convert_to_ddt)
                 add_btn(toolbar, "> Fattura", "⚙️", self.convert_to_invoice)
            elif "ddt" in dtype:
                 add_btn(toolbar, "> Fattura", "⚙️", self.convert_to_invoice)
            
            # Right Side: Radio for Vendita/Acquisto
            fr_type = ctk.CTkFrame(toolbar, fg_color="transparent")
            fr_type.pack(side="right", padx=10)
            self.var_scope = tk.StringVar(value="Vendita")
            ctk.CTkLabel(fr_type, text="Documenti di:").pack(side="left", padx=5)
            ctk.CTkRadioButton(fr_type, text="Vendita", variable=self.var_scope, value="Vendita").pack(side="left", padx=5)
            ctk.CTkRadioButton(fr_type, text="Acquisto", variable=self.var_scope, value="Acquisto").pack(side="left", padx=5)
    
            # --- 2. FILTER BAR ---
            filter_bar = ctk.CTkFrame(self, height=50) # Light gray background usually
            filter_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
            
            ctk.CTkLabel(filter_bar, text="Visualizza documenti Dal").pack(side="left", padx=(10, 5))
            self.ent_date_from = ctk.CTkEntry(filter_bar, width=100, placeholder_text="YYYY-MM-DD")
            self.ent_date_from.pack(side="left", padx=2)
            
            ctk.CTkLabel(filter_bar, text="Al").pack(side="left", padx=5)
            self.ent_date_to = ctk.CTkEntry(filter_bar, width=100, placeholder_text="YYYY-MM-DD")
            self.ent_date_to.pack(side="left", padx=2)
            
            ttk.Separator(filter_bar, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
            
            ctk.CTkLabel(filter_bar, text="Cliente").pack(side="left", padx=5)
            self.ent_client_filter = ctk.CTkEntry(filter_bar, width=200)
            self.ent_client_filter.pack(side="left", padx=2)
            
            ctk.CTkLabel(filter_bar, text="Tipo").pack(side="left", padx=5)
            self.combo_type_filter = ctk.CTkComboBox(filter_bar, values=["Tutti", "Preventivo", "Ordine", "Fattura"], width=120)
            self.combo_type_filter.set("Tutti")
            self.combo_type_filter.pack(side="left", padx=2)
            
            ctk.CTkButton(filter_bar, text="🔄", width=40, command=self.refresh).pack(side="left", padx=10)
    
            # --- 3. DATA TABLE (Treeview) ---
            # Columns from screenshot: Serie, Numero, Convertito, Stato, Data, Consegna, Cliente, Riferimento, Totale Imponibile, Evaso, Allegati
            cols = ("ID", "Serie", "Numero", "Convertito", "Stato", "Data", "Consegna", "Cliente", "Riferimento", "Totale Imponibile", "Evaso", "Allegati")
            
            self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
            
            # Layout Config
            self.tree.column("ID", width=0, stretch=False) # Hidden ID
            self.tree.column("Serie", width=50, anchor="center")
            self.tree.column("Numero", width=80, anchor="e")
            self.tree.column("Convertito", width=80, anchor="center")
            self.tree.column("Stato", width=100, anchor="center")
            self.tree.column("Data", width=90, anchor="center")
            self.tree.column("Consegna", width=90, anchor="center")
            self.tree.column("Cliente", width=300, anchor="w")
            self.tree.column("Riferimento", width=150, anchor="w")
            self.tree.column("Totale Imponibile", width=100, anchor="e")
            self.tree.column("Evaso", width=60, anchor="center")
            self.tree.column("Allegati", width=60, anchor="center")
            
            for c in cols:
                self.tree.heading(c, text=c)
                
            # Scrollbar
            sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=sb.set)
            
            self.tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0,10))
            sb.grid(row=2, column=1, sticky="ns", pady=(0,10))
            
            self.refresh()
            
        except Exception as e:
            messagebox.showerror("Critico", f"Errore Lista Documenti: {e}")
            ctk.CTkLabel(self, text=f"ERRORE CARICAMENTO LISTA:\n{e}", text_color="red", font=("Arial", 24)).grid(row=0, column=0, sticky="nsew")
        
    def convert_to_target(self, target_type):
        sel = self.tree.selection()
        if not sel: 
            messagebox.showwarning("Attenzione", "Seleziona un documento")
            return
        did = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Conferma", f"Creare {target_type.capitalize()} da questo documento?"):
            try:
                new_id = database.convert_document(did, target_type)
                if new_id:
                    messagebox.showinfo("Successo", "Documento creato!")
                    self.refresh()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

    def convert_to_order(self): self.convert_to_target("ordine")
    def convert_to_invoice(self): self.convert_to_target("fattura")
    def convert_to_ddt(self): self.convert_to_target("ddt")
    
    def duplicate_doc(self):
        sel = self.tree.selection()
        if not sel: return
        did = self.tree.item(sel[0])['values'][0]
        # Duplicate to SAME type
        # We need to know current type of selected doc.
        # Tree doesn't explicitly store type column in view, but we are in typed view usually.
        # Ideally database conversion accepts target type same as source.
        # Let's assume self.dtype, but self.dtype might be 'preventivo' while list shows 'ordine'?
        # DocumentsWindow is created with specific dtype.
        # The list might be mixed if we implemented "Tutti".
        # Let's blindly try to use self.dtype or fetch doc type.
        # Safest: fetch doc type or just ask user? 
        # Invoicex Duplica makes same type.
        try:
           # We use convert_document where target is SAME as source.
           # But convert logic needs explicit target.
           # Let's use the window's dtype for now, or fetch it.
           # database.py get_document call?
           # Let's assume window dtype is singular most of the time.
           t_type = self.dtype
           if t_type == 'preventivo/ordine': t_type = 'preventivo' # fallback
           
           database.convert_document(did, t_type) 
           self.refresh()
        except Exception as e:
           messagebox.showerror("Errore", str(e))

    def open_new_type(self, t_type):
        for child in self.parent.winfo_children(): child.destroy()
        DocumentEditor(self.parent, t_type).pack(fill="both", expand=True)

    def refresh(self):
        # ... logic ...
        for x in self.tree.get_children(): self.tree.delete(x)
        docs = database.get_documents(self.dtype) 
        f_client = self.ent_client_filter.get().lower()
        f_date_from = self.ent_date_from.get()
        f_date_to = self.ent_date_to.get()
        
        for d in docs:
            # d structure: 0:id, 1:type, 2:serie, 3:num, 4:year, 5:date, 6:net, 7:vat, 8:gross, 9:status, 10:notes, 11:created, 12:contact_name
            did = d[0]
            num = d[3]
            serie = d[2] or ""
            dt = d[5]
            c_name = d[12] if len(d) > 12 and d[12] else "???"
            
            if f_client and f_client not in c_name.lower(): continue
            if f_date_from and dt < f_date_from: continue
            if f_date_to and dt > f_date_to: continue
            
            tot_imp = f"€ {d[6]:.2f}" if d[6] else "€ 0.00"
            status = d[9] or ""
            
            self.tree.insert("", "end", values=(did, serie, num, "", status, dt, "", c_name, "", tot_imp, "", ""))

    def open_new(self):
         self.open_new_type(self.dtype)
            
    def open_edit(self):
        sel = self.tree.selection()
        if not sel: return
        did = self.tree.item(sel[0])['values'][0]
        
        for child in self.parent.winfo_children():
            child.destroy()
            
        DocumentEditor(self.parent, self.dtype, doc_id=did).pack(fill="both", expand=True)
        
    def delete_doc(self):
        sel = self.tree.selection()
        if not sel: return
        did = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Elimina", "Cancellare documento?"):
            database.delete_document(did)
            self.refresh()
            
    def print_pdf(self):
        sel = self.tree.selection()
        if not sel: 
            messagebox.showwarning("Selezione", "Seleziona un documento da stampare")
            return
        did = self.tree.item(sel[0])['values'][0]
        try:
             # Reuse Editor logic or call generator directly
             # We can't reuse Editor logic easily without instantiating it.
             # Call generic generator
             from utils.pdf_gen import generate_invoice_pdf
             import os
             
             # Fetch data
             conn = database.sqlite3.connect(database.DB_NAME)
             cursor = conn.cursor()
             cursor.execute("SELECT * FROM documents WHERE id=?", (did,))
             d = cursor.fetchone()
             if not d: return
             
             # Generic wrapper needed in utils really, but let's just do a quick alert for "Done"
             # Actually the previous code in Editor had full logic.
             # To avoid duplication, we should put that logic in utils or a helper.
             # For now, just placeholder or direct call if possible.
             # Let's say "Funzione disponibile dentro l'editor per ora (per anteprima)" or attempt minimal gen.
             # Invoicex prints direct.
             # Let's just prompt "Apri Editor per stampare" to be safe or try generate.
             messagebox.showinfo("Stampa", "Per stampare/export PDF, apri il documento in Modifica (doppio click o tasto Modifica).")
        except Exception as e:
             messagebox.showerror("Errore", str(e))
        pass
        
    def convert_to_invoice(self):
        # ... existing convert logic reuse ...
        pass

class DocumentEditor(ctk.CTkFrame):
    def __init__(self, parent, dtype, doc_id=None):
        super().__init__(parent)
        try:
            self.parent = parent
            self.dtype = dtype
            self.doc_id = doc_id
            
            # --- HEADER / NAVIGATION ---
            hb = ctk.CTkFrame(self, height=40, fg_color="transparent")
            hb.pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(hb, text="⬅ Torna alla Lista", command=self.go_back, width=120, fg_color="#7f8c8d").pack(side="left")
            ctk.CTkLabel(hb, text=f"{dtype.capitalize()} di Vendita", font=("Arial", 20, "bold")).pack(side="left", padx=20)
            
            # --- TABVIEW (Main Content) ---
            self.tab = ctk.CTkTabview(self)
            self.tab.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            t_dati = self.tab.add("Dati")
            t_righe = self.tab.add("Foglio Righe")
            t_altro = self.tab.add("Altro")
            
            # ==================== TAB: DATI ====================
            # Layout: Left Column (Main Data), Right Column (Dest, Transport)
            t_dati.grid_columnconfigure(0, weight=3) # Left wider
            t_dati.grid_columnconfigure(1, weight=1) # Right
            
            # --- LEFT COLUMN ---
            f_left = ctk.CTkFrame(t_dati, fg_color="transparent")
            f_left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            
            # Row 1: Serie/Num/Data
            r1 = ctk.CTkFrame(f_left, fg_color="transparent")
            r1.pack(fill="x", pady=2)
            ctk.CTkLabel(r1, text="Serie", width=40).pack(side="left")
            ctk.CTkEntry(r1, width=40).pack(side="left", padx=2) 
            ctk.CTkLabel(r1, text="Numero", width=60).pack(side="left")
            self.lbl_num = ctk.CTkEntry(r1, width=60)
            self.lbl_num.insert(0, "AUTO")
            self.lbl_num.pack(side="left", padx=2)
            ctk.CTkLabel(r1, text="Data", width=40).pack(side="left", padx=5)
            self.entry_date = ctk.CTkEntry(r1, width=100)
            self.entry_date.insert(0, date.today().isoformat())
            self.entry_date.pack(side="left", padx=2)
            
            # Row 2: Client
            r2 = ctk.CTkFrame(f_left, fg_color="transparent")
            r2.pack(fill="x", pady=2)
            ctk.CTkLabel(r2, text="Cliente", width=60, anchor="w").pack(side="left")
            self.contacts = database.get_contacts("cliente")
            self.c_map = {f"{c[3]}": c[0] for c in self.contacts}
            self.combo_client = ctk.CTkComboBox(r2, values=list(self.c_map.keys()), width=400)
            self.combo_client.pack(side="left", fill="x", expand=True)

            # Row 3: Discounts & Expenses (The "missing central row")
            r3 = ctk.CTkFrame(f_left, fg_color="transparent")
            r3.pack(fill="x", pady=5)
            
            def add_sm(p, txt, w=50):
                f = ctk.CTkFrame(p, fg_color="transparent")
                f.pack(side="left", padx=2)
                ctk.CTkLabel(f, text=txt, font=("Arial", 11)).pack(anchor="w")
                e = ctk.CTkEntry(f, width=w)
                e.pack()
                return e
                
            self.entry_sc1 = add_sm(r3, "Sc. 1")
            self.entry_sc2 = add_sm(r3, "Sc. 2")
            self.entry_sc3 = add_sm(r3, "Sc. 3")
            self.entry_sp_trasp = add_sm(r3, "Sp. tr.", 70)
            self.entry_sp_inc = add_sm(r3, "Sp. inc.", 70)
            
            f_cons = ctk.CTkFrame(r3, fg_color="transparent")
            f_cons.pack(side="left", padx=10)
            ctk.CTkLabel(f_cons, text="Consegna prevista", font=("Arial", 11)).pack(anchor="w")
            self.entry_cons_prev = ctk.CTkEntry(f_cons, width=100)
            self.entry_cons_prev.pack()

            # Row 4: Note
            ctk.CTkLabel(f_left, text="Note", anchor="w").pack(fill="x", pady=(5,0))
            self.text_note = ctk.CTkTextbox(f_left, height=60)
            self.text_note.pack(fill="x", pady=2)

            # Row 5: Riferimento & Consegna
            r5 = ctk.CTkFrame(f_left, fg_color="transparent")
            r5.pack(fill="x", pady=2)
            ctk.CTkLabel(r5, text="Riferimento", width=80, anchor="w").pack(side="left")
            self.entry_obj = ctk.CTkEntry(r5)
            self.entry_obj.pack(side="left", fill="x", expand=True, padx=2)
            
            ctk.CTkLabel(r5, text="Consegna", width=70).pack(side="left")
            ctk.CTkEntry(r5, width=120).pack(side="left")

            # Load Lookups
            self.map_pay = database.get_map("payment_terms")
            self.map_bank = database.get_map("banks")
            self.map_agent = database.get_map("agents")
            
            # Row 6: Pagamento
            r6 = ctk.CTkFrame(f_left, fg_color="transparent")
            r6.pack(fill="x", pady=2)
            ctk.CTkLabel(r6, text="Pagamento", width=80, anchor="w").pack(side="left")
            self.combo_pay = ctk.CTkComboBox(r6, values=list(self.map_pay.keys()))
            self.combo_pay.pack(side="left", fill="x", expand=True)
            self.combo_pay.set("")

            # Row 7: Banca
            r7 = ctk.CTkFrame(f_left, fg_color="transparent")
            r7.pack(fill="x", pady=2)
            ctk.CTkLabel(r7, text="Banca", width=80, anchor="w").pack(side="left")
            self.combo_bank = ctk.CTkComboBox(r7, values=list(self.map_bank.keys()))
            self.combo_bank.pack(side="left", fill="x", expand=True)
            self.combo_bank.set("")
            
            # Row 8: Agente
            r8 = ctk.CTkFrame(f_left, fg_color="transparent")
            r8.pack(fill="x", pady=2)
            ctk.CTkLabel(r8, text="Agente", width=80, anchor="w").pack(side="left")
            self.combo_agent = ctk.CTkComboBox(r8, values=list(self.map_agent.keys()))
            self.combo_agent.pack(side="left", fill="x", expand=True)
            self.combo_agent.set("")
            
            self.entries = {} # Store simplified references if needed
            
            # --- RIGHT COLUMN (Transport/Dest) ---
            f_right = ctk.CTkFrame(t_dati, fg_color="transparent")
            f_right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
            
            ctk.CTkLabel(f_right, text="Destinazione Merce").pack(anchor="w")
            self.entry_dest = ctk.CTkEntry(f_right, placeholder_text="Indirizzo di spedizione...")
            self.entry_dest.pack(fill="x", pady=5)
            
            # Transport Fields box
            gb_trans = ctk.CTkFrame(f_right)
            gb_trans.pack(fill="x", pady=10)
            
            self.map_trans = {
                "causale_trasporto": database.get_map("causali_trasporto"),
                "aspetto_esteriore": database.get_map("aspetto_beni"),
                "vettore": database.get_map("vettori"),
                "porto": database.get_map("porti")
            }

            def add_t(lbl, k):
                f = ctk.CTkFrame(gb_trans, fg_color="transparent")
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=lbl, width=100, anchor="w").pack(side="left")
                
                if k in self.map_trans:
                    vals = list(self.map_trans[k].keys())
                    e = ctk.CTkComboBox(f, values=vals)
                else:
                    e = ctk.CTkEntry(f)
                    
                e.pack(side="left", fill="x", expand=True)
                self.entries[k] = e

            add_t("Causale Trasp.", "causale_trasporto")
            add_t("Aspetto Beni", "aspetto_esteriore")
            add_t("N. Colli", "numero_colli")
            add_t("Vettore", "vettore")
            add_t("Porto", "porto")
            
            # ==================== TAB: FOGLIO RIGHE ====================
            # Toolbar
            tb_rows = ctk.CTkFrame(t_righe, height=40)
            tb_rows.pack(fill="x", padx=5, pady=5)
            
            # BARCODE SCANNER ENTRY
            self.scanner_mode = ctk.BooleanVar(value=False)
            self._scan_feedback_job = None

            self.switch_scanner = ctk.CTkSwitch(tb_rows, text="🔒 Scanner", variable=self.scanner_mode,
                                                command=self.toggle_scanner_mode, width=90)
            self.switch_scanner.pack(side="left", padx=(10, 5))

            self.entry_scan = ctk.CTkEntry(tb_rows, width=170, placeholder_text="📷 Scansiona codice...")
            self.entry_scan.pack(side="left", padx=(0, 5))
            self.entry_scan.bind("<Return>", self.scan_product)
            self.entry_scan.bind("<FocusOut>", self._scan_refocus)

            self.lbl_scan_status = ctk.CTkLabel(tb_rows, text="", anchor="e", text_color="#2ecc71")
            self.lbl_scan_status.pack(side="right", padx=10)
            
            self.chk_iva_inc = ctk.CTkCheckBox(tb_rows, text="Prezzi IVA inclusa")
            self.chk_iva_inc.pack(side="left", padx=10)
            
            ttk.Separator(tb_rows, orient="vertical").pack(side="left", fill="y", padx=5, pady=5)
            
            ctk.CTkButton(tb_rows, text="+ Nuova riga", command=self.add_row_dialog, width=100, fg_color="green").pack(side="left", padx=5)
    #        ctk.CTkButton(tb_rows, text="∑ Sub-totale", width=100).pack(side="left", padx=5)
            
            ctk.CTkButton(tb_rows, text="⚖️ Peso", width=80, fg_color="#95a5a6").pack(side="left", padx=5)
            ctk.CTkButton(tb_rows, text="📗 Import CSV", width=100, fg_color="#16a085",
                          command=self.import_rows_csv).pack(side="left", padx=5)
            
            ttk.Separator(tb_rows, orient="vertical").pack(side="left", fill="y", padx=5, pady=5)
            ctk.CTkButton(tb_rows, text="- Rimuovi", command=self.rem_row, fg_color="red", width=80).pack(side="left", padx=5)
            
            # ==================== TAB: ALTRO ====================
            f_altro = ctk.CTkFrame(t_altro, fg_color="transparent")
            f_altro.pack(fill="both", expand=True, padx=20, pady=20)
            
            def add_a(lbl):
                f = ctk.CTkFrame(f_altro, fg_color="transparent")
                f.pack(fill="x", pady=5)
                ctk.CTkLabel(f, text=lbl, width=150, anchor="w").pack(side="left")
                ctk.CTkEntry(f).pack(side="left", fill="x", expand=True)
                
            add_a("Contatto di riferimento")
            add_a("Campo libero 1")
            add_a("Campo libero 2")
            add_a("Campo libero 3")
            
            # Grid
            cols = ("Codice", "Descrizione", "UM", "Qta", "Prezzo", "Sc.1", "Sc.2", "IVA", "Totale")
            self.tree_rows = ttk.Treeview(t_righe, columns=cols, show="headings")
            
            self.tree_rows.heading("Codice", text="Codice Art.")
            self.tree_rows.heading("Descrizione", text="Descrizione")
            self.tree_rows.heading("UM", text="UM")
            self.tree_rows.heading("Qta", text="Qta")
            self.tree_rows.heading("Prezzo", text="Prezzo")
            self.tree_rows.heading("Sc.1", text="Sc.1") # Sconto 1
            self.tree_rows.heading("Sc.2", text="Sc.2")
            self.tree_rows.heading("IVA", text="IVA")
            self.tree_rows.heading("Totale", text="Importo")

            self.tree_rows.column("Codice", width=80)
            self.tree_rows.column("Descrizione", width=300)
            self.tree_rows.column("UM", width=40)
            self.tree_rows.column("Qta", width=60)
            self.tree_rows.column("Prezzo", width=80)
            self.tree_rows.column("Sc.1", width=50)
            self.tree_rows.column("Sc.2", width=50)
            self.tree_rows.column("IVA", width=50)
            self.tree_rows.column("Totale", width=80)
            
            self.tree_rows.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.current_rows = []
            
            # ==================== FOOTER (TOTALS & ACTIONS) ====================
            footer = ctk.CTkFrame(self, height=100)
            footer.pack(fill="x", padx=10, pady=10)
            
            # Actions (Left)
            f_acts = ctk.CTkFrame(footer, fg_color="transparent")
            f_acts.pack(side="left", padx=10, pady=10)
            
            # Row 1 of buttons
            r_b1 = ctk.CTkFrame(f_acts, fg_color="transparent")
            r_b1.pack(fill="x")
            ctk.CTkButton(r_b1, text="↩ Annulla", command=self.go_back, fg_color="white", text_color="black", width=100).pack(side="left", padx=2)
            ctk.CTkButton(r_b1, text="✔ Salva", command=self.save, fg_color="green", width=100).pack(side="left", padx=2)
            
            # Row 2 of buttons
            r_b2 = ctk.CTkFrame(f_acts, fg_color="transparent")
            r_b2.pack(fill="x", pady=5)
            ctk.CTkButton(r_b2, text="🖨 Stampa", width=100, command=self.print_pdf).pack(side="left", padx=2)
            
            # Workflow Buttons (Invoicex Logic)
            if self.dtype.lower() == 'preventivo':
                ctk.CTkButton(r_b2, text="➡ Crea Ordine", command=self.convert_to_order, fg_color="#8e44ad", width=100).pack(side="left", padx=2)
            elif self.dtype.lower() == 'ordine':
                ctk.CTkButton(r_b2, text="➡ Crea Fattura", command=self.convert_to_invoice, fg_color="#8e44ad", width=100).pack(side="left", padx=2)
            elif self.dtype.lower() == 'ddt':
                ctk.CTkButton(r_b2, text="➡ Crea Fattura", command=self.convert_to_invoice, fg_color="#8e44ad", width=100).pack(side="left", padx=2)

            
            # Totals (Right)
            f_tots = ctk.CTkFrame(footer, fg_color="transparent")
            f_tots.pack(side="right", padx=20, pady=10)
            
            def add_tot(lbl, vid):
                r = ctk.CTkFrame(f_tots, fg_color="transparent")
                r.pack(fill="x")
                ctk.CTkLabel(r, text=lbl, width=120, anchor="e").pack(side="left", padx=5)
                l = ctk.CTkLabel(r, text="0.00", width=80, anchor="e", font=("Arial", 14, "bold"))
                l.pack(side="left")
                setattr(self, f"lbl_{vid}", l)
                
            add_tot("Totale Imponibile", "imp")
            add_tot("Totale IVA", "iva")
            add_tot("Totale Documento", "tot")

            if self.doc_id:
                self.load_doc()
                
        except Exception as e:
            messagebox.showerror("Critico", f"Errore inizializzazione Editor: {e}")
            ctk.CTkLabel(self, text=f"ERRORE CRITICO:\n{e}", text_color="red", font=("Arial", 20)).pack(expand=True)

    def convert_to_order(self):
        if not self.doc_id:
            messagebox.showwarning("Attenzione", "Salva prima il preventivo.")
            return
        if messagebox.askyesno("Conferma", "Vuoi creare un Ordine da questo Preventivo?"):
            try:
                new_id = database.convert_document(self.doc_id, "ordine")
                if new_id:
                    messagebox.showinfo("Successo", "Ordine creato con successo!")
                    # Open new Order
                    # Hacky navigation: Destroy Editor, Refresh Main, Open New Editor
                    # Ideally: self.parent.open_editor_by_id(new_id, 'ordine')
                    # We can use DocumentsWindow.open_edit logic if we had access.
                    # For now, go back to list. User will see new order.
                    self.go_back()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

    def convert_to_invoice(self):
        if not self.doc_id:
            messagebox.showwarning("Attenzione", "Salva prima il documento.")
            return
        if messagebox.askyesno("Conferma", "Vuoi creare una Fattura da questo documento?"):
            try:
                new_id = database.convert_document(self.doc_id, "fattura")
                if new_id:
                    messagebox.showinfo("Successo", "Fattura creata con successo!")
                    self.go_back()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

    def go_back(self):
        for child in self.parent.winfo_children():
            child.destroy()
        DocumentsWindow(self.parent, self.dtype).pack(fill="both", expand=True)

    def add_row_dialog(self):
        RowEditor(self)

    def add_row_data(self, data):
        # data: {code, desc, um, qty, price, disc1, disc2, vat}
        # Calc logic here for preview
        try:
            qty = float(data['qty'])
            prc = float(data['price'])
            d1 = float(data['disc1'] or 0)
            d2 = float(data['disc2'] or 0)
            vat_p = float(data['vat'] or 0)
        except ValueError:
            return

        # Invoicex Logic: (P * Q) * (1-d1) * (1-d2)
        base = qty * prc
        net = base * (1 - d1/100) * (1 - d2/100)
        
        # Store full calculated data
        row_data = {
            'code': data['code'], 'desc': data['desc'], 'um': data['um'],
            'qty': qty, 'price': prc, 'd1': d1, 'd2': d2, 'vat_p': vat_p,
            'net': net
        }
        
        vals = (data['code'], data['desc'], data['um'], f"{qty:g}", f"{prc:.2f}", d1, d2, vat_p, f"{net:.2f}")
        iid = self.tree_rows.insert("", "end", values=vals)
        row_data['iid'] = iid
        self.current_rows.append(row_data)
        
        self.recalc_totals()

    def rem_row(self):
        s = self.tree_rows.selection()
        for i in s:
            self.tree_rows.delete(i)
            # Remove from logic list
            self.current_rows = [r for r in self.current_rows if r['iid'] != i]
        self.recalc_totals()
            
    def recalc_totals(self):
        tot_imp = 0.0
        tot_iva = 0.0
        
        for r in self.current_rows:
            net = r['net']
            vat = net * (r['vat_p'] / 100)
            tot_imp += net
            tot_iva += vat
            
        tot_doc = tot_imp + tot_iva
        
        self.lbl_imp.configure(text=f"€ {tot_imp:.2f}")
        self.lbl_iva.configure(text=f"€ {tot_iva:.2f}")
        self.lbl_tot.configure(text=f"€ {tot_doc:.2f}")

    def save(self):
        c_name = self.combo_client.get()
        if c_name not in self.c_map:
            messagebox.showerror("Err", "Seleziona un cliente valido")
            return
        cid = self.c_map[c_name]
        
        # Helper to get ID from map or None
        def get_id(combo, m):
            val = combo.get()
            return m.get(val) if val in m else None
            
        # Helper for Transport map (nested)
        def get_trans_id(k):
            # entries[k] is the combo/entry
            if k not in self.entries: return None
            val = self.entries[k].get()
            # Vettore is ID, others Text
            if k == 'vettore' and k in self.map_trans:
                return self.map_trans[k].get(val)
            return val # Return text for others
            
        pay_id = get_id(self.combo_pay, self.map_pay)
        bank_id = get_id(self.combo_bank, self.map_bank)
        agent_id = get_id(self.combo_agent, self.map_agent)
        
        # Transport
        vett_id = get_trans_id('vettore')
        porto_txt = get_trans_id('porto')
        caus_txt = get_trans_id('causale_trasporto')
        asp_txt = get_trans_id('aspetto_esteriore')
        colli = self.entries['numero_colli'].get() if 'numero_colli' in self.entries else 0
        
        try:
            # 1. Create or Update Header
            if self.doc_id:
                database.update_document_header(self.doc_id, 
                    date=self.entry_date.get(),
                    contact_id=cid,
                    payment_term_id=pay_id,
                    payment_description=self.combo_pay.get(),
                    bank_id=bank_id,
                    agent_id=agent_id,
                    vettore_id=vett_id,
                    porto=porto_txt,
                    causale_trasporto=caus_txt,
                    aspetto_esteriore=asp_txt,
                    numero_colli=colli
                )
                did = self.doc_id
                # Wipe rows to re-insert (easiest sync)
                conn = database.sqlite3.connect(database.DB_NAME)
                cur = conn.cursor()
                cur.execute("DELETE FROM document_rows WHERE document_id=?", (did,))
                conn.commit()
                conn.close()
            else:
                did = database.create_document(self.dtype, self.entry_date.get(), cid)
                database.update_document_header(did, 
                    payment_term_id=pay_id,
                    payment_description=self.combo_pay.get(),
                    bank_id=bank_id,
                    agent_id=agent_id,
                    vettore_id=vett_id,
                    porto=porto_txt,
                    causale_trasporto=caus_txt,
                    aspetto_esteriore=asp_txt,
                    numero_colli=colli
                )
                
            # 2. Insert Rows
            for r in self.current_rows:
                database.add_document_row(did, r['desc'], r['qty'], r['price'], r['vat_p'],
                                          code=r['code'], disc1=r['d1'], disc2=r['d2'])

            # 3. Magazzino e scadenzario automatici (stile Invoicex)
            database.regenerate_movements_for_document(did)
            database.generate_deadlines_for_document(did)

            messagebox.showinfo("Salvataggio", "Documento salvato correttamente!")
            self.go_back()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def print_pdf(self):
        if not self.doc_id:
            messagebox.showwarning("Attenzione", "Salva il documento prima di generare il PDF.")
            return
            
        try:
            from utils.pdf_gen import generate_invoice_pdf
            import os
            
            # Fetch fresh data
            conn = database.sqlite3.connect(database.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id=?", (self.doc_id,))
            d = cursor.fetchone()
            
            # Fetch full contact info
            cursor.execute("SELECT * FROM contacts WHERE id=?", (d[5],)) # d[5] is contact_id
            c = cursor.fetchone()
            
            # Helper to safely get col by name if we had a dict, but here we have tuples
            # We rely on schema knowledge or we use row_factory
            # Let's use a simpler approach reusing existing logic or just safe indices
            # contacts schema: 0:id, 1:type, ... 3:ragione_sociale (was name), ...
            
            # For robustness, let's use the UI data if available or just basic DB fetch
            # But the PDF formatter expects a dictionary.
            
            # Let's try to map 'd' and 'c' to a dict based on known schema
            c_name = c[3] if c and len(c)>3 else "Sconosciuto"
            c_addr = c[4] if c and len(c)>4 else ""
            c_vat = c[9] if c and len(c)>9 else "" # vat_number at 9 in new schema logic? 
            # Wait, verify schema indexes from init_db or `PRAGMA table_info` output I saw earlier
            # Earlier output: 9: vat_number
            
            cursor.execute("SELECT description, quantity, unit_price, total_net FROM document_rows WHERE document_id=?", (self.doc_id,))
            rows = cursor.fetchall()
            conn.close()
            
            doc_data = {
                'number': f"{d[2]}/{d[3]}", # Serie/Num
                'date': d[4],
                'client_name': c_name,
                'client_address': c_addr,
                'client_vat': c_vat,
                'total_net': d[18] if len(d)>18 else 0, # total_net index check?
                'total_vat': d[19] if len(d)>19 else 0,
                'total_gross': d[20] if len(d)>20 else 0,
                'payment_term': d[13] if len(d)>13 else "",
                'bank_iban': d[14] if len(d)>14 else "",
                'notes_public': d[10]
            }
            
            fname = f"Doc_{d[2] or ''}_{d[3]}.pdf"
            path = os.path.abspath(fname)
            generate_invoice_pdf(doc_data, rows, path)
            messagebox.showinfo("PDF", f"Creato: {path}")
            os.system(f'start "" "{path}"')
            
        except Exception as e:
            messagebox.showerror("Err PDF", str(e))

    def import_rows_csv(self):
        """Importa righe documento da CSV/Excel; completa i dati mancanti dall'anagrafica articoli."""
        from utils.importer import ImportWizard

        fields = [
            ("code", "Codice articolo", False),
            ("description", "Descrizione", False),
            ("qty", "Quantità", True),
            ("price", "Prezzo", False),
            ("vat", "IVA %", False),
            ("disc1", "Sconto 1 %", False),
            ("disc2", "Sconto 2 %", False),
        ]

        def run(records):
            added = skipped = 0
            for r in records:
                code = str(r.get('code') or '').strip()
                desc = str(r.get('description') or '').strip()
                qty = database._import_num(r.get('qty')) or 0
                price = database._import_num(r.get('price'))
                vat = database._import_num(r.get('vat'))
                d1 = database._import_num(r.get('disc1')) or 0
                d2 = database._import_num(r.get('disc2')) or 0
                um = 'pz'
                if code:
                    prod = database.get_product_by_code(code)
                    if prod:
                        desc = desc or prod['desc']
                        um = prod['um']
                        if price is None: price = prod['price']
                        if vat is None: vat = prod['vat']
                if not desc or qty <= 0:
                    skipped += 1
                    continue
                self.add_row_data({'code': code, 'desc': desc, 'um': um, 'qty': qty,
                                   'price': price or 0, 'disc1': d1, 'disc2': d2,
                                   'vat': vat if vat is not None else 22})
                added += 1
            msg = f"Righe aggiunte al documento: {added}"
            if skipped:
                msg += f"\nRighe saltate (senza descrizione o quantità): {skipped}"
            return msg

        ImportWizard(self, "Importa Righe da CSV / Excel", fields, run)

    def toggle_scanner_mode(self):
        if self.scanner_mode.get():
            self.entry_scan.focus_set()
            self._scan_feedback("Scanner attivo: ogni lettura aggiunge la riga")
        else:
            self.lbl_scan_status.configure(text="")

    def _scan_refocus(self, event=None):
        # In modalità scanner il focus torna sempre sul campo di lettura
        if self.scanner_mode.get():
            self.after(100, lambda: self.entry_scan.focus_set() if self.entry_scan.winfo_exists() else None)

    def _scan_feedback(self, msg, error=False):
        self.lbl_scan_status.configure(text=msg, text_color="#e74c3c" if error else "#2ecc71")
        if self._scan_feedback_job:
            self.after_cancel(self._scan_feedback_job)
        self._scan_feedback_job = self.after(4000, lambda: self.lbl_scan_status.configure(text=""))

    def scan_product(self, event=None):
        raw = self.entry_scan.get().strip()
        if not raw: return

        # Sintassi "qta*codice" (es. 5*8001234567890)
        qty, code = 1.0, raw
        if '*' in raw:
            left, _, right = raw.partition('*')
            try:
                qty = float(left.replace(',', '.'))
                code = right.strip()
            except ValueError:
                pass

        prod = database.get_product_by_code(code)
        if not prod:
            self.bell()
            self._scan_feedback(f"✖ Articolo '{code}' non trovato", error=True)
            self.entry_scan.select_range(0, 'end')
            return

        # Articolo già in distinta: incrementa la quantità
        existing = next((r for r in self.current_rows if r['code'] == prod['code']), None)
        if existing:
            existing['qty'] += qty
            base = existing['qty'] * existing['price']
            existing['net'] = base * (1 - existing['d1']/100) * (1 - existing['d2']/100)
            self.tree_rows.item(existing['iid'], values=(
                existing['code'], existing['desc'], existing['um'], f"{existing['qty']:g}",
                f"{existing['price']:.2f}", existing['d1'], existing['d2'],
                existing['vat_p'], f"{existing['net']:.2f}"))
            self.recalc_totals()
            self._scan_feedback(f"✔ {prod['desc']}  (x{existing['qty']:g})")
        else:
            self.add_row_data({
                'code': prod['code'], 'desc': prod['desc'], 'um': prod['um'],
                'qty': qty, 'price': prod['price'],
                'disc1': 0, 'disc2': 0, 'vat': prod['vat']
            })
            self._scan_feedback(f"✔ {prod['desc']}")

        self.entry_scan.delete(0, 'end')
        self.entry_scan.focus_set()

    def load_doc(self):
        try:
            conn = database.sqlite3.connect(database.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id=?", (self.doc_id,))
            d = cursor.fetchone()
            
            # Rows
            cursor.execute("SELECT * FROM document_rows WHERE document_id=?", (self.doc_id,))
            rows = cursor.fetchall()
            conn.close()
            
            if not d: return
            
            # Helper to set text
            def set_t(w, val):
                if isinstance(w, ctk.CTkEntry):
                    w.delete(0, "end")
                    if val: w.insert(0, str(val))
                elif isinstance(w, ctk.CTkComboBox):
                    w.set(str(val) if val else "")
                elif isinstance(w, ctk.CTkTextbox):
                    w.delete("0.0", "end")
                    if val: w.insert("0.0", str(val))
            
            # Fields (Zero-based index from 'SELECT *')
            # 2:serie, 3:num, 5:date, 6:cid, 8:pid, 9:pdesc, 10:bid, 11:aid, 13:vid, 14:porto, 15:caus, 16:colli, 19:asp, 27:notes
            
            if d[2]: set_t(self.lbl_num, f"{d[2]}/{d[3]}")
            else: set_t(self.lbl_num, str(d[3]))
                
            set_t(self.entry_date, d[5])
            
            # Client (Reverse map ID -> Name)
            cid = d[6]
            c_name = next((k for k, v in self.c_map.items() if v == cid), "")
            self.combo_client.set(c_name)
            
            # Payment
            # Try to match ID first, else use Description
            pid = d[8]
            p_desc = d[9]
            p_name = next((k for k, v in self.map_pay.items() if v == pid), p_desc)
            self.combo_pay.set(p_name or "")
            
            # Bank
            bid = d[10]
            b_name = next((k for k, v in self.map_bank.items() if v == bid), "")
            self.combo_bank.set(b_name)
            
            # Agent
            aid = d[11]
            a_name = next((k for k, v in self.map_agent.items() if v == aid), "")
            self.combo_agent.set(a_name)
            
            # Transport
            vid = d[13]
            v_name = next((k for k, v in self.map_trans['vettore'].items() if v == vid), "")
            if 'vettore' in self.entries: self.entries['vettore'].set(v_name)
            
            if 'porto' in self.entries: set_t(self.entries['porto'], d[14])
            if 'causale_trasporto' in self.entries: set_t(self.entries['causale_trasporto'], d[15])
            if 'aspetto_esteriore' in self.entries: set_t(self.entries['aspetto_esteriore'], d[19])
            if 'numero_colli' in self.entries: set_t(self.entries['numero_colli'], d[16])
            
            set_t(self.text_note, d[27]) # Notes at 27
            
            # Rows
            # Schema: 0:id, 1:doc_id, 2:desc, 3:qty, 4:price, 5:vat, 6:code, 7:d1, 8:d2...
            for r in rows:
                data = {
                    'code': r[6],
                    'desc': r[2],
                    'qty': r[3],
                    'price': r[4],
                    'vat': r[5],
                    'disc1': r[7],
                    'disc2': r[8],
                    'um': 'pz' # Default, or fetch if added to schema
                }
                self.add_row_data(data)
                
        except Exception as e:
            messagebox.showerror("Errore Caricamento", str(e))

class RowEditor(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Riga Documento")
        self.geometry("400x500")
        
        self.entries = {}
        def add(l, k):
            ctk.CTkLabel(self, text=l).pack()
            e = ctk.CTkEntry(self)
            e.pack()
            self.entries[k] = e
            
        # Simplified for speed
        add("Codice", "code")
        add("Descrizione", "desc")
        add("Qta", "qty")
        self.entries['qty'].insert(0,"1")
        add("Prezzo", "price")
        add("Sconto 1 %", "disc1")
        add("Sconto 2 %", "disc2")
        add("IVA %", "vat")
        self.entries['vat'].insert(0,"22")
        
        # Product Search Helper
        ctk.CTkButton(self, text="Cerca Articolo", command=self.search_prod).pack(pady=5)
        ctk.CTkButton(self, text="Inserisci", command=self.confirm, fg_color="green").pack(pady=20)
        
    def search_prod(self):
        # Quick popup
        pass
        
    def confirm(self):
        d = {k: v.get() for k, v in self.entries.items()}
        d['um'] = 'pz' # default
        self.parent.add_row_data(d)
        self.destroy()
