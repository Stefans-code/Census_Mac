import sqlite3
import os
from datetime import datetime

import sys

# Ensure DB is in the executable directory or local path
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    # Use dirname of executable to store DB persistently
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running from script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(BASE_DIR, "magazzino.db")

def init_db():
    """Initializes the database tables with FULL ERP SCHEMA."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # --- 1. COMPANY SETTINGS (Dati Azienda) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_settings (
            id INTEGER PRIMARY KEY, -- Single row usually
            name TEXT,
            address TEXT,
            city TEXT,
            zip_code TEXT,
            province TEXT,
            country TEXT DEFAULT 'Italia',
            vat_number TEXT,
            tax_code TEXT,
            email TEXT,
            pec TEXT,
            phone TEXT,
            fax TEXT,
            website TEXT,
            logo_path TEXT,
            default_vat_rate REAL DEFAULT 22.0,
            default_bank TEXT,
            default_payment_terms TEXT,
            regime_fiscale TEXT,
            sdi_code TEXT
        )
    ''')
    
    # Migration for new columns
    try: cursor.execute("ALTER TABLE company_settings ADD COLUMN fax TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE company_settings ADD COLUMN regime_fiscale TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE company_settings ADD COLUMN sdi_code TEXT")
    except: pass

    # --- 2. AUXILIARY TABLES (Lookups) ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS vat_rates (id INTEGER PRIMARY KEY, code TEXT, rate REAL, description TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payment_terms (id INTEGER PRIMARY KEY, name TEXT, days INTEGER, type TEXT)''') # type: RB, Bonifico, Rimessa
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS units (id INTEGER PRIMARY KEY, code TEXT, name TEXT)''')

    # --- 3. CONTACTS (Clienti/Fornitori) ---
    # Enhanced with SDI, PEC, Bank, Price List, Type (C/F/Both)
    # --- 3. CONTACTS (Clienti/Fornitori) ---
    # Parity with Invoicex 'clie_forn'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL, -- 'cliente', 'fornitore', 'both'
            code TEXT, -- Codice (codice_esterno)
            
            -- Main Info
            ragione_sociale TEXT NOT NULL,
            cognome TEXT,
            nome TEXT,
            address TEXT,
            cap TEXT,
            city TEXT,
            province TEXT,
            country TEXT DEFAULT 'Italia',
            
            -- Contact
            phone TEXT,
            mobile TEXT,
            fax TEXT,
            email TEXT,
            website TEXT,
            persona_riferimento TEXT,
            
            -- Fiscal (E-Invoice)
            vat_number TEXT, -- P.IVA
            tax_code TEXT,   -- Codice Fiscale
            sdi_code TEXT,   -- Codice Destinatario (SDI)
            pec TEXT,
            esigibilita_iva TEXT, -- I (Immediata), D (Differita), S (Split)
            
            -- Commercial
            listino_id INTEGER,       -- codice_listino
            pagamento_id INTEGER,     -- terminid di pagamento
            agente_id INTEGER,        -- agente
            provvigione_agente REAL,  -- %
            banca_nome TEXT,          -- banca appoggio cliente
            iban TEXT,
            
            -- Discounts
            sconto1 REAL,
            sconto2 REAL,
            
            -- Logistics
            vettore_id INTEGER,
            porto_id INTEGER, 
            
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Destination Addresses (Sedi secondarie)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            label TEXT, -- 'Magazzino', 'Ufficio'
            address TEXT,
            city TEXT,
            zip_code TEXT,
            province TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
        )
    ''')

    # --- 4. PRODUCTS (Articoli) ---
    # Parity with Invoicex 'articoli' — schema canonico allineato al DB di produzione
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            barcode TEXT,
            supplier_code TEXT,
            name TEXT NOT NULL DEFAULT '',
            description TEXT,
            category_id INTEGER,
            unit TEXT DEFAULT 'pz',
            cost_last REAL DEFAULT 0.0,
            cost_avg REAL DEFAULT 0.0,
            price_base REAL DEFAULT 0.0,
            vat_rate REAL DEFAULT 22.0,
            stock_quantity REAL DEFAULT 0.0,
            min_stock REAL DEFAULT 0.0,
            warehouse_location TEXT,
            image_path TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            subcategory_id INTEGER,
            is_kit INTEGER DEFAULT 0,
            is_service INTEGER DEFAULT 0,
            is_description INTEGER DEFAULT 0,
            pieces_per_pack REAL,
            purchase_type TEXT DEFAULT 'Both',
            description_en TEXT,
            weight_net REAL,
            weight_gross REAL,
            supplier_id INTEGER,
            vat_rate_id INTEGER
        )
    ''')

    # --- MASTER DATA TABLES (Anagrafiche) ---
    
    # Generic Lookups
    tables = {
        "vettori": "CREATE TABLE IF NOT EXISTS vettori (id INTEGER PRIMARY KEY, name TEXT)",
        "porti": "CREATE TABLE IF NOT EXISTS porti (id INTEGER PRIMARY KEY, name TEXT)",
        "causali_trasporto": "CREATE TABLE IF NOT EXISTS causali_trasporto (id INTEGER PRIMARY KEY, name TEXT)",
        "aspetto_beni": "CREATE TABLE IF NOT EXISTS aspetto_beni (id INTEGER PRIMARY KEY, name TEXT)",
        
        "categories": "CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, code TEXT, name TEXT)",
        "client_categories": "CREATE TABLE IF NOT EXISTS client_categories (id INTEGER PRIMARY KEY, code TEXT, name TEXT)",
        "subcategories": "CREATE TABLE IF NOT EXISTS subcategories (id INTEGER PRIMARY KEY, code TEXT, name TEXT, category_id INTEGER)",
        
        "brands": "CREATE TABLE IF NOT EXISTS brands (id INTEGER PRIMARY KEY, name TEXT)",
        
        # Complex Lookup Tables
        "banks": """CREATE TABLE IF NOT EXISTS banks (
            id INTEGER PRIMARY KEY, 
            abi TEXT, 
            name TEXT
        )""",
        
        "company_accounts": """CREATE TABLE IF NOT EXISTS company_accounts (
            id INTEGER PRIMARY KEY,
            iban TEXT,
            abi TEXT,
            cab TEXT,
            account_number TEXT,
            notes TEXT
        )""",
        
        "price_lists": """CREATE TABLE IF NOT EXISTS price_lists (
            id INTEGER PRIMARY KEY,
            code TEXT,
            description TEXT,
            vat_included INTEGER DEFAULT 0,
            markup REAL DEFAULT 0
        )""",
        
        "payment_terms": """CREATE TABLE IF NOT EXISTS payment_terms (
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            days INTEGER, 
            type TEXT,
            fe_code TEXT,
            is_riba INTEGER DEFAULT 0,
            is_rid INTEGER DEFAULT 0,
            is_bank_needed INTEGER DEFAULT 0,
            description TEXT   -- Detailed description
        )""",

        

        
        "vat_rates": """CREATE TABLE IF NOT EXISTS vat_rates (
            id INTEGER PRIMARY KEY, 
            code TEXT, 
            description TEXT, 
            rate REAL DEFAULT 0.0
        )""",
        
        "agents": """CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            commission_percent REAL DEFAULT 0.0
        )""",
        
        "document_statuses": "CREATE TABLE IF NOT EXISTS document_statuses (id INTEGER PRIMARY KEY, code TEXT, name TEXT)",
        "delivery_methods": "CREATE TABLE IF NOT EXISTS delivery_methods (id INTEGER PRIMARY KEY, code TEXT, name TEXT)",
        
        "cities": "CREATE TABLE IF NOT EXISTS cities (id INTEGER PRIMARY KEY, code TEXT, name TEXT, province TEXT, region TEXT)",
        "countries": "CREATE TABLE IF NOT EXISTS countries (id INTEGER PRIMARY KEY, code TEXT, name TEXT)" 
    }
    
    for t_name, sql in tables.items():
        cursor.execute(sql)
        
    # Seed default VAT rates if empty
    cursor.execute("SELECT count(*) FROM vat_rates")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO vat_rates (code, description, rate) VALUES ('22', 'IVA 22%', 22.0)")
        cursor.execute("INSERT INTO vat_rates (code, description, rate) VALUES ('10', 'IVA 10%', 10.0)")
        cursor.execute("INSERT INTO vat_rates (code, description, rate) VALUES ('4', 'IVA 4%', 4.0)")
        cursor.execute("INSERT INTO vat_rates (code, description, rate) VALUES ('0', 'Esente', 0.0)")
        
    # Seed default Payment Terms if empty
    cursor.execute("SELECT count(*) FROM payment_terms")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO payment_terms (name, days, type) VALUES ('Rimessa Diretta', 0, 'Rimessa Diretta')")
        cursor.execute("INSERT INTO payment_terms (name, days, type) VALUES ('Bonifico 30 gg', 30, 'Bonifico')")
        cursor.execute("INSERT INTO payment_terms (name, days, type) VALUES ('RiBa 30 gg fm', 30, 'RiBa')")
        
    # Seed default Categories if empty
    cursor.execute("SELECT count(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO categories (name) VALUES ('Generale')")

    # --- 5. DOCUMENTS (Testata) ---
    # Parity with Invoicex 'test_fatt'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL, -- 'Fattura', 'DDT', 'Preventivo', 'Ordine'
            
            -- References
            serie TEXT DEFAULT 'A',
            number INTEGER,
            year INTEGER,
            date DATE,
            
            -- Entities
            contact_id INTEGER, -- cliente/fornitore
            dest_address_id INTEGER, -- spedizione
            
            -- Commercial
            payment_term_id INTEGER,
            payment_description TEXT, -- descrizione libera
            bank_id INTEGER, -- Banca Nostra (per bonifici)
            agent_id INTEGER,
            agent_perc REAL,
            
            -- Logistics (Trasporto)
            vettore_id INTEGER,
            porto TEXT, -- Franco/Assegnato
            causale_trasporto TEXT, -- Vendita/C/Visione
            numero_colli INTEGER,
            peso_lordo REAL,
            peso_netto REAL,
            aspetto_esteriore TEXT, -- Cartoni/Pallet
            data_consegna DATE,
            
            -- Totals
            total_net REAL, -- Imponibile
            total_vat REAL, -- Iva
            total_gross REAL, -- Totale Doc
            total_ritenuta REAL DEFAULT 0, 
            total_busta REAL DEFAULT 0,
            
            status TEXT DEFAULT 'Bozza', -- Bozza, Emesso, Pagato
            notes TEXT,
            internal_notes TEXT,
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    ''')

    # --- 6. DOCUMENT ROWS (Righe) ---
    # Parity with Invoicex 'righ_fatt'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            row_order INTEGER DEFAULT 0,
            
            type TEXT DEFAULT 'product', -- 'product', 'service', 'info', 'advance'
            product_id INTEGER,
            
            code TEXT,
            description TEXT NOT NULL,
            
            quantity REAL DEFAULT 1.0,
            unit_price REAL DEFAULT 0.0,
            discount_1 REAL DEFAULT 0.0, -- %
            discount_2 REAL DEFAULT 0.0, -- %
            vat_rate REAL DEFAULT 22.0,
            
            total_net REAL DEFAULT 0.0,
            
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
        )
    ''')
    
    # --- 7. MOVEMENTS (Magazzino) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity REAL NOT NULL, 
            direction TEXT, -- 'IN', 'OUT'
            reason TEXT,
            document_id INTEGER,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    ''')

    # --- MIGRATION CHECK ---
    # Check if 'contacts' has 'ragione_sociale'
    try:
        cursor.execute("SELECT ragione_sociale FROM contacts LIMIT 1")
    except sqlite3.OperationalError:
        # Missing column, migrate
        print("Migrating DB schema...")
        cols = [
            ("ragione_sociale", "TEXT"),
            ("sdi_code", "TEXT"),
            ("pec", "TEXT"),
            ("esigibilita_iva", "TEXT"),
            ("listino_id", "INTEGER"),
            ("pagamento_id", "INTEGER"),
            ("agente_id", "INTEGER"),
            ("provvigione_agente", "REAL"),
            ("banca_nome", "TEXT"),
            ("iban", "TEXT"),
            ("sconto1", "REAL"),
            ("sconto2", "REAL"),
            ("vettore_id", "INTEGER"),
            ("porto_id", "INTEGER"),
        ]
        for c_name, c_type in cols:
            try:
                cursor.execute(f"ALTER TABLE contacts ADD COLUMN {c_name} {c_type}")
            except sqlite3.OperationalError:
                pass # Already exists maybe
        
        # Populate ragione_sociale from name if empty
        try:
            cursor.execute("UPDATE contacts SET ragione_sociale = name WHERE ragione_sociale IS NULL OR ragione_sociale = ''")
        except: pass

    print("Verifying/Migrating Documents schema...")
    cols = [
        ("serie", "TEXT DEFAULT 'A'"),
        ("number", "INTEGER"),
        ("year", "INTEGER"),
        ("internal_notes", "TEXT"),
        ("notes", "TEXT"),
        ("payment_term_id", "INTEGER"),
        ("payment_description", "TEXT"),
        ("bank_id", "INTEGER"),
        ("agent_id", "INTEGER"),
        ("agent_perc", "REAL"),
        ("vettore_id", "INTEGER"),
        ("porto", "TEXT"),
        ("causale_trasporto", "TEXT"),
        ("numero_colli", "INTEGER"),
        ("peso_lordo", "REAL"),
        ("peso_netto", "REAL"),
        ("aspetto_esteriore", "TEXT"),
        ("data_consegna", "DATE"),
        ("total_ritenuta", "REAL"),
        ("total_busta", "REAL")
    ]
    for c_name, c_type in cols:
        try:
            cursor.execute(f"ALTER TABLE documents ADD COLUMN {c_name} {c_type}")
            print(f"  -> Added missing column: {c_name}")
        except sqlite3.OperationalError: 
            pass # Column likely already exists

    # Phase 17 Migrations
    try: cursor.execute("ALTER TABLE categories ADD COLUMN code TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE client_categories ADD COLUMN code TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN subcategory_id INTEGER")
    except: pass
    
    # Phase 17 - Contacts Migrations
    try: cursor.execute("ALTER TABLE contacts ADD COLUMN category_id INTEGER")
    except: pass
    try: cursor.execute("ALTER TABLE contacts ADD COLUMN external_code TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE contacts ADD COLUMN is_obsolete INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE contacts ADD COLUMN is_person INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE contacts ADD COLUMN title TEXT")
    except: pass

    # Phase 17 - Product Migrations
    try: cursor.execute("ALTER TABLE products ADD COLUMN is_kit INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN is_service INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN is_description INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN pieces_per_pack REAL")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN supplier_code TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN purchase_type TEXT DEFAULT 'Both'")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN description_en TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN weight_net REAL")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN weight_gross REAL")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN supplier_id INTEGER")
    except: pass
    try: cursor.execute("ALTER TABLE products ADD COLUMN vat_rate_id INTEGER")
    except: pass

    # Phase 18 - Parameters Migrations
    try: cursor.execute("ALTER TABLE vat_rates ADD COLUMN nature TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE vat_rates ADD COLUMN external_code TEXT")
    except: pass
    
    try: cursor.execute("ALTER TABLE payment_terms ADD COLUMN fe_code TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE payment_terms ADD COLUMN is_riba INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE payment_terms ADD COLUMN is_rid INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE payment_terms ADD COLUMN is_bank_needed INTEGER DEFAULT 0")
    except: pass
    
    
    # Phase 19 - Logistics & Statuses
    try: cursor.execute("ALTER TABLE porti ADD COLUMN code TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE causali_trasporto ADD COLUMN code TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE aspetto_beni ADD COLUMN code TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE vettori ADD COLUMN code TEXT")
    except: pass
    
    # Phase 21 - Collegamenti documenti (es. fattura generata da DDT: niente doppio scarico)
    try: cursor.execute("ALTER TABLE documents ADD COLUMN source_document_id INTEGER")
    except: pass

    # Phase 20 - Geographic & Carriers Enhanced
    try: cursor.execute("ALTER TABLE vettori ADD COLUMN vat_country TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE vettori ADD COLUMN vat_number TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE vettori ADD COLUMN first_name TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE vettori ADD COLUMN last_name TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE vettori ADD COLUMN tax_code TEXT")
    except: pass

    conn.commit()
    conn.close()

    init_legacy_tables()

# --- HELPER FUNCTIONS FOR MIGRATION/INIT ---
def reset_db_full():
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
        except:
            pass # File might be locked
    init_db()

# --- DATA ACCESS OBJECTS (DAO) PATTERN ---
# (We will implement getters/setters as needed in the Views, sticking to barebones here to avoid file bloat)

def get_dashboard_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Monthly Revenue
    current_month = datetime.now().strftime("%Y-%m")
    try:
        cursor.execute("SELECT SUM(total_gross) FROM documents WHERE type='fattura' AND strftime('%Y-%m', date) = ?", (current_month,))
        res_rev = cursor.fetchone()
        revenue = res_rev[0] if res_rev[0] else 0.0
    except:
        revenue = 0.0
    
    # 2. Total Clients
    try:
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type='cliente'")
        res_cli = cursor.fetchone()
        clients = res_cli[0] if res_cli[0] else 0
    except:
        clients = 0
    
    # 3. Low Stock
    try:
        cursor.execute("SELECT COUNT(*) FROM products WHERE stock_quantity <= min_stock")
        res_stock = cursor.fetchone()
        low_stock = res_stock[0] if res_stock[0] else 0
    except:
        low_stock = 0
    
    conn.close()
    return {
        "revenue": revenue,
        "clients": clients,
        "low_stock": low_stock
    }

def get_dashboard_data():
    """Tutti i dati della dashboard in una chiamata."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now()
    ym, y = now.strftime('%Y-%m'), now.strftime('%Y')

    def one(q, a=()):
        try:
            cursor.execute(q, a)
            r = cursor.fetchone()
            return r[0] if r and r[0] else 0
        except Exception:
            return 0

    d = {
        'fatt_mese':    one("SELECT SUM(total_gross) FROM documents WHERE type='fattura' AND strftime('%Y-%m',date)=?", (ym,)),
        'fatt_anno':    one("SELECT SUM(total_gross) FROM documents WHERE type='fattura' AND strftime('%Y',date)=?", (y,)),
        'doc_anno':     one("SELECT COUNT(*) FROM documents WHERE strftime('%Y',date)=?", (y,)),
        'da_incassare': one("SELECT SUM(amount) FROM deadlines WHERE type='Incasso' AND status!='Pagato'"),
        'da_pagare':    one("SELECT SUM(amount) FROM deadlines WHERE type='Pagamento' AND status!='Pagato'"),
        'sotto_scorta': one("SELECT COUNT(*) FROM products WHERE COALESCE(min_stock,0)>0 AND COALESCE(stock_quantity,0)<=min_stock"),
        'clienti':      one("SELECT COUNT(*) FROM contacts WHERE type IN ('cliente','both')"),
        'articoli':     one("SELECT COUNT(*) FROM products"),
    }
    try:
        cursor.execute("""SELECT d.date, COALESCE(d.serie,'')||'/'||COALESCE(d.number,''), COALESCE(c.ragione_sociale,'-'), COALESCE(d.total_gross,0)
                          FROM documents d LEFT JOIN contacts c ON c.id=d.contact_id
                          WHERE d.type='fattura' ORDER BY d.date DESC, d.id DESC LIMIT 6""")
        d['ultime_fatture'] = cursor.fetchall()
    except Exception:
        d['ultime_fatture'] = []
    try:
        cursor.execute("""SELECT date, type, entity, amount FROM deadlines
                          WHERE status!='Pagato' ORDER BY date ASC LIMIT 6""")
        d['prossime_scadenze'] = cursor.fetchall()
    except Exception:
        d['prossime_scadenze'] = []
    conn.close()
    return d

