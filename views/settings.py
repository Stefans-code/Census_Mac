import customtkinter as ctk
from tkinter import messagebox
import database

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Dati Azienda")
        self.geometry("700x550")
        
        # Main Container with Padding
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        # Icon placeholder (just text for now)
        ctk.CTkLabel(header, text="ℹ️", font=("Arial", 30)).pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Inserisci i dati anagrafici dell'azienda", font=("Arial", 16, "bold")).pack(side="left")

        # Entries Map
        self.entries = {}

        # Form Grid
        form = ctk.CTkFrame(main, fg_color="transparent")
        form.pack(fill="x")
        
        # Helper for rows
        def row(lbl, key, r, c=0, w=None, colspan=1):
            ctk.CTkLabel(form, text=lbl, anchor="e").grid(row=r, column=c, padx=5, pady=5, sticky="e")
            entry = ctk.CTkEntry(form, width=w if w else 400)
            entry.grid(row=r, column=c+1, columnspan=colspan, padx=5, pady=5, sticky="w")
            self.entries[key] = entry
            return entry

        # 1. Ragione Sociale
        row("Ragione sociale", "name", 0, w=450)
        
        # 2. P.IVA
        row("Partita Iva", "vat_number", 1, w=450)
        
        # 3. Codice Fiscale
        row("Codice Fiscale", "tax_code", 2, w=450)
        
        # 4. Regime Fiscale
        self.entries['regime_fiscale'] = ctk.CTkComboBox(form, values=["Ordinale", "Forfettario", "Minimi"], width=450)
        ctk.CTkLabel(form, text="Regime fiscale", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entries['regime_fiscale'].grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # 5. Indirizzo
        row("Indirizzo", "address", 4, w=450)
        
        # 6. CAP | Localita | Prov
        # Custom row for split fields
        ctk.CTkLabel(form, text="Cap", anchor="e").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        
        sub_frame = ctk.CTkFrame(form, fg_color="transparent")
        sub_frame.grid(row=5, column=1, sticky="w")
        
        self.entries['zip_code'] = ctk.CTkEntry(sub_frame, width=80)
        self.entries['zip_code'].pack(side="left", padx=5)
        
        ctk.CTkLabel(sub_frame, text="Localita").pack(side="left", padx=5)
        self.entries['city'] = ctk.CTkEntry(sub_frame, width=220)
        self.entries['city'].pack(side="left", padx=5)
        
        ctk.CTkLabel(sub_frame, text="Prov.").pack(side="left", padx=5)
        self.entries['province'] = ctk.CTkEntry(sub_frame, width=50)
        self.entries['province'].pack(side="left", padx=5)
        
        # 7. Telefono | Fax
        ctk.CTkLabel(form, text="Telefono", anchor="e").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        sub_ph = ctk.CTkFrame(form, fg_color="transparent")
        sub_ph.grid(row=6, column=1, sticky="w")
        
        self.entries['phone'] = ctk.CTkEntry(sub_ph, width=150)
        self.entries['phone'].pack(side="left", padx=5)
        
        ctk.CTkLabel(sub_ph, text="Fax").pack(side="left", padx=15)
        self.entries['fax'] = ctk.CTkEntry(sub_ph, width=150)
        self.entries['fax'].pack(side="left", padx=5)
        
        # 8. Web
        row("Sito Web", "website", 7, w=450)
        
        # 9. Email
        row("Email", "email", 8, w=450)
        
        # 10. PEC
        row("PEC", "pec", 9, w=450)
        
        # 11. Codice Destinatario
        row("Codice Destinatario F.E.", "sdi_code", 10, w=100)

        # Footer Actions
        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=10)
        
        ctk.CTkButton(footer, text="Annulla", fg_color="gray", command=self.destroy, width=100).pack(side="right", padx=10)
        ctk.CTkButton(footer, text="Conferma", fg_color="#27ae60", command=self.save, width=100).pack(side="right") # Green check
        
        self.load_data()

    def load_data(self):
        d = database.get_company_settings()
        if not d: return
        
        for k, v in d.items():
            if k in self.entries:
                if isinstance(self.entries[k], ctk.CTkComboBox):
                    self.entries[k].set(str(v) if v else "")
                else:
                    self.entries[k].delete(0, "end")
                    if v: self.entries[k].insert(0, str(v))

    def save(self):
        data = {k: v.get() for k, v in self.entries.items()}
        try:
            database.save_company_settings(data)
            messagebox.showinfo("Salvataggio", "Dati salvati correttamente")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Errore", str(e))
