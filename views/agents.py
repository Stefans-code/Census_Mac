"""Agenti: anagrafica e situazione provvigioni."""
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import database
from utils import theme


class AgentsWindow(ctk.CTkFrame):
    def __init__(self, parent, start_tab=None):
        super().__init__(parent, fg_color=theme.BG)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(head, text="Agenti", font=theme.font(22, bold=True),
                     text_color=theme.TEXT).pack(side="left")

        self.tabs = ctk.CTkTabview(self, fg_color=theme.SURFACE,
                                   segmented_button_selected_color=theme.ACCENT)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.tabs.add("Anagrafica")
        self.tabs.add("Situazione")

        # ============ TAB ANAGRAFICA ============
        t1 = self.tabs.tab("Anagrafica")
        t1.grid_columnconfigure(0, weight=1)
        t1.grid_rowconfigure(1, weight=1)

        form = ctk.CTkFrame(t1, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(form, text="Nome:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(4, 6))
        self.ent_name = ctk.CTkEntry(form, width=240, placeholder_text="Nome agente")
        self.ent_name.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(form, text="Provvigione %:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(0, 6))
        self.ent_comm = ctk.CTkEntry(form, width=80)
        self.ent_comm.pack(side="left", padx=(0, 14))

        ctk.CTkButton(form, text="💾 Salva", width=90, fg_color=theme.GREEN_D,
                      hover_color=theme.darken(theme.GREEN_D), command=self.save_agent).pack(side="left", padx=3)
        ctk.CTkButton(form, text="📄 Nuovo", width=90, fg_color=theme.SURFACE_2,
                      hover_color=theme.BORDER, command=self.new_agent).pack(side="left", padx=3)
        ctk.CTkButton(form, text="❌ Elimina", width=90, fg_color=theme.RED_D,
                      hover_color=theme.darken(theme.RED_D), command=self.delete_agent).pack(side="left", padx=3)

        tree_fr = ctk.CTkFrame(t1, fg_color="transparent")
        tree_fr.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        tree_fr.grid_columnconfigure(0, weight=1)
        tree_fr.grid_rowconfigure(0, weight=1)

        cols = ("ID", "Nome", "Provvigione %")
        self.tree = ttk.Treeview(tree_fr, columns=cols, show="headings")
        for c, w in zip(cols, (60, 320, 120)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="e" if c == "Provvigione %" else "w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(tree_fr, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.current_id = None

        # ============ TAB SITUAZIONE ============
        t2 = self.tabs.tab("Situazione")
        t2.grid_columnconfigure(0, weight=1)
        t2.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(t2, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(bar, text="Anno:", font=theme.font(11),
                     text_color=theme.TEXT_DIM).pack(side="left", padx=(4, 6))
        years = self._years()
        self.combo_year = ctk.CTkOptionMenu(bar, values=years, width=90,
                                            command=lambda x: self.refresh_situation())
        self.combo_year.pack(side="left")
        ctk.CTkLabel(bar, text="(provvigioni calcolate sull'imponibile delle fatture)",
                     font=theme.font(10), text_color=theme.TEXT_DIM).pack(side="left", padx=12)

        sit_fr = ctk.CTkFrame(t2, fg_color="transparent")
        sit_fr.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        sit_fr.grid_columnconfigure(0, weight=1)
        sit_fr.grid_rowconfigure(0, weight=1)

        cols2 = ("Agente", "Provv. %", "N. Fatture", "Imponibile", "Provvigione")
        self.tree_sit = ttk.Treeview(sit_fr, columns=cols2, show="headings")
        for c, w in zip(cols2, (240, 90, 90, 140, 140)):
            self.tree_sit.heading(c, text=c)
            self.tree_sit.column(c, width=w, anchor="w" if c == "Agente" else "e")
        self.tree_sit.grid(row=0, column=0, sticky="nsew")
        sb2 = ctk.CTkScrollbar(sit_fr, command=self.tree_sit.yview)
        sb2.grid(row=0, column=1, sticky="ns")
        self.tree_sit.configure(yscrollcommand=sb2.set)

        if start_tab == "situazione":
            self.tabs.set("Situazione")

        self.refresh_list()
        self.refresh_situation()

    def _years(self):
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

    # ---- Anagrafica ----
    def refresh_list(self):
        for x in self.tree.get_children():
            self.tree.delete(x)
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, name, COALESCE(commission_percent,0) FROM agents ORDER BY name")
        for r in cur.fetchall():
            self.tree.insert("", "end", values=(r[0], r[1], f"{r[2]:g}"))
        conn.close()
        theme.stripe(self.tree)

    def on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        self.current_id = vals[0]
        self.ent_name.delete(0, "end")
        self.ent_name.insert(0, vals[1])
        self.ent_comm.delete(0, "end")
        self.ent_comm.insert(0, vals[2])

    def new_agent(self):
        self.current_id = None
        self.ent_name.delete(0, "end")
        self.ent_comm.delete(0, "end")
        self.tree.selection_remove(*self.tree.selection())

    def save_agent(self):
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("Agente", "Inserisci il nome dell'agente.")
            return
        try:
            comm = float((self.ent_comm.get() or "0").strip().replace(',', '.'))
        except ValueError:
            messagebox.showwarning("Agente", "Provvigione non valida.")
            return
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        if self.current_id:
            cur.execute("UPDATE agents SET name=?, commission_percent=? WHERE id=?",
                        (name, comm, self.current_id))
        else:
            cur.execute("INSERT INTO agents (name, commission_percent) VALUES (?, ?)", (name, comm))
        conn.commit()
        conn.close()
        self.refresh_list()
        self.refresh_situation()
        self.new_agent()

    def delete_agent(self):
        if not self.current_id:
            return
        if not messagebox.askyesno("Elimina", "Eliminare l'agente selezionato?"):
            return
        conn = database.sqlite3.connect(database.DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM agents WHERE id=?", (self.current_id,))
        conn.commit()
        conn.close()
        self.refresh_list()
        self.refresh_situation()
        self.new_agent()

    # ---- Situazione ----
    def refresh_situation(self):
        for x in self.tree_sit.get_children():
            self.tree_sit.delete(x)
        rows = database.get_agents_situation(self.combo_year.get())
        tot_net = tot_comm = 0.0
        for r in rows:
            # name, comm%, n_doc, imponibile, provvigione
            tot_net += r[3] or 0
            tot_comm += r[4] or 0
            self.tree_sit.insert("", "end", values=(
                r[0], f"{r[1]:g}%", r[2] or 0, theme.euro(r[3]), theme.euro(r[4])))
        self.tree_sit.insert("", "end", values=(
            "TOTALE", "", "", theme.euro(tot_net), theme.euro(tot_comm)), tags=("green",))
        theme.stripe(self.tree_sit)