# Forward compatibility wrappers for existing code
def get_products():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Align with old tuple: (id, code, name, desc, cat, unit, purchase, sale, vat, stock, min, img, created)
    # New schema: id, code, name, description, category_id, unit, cost_last, price_base, vat_rate, stock_quantity, min_stock, image_path, created_at
    # We need to map category_id to name or null
    cursor.execute("SELECT id, code, name, description, category_id, unit, cost_last, price_base, vat_rate, stock_quantity, min_stock, image_path, created_at FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_contacts(ctype=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if ctype:
        cursor.execute("SELECT * FROM contacts WHERE type = ? OR type = 'both'", (ctype,))
    else:
        cursor.execute("SELECT * FROM contacts")
    rows = cursor.fetchall()
    conn.close()
    return rows
    

def get_documents(dtype=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Need to join with contacts to get name
    # FIXED: Re-aligned columns to match DocumentsWindow expectations (Serie at 2, Number, Year, Date, Net at 6, Client at 12)
    base_q = "SELECT d.id, d.type, d.serie, d.number, d.year, d.date, d.total_net, d.total_vat, d.total_gross, d.status, d.notes, d.created_at, c.ragione_sociale, d.payment_description, d.bank_id FROM documents d LEFT JOIN contacts c ON d.contact_id = c.id"
    if dtype:
        cursor.execute(f"{base_q} WHERE d.type = ?", (dtype,))
    else:
        cursor.execute(base_q)
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- INSERT WRAPPERS ---
def add_product(**kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Filter kwargs to match columns 
    # Simplified generic insert
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?"] * len(kwargs))
    vals = list(kwargs.values())
    sql = f"INSERT INTO products ({cols}) VALUES ({placeholders})"
    cursor.execute(sql, vals)
    conn.commit()
    conn.close()

def get_product_by_code(code):
    """Cerca un articolo per codice a barre o codice articolo (match esatto, case-insensitive).
    Ritorna un dict pronto per la riga documento, oppure None se non trovato."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, v.rate AS resolved_vat
        FROM products p
        LEFT JOIN vat_rates v ON v.id = p.vat_rate_id
        WHERE p.barcode = ? COLLATE NOCASE OR p.code = ? COLLATE NOCASE
        ORDER BY (p.barcode = ? COLLATE NOCASE) DESC
        LIMIT 1
    """, (code, code, code))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    keys = row.keys()
    vat = row['resolved_vat']
    if vat is None and 'vat_rate' in keys:
        vat = row['vat_rate']

    return {
        'id': row['id'],
        'code': row['code'] or '',
        'desc': row['description'] or (row['name'] if 'name' in keys else '') or '',
        'um': (row['unit'] if 'unit' in keys else None) or 'pz',
        'price': (row['price_base'] if 'price_base' in keys else None) or 0.0,
        'vat': vat if vat is not None else 22,
    }

def update_product_generic(pid, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    set_clauses = []
    vals = []
    for k, v in data.items():
        set_clauses.append(f"{k} = ?")
        vals.append(v)
    vals.append(pid)
    sql = f"UPDATE products SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(sql, vals)
    conn.commit()
    conn.close()

def delete_product(pid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()

def add_contact(ctype, name, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    kwargs['type'] = ctype
    # handle mismatch between 'name' arg and 'ragione_sociale' column if needed, 
    # but based on new schema 'ragione_sociale' is the column. 
    # The UI sends 'ragione_sociale'.
    if 'ragione_sociale' not in kwargs:
        kwargs['ragione_sociale'] = name
    
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?"] * len(kwargs))
    vals = list(kwargs.values())
    sql = f"INSERT INTO contacts ({cols}) VALUES ({placeholders})"
    cursor.execute(sql, vals)
    conn.commit()
    conn.close()

def delete_contact(contact_id, dummy=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
    conn.commit()
    conn.close()

def create_document(dtype, date, contact_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    year = int(date.split('-')[0])
    cursor.execute("SELECT MAX(number) FROM documents WHERE type = ? AND year = ?", (dtype, year))
    res = cursor.fetchone()
    next_num = 1 if res[0] is None else res[0] + 1
    
    cursor.execute("INSERT INTO documents (type, number, year, date, contact_id) VALUES (?, ?, ?, ?, ?)", 
                   (dtype, next_num, year, date, contact_id))
    lid = cursor.lastrowid
    conn.commit()
    conn.close()
    return lid


def update_document_header(doc_id, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cols = []
    vals = []
    for k, v in kwargs.items():
        cols.append(f"{k} = ?")
        vals.append(v)
    
    vals.append(doc_id)
    sql = f"UPDATE documents SET {', '.join(cols)} WHERE id = ?"
    cursor.execute(sql, vals)
    conn.commit()
    conn.close()



def get_revenue_history():
    """Returns last 6 months revenue: [('YYYY-MM', amount), ...]"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Simplified: Group by YYYY-MM
    cursor.execute('''
        SELECT strftime('%Y-%m', date) as month, SUM(total_gross)
        FROM documents 
        WHERE type='fattura' 
        GROUP BY month 
        ORDER BY month DESC 
        LIMIT 6
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows[::-1] # Reverse to chronological order

def get_lookup(table_name):
    """Returns all rows from a table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_map(table_name, key_col='name', val_col='id'):
    """Returns a dict {name: id} for combos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT {key_col}, {val_col} FROM {table_name}")
        data = cursor.fetchall()
    except:
        data = []
    conn.close()
    return {str(r[0]): r[1] for r in data}




def convert_document(src_id, target_type):
    """Duplicates a document to a new type (e.g. Preventivo -> Fattura)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Fetch Source Header
    # columns: contact_id, total_net, total_vat, total_gross, payment_description, bank_id, notes, internal_notes, payment_term_id, agent_id
    cursor.execute("""
        SELECT contact_id, total_net, total_vat, total_gross, payment_description, bank_id, notes, internal_notes, payment_term_id, agent_id 
        FROM documents WHERE id = ?
    """, (src_id,))
    src = cursor.fetchone()
    if not src: 
        conn.close()
        return False
    
    # 2. Create new Header
    dt = datetime.now().strftime("%Y-%m-%d")
    year = int(dt.split('-')[0])
    
    # Get next number for target type
    cursor.execute("SELECT MAX(number) FROM documents WHERE type = ? AND year = ?", (target_type, year))
    res = cursor.fetchone()
    next_num = 1 if res[0] is None else res[0] + 1
    
    # Insert
    cursor.execute('''
        INSERT INTO documents (
            type, number, year, date, contact_id, 
            total_net, total_vat, total_gross, 
            payment_description, bank_id, notes, internal_notes, payment_term_id, agent_id,
            status, serie
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Bozza', 'A')
    ''', (target_type, next_num, year, dt, src[0], src[1], src[2], src[3], src[4], src[5], src[6], src[7], src[8], src[9]))

    cursor.execute("UPDATE documents SET source_document_id = ? WHERE id = ?", (src_id, cursor.lastrowid))
    
    new_id = cursor.lastrowid
    
    # 3. Copy Rows
    # columns: description, quantity, unit_price, discount_1, discount_2, vat_rate, total_net, product_id, code, um
    cursor.execute("""
        SELECT description, quantity, unit_price, discount_1, discount_2, vat_rate, total_net, product_id, code 
        FROM document_rows WHERE document_id = ?
    """, (src_id,))
    rows = cursor.fetchall()
    
    for r in rows:
        cursor.execute('''
            INSERT INTO document_rows (document_id, description, quantity, unit_price, discount_1, discount_2, vat_rate, total_net, product_id, code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (new_id, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]))
        
    conn.commit()
    conn.close()
    return new_id

def get_scadenzario():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Fetch invoices that are not 'pagata'
    cursor.execute('''
        SELECT d.id, d.number, d.year, d.date, c.ragione_sociale, d.total_gross, d.status
        FROM documents d
        LEFT JOIN contacts c ON d.contact_id = c.id
        WHERE d.type = 'fattura' AND d.status != 'pagata'
        ORDER BY d.date ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_as_paid(doc_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE documents SET status = 'pagata' WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

def add_document_row(doc_id, desc, qty, price, vat, code="", disc1=0.0, disc2=0.0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Invoicex Logic: Net = Qty * Price * (1-d1) * (1-d2)
    # Price is Unit Price. 
    # Actually Invoicex typically does:
    # Row Total = (Price * Qty) - Discounts
    
    base_amount = float(qty) * float(price)
    
    # Apply Discount 1
    amount_d1 = base_amount * (float(disc1) / 100.0)
    net_1 = base_amount - amount_d1
    
    # Apply Discount 2 (Compound)
    amount_d2 = net_1 * (float(disc2) / 100.0)
    final_net = net_1 - amount_d2
    
    cursor.execute('''
        INSERT INTO document_rows (document_id, code, description, quantity, unit_price, vat_rate, discount_1, discount_2, total_net) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (doc_id, code, desc, qty, price, vat, disc1, disc2, final_net))
    
    # Update Document Totals
    # Fetch all rows to sum up
    cursor.execute("SELECT total_net, vat_rate FROM document_rows WHERE document_id=?", (doc_id,))
    rows = cursor.fetchall()
    
    grand_net = 0.0
    grand_vat = 0.0
    
    for r in rows:
        r_net = r[0]
        r_vat_rate = r[1]
        grand_net += r_net
        grand_vat += r_net * (r_vat_rate / 100.0)
        
    grand_total = grand_net + grand_vat
    
    cursor.execute("UPDATE documents SET total_net=?, total_vat=?, total_gross=? WHERE id=?", (grand_net, grand_vat, grand_total, doc_id))
    conn.commit()
    conn.close()

def get_row_details(doc_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM document_rows WHERE document_id=?", (doc_id,))
    rows = cursor.fetchall()
    conn.close()

def init_legacy_tables():
    """Tabelle accessorie (scadenze, distinte RiBa, prima nota). Richiamata da init_db."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Original Inventory Table (Simple)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL DEFAULT 0,
            description TEXT
        )
    ''')
    
    # New Articles Table (Detailed)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            barcode TEXT,
            category TEXT,
            description TEXT,
            iva INTEGER,
            unit TEXT,
            weight REAL,
            min_stock INTEGER,
            supplier TEXT,
            price REAL,
            image_path TEXT
        )
    ''')
    
    # New Deadlines Table (Scadenziario)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT, -- 'Incasso' or 'Pagamento'
            entity TEXT, -- Client or Supplier Name
            amount REAL,
            status TEXT, -- 'Pagato' or 'Da Pagare'
            notes TEXT
        )
    ''')
    
    # New RiBa Distinte Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS riba_distinte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            data_stampa TEXT,
            tipo TEXT
        )
    ''')

    # Prima Nota (entrate/uscite di cassa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prima_nota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            amount REAL,
            type TEXT -- 'E' entrata / 'U' uscita
        )
    ''')

    # Collegamento scadenze <-> documenti (generazione automatica da fatture)
    try: cursor.execute("ALTER TABLE deadlines ADD COLUMN doc_id INTEGER")
    except: pass

    conn.commit()
    conn.close()

# --- Inventory Functions ---

def add_stock(name, quantity, description=""):
    """Adds stock to the inventory. If item exists, updates quantity."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Check if item exists
        cursor.execute("SELECT quantity FROM inventory WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result:
            new_qty = result[0] + quantity
            cursor.execute("UPDATE inventory SET quantity = ? WHERE name = ?", (new_qty, name))
        else:
            cursor.execute("INSERT INTO inventory (name, quantity, description) VALUES (?, ?, ?)", (name, quantity, description))
        
        conn.commit()
    except Exception as e:
        print(f"Error adding stock: {e}")
    finally:
        conn.close()

def remove_stock(name, quantity):
    """Removes stock from inventory. Returns True if successful, False if insufficient stock."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT quantity FROM inventory WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result and result[0] >= quantity:
            new_qty = result[0] - quantity
            cursor.execute("UPDATE inventory SET quantity = ? WHERE name = ?", (new_qty, name))
            conn.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Error removing stock: {e}")
        return False
    finally:
        conn.close()

def get_inventory():
    """Returns a list of all items in inventory."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    conn.close()
    return items

# --- Articles Functions ---

def upsert_article(code, barcode, category, description, iva, unit, weight, min_stock, supplier, price, image_path=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Check if exists by code
        cursor.execute("SELECT id FROM articles WHERE code = ?", (code,))
        if cursor.fetchone():
            cursor.execute('''
                UPDATE articles SET barcode=?, category=?, description=?, iva=?, unit=?, weight=?, min_stock=?, supplier=?, price=?, image_path=?
                WHERE code=?
            ''', (barcode, category, description, iva, unit, weight, min_stock, supplier, price, image_path, code))
        else:
            cursor.execute('''
                INSERT INTO articles (code, barcode, category, description, iva, unit, weight, min_stock, supplier, price, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, barcode, category, description, iva, unit, weight, min_stock, supplier, price, image_path))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def get_articles():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles")
    items = cursor.fetchall()
    conn.close()
    return items

def delete_article(code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM articles WHERE code = ?", (code,))
    conn.commit()
    conn.close()

# --- Deadlines Functions ---

def add_deadline(date, dtype, entity, amount, status, notes=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO deadlines (date, type, entity, amount, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, dtype, entity, amount, status, notes))
    conn.commit()
    conn.close()

def get_deadlines(filter_type=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if filter_type:
        cursor.execute("SELECT * FROM deadlines WHERE type = ?", (filter_type,))
    else:
        cursor.execute("SELECT * FROM deadlines")
    items = cursor.fetchall()
    conn.close()
    return items

# --- RiBa Functions ---

def get_riba_distinte():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM riba_distinte")
    items = cursor.fetchall()
    conn.close()
    return items

def add_riba_distinta(numero, data_stampa, tipo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO riba_distinte (numero, data_stampa, tipo) VALUES (?, ?, ?)", (numero, data_stampa, tipo))
    conn.commit()
    conn.close()

def delete_document(doc_id):
    # Prima di cancellare: storna l'effetto sulle giacenze e rimuove scadenze collegate
    try: regenerate_movements_for_document(doc_id, delete_only=True)
    except Exception as e: print(f"Warn movimenti delete: {e}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # I FK CASCADE valgono solo con PRAGMA foreign_keys=ON (non attivo qui): pulizia esplicita
    cursor.execute("DELETE FROM document_rows WHERE document_id=?", (doc_id,))
    try: cursor.execute("DELETE FROM deadlines WHERE doc_id=?", (doc_id,))
    except: pass
    cursor.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()

def update_contact_generic(contact_id, data):
    """Dynamically updates contact fields based on dict keys."""
    if not data: return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Filter keys that match table columns (simple safety)
    # Ideally should check PRAGMA table_info, but let's assume valid keys from Editor
    # Construct SET clause
    keys = list(data.keys())
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    values = list(data.values())
    values.append(contact_id)
    
    try:
        cursor.execute(f"UPDATE contacts SET {set_clause} WHERE id = ?", values)
        conn.commit()
    except Exception as e:
        print(f"Update Contact Error: {e}")
        raise e
    finally:
        conn.close()

def get_company_settings():
    """Returns company settings as a dictionary, or default dict if empty."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM company_settings WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {}
    except Exception as e:
        print(f"Error fetching company settings: {e}")
        return {}
    finally:
        conn.close()

# --- PRIMA NOTA ---

def get_prima_nota():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, description, amount, type FROM prima_nota ORDER BY date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_prima_nota(date, description, amount, ptype):
    if isinstance(amount, str):
        amount = float(amount.strip().replace(',', '.') or 0)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prima_nota (date, description, amount, type) VALUES (?, ?, ?, ?)",
                   (str(date), description, amount, ptype))
    conn.commit()
    conn.close()

# =====================================================================
# MOTORE MAGAZZINO (movimenti automatici dai documenti, stile Invoicex)
# =====================================================================

MOVEMENT_RULES = {
    'ddt':              ('OUT', 'Scarico da DDT'),
    'fattura':          ('OUT', 'Scarico da Fattura'),
    'ddt_acquisto':     ('IN',  'Carico da DDT Acquisto'),
    'fattura_acquisto': ('IN',  'Carico da Fattura Acquisto'),
}

def regenerate_movements_for_document(doc_id, delete_only=False):
    """Rigenera i movimenti di magazzino di un documento: storna i vecchi e ricrea.
    Le fatture generate da un DDT non scaricano di nuovo (lo ha già fatto il DDT)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # 1. Storno dei movimenti esistenti
        cursor.execute("SELECT product_id, quantity, direction FROM stock_movements WHERE document_id=?", (doc_id,))
        for pid, qty, direction in cursor.fetchall():
            delta = -qty if direction == 'IN' else qty
            cursor.execute("UPDATE products SET stock_quantity = COALESCE(stock_quantity,0) + ? WHERE id=?", (delta, pid))
        cursor.execute("DELETE FROM stock_movements WHERE document_id=?", (doc_id,))

        if delete_only:
            conn.commit()
            return

        cursor.execute("SELECT type, date, source_document_id, serie, number FROM documents WHERE id=?", (doc_id,))
        doc = cursor.fetchone()
        if not doc:
            conn.commit(); return
        dtype, ddate, src_id = doc[0], doc[1], doc[2]

        rule = MOVEMENT_RULES.get(dtype)
        if not rule:
            conn.commit(); return

        # Fattura creata da DDT: niente doppio scarico
        if dtype == 'fattura' and src_id:
            cursor.execute("SELECT type FROM documents WHERE id=?", (src_id,))
            r = cursor.fetchone()
            if r and r[0] == 'ddt':
                conn.commit(); return

        direction, reason_base = rule
        reason = f"{reason_base} {doc[3] or ''}/{doc[4] or ''}".strip()

        # 2. Movimenti per le righe con articolo censito
        cursor.execute("SELECT code, quantity FROM document_rows WHERE document_id=? AND code IS NOT NULL AND code != ''", (doc_id,))
        for code, qty in cursor.fetchall():
            cursor.execute("SELECT id FROM products WHERE code=? COLLATE NOCASE", (code,))
            p = cursor.fetchone()
            if not p: continue
            try: qty = float(qty or 0)
            except (TypeError, ValueError): qty = 0
            if qty == 0: continue
            cursor.execute(
                "INSERT INTO stock_movements (product_id, quantity, direction, reason, document_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                (p[0], qty, direction, reason, doc_id, ddate))
            delta = qty if direction == 'IN' else -qty
            cursor.execute("UPDATE products SET stock_quantity = COALESCE(stock_quantity,0) + ? WHERE id=?", (delta, p[0]))
        conn.commit()
    finally:
        conn.close()

def add_manual_movement(product_id, qty, direction, reason=""):
    """Carico/scarico manuale: registra il movimento e aggiorna la giacenza."""
    qty = float(str(qty).strip().replace(',', '.'))
    if qty <= 0:
        raise ValueError("Quantità non valida")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO stock_movements (product_id, quantity, direction, reason, date) VALUES (?, ?, ?, ?, ?)",
        (product_id, qty, direction,
         reason or ('Carico manuale' if direction == 'IN' else 'Scarico manuale'),
         datetime.now().strftime('%Y-%m-%d %H:%M')))
    delta = qty if direction == 'IN' else -qty
    cursor.execute("UPDATE products SET stock_quantity = COALESCE(stock_quantity,0) + ? WHERE id=?", (delta, product_id))
    conn.commit()
    conn.close()

def get_movements(search=None, direction=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q = """SELECT m.id, m.date, p.code, COALESCE(NULLIF(p.description,''), p.name) AS articolo,
                  m.quantity, m.direction, m.reason,
                  CASE WHEN d.id IS NULL THEN '' ELSE d.type || ' ' || COALESCE(d.serie,'') || '/' || COALESCE(d.number,'') END
           FROM stock_movements m
           JOIN products p ON m.product_id = p.id
           LEFT JOIN documents d ON m.document_id = d.id
           WHERE 1=1"""
    args = []
    if search:
        s = f"%{search}%"
        q += " AND (p.code LIKE ? OR p.description LIKE ? OR p.name LIKE ?)"
        args += [s, s, s]
    if direction in ('IN', 'OUT'):
        q += " AND m.direction = ?"
        args.append(direction)
    q += " ORDER BY m.date DESC, m.id DESC LIMIT 1000"
    cursor.execute(q, args)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_inventory_report(only_low_stock=False):
    """Giacenze: (id, codice, descrizione, um, giacenza, scorta_min, prezzo, valore, sotto_scorta)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q = """SELECT id, COALESCE(code,''), COALESCE(NULLIF(description,''), name), COALESCE(unit,'pz'),
                  COALESCE(stock_quantity,0), COALESCE(min_stock,0), COALESCE(price_base,0),
                  COALESCE(stock_quantity,0) * COALESCE(price_base,0),
                  CASE WHEN COALESCE(min_stock,0) > 0 AND COALESCE(stock_quantity,0) <= COALESCE(min_stock,0) THEN 1 ELSE 0 END AS low
           FROM products
           WHERE COALESCE(is_service,0)=0 AND COALESCE(is_description,0)=0"""
    if only_low_stock:
        q += " AND COALESCE(min_stock,0) > 0 AND COALESCE(stock_quantity,0) <= COALESCE(min_stock,0)"
    q += " ORDER BY code"
    cursor.execute(q)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_prices():
    """Ultimo prezzo praticato per articolo, separato vendita/acquisto."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT code, description, date, unit_price, tipo FROM (
            SELECT r.code, r.description, d.date, r.unit_price,
                   CASE WHEN d.type LIKE '%acquisto%' THEN 'Acquisto' ELSE 'Vendita' END AS tipo,
                   ROW_NUMBER() OVER (
                       PARTITION BY r.code, (d.type LIKE '%acquisto%')
                       ORDER BY d.date DESC, r.id DESC) AS rn
            FROM document_rows r
            JOIN documents d ON d.id = r.document_id
            WHERE r.code IS NOT NULL AND r.code != ''
        ) WHERE rn = 1
        ORDER BY code, tipo
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# =====================================================================
# SCADENZE AUTOMATICHE DA FATTURE
# =====================================================================

def generate_deadlines_for_document(doc_id):
    """Genera/aggiorna la scadenza di una fattura in base ai giorni del tipo pagamento."""
    from datetime import timedelta
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT d.type, d.date, d.total_gross, d.payment_term_id, c.ragione_sociale, d.serie, d.number
            FROM documents d LEFT JOIN contacts c ON c.id = d.contact_id
            WHERE d.id=?""", (doc_id,))
        doc = cursor.fetchone()
        if not doc:
            return
        dtype, ddate, gross, pay_id, entity, serie, number = doc

        cursor.execute("DELETE FROM deadlines WHERE doc_id=?", (doc_id,))
        if dtype not in ('fattura', 'fattura_acquisto') or not gross:
            conn.commit(); return

        days = 0
        if pay_id:
            cursor.execute("SELECT days FROM payment_terms WHERE id=?", (pay_id,))
            r = cursor.fetchone()
            if r and r[0]: days = int(r[0])

        try:
            base = datetime.strptime(str(ddate)[:10], '%Y-%m-%d')
            due = (base + timedelta(days=days)).strftime('%Y-%m-%d')
        except ValueError:
            due = str(ddate)

        dl_type = 'Incasso' if dtype == 'fattura' else 'Pagamento'
        note = f"Fattura {(serie + '/') if serie else ''}{number}"
        cursor.execute(
            "INSERT INTO deadlines (date, type, entity, amount, status, notes, doc_id) VALUES (?, ?, ?, ?, 'Da Pagare', ?, ?)",
            (due, dl_type, entity or '', gross, note, doc_id))
        conn.commit()
    finally:
        conn.close()

def set_deadline_status(deadline_id, status):
    """Aggiorna lo stato di una scadenza; se 'Pagato' e collegata a fattura, segna anche quella."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE deadlines SET status=? WHERE id=?", (status, deadline_id))
    cursor.execute("SELECT doc_id, type FROM deadlines WHERE id=?", (deadline_id,))
    r = cursor.fetchone()
    if r and r[0] and status == 'Pagato':
        cursor.execute("UPDATE documents SET status='pagata' WHERE id=?", (r[0],))
    conn.commit()
    conn.close()

def get_deadlines_full(filter_type=None, filter_status=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q = "SELECT id, date, type, entity, amount, status, COALESCE(notes,''), doc_id FROM deadlines WHERE 1=1"
    args = []
    if filter_type in ('Incasso', 'Pagamento'):
        q += " AND type=?"; args.append(filter_type)
    if filter_status:
        q += " AND status=?"; args.append(filter_status)
    q += " ORDER BY date ASC"
    cursor.execute(q, args)
    rows = cursor.fetchall()
    conn.close()
    return rows

# =====================================================================
# STATISTICHE E REGISTRO IVA
# =====================================================================

def get_stats_obf(year):
    """Ordinato/Bollettato/Fatturato (imponibile) per mese dell'anno scelto."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%m', date), type, SUM(COALESCE(total_net,0))
        FROM documents
        WHERE strftime('%Y', date) = ? AND type IN ('ordine','preventivo','ddt','fattura')
        GROUP BY 1, 2
    """, (str(year),))
    data = {f"{m:02d}": {'ordinato': 0.0, 'bollettato': 0.0, 'fatturato': 0.0} for m in range(1, 13)}
    for month, dtype, total in cursor.fetchall():
        if month not in data: continue
        if dtype in ('ordine', 'preventivo'): data[month]['ordinato'] += total or 0
        elif dtype == 'ddt': data[month]['bollettato'] += total or 0
        elif dtype == 'fattura': data[month]['fatturato'] += total or 0
    conn.close()
    return data

def get_invoice_totals(year, purchases=False):
    """Totale fatture per mese: (mese, n_documenti, imponibile, iva, totale)."""
    dtype = 'fattura_acquisto' if purchases else 'fattura'
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%m', date), COUNT(*),
               SUM(COALESCE(total_net,0)), SUM(COALESCE(total_vat,0)), SUM(COALESCE(total_gross,0))
        FROM documents
        WHERE type = ? AND strftime('%Y', date) = ?
        GROUP BY 1 ORDER BY 1
    """, (dtype, str(year)))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_top_clients(year=None, limit=25):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q = """SELECT c.ragione_sociale, COUNT(d.id), SUM(COALESCE(d.total_gross,0))
           FROM documents d JOIN contacts c ON c.id = d.contact_id
           WHERE d.type = 'fattura'"""
    args = []
    if year:
        q += " AND strftime('%Y', d.date) = ?"; args.append(str(year))
    q += " GROUP BY c.id ORDER BY 3 DESC LIMIT ?"
    args.append(limit)
    cursor.execute(q, args)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_top_products(year=None, limit=25):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q = """SELECT COALESCE(r.code,''), r.description, SUM(COALESCE(r.quantity,0)), SUM(COALESCE(r.total_net,0))
           FROM document_rows r JOIN documents d ON d.id = r.document_id
           WHERE d.type IN ('fattura','ddt')"""
    args = []
    if year:
        q += " AND strftime('%Y', d.date) = ?"; args.append(str(year))
    q += " GROUP BY r.code, r.description ORDER BY 4 DESC LIMIT ?"
    args.append(limit)
    cursor.execute(q, args)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_vat_register(year, purchases=False):
    """Registro IVA: (mese, aliquota, imponibile, imposta) per fatture vendita o acquisto."""
    dtype = 'fattura_acquisto' if purchases else 'fattura'
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%m', d.date), COALESCE(r.vat_rate,0),
               SUM(COALESCE(r.total_net,0)), SUM(COALESCE(r.total_net,0) * COALESCE(r.vat_rate,0) / 100.0)
        FROM document_rows r JOIN documents d ON d.id = r.document_id
        WHERE d.type = ? AND strftime('%Y', d.date) = ?
        GROUP BY 1, 2 ORDER BY 1, 2
    """, (dtype, str(year)))
    rows = cursor.fetchall()
    conn.close()
    return rows

# =====================================================================
# AGENTI
# =====================================================================

def get_agents_situation(year=None):
    """Per agente: documenti, imponibile fatturato e provvigione maturata."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q = """SELECT a.name, COALESCE(a.commission_percent,0), COUNT(d.id),
                  SUM(COALESCE(d.total_net,0)),
                  SUM(COALESCE(d.total_net,0)) * COALESCE(a.commission_percent,0) / 100.0
           FROM agents a LEFT JOIN documents d
                ON d.agent_id = a.id AND d.type = 'fattura'"""
    args = []
    if year:
        q += " AND strftime('%Y', d.date) = ?"; args.append(str(year))
    q += " GROUP BY a.id ORDER BY 4 DESC"
    cursor.execute(q, args)
    rows = cursor.fetchall()
    conn.close()
    return rows

# =====================================================================
# IMPORT DA CSV / EXCEL
# =====================================================================

def _import_num(v):
    """'1.234,56' / '12,5' / '12.5' -> float, oppure None."""
    if v is None:
        return None
    s = str(v).strip().replace('€', '').replace(' ', '')
    if not s:
        return None
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None

def import_products(rows):
    """Importa/aggiorna articoli. Match per codice (case-insensitive).
    Ritorna (inseriti, aggiornati, errori)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    inserted = updated = 0
    errors = []
    text_cols = ('barcode', 'supplier_code', 'unit', 'warehouse_location')
    num_cols = ('price_base', 'cost_last', 'vat_rate', 'stock_quantity', 'min_stock')
    for i, r in enumerate(rows, start=2):  # riga 1 = intestazioni
        try:
            code = str(r.get('code') or '').strip()
            desc = str(r.get('description') or '').strip()
            if not code and not desc:
                continue
            data = {}
            for k in text_cols:
                v = str(r.get(k) or '').strip()
                if v:
                    data[k] = v
            for k in num_cols:
                v = _import_num(r.get(k))
                if v is not None:
                    data[k] = v
            if desc:
                data['description'] = desc
                data['name'] = desc

            existing = None
            if code:
                cursor.execute("SELECT id FROM products WHERE code=? COLLATE NOCASE", (code,))
                existing = cursor.fetchone()
            if existing:
                if data:
                    sets = ", ".join(f"{k}=?" for k in data)
                    cursor.execute(f"UPDATE products SET {sets} WHERE id=?",
                                   list(data.values()) + [existing[0]])
                updated += 1
            else:
                data['code'] = code or None
                if 'name' not in data:
                    data['name'] = desc or code
                cols = ", ".join(data.keys())
                q = ", ".join("?" * len(data))
                cursor.execute(f"INSERT INTO products ({cols}) VALUES ({q})", list(data.values()))
                inserted += 1
        except Exception as e:
            errors.append(f"riga {i}: {e}")
    conn.commit()
    conn.close()
    return inserted, updated, errors

def import_contacts(rows, default_type='cliente'):
    """Importa/aggiorna clienti-fornitori. Match per P.IVA, poi per ragione sociale.
    Ritorna (inseriti, aggiornati, errori)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    inserted = updated = 0
    errors = []
    text_cols = ('address', 'cap', 'city', 'province', 'phone', 'mobile', 'email',
                 'pec', 'vat_number', 'tax_code', 'sdi_code', 'code')
    for i, r in enumerate(rows, start=2):
        try:
            name = str(r.get('ragione_sociale') or '').strip()
            if not name:
                continue
            data = {'ragione_sociale': name}
            for k in text_cols:
                v = str(r.get(k) or '').strip()
                if v:
                    data[k] = v
            ctype = str(r.get('type') or '').strip().lower()
            if ctype.startswith('forn'):
                data['type'] = 'fornitore'
            elif ctype.startswith('cli'):
                data['type'] = 'cliente'
            elif ctype in ('both', 'entrambi'):
                data['type'] = 'both'

            existing = None
            piva = data.get('vat_number')
            if piva:
                cursor.execute("SELECT id FROM contacts WHERE vat_number=?", (piva,))
                existing = cursor.fetchone()
            if not existing:
                cursor.execute("SELECT id FROM contacts WHERE ragione_sociale=? COLLATE NOCASE", (name,))
                existing = cursor.fetchone()

            if existing:
                sets = ", ".join(f"{k}=?" for k in data)
                cursor.execute(f"UPDATE contacts SET {sets} WHERE id=?",
                               list(data.values()) + [existing[0]])
                updated += 1
            else:
                data.setdefault('type', default_type)
                cols = ", ".join(data.keys())
                q = ", ".join("?" * len(data))
                cursor.execute(f"INSERT INTO contacts ({cols}) VALUES ({q})", list(data.values()))
                inserted += 1
        except Exception as e:
            errors.append(f"riga {i}: {e}")
    conn.commit()
    conn.close()
    return inserted, updated, errors

# =====================================================================
# UTILITÀ DATABASE (backup, ripristino, manutenzione)
# =====================================================================

def backup_db(dest_path):
    import shutil
    shutil.copy2(DB_NAME, dest_path)
    return dest_path

def restore_db(src_path):
    import shutil
    shutil.copy2(src_path, DB_NAME)
    init_db()  # applica eventuali migrazioni mancanti al backup ripristinato

def vacuum_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("VACUUM")
    conn.close()

def integrity_check():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]
    conn.close()
    return result

def save_company_settings(data):
    """Upserts company settings (always ID=1)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Check if exists
        cursor.execute("SELECT id FROM company_settings WHERE id = 1")
        exists = cursor.fetchone()
        
        cols = list(data.keys())
        
        if exists:
            set_clause = ", ".join([f"{k}=?" for k in cols])
            vals = list(data.values())
            vals.append(1)
            cursor.execute(f"UPDATE company_settings SET {set_clause} WHERE id=?", vals)
        else:
            # Force ID=1
            cols.append("id")
            vals = list(data.values())
            vals.append(1)
            
            q_cols = ", ".join(cols)
            q_vals = ", ".join(["?"] * len(vals))
            cursor.execute(f"INSERT INTO company_settings ({q_cols}) VALUES ({q_vals})", vals)
            
        conn.commit()
    except Exception as e:
        print(f"Error saving company settings: {e}")
        raise e
    finally:
        conn.close()

# Auto-init: garantisce schema completo e migrazioni a ogni import
init_db()
