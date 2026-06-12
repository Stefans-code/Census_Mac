"""Prima Nota: entrate e uscite di cassa con saldo."""
import customtkinter as ctk
from tkinter import ttk, messagebox
import database
from utils import theme


class PrimaNotaWindow(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.BG)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(head, text="Prima Nota", font=theme.font(22, bold=True),
                     text_color=theme.TEXT).pack(side="left")
        ctk.CTkButton(head, text="- Uscita", width=100, fg_color=theme.RED_D,
                      hover_color=theme.darken(theme.RED_D),
                      command=lambda: self.add("U")).pack(side="right", padx=4)
        ctk.CTkButton(head, text="+ Entrata", width=100, fg_color=theme.GREEN_D,
                      hover_color=theme.darken(theme.GREEN_D),
                      command=lambda: self.add("E")).pack(side="right", padx=4)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 4))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        cols = ("Data", "Descrizione", "Entrata", "Uscita")
        self.tree = ttk.Treeview(body, columns=cols, show="headings")
        for c, w in zip(cols, (120, 380, 120, 120)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w" if c in ("Data", "Descrizione") else "e")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(body, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=20, pady=(4, 14))
        self.lbl_saldo = ctk.CTkLabel(foot, text="", font=theme.font(14, bold=True),
                                      text_color=theme.TEXT)
        self.lbl_saldo.pack(side="right")

        self.refresh()

    def refresh(self):
        for x in self.tree.get_children():
            self.tree.delete(x)
        saldo = 0.0
        for r in database.get_prima_nota():
            # id, date, desc, amount, type
            amount = r[3] or 0
            if r[4] == 'E':
                saldo += amount
                self.tree.insert("", "end", values=(r[1], r[2], theme.euro(amount), ""),
                                 tags=("green",))
            else:
                saldo -= amount
                self.tree.insert("", "end", values=(r[1], r[2], "", theme.euro(amount)),
                                 tags=("red",))
        theme.stripe(self.tree)
        color = theme.GREEN if saldo >= 0 else "#ff7a6e"
        self.lbl_saldo.configure(text=f"Saldo: {theme.euro(saldo)}", text_color=color)

    def add(self, t):
        AddEntryDialog(self, t)


class AddEntryDialog(ctk.CTkToplevel):
    def __init__(self, parent, t):
        super().__init__(parent)
        self.parent = parent
        self.t = t
        self.title("Nuova Entrata" if t == "E" else "Nuova Uscita")
        self.geometry("400x300")
        self.configure(fg_color=theme.BG)
        self.grab_set()

        color = theme.GREEN_D if t == "E" else theme.RED_D
        ctk.CTkLabel(self, text="+ ENTRATA" if t == "E" else "- USCITA",
                     font=theme.font(16, bold=True), text_color=color).pack(pady=(18, 10))

        self.desc = ctk.CTkEntry(self, placeholder_text="Descrizione")
        self.desc.pack(pady=8, padx=24, fill="x")
        self.amt = ctk.CTkEntry(self, placeholder_text="Importo (es. 120,50)")
        self.amt.pack(pady=8, padx=24, fill="x")

        ctk.CTkButton(self, text="SALVA", fg_color=color, hover_color=theme.darken(color),
                      height=36, command=self.save).pack(pady=16, padx=24, fill="x")
        self.after(150, self.desc.focus_set)

    def save(self):
        from datetime import date
        try:
            database.add_prima_nota(date.today().isoformat(), self.desc.get().strip(),
                                    self.amt.get(), self.t)
        except ValueError:
            messagebox.showwarning("Prima Nota", "Importo non valido.", parent=self)
            return
        self.parent.refresh()
        self.destroy()
