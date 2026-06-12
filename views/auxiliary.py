import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import database

class SimpleTableEditor(ctk.CTkFrame):
    """
    Generic Editor for simple tables (id, name).
    Usage: SimpleTableEditor(parent, "vettori", "Vettori")
    """
    def __init__(self, parent, table_name, title):
        super().__init__(parent)
        self.table_name = table_name
        self.title_text = title
        
        # Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(top, text=f"Gestione {title}", font=("Arial", 20, "bold")).pack(side="left", padx=10)
        
        self.ent_name = ctk.CTkEntry(top, width=300, placeholder_text="Nuovo elemento...")
        self.ent_name.pack(side="left", padx=10)
        
        ctk.CTkButton(top, text="+ Aggiungi", command=self.add_item, width=100, fg_color="green").pack(side="left")
        ctk.CTkButton(top, text="Elimina Selezionato", command=self.delete_item, fg_color="red").pack(side="right", padx=10)
        
        # Tree
        self.tree = ttk.Treeview(self, columns=("ID", "Nome"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Descrizione")
        self.tree.column("ID", width=50)
        self.tree.column("Nome", width=500)
        
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.refresh()
        
    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        
        # Generic Fetch
        try:
            # Direct SQL since we couldn't add generic helper
            # (or we can add it now properly if we want, but let's be self-contained)
            conn = database.sqlite3.connect(database.DB_NAME)
            cur = conn.cursor()
            cur.execute(f"SELECT id, name FROM {self.table_name}")
            rows = cur.fetchall()
            conn.close()
            
            for r in rows:
                self.tree.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def add_item(self):
        name = self.ent_name.get()
        if not name: return
        try:
            conn = database.sqlite3.connect(database.DB_NAME)
            cur = conn.cursor()
            cur.execute(f"INSERT INTO {self.table_name} (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            self.ent_name.delete(0, "end")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            
    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Conferma", "Eliminare elemento?"):
            try:
                conn = database.sqlite3.connect(database.DB_NAME)
                cur = conn.cursor()
                cur.execute(f"DELETE FROM {self.table_name} WHERE id=?", (iid,))
                conn.commit()
                conn.close()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

class ComplexTableEditor(ctk.CTkFrame):
    """
    Editor for specific tables: Banks, Payments, VAT.
    """
    def __init__(self, parent, table_name, title):
        super().__init__(parent)
        self.table_name = table_name
        self.title_text = title
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Top: Title
        ctk.CTkLabel(self, text=f"Gestione {title}", font=("Arial", 20, "bold")).grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        # Middle: Form
        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        self.entries = {}
        
        # Schema definition based on table name
        self.fields = []
        if table_name == "banks":
            self.fields = [("Nome Banca", "name"), ("IBAN", "iban"), ("ABI", "abi"), ("CAB", "cab")]
        elif table_name == "payment_terms":
            self.fields = [("Descrizione", "name"), ("Giorni", "days"), ("Tipo", "type")]
        elif table_name == "vat_rates":
            self.fields = [("Codice", "code"), ("Descrizione", "description"), ("Aliquota %", "rate")]
        elif table_name == "categories":
            self.fields = [("Nome Categoria", "name")]
            
        for i, (lbl, key) in enumerate(self.fields):
            ctk.CTkLabel(form, text=lbl).grid(row=0, column=i*2, padx=5, pady=5)
            e = ctk.CTkEntry(form, width=150)
            e.grid(row=0, column=i*2+1, padx=5, pady=5)
            self.entries[key] = e
            
        ctk.CTkButton(form, text="Aggiungi", command=self.add_item, fg_color="green").grid(row=0, column=len(self.fields)*2, padx=10)
        
        # Bottom: List
        self.tree = ttk.Treeview(self, columns=[f[1] for f in self.fields], show="headings")
        for lbl, key in self.fields:
            self.tree.heading(key, text=lbl)
            self.tree.column(key, width=150)
            
        self.tree.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        ctk.CTkButton(self, text="Elimina Selezionato", command=self.delete_item, fg_color="red").grid(row=3, column=0, pady=10)
        
        self.refresh()
        
    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        try:
            conn = database.sqlite3.connect(database.DB_NAME)
            cur = conn.cursor()
            # Select columns dynamically
            cols = [f[1] for f in self.fields]
            c_str = ", ".join(cols)
            cur.execute(f"SELECT id, {c_str} FROM {self.table_name}")
            rows = cur.fetchall()
            conn.close()
            
            for r in rows:
                # r[0] is id, rest are values
                self.tree.insert("", "end", values=r[1:], tags=(str(r[0]),))
        except Exception as e:
            messagebox.showerror("Err", str(e))
            
    def add_item(self):
        vals = []
        keys = []
        for lbl, key in self.fields:
            val = self.entries[key].get()
            if not val and key != 'days': return 
            vals.append(val)
            keys.append(key)
            
        try:
            conn = database.sqlite3.connect(database.DB_NAME)
            cur = conn.cursor()
            q = ", ".join(["?"]*len(vals))
            k = ", ".join(keys)
            cur.execute(f"INSERT INTO {self.table_name} ({k}) VALUES ({q})", vals)
            conn.commit()
            conn.close()
            for e in self.entries.values(): e.delete(0, "end")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Err", str(e))
            
    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        if messagebox.askyesno("Confirm", "Delete?"):
            conn = database.sqlite3.connect(database.DB_NAME)
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self.table_name} WHERE id=?", (iid,))
            conn.commit()
            conn.close()
            self.refresh()
class TabbedMasterDataEditor(ctk.CTkFrame):
    def __init__(self, parent, table_name, title):
        super().__init__(parent)
        self.table_name = table_name
        self.title_text = title
        self.current_id = None
        
        # Schema Definition
        self.fields = [] # (Label, DB_Col, Type, Lookup/Vals)
        
        # Tables with Code + Name
        code_name_tables = [
            "categories", "client_categories", 
            "document_statuses", "delivery_methods",
            "porti", "causali_trasporto", "aspetto_beni", "vettori", "countries"
        ]
        
        if table_name in code_name_tables:
            self.fields = [
                ("Codice", "code", "entry", None),
                ("Descrizione", "name", "entry", None)
            ]
        elif table_name == "subcategories":
            self.fields = [
                ("Codice", "code", "entry", None),
                ("Categoria Padre", "category_id", "combo", "categories"),
                ("Descrizione", "name", "entry", None)
            ]
        
        # --- Toolbar ---
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(toolbar, text="📄 Nuovo", width=80, fg_color="#3498db", command=self.clear_form).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="❌ Elimina", width=80, fg_color="#e74c3c", command=self.delete_item).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="🔍 Trova", width=80, fg_color="#f39c12", command=lambda: self.tabs.set("Elenco")).pack(side="left", padx=2)
        
        # --- Tabs ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=5, pady=5)
        self.tabs.add("Dati")
        self.tabs.add("Elenco")
        
        # --- Tab: Dati (Form) ---
        t_dati = self.tabs.tab("Dati")
        
        self.entries = {}
        for i, (lbl, col, wtype, lookup) in enumerate(self.fields):
            ctk.CTkLabel(t_dati, text=lbl, anchor="e").grid(row=i, column=0, padx=10, pady=10, sticky="e")
            
            if wtype == "entry":
                e = ctk.CTkEntry(t_dati, width=300)
            elif wtype == "combo":
                vals = []
                self.lookup_map = {} # Store map for combos
                if lookup: # Table name
                    vals = self.load_lookup(lookup)
                e = ctk.CTkComboBox(t_dati, values=vals, width=300)
            
            e.grid(row=i, column=1, padx=10, pady=10, sticky="w")
            self.entries[col] = e
            
        # Button Bar for Form
        f_btns = ctk.CTkFrame(t_dati, fg_color="transparent")
        f_btns.grid(row=len(self.fields)+1, column=0, columnspan=2, pady=20)
        
        ctk.CTkButton(f_btns, text="Annulla", fg_color="gray", command=self.clear_form).pack(side="left", padx=10)
        ctk.CTkButton(f_btns, text="Salva", fg_color="#27ae60", command=self.save).pack(side="left", padx=10)
        
        # --- Tab: Elenco (List) ---
        t_list = self.tabs.tab("Elenco")
        
        cols = [f[0] for f in self.fields]
        self.tree = ttk.Treeview(t_list, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)
            
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        self.refresh_list()
        
    def load_lookup(self, table):
        # Returns list of names and builds dynamic map
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        cur.execute(f"SELECT id, name FROM {table}")
        rows = cur.fetchall()
        conn.close()
        
        # Create map: Name -> ID
        self.lookup_map = {r[1]: r[0] for r in rows}
        # Also ID -> Name for loading
        self.rev_lookup_map = {r[0]: r[1] for r in rows}
        
        return list(self.lookup_map.keys())

    def save(self):
        data = {}
        keys = []
        vals = []
        
        for lbl, col, wtype, lookup in self.fields:
            val = self.entries[col].get()
            if wtype == "combo" and lookup:
                # Resolve ID
                val = self.lookup_map.get(val, None)
            
            data[col] = val
            keys.append(col)
            vals.append(val)
            
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        
        try:
            if self.current_id:
                # Update
                set_clause = ", ".join([f"{k}=?" for k in keys])
                vals.append(self.current_id)
                cur.execute(f"UPDATE {self.table_name} SET {set_clause} WHERE id=?", vals)
            else:
                # Insert
                q_marks = ", ".join(["?"] * len(vals))
                cur.execute(f"INSERT INTO {self.table_name} ({', '.join(keys)}) VALUES ({q_marks})", vals)
                
            conn.commit()
            messagebox.showinfo("Info", "Salvato!")
            self.refresh_list()
            self.clear_form() # Reset to New
        except Exception as e:
            messagebox.showerror("Errore", str(e))
        finally:
            conn.close()

    def refresh_list(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        cols = [f[1] for f in self.fields]
        cur.execute(f"SELECT id, {', '.join(cols)} FROM {self.table_name}")
        rows = cur.fetchall()
        conn.close()
        
        for r in rows:
            # Resolve Lookups for Display
            display_vals = []
            for i, val in enumerate(r[1:]): # Skip ID
                # Check if this column is a lookup
                # This logic is a bit brittle, ideally map col index to lookup
                # fields[i] corresponds to r[i+1]
                field_def = self.fields[i]
                if field_def[2] == "combo":
                    # Try resolve
                     display_vals.append(self.rev_lookup_map.get(val, val))
                else:
                    display_vals.append(val)
            
            self.tree.insert("", "end", values=display_vals, tags=(str(r[0]),))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        iid = self.tree.item(sel[0])['tags'][0]
        self.load_item(iid)
        self.tabs.set("Dati")

    def load_item(self, iid):
        self.current_id = iid
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        # Fetch all fields
        cols = [f[1] for f in self.fields]
        cur.execute(f"SELECT {', '.join(cols)} FROM {self.table_name} WHERE id=?", (iid,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            for i, (lbl, col, wtype, lookup) in enumerate(self.fields):
                val = row[i]
                if wtype == "combo":
                    # Set Name from ID
                    if hasattr(self, 'rev_lookup_map'):
                        val = self.rev_lookup_map.get(val, "")
                    self.entries[col].set(str(val))
                else:
                    self.entries[col].delete(0, "end")
                    if val: self.entries[col].insert(0, str(val))

    def clear_form(self):
        self.current_id = None
        for k, e in self.entries.items():
            if isinstance(e, ctk.CTkEntry):
                e.delete(0, "end")
            else:
                e.set("")
        self.tabs.set("Dati")
        
    def delete_item(self):
        if not self.current_id:
             sel = self.tree.selection()
             if sel: self.current_id = self.tree.item(sel[0])['tags'][0]
             else: return

        if messagebox.askyesno("Conferma", "Eliminare?"):
            conn = database.sqlite3.connect(database.DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id=?", (self.current_id,))
            conn.commit()
            conn.close()
            self.refresh_list()
            self.clear_form()
