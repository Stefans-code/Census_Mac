import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, Menu, filedialog
import sys
import os
import database
from PIL import Image

# Ensure we can import views
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import views after path setup
import views.auxiliary
import views.parameters
from utils import theme

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- Constants (compatibilità: ora derivano dal tema) ---
COLOR_BG = theme.BG
COLOR_ACCENT = theme.ACCENT
COLOR_ACCENT_HOVER = theme.ACCENT_H
COLOR_SURFACE = theme.SURFACE
COLOR_TEXT = theme.TEXT
FONT_TITLE = theme.font(24, bold=True)

class CensusModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Census ERP")
        self.geometry("1100x700")
        self.state("zoomed")
        self.configure(fg_color=theme.BG)

        # DB pronto prima di costruire qualsiasi vista
        database.init_db()
        # Stile scuro globale per tutte le tabelle ttk
        theme.setup_treeview_style()

        # Set Window Icon
        import sys, os
        try:
            if getattr(sys, 'frozen', False):
                # If run via PyInstaller
                icon_path = os.path.join(sys._MEIPASS, "icon.ico")
            else:
                icon_path = "icon.ico"
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Warning: Could not set icon: {e}")
        
        # --- 1. MENUBAR (Top System Menu) ---
        self.menubar = Menu(self)
        self.config(menu=self.menubar)
        
        # Helper to add menus
        def add_menu(label, items):
            m = Menu(self.menubar, tearoff=0)
            for lbl, cmd in items:
                if lbl == "-": 
                    m.add_separator()
                elif isinstance(cmd, list): # Submenu
                    sub = Menu(m, tearoff=0)
                    for sub_lbl, sub_cmd in cmd:
                        sub.add_command(label=sub_lbl, command=sub_cmd)
                    m.add_cascade(label=lbl, menu=sub)
                else: 
                    m.add_command(label=lbl, command=cmd)
            self.menubar.add_cascade(label=label, menu=m)

        def wip(name):
             return lambda: messagebox.showinfo("In Sviluppo", f"Gestione {name} in arrivo...")

        # --- ANAGRAFICHE ---
        add_menu("Anagrafiche", [
            ("Azienda", lambda: self.open_module("settings")),
            ("-", None),
            ("Clienti/Fornitori", lambda: self.open_module("contacts")),
            ("Categorie Clienti/Fornitori", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "client_categories", "Categorie Clienti")),
            ("-", None),
            ("Articoli", lambda: self.open_module("products")),
            ("Categorie Articoli", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "categories", "Categorie Articoli")),
            ("Sottocategorie Articoli", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "subcategories", "Sottocategorie Articoli")),
            ("-", None),
            ("Codici IVA", lambda: self.open_aux_window(views.parameters.VatRatesEditor, "vat_rates", "Codici IVA")),
            ("Banche", lambda: self.open_aux_window(views.parameters.BanksEditor, "banks", "Banche")),
            ("Conti Correnti Aziendali", lambda: self.open_aux_window(views.parameters.CompanyAccountsEditor, "company_accounts", "Conti Correnti")),
            ("-", None),
            ("Listini", lambda: self.open_aux_window(views.parameters.PriceListsEditor, "price_lists", "Listini")),
            ("Tipi Pagamento", lambda: self.open_aux_window(views.parameters.PaymentsEditor, "payment_terms", "Tipi Pagamento")),
            ("-", None),
            ("Aspetto esteriore dei beni", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "aspetto_beni", "Aspetto Beni")),
            ("Causali di Trasporto", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "causali_trasporto", "Causali di Trasporto")),
            ("Tipi Porto", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "porti", "Tipi Porto")),
            ("Vettori", lambda: self.open_aux_window(views.parameters.CarriersEditor, "vettori", "Vettori")),
            ("Modalità di Consegna", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "delivery_methods", "Modalità di Consegna")),
            ("-", None),
            ("Stati Preventivo/Ordine", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "document_statuses", "Anagrafica Stati Preventivo/Ordine")),
            ("-", None),
            ("Comuni italiani", lambda: self.open_aux_window(views.parameters.CitiesEditor, "cities", "Comuni italiani")),
            ("Nazioni", lambda: self.open_aux_window(views.auxiliary.TabbedMasterDataEditor, "countries", "Nazioni")),
            ("Esci", self.quit)
        ])

        # --- GESTIONE ---
        add_menu("Gestione", [
            ("Documenti di Vendita", [
                ("Preventivi e Ordini", lambda: self.open_module("documents", "preventivo")),
                ("DDT", lambda: self.open_module("documents", "ddt")),
                ("Fatture", lambda: self.open_module("documents", "fattura"))
            ]),
            ("Documenti di Acquisto", [
                ("Preventivi e Ordini", lambda: self.open_module("documents", "ordine_acquisto")),
                ("DDT", lambda: self.open_module("documents", "ddt_acquisto")),
                ("Fatture", lambda: self.open_module("documents", "fattura_acquisto"))
            ]),
            ("-", None),
            ("Scadenzario", lambda: self.open_module("scadenzario")),
            ("Prima Nota", lambda: self.open_module("primanota")),
            ("Ristampa distinte Ri.Ba.", lambda: self.open_module("riba_distinte"))
        ])

        # --- MAGAZZINO ---
        add_menu("Magazzino", [
            ("Gestione Movimenti", lambda: self.open_module("movements")),
            ("-", None),
            ("Giacenze", lambda: self.open_module("inventory")),
            ("Report scorta minima", lambda: self.open_module("inventory", "low")),
            ("Ultimi prezzi", lambda: self.open_module("last_prices")),
            ("-", None),
            ("Giacenze per Matricole", wip("Giacenze Matricole")),
            ("Giacenze per Lotti", wip("Giacenze Lotti")),
            ("-", None),
            ("Anagrafica Depositi", wip("Depositi")),
            ("Impostazione Deposito Predefinito", wip("Deposito Default"))
        ])

        # --- GESTIONE IVA ---
        add_menu("Gestione IVA", [
            ("Registro IVA Vendite", lambda: self.open_module("vat_register", "vendite")),
            ("Registro IVA Acquisti", lambda: self.open_module("vat_register", "acquisti"))
        ])

        # --- STATISTICHE ---
        add_menu("Statistiche", [
            ("Ordinato / Bollettato / Fatturato", lambda: self.open_module("stats", "obf")),
            ("Totale Fatture", lambda: self.open_module("stats", "fatture")),
            ("Chi / Cosa", lambda: self.open_module("stats", "chicosa")),
            ("-", None),
            ("Export Acquisti / Vendite", wip("Export")),
            ("Chi / Cosa avanzato", wip("Chi / Cosa Adv")),
            ("Elenco DDT", lambda: self.open_module("documents", "ddt")),
            ("Consegne", wip("Consegne"))
        ])

        # --- UTILITA ---
        add_menu("Utilità", [
            ("Impostazioni", lambda: self.open_module("settings")),
            ("-", None),
            ("Copia di sicurezza", self.do_backup),
            ("Recupero Database", self.do_restore),
            ("-", None),
            ("Controlla integrita' dei dati", self.do_integrity),
            ("Ottimizzazione database", self.do_vacuum),
            ("-", None),
            ("Controlla aggiornamenti", wip("Aggiornamenti")),
            ("Backup e Ripristino con Dropbox", wip("Dropbox")),
            ("Plugins", wip("Plugins"))
        ])

        # --- AGENTI ---
        add_menu("Agenti", [
            ("Anagrafica Agenti", lambda: self.open_module("agents")),
            ("Situazione Agenti", lambda: self.open_module("agents", "situazione"))
        ])

        # --- IMPORT/EXPORT ---
        def import_products_menu():
            from utils.importer import open_products_import
            open_products_import(self, on_done=self.update_status_bar)

        def import_contacts_menu():
            from utils.importer import open_contacts_import
            open_contacts_import(self, on_done=self.update_status_bar)

        add_menu("Import/Export", [
            ("Importa Articoli (CSV/Excel)", import_products_menu),
            ("Importa Clienti/Fornitori (CSV/Excel)", import_contacts_menu),
            ("-", None),
            ("Export Teamsystem FATSEQ", wip("Teamsystem")),
            ("Export Datev Koinos", wip("Datev")),
            ("Export Filconad", wip("Filconad")),
            ("Export Ipsoa", wip("Ipsoa")),
            ("Export Profis", wip("Profis")),
            ("Export Dati Fatture - Esterometro 2019", wip("Esterometro")),
            ("Export Dati Fatture - Spesometro", wip("Spesometro")),
            ("EasyFatt XML", [
                ("Esporta XML", wip("EasyFatt Export"))
            ])
        ])

        # Removed Finestre and Aiuto as requested

        # --- 2. MODERN TOOLBAR ---
        self.toolbar = ctk.CTkFrame(self, height=64, corner_radius=12,
                                    fg_color=theme.SURFACE, border_width=1, border_color=theme.BORDER)
        self.toolbar.pack(side="top", fill="x", padx=12, pady=(10, 0))

        def add_tile(parent, text, icon, color, cmd):
            btn = ctk.CTkButton(parent, text=f"{icon}  {text}", command=cmd,
                                width=10, height=36,
                                corner_radius=8,
                                fg_color="transparent", hover_color=theme.SURFACE_2,
                                border_width=1, border_color=theme.BORDER,
                                font=theme.font(12, bold=True),
                                text_color=color, anchor="center")
            btn.pack(side="left", padx=3, pady=10)

        def add_separator(parent):
            sep = ctk.CTkFrame(parent, width=1, height=28, fg_color=theme.BORDER)
            sep.pack(side="left", padx=8, pady=16)

        # Home
        toolbar_inner = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        toolbar_inner.pack(expand=True, anchor="center")

        add_tile(toolbar_inner, "HOME", "🏠", theme.TEXT, lambda: self.show_frame("HomeFrame"))
        add_separator(toolbar_inner)

        # VENDITE
        add_tile(toolbar_inner, "PREVENTIVI/ORDINI", "📄", theme.GREEN, lambda: self.open_module("documents", "preventivo"))
        add_tile(toolbar_inner, "DDT", "🚚", theme.GREEN, lambda: self.open_module("documents", "ddt"))
        add_tile(toolbar_inner, "FATTURE", "💶", theme.GREEN, lambda: self.open_module("documents", "fattura"))

        add_separator(toolbar_inner)

        # ACQUISTI
        add_tile(toolbar_inner, "ORDINI ACQ.", "📥", "#ff8a7a", lambda: self.open_module("documents", "ordine_acquisto"))
        add_tile(toolbar_inner, "DDT ACQ.", "🚛", "#ff8a7a", lambda: self.open_module("documents", "ddt_acquisto"))
        add_tile(toolbar_inner, "FATT. ACQ.", "💸", "#ff8a7a", lambda: self.open_module("documents", "fattura_acquisto"))

        add_separator(toolbar_inner)

        # ANAGRAFICHE & MAGAZZINO
        add_tile(toolbar_inner, "CLIENTI", "👥", "#6aa9ff", lambda: self.open_module("contacts"))
        add_tile(toolbar_inner, "ARTICOLI", "📦", theme.PURPLE, lambda: self.open_module("products"))
        add_tile(toolbar_inner, "MAGAZZINO", "🏭", theme.CYAN, lambda: self.open_module("movements"))
        add_tile(toolbar_inner, "SCADENZARIO", "📅", theme.ORANGE, lambda: self.open_module("scadenzario"))

        # --- 3. MAIN AREA ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color=theme.BG)
        self.main_area.pack(fill="both", expand=True)

        # --- 4. STATUS BAR ---
        self.status_bar = ctk.CTkFrame(self, height=26, corner_radius=0, fg_color=theme.SURFACE)
        self.status_bar.pack(side="bottom", fill="x")
        self.lbl_status = ctk.CTkLabel(self.status_bar, text="", font=theme.font(10),
                                       text_color=theme.TEXT_DIM, anchor="w")
        self.lbl_status.pack(side="left", padx=12)
        ctk.CTkLabel(self.status_bar, text="Census ERP 2.0", font=theme.font(10, bold=True),
                     text_color=theme.TEXT_DIM).pack(side="right", padx=12)

        self.open_windows = {}
        self.show_dashboard()
        self.update_status_bar()

    def update_status_bar(self):
        try:
            d = database.get_dashboard_data()
            self.lbl_status.configure(
                text=f"📦 {d['articoli']} articoli   •   👥 {d['clienti']} clienti   •   📄 {d['doc_anno']} documenti quest'anno")
        except Exception:
            self.lbl_status.configure(text="")

    # ==================== DASHBOARD ====================
    def show_dashboard(self):
        for child in self.main_area.winfo_children():
            child.destroy()

        d = database.get_dashboard_data()

        wrap = ctk.CTkFrame(self.main_area, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=24, pady=18)

        # Header
        head = ctk.CTkFrame(wrap, fg_color="transparent")
        head.pack(fill="x", pady=(0, 14))
        from datetime import datetime as _dt
        mesi = ["gennaio","febbraio","marzo","aprile","maggio","giugno",
                "luglio","agosto","settembre","ottobre","novembre","dicembre"]
        oggi = _dt.now()
        ctk.CTkLabel(head, text="Dashboard", font=theme.font(26, bold=True),
                     text_color=theme.TEXT).pack(side="left")
        ctk.CTkLabel(head, text=f"  {oggi.day} {mesi[oggi.month-1]} {oggi.year}",
                     font=theme.font(13), text_color=theme.TEXT_DIM).pack(side="left", pady=(8, 0))

        # KPI row
        kpis = ctk.CTkFrame(wrap, fg_color="transparent")
        kpis.pack(fill="x", pady=(0, 16))
        kpis.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="kpi")

        cards = [
            ("Fatturato mese", theme.euro(d['fatt_mese']), theme.GREEN, ""),
            ("Fatturato anno", theme.euro(d['fatt_anno']), theme.ACCENT, f"{d['doc_anno']} documenti"),
            ("Da incassare", theme.euro(d['da_incassare']), theme.ORANGE, "scadenze aperte"),
            ("Da pagare", theme.euro(d['da_pagare']), "#ff8a7a", "scadenze aperte"),
            ("Sotto scorta", str(d['sotto_scorta']), theme.PURPLE, "articoli da riordinare"),
        ]
        for i, (t, v, c, s) in enumerate(cards):
            theme.kpi_card(kpis, t, v, c, s).grid(row=0, column=i, padx=6, sticky="nsew")

        # Pannelli: ultime fatture + prossime scadenze
        panels = ctk.CTkFrame(wrap, fg_color="transparent")
        panels.pack(fill="both", expand=True)
        panels.grid_columnconfigure((0, 1), weight=1, uniform="pan")
        panels.grid_rowconfigure(0, weight=1)

        def mini_table(parent, title, cols, rows, empty_msg):
            panel = theme.card(parent)
            theme.section_title(panel, title).pack(fill="x", padx=16, pady=(12, 6))
            if not rows:
                ctk.CTkLabel(panel, text=empty_msg, font=theme.font(11),
                             text_color=theme.TEXT_DIM).pack(pady=30)
                return panel
            tree = ttk.Treeview(panel, columns=cols, show="headings", height=6)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=110, anchor="w")
            tree.column(cols[-1], anchor="e")
            for r in rows:
                tree.insert("", "end", values=r)
            theme.stripe(tree)
            tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            return panel

        fatt_rows = [(r[0], r[1], r[2], theme.euro(r[3])) for r in d['ultime_fatture']]
        scad_rows = [(r[0], r[1], r[2], theme.euro(r[3])) for r in d['prossime_scadenze']]

        mini_table(panels, "🧾  Ultime fatture", ("Data", "Numero", "Cliente", "Importo"),
                   fatt_rows, "Nessuna fattura emessa").grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        mini_table(panels, "⏰  Prossime scadenze", ("Data", "Tipo", "Soggetto", "Importo"),
                   scad_rows, "Nessuna scadenza aperta").grid(row=0, column=1, padx=(8, 0), sticky="nsew")

    # ==================== UTILITÀ DATABASE ====================
    def do_backup(self):
        from datetime import datetime as _dt
        default = f"census_backup_{_dt.now().strftime('%Y%m%d_%H%M')}.db"
        path = filedialog.asksaveasfilename(title="Copia di sicurezza", initialfile=default,
                                            defaultextension=".db",
                                            filetypes=[("Database", "*.db"), ("Tutti i file", "*.*")])
        if not path: return
        try:
            database.backup_db(path)
            messagebox.showinfo("Backup", f"Copia di sicurezza creata:\n{path}")
        except Exception as e:
            messagebox.showerror("Backup", f"Errore durante il backup:\n{e}")

    def do_restore(self):
        path = filedialog.askopenfilename(title="Recupero Database",
                                          filetypes=[("Database", "*.db"), ("Tutti i file", "*.*")])
        if not path: return
        if not messagebox.askyesno("Recupero Database",
                                   "Il database attuale verrà SOSTITUITO con il backup selezionato.\nContinuare?"):
            return
        try:
            database.restore_db(path)
            messagebox.showinfo("Recupero", "Database ripristinato correttamente.")
            self.show_dashboard()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Recupero", f"Errore durante il ripristino:\n{e}")

    def do_integrity(self):
        try:
            res = database.integrity_check()
            if res == "ok":
                messagebox.showinfo("Integrità", "✔ Il database è integro.")
            else:
                messagebox.showwarning("Integrità", f"Problemi rilevati:\n{res}")
        except Exception as e:
            messagebox.showerror("Integrità", str(e))

    def do_vacuum(self):
        try:
            database.vacuum_db()
            messagebox.showinfo("Ottimizzazione", "✔ Database ottimizzato (VACUUM completato).")
        except Exception as e:
            messagebox.showerror("Ottimizzazione", str(e))

    def adjust_color(self, hex_color, factor=0.8):
        return theme.darken(hex_color, factor)

    def open_module(self, module_name, sub_type=None):
        try:
            # Clear main area
            for child in self.main_area.winfo_children():
                child.destroy()
                
            frame = None
            if module_name == "dashboard":
                self.setup_complete_dashboard(self.main_area)
                
            elif module_name == "documents":
                 from views.documents import DocumentsWindow
                 frame = DocumentsWindow(self.main_area, sub_type)
            
            elif module_name == "products":
                from views.products import ProductsWindow
                frame = ProductsWindow(self.main_area)
                
            elif module_name == "contacts":
                from views.contacts import ContactsWindow
                frame = ContactsWindow(self.main_area, sub_type)
                
            elif module_name == "movements":
                from views.movements import MovementsWindow
                frame = MovementsWindow(self.main_area)

            elif module_name == "inventory":
                from views.movements import InventoryWindow
                frame = InventoryWindow(self.main_area, only_low=(sub_type == "low"))

            elif module_name == "last_prices":
                from views.movements import LastPricesWindow
                frame = LastPricesWindow(self.main_area)

            elif module_name == "stats":
                from views.statistics import StatisticsWindow
                frame = StatisticsWindow(self.main_area, start_tab=sub_type)

            elif module_name == "vat_register":
                from views.statistics import VatRegisterWindow
                frame = VatRegisterWindow(self.main_area, purchases=(sub_type == "acquisti"))

            elif module_name == "agents":
                from views.agents import AgentsWindow
                frame = AgentsWindow(self.main_area, start_tab=sub_type)

            elif module_name == "scadenzario":
                # from views.scadenzario import ScadenzarioWindow # REMOVED: Using local class
                frame = ScadenzarioWindow(self.main_area, self) # Pass self as controller
            
            elif module_name == "riba_distinte":
                # This is the new module to open RibaDistinteFrame
                frame = RibaDistinteFrame(self.main_area, self)

            elif module_name == "primanota":
                from views.primanota import PrimaNotaWindow
                frame = PrimaNotaWindow(self.main_area)

            elif module_name == "settings":
                 from views.settings import SettingsWindow
                 win = SettingsWindow(self) # Toplevel
                 return

            if frame:
                frame.pack(fill="both", expand=True)
                
        except Exception as e:
            messagebox.showerror("Errore Modulo", f"Impossibile aprire '{module_name}':\n{e}")

    def open_aux_window(self, cls, table, title):
        for child in self.main_area.winfo_children():
            child.destroy()
        cls(self.main_area, table, title).pack(fill="both", expand=True)

    # This method is needed by ScadenziarioFrame and RibaDistinteFrame
    # to navigate between them, acting as a 'controller'.
    def show_frame(self, page_name):
        # This implementation assumes 'page_name' refers to a module name
        # that can be opened by open_module.
        # If 'page_name' is "RibaDistinteFrame", it maps to "riba_distinte" module.
        if page_name == "RibaDistinteFrame":
            self.open_module("riba_distinte")
        elif page_name == "ScadenziarioFrame": # If ScadenziarioFrame needs to be opened this way
            self.open_module("scadenzario")
        elif page_name == "HomeFrame":
            self.show_dashboard()
            self.update_status_bar()
        else:
            messagebox.showerror("Navigazione", f"Modulo '{page_name}' non riconosciuto per show_frame.")


