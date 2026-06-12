"""Tema grafico globale di Census ERP.

Palette scura coerente + stile ttk per le tabelle (Treeview), che di default
su Windows restano bianche e stonano con il resto dell'interfaccia.
"""
import customtkinter as ctk
from tkinter import ttk

# --- PALETTE ---
BG        = "#10131a"   # sfondo finestra
SURFACE   = "#171c26"   # pannelli / tabelle
SURFACE_2 = "#1f2633"   # elementi rialzati / heading
BORDER    = "#2c3547"
ACCENT    = "#4f7cff"   # blu primario
ACCENT_H  = "#3a5fd0"
GREEN     = "#2ecc71"
GREEN_D   = "#27ae60"
RED       = "#e74c3c"
RED_D     = "#c0392b"
ORANGE    = "#e67e22"
PURPLE    = "#9b59b6"
CYAN      = "#1abc9c"
TEXT      = "#e9ecf2"
TEXT_DIM  = "#8d97ab"

FONT = "Segoe UI"

def font(size=11, bold=False):
    return (FONT, size, "bold") if bold else (FONT, size)

def darken(hex_color, factor=0.78):
    """Scurisce un colore esadecimale (per gli hover dei pulsanti)."""
    try:
        h = hex_color.lstrip('#')
        r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
        return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"
    except Exception:
        return hex_color

def setup_treeview_style():
    """Stile scuro per TUTTI i ttk.Treeview dell'app. Chiamare una volta dopo CTk()."""
    style = ttk.Style()
    try:
        style.theme_use("clam")  # unico theme che rispetta i colori custom su Windows
    except Exception:
        pass
    style.configure("Treeview",
                    background=SURFACE, fieldbackground=SURFACE, foreground=TEXT,
                    rowheight=30, borderwidth=0, font=font(10))
    style.configure("Treeview.Heading",
                    background=SURFACE_2, foreground=TEXT_DIM, relief="flat",
                    font=font(10, bold=True), padding=(8, 6))
    style.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#ffffff")])
    style.map("Treeview.Heading", background=[("active", BORDER)])
    # Scrollbar ttk coerenti
    style.configure("Vertical.TScrollbar", background=SURFACE_2, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TEXT_DIM)

def stripe(tree):
    """Righe zebrate + tag colore standard. Chiamare dopo aver riempito il Treeview."""
    tree.tag_configure("even", background=SURFACE)
    tree.tag_configure("odd", background="#1b212c")
    tree.tag_configure("red", foreground="#ff7a6e")
    tree.tag_configure("green", foreground=GREEN)
    tree.tag_configure("dim", foreground=TEXT_DIM)
    for i, iid in enumerate(tree.get_children()):
        tags = [t for t in (tree.item(iid, "tags") or ()) if t not in ("even", "odd")]
        tags.append("even" if i % 2 == 0 else "odd")
        tree.item(iid, tags=tuple(tags))

def card(parent, **kwargs):
    """Pannello 'card' standard."""
    opts = dict(fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
    opts.update(kwargs)
    return ctk.CTkFrame(parent, **opts)

def kpi_card(parent, title, value, color=ACCENT, subtitle=""):
    """Card KPI per la dashboard: titolo piccolo, valore grande, riga colorata."""
    c = card(parent)
    bar = ctk.CTkFrame(c, height=4, corner_radius=2, fg_color=color)
    bar.pack(fill="x", padx=14, pady=(12, 0))
    ctk.CTkLabel(c, text=title.upper(), font=font(10, bold=True), text_color=TEXT_DIM,
                 anchor="w").pack(fill="x", padx=14, pady=(8, 0))
    val = ctk.CTkLabel(c, text=value, font=font(22, bold=True), text_color=TEXT, anchor="w")
    val.pack(fill="x", padx=14)
    if subtitle:
        ctk.CTkLabel(c, text=subtitle, font=font(9), text_color=TEXT_DIM,
                     anchor="w").pack(fill="x", padx=14, pady=(0, 10))
    else:
        ctk.CTkFrame(c, height=10, fg_color="transparent").pack()
    return c

def section_title(parent, text):
    return ctk.CTkLabel(parent, text=text, font=font(15, bold=True), text_color=TEXT, anchor="w")

def euro(value):
    """Formato importo italiano: € 1.234,56"""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        v = 0.0
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {s}"
