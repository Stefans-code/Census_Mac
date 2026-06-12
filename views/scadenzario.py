import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import database

class ScadenzarioFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        # self.title("Scadenzario")
        # self.geometry("800x600")
        
        self.lbl = ctk.CTkLabel(self, text="Totale da Incassare", font=("Arial", 20, "bold"))
        self.lbl.pack(pady=20)
        
        cols = ("Scadenza", "Fattura", "Cliente", "Importo")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkButton(self, text="Segna come Pagato", command=self.pay, fg_color="green").pack(pady=20)
        self.refresh()
        
    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        rows = database.get_scadenzario()
        tot = 0
        for r in rows:
            tot += r[5]
            self.tree.insert("", "end", iid=r[0], values=(r[3], f"{r[1]}/{r[2]}", r[4], r[5]))
        self.lbl.configure(text=f"Totale Scaduto: € {tot:.2f}")

    def pay(self):
        sel = self.tree.selection()
        if not sel: return
        database.mark_as_paid(sel[0])
        self.refresh()