class BaseSubFrame(ctk.CTkFrame):
    """Helper class to provide common styling and Back button"""
    def __init__(self, parent, controller, title):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        
        # Header Frame
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=40)
        
        # Back Button
        back_btn = ctk.CTkButton(header, text="← Indietro", font=("Segoe UI", 14), width=100, height=32,
                                 fg_color="transparent", border_width=1, border_color="#555",
                                 command=lambda: self.controller.open_module("scadenzario")) # Changed to go back to scadenzario
        back_btn.pack(side="left")
        
        # Title
        lbl = ctk.CTkLabel(header, text=title, font=FONT_TITLE, text_color=COLOR_TEXT)
        lbl.pack(side="left", padx=30)
        
        self.content_area = ctk.CTkFrame(self, fg_color=COLOR_BG) # Transparent container
        self.content_area.pack(expand=True, fill="both", padx=40, pady=(0, 40))


# The original ScadenziarioWindow from views.scadenzario needs to be modified
# to include the "DISTINTE RI.BA" button.
# Since the user provided a ScadenziarioFrame class, I will assume this is the
# intended replacement or modification for views.scadenzario.ScadenziarioWindow.
# I will place it here for now, but ideally it should be in views/scadenzario.py
# and imported. For this edit, I'll put it in main.py.

# If views.scadenzario.ScadenziarioWindow already exists, this will conflict.
# Assuming the user wants to replace/update it with this definition.
class ScadenzarioWindow(ctk.CTkFrame):
    """Scadenzario: scadenze manuali + quelle generate automaticamente dalle fatture."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.BG)
        self.controller = controller

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(head, text="Scadenzario", font=theme.font(22, bold=True),
                     text_color=theme.TEXT).pack(side="left")
        ctk.CTkButton(head, text="+ SCADENZA", width=110, fg_color=theme.GREEN_D,
                      hover_color=theme.darken(theme.GREEN_D),
                      command=self.add_deadline_dialog).pack(side="right", padx=4)
        ctk.CTkButton(head, text="DISTINTE RI.BA", width=120, fg_color=theme.SURFACE_2,
                      hover_color=theme.BORDER,
                      command=lambda: controller.show_frame("RibaDistinteFrame")).pack(side="right", padx=4)

        # Filtri + azioni
        filt = theme.card(self)
        filt.pack(fill="x", padx=20, pady=(0, 10))
        inner = ctk.CTkFrame(filt, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(inner, text="Tipo:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(0, 6))
        self.filter_type = ctk.CTkOptionMenu(inner, values=["Tutti", "Incasso", "Pagamento"],
                                             width=110, command=lambda x: self.update_data())
        self.filter_type.pack(side="left", padx=(0, 14))

        ctk.CTkLabel(inner, text="Stato:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(0, 6))
        self.filter_status = ctk.CTkOptionMenu(inner, values=["Aperte", "Pagate", "Tutte"],
                                               width=100, command=lambda x: self.update_data())
        self.filter_status.pack(side="left", padx=(0, 14))

        ctk.CTkButton(inner, text="✔ Segna Pagato", width=120, fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_H,
                      command=lambda: self.set_status("Pagato")).pack(side="left", padx=3)
        ctk.CTkButton(inner, text="↩ Riapri", width=90, fg_color=theme.SURFACE_2,
                      hover_color=theme.BORDER,
                      command=lambda: self.set_status("Da Pagare")).pack(side="left", padx=3)
        ctk.CTkLabel(inner, text="(doppio clic = pagato/riapri)", font=theme.font(10),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=10)

        # Tabella
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 4))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        cols = ("Data", "Tipo", "Soggetto", "Importo", "Stato", "Note")
        self.tree = ttk.Treeview(body, columns=cols, show="headings")
        widths = {"Data": 110, "Tipo": 100, "Soggetto": 260, "Importo": 110,
                  "Stato": 100, "Note": 200}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="e" if c == "Importo" else "w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(body, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-Button-1>", self.toggle_paid)

        # Totali
        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=20, pady=(4, 14))
        self.lbl_totals = ctk.CTkLabel(foot, text="", font=theme.font(13, bold=True),
                                       text_color=theme.TEXT)
        self.lbl_totals.pack(side="right")

        self.update_data()

    def update_data(self):
        for w in self.tree.get_children():
            self.tree.delete(w)

        ft = self.filter_type.get()
        req_type = None if ft == "Tutti" else ft
        st_map = {"Aperte": "Da Pagare", "Pagate": "Pagato", "Tutte": None}
        req_status = st_map.get(self.filter_status.get())

        from datetime import date as _date
        today = _date.today().isoformat()

        items = database.get_deadlines_full(req_type, req_status)
        tot_in = tot_out = 0.0
        for item in items:
            # id, date, type, entity, amount, status, notes, doc_id
            tags = []
            if item[5] == "Pagato":
                tags.append("green")
            elif str(item[1]) < today:
                tags.append("red")  # scaduta
            if item[5] != "Pagato":
                if item[2] == "Incasso": tot_in += item[4] or 0
                else: tot_out += item[4] or 0
            self.tree.insert("", "end", iid=str(item[0]), values=(
                item[1], item[2], item[3], theme.euro(item[4]), item[5], item[6]),
                tags=tuple(tags))
        theme.stripe(self.tree)
        self.lbl_totals.configure(
            text=f"Da incassare: {theme.euro(tot_in)}      Da pagare: {theme.euro(tot_out)}")

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def set_status(self, status):
        did = self._selected_id()
        if not did:
            return
        database.set_deadline_status(did, status)
        self.update_data()

    def toggle_paid(self, event=None):
        did = self._selected_id()
        if not did:
            return
        current = self.tree.item(str(did))['values'][4]
        database.set_deadline_status(did, "Da Pagare" if current == "Pagato" else "Pagato")
        self.update_data()

    def add_deadline_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nuova Scadenza")
        dialog.geometry("420x420")
        dialog.configure(fg_color=theme.BG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nuova Scadenza", font=theme.font(16, bold=True),
                     text_color=theme.TEXT).pack(pady=(16, 10))

        def field(label):
            ctk.CTkLabel(dialog, text=label, font=theme.font(11),
                         text_color=theme.TEXT_DIM).pack(anchor="w", padx=24, pady=(6, 0))

        from datetime import date as _date
        field("Data (YYYY-MM-DD)")
        e_date = ctk.CTkEntry(dialog)
        e_date.insert(0, _date.today().isoformat())
        e_date.pack(fill="x", padx=24)

        field("Tipo")
        e_type = ctk.CTkOptionMenu(dialog, values=["Incasso", "Pagamento"])
        e_type.pack(fill="x", padx=24)

        field("Soggetto (Cliente/Fornitore)")
        e_entity = ctk.CTkEntry(dialog)
        e_entity.pack(fill="x", padx=24)

        field("Importo")
        e_amount = ctk.CTkEntry(dialog)
        e_amount.pack(fill="x", padx=24)

        def save():
            try:
                amount = float((e_amount.get() or "0").replace(',', '.'))
            except ValueError:
                messagebox.showwarning("Scadenza", "Importo non valido.", parent=dialog)
                return
            database.add_deadline(e_date.get(), e_type.get(), e_entity.get(), amount, "Da Pagare")
            dialog.destroy()
            self.update_data()

        ctk.CTkButton(dialog, text="SALVA", fg_color=theme.GREEN_D,
                      hover_color=theme.darken(theme.GREEN_D), height=36,
                      command=save).pack(pady=18, padx=24, fill="x")


class RibaDistinteFrame(BaseSubFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Lista distinte Ri.Ba.")

        # Subtitle
        ctk.CTkLabel(self.content_area, text="fai doppio clic sulla distinta per ristamparla", text_color="gray").pack(pady=(0, 20))

        # List
        self.scroll_list = ctk.CTkScrollableFrame(self.content_area)
        self.scroll_list.pack(fill="both", expand=True)

        self.update_data()

    def update_data(self):
        for w in self.scroll_list.winfo_children():
            w.destroy()

        # Dummy data if empty, or fetch from DB
        items = database.get_riba_distinte()
        if not items:
            # Demo Data
            items = [
                (1, "RB-2025-001", "2025-01-10", "Incasso Clienti"),
                (2, "RB-2025-002", "2025-01-11", "Incasso Clienti"),
            ]

        # Header
        h_frame = ctk.CTkFrame(self.scroll_list, fg_color="#444", height=30)
        h_frame.pack(fill="x")
        ctk.CTkLabel(h_frame, text="NUMERO", width=200, anchor="w", font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="DATA DI STAMPA", width=200, anchor="w", font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="TIPO", width=200, anchor="w", font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)

        for item in items:
            # item: id, numero, data, tipo
            # Using Frame inside Button is tricky in ctk.
            # Instead build a frame that binds Click
            
            # Simplified: Just labels in a frame, bind click to frame and labels
            f = ctk.CTkFrame(self.scroll_list, fg_color="transparent", height=30)
            f.pack(fill="x", pady=1)
            
            l1 = ctk.CTkLabel(f, text=item[1], width=200, anchor="w")
            l1.pack(side="left", padx=5)
            l2 = ctk.CTkLabel(f, text=item[2], width=200, anchor="w")
            l2.pack(side="left", padx=5)
            l3 = ctk.CTkLabel(f, text=item[3], width=200, anchor="w")
            l3.pack(side="left", padx=5)
            
            # Bind Double Click
            for w in (f, l1, l2, l3):
                w.bind("<Double-Button-1>", lambda e, i=item: self.reprint_riba(i))

    def reprint_riba(self, item):
        messagebox.showinfo("Ristampa", f"Ristampa in corso della distinta {item[1]}...") 

if __name__ == "__main__":
    app = CensusModernApp()
    app.mainloop()
