from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
import os


def generate_invoice_pdf(doc_data, items, filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # --- COMPANY HEADER (Static for now) ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, "LA TUA AZIENDA S.R.L.")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 2.5*cm, "Via Roma 1 - 00100 Roma (RM)")
    c.drawString(2*cm, height - 3.0*cm, "P.IVA: 12345678901 - Cod.Fisc: 12345678901")
    c.drawString(2*cm, height - 3.5*cm, "Email: info@azienda.it")

    # --- DOCUMENT INFO ---
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(width/2, height - 4.5*cm, width/2 - 1*cm, 2.5*cm, fill=1, stroke=0)
    c.setFillColorRGB(0,0,0)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(12*cm, height - 2.5*cm, f"FATTURA n. {doc_data['number']}")
    c.setFont("Helvetica", 12)
    c.drawString(12*cm, height - 3.2*cm, f"Data: {doc_data['date']}")
    
    # --- CLIENT ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, height - 5.5*cm, "DESTINATARIO:")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 6.2*cm, doc_data['client_name'])
    c.setFont("Helvetica", 10)
    if doc_data.get('client_address'):
        c.drawString(2*cm, height - 6.7*cm, doc_data['client_address'])
    
    vat_line = ""
    if doc_data.get('client_vat'): vat_line += f"P.IVA: {doc_data['client_vat']} "
    c.drawString(2*cm, height - 7.2*cm, vat_line)

    # --- COMMERCIAL INFO ---
    y_comm = height - 8.5*cm
    c.line(2*cm, y_comm + 0.2*cm, width - 2*cm, y_comm + 0.2*cm)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm, y_comm - 0.3*cm, "PAGAMENTO")
    c.drawString(10*cm, y_comm - 0.3*cm, "BANCA D'APPOGGIO")
    
    c.setFont("Helvetica", 9)
    pay = doc_data.get('payment_term') or "-"
    bank = doc_data.get('bank_iban') or "-"
    c.drawString(2*cm, y_comm - 0.8*cm, pay[:35])
    c.drawString(10*cm, y_comm - 0.8*cm, bank[:45])

    # --- TABLE HEADER ---
    y = height - 10*cm
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(2*cm, y - 0.2*cm, width - 4*cm, 0.6*cm, fill=1, stroke=0)
    c.setFillColorRGB(0,0,0)
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.2*cm, y, "DESCRIZIONE")
    c.drawRightString(14*cm, y, "Q.TÀ")
    c.drawRightString(16*cm, y, "PREZZO")
    c.drawRightString(17.5*cm, y, "IVA")
    c.drawRightString(19*cm, y, "TOTALE")

    # --- ITEMS ---
    y -= 0.8*cm
    c.setFont("Helvetica", 9)
    
    # items comes from DB as (desc, qty, price, total_net) usually, or custom dict
    # We expect DB rows: (desc, qty, price, net)
    # But wait, database.py add_row saves 'vat' now too? Yes.
    # We need to ensure we pass the right struct.
    
    for item in items:
        # Assuming item is now: (desc, qty, price, vat_rate, total_net) or something similar
        # Let's handle flexible input
        desc = item[0]
        qty = item[1]
        price = item[2]
        # net = item[3]
        
        c.drawString(2.2*cm, y, desc[:55])
        c.drawRightString(14*cm, y, f"{qty}")
        c.drawRightString(16*cm, y, f"{price:.2f}")
        c.drawRightString(17.5*cm, y, "22%") # Placeholder if not passed
        c.drawRightString(19*cm, y, f"{qty*price:.2f}")
        y -= 0.6*cm
        
        if y < 3*cm: 
            c.showPage()
            y = height - 2*cm

    # --- TOTALS ---
    y -= 0.5*cm
    c.line(12*cm, y, width - 2*cm, y)
    y -= 0.5*cm
    
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(16*cm, y, "IMPONIBILE:")
    c.drawRightString(19*cm, y, f"€ {doc_data['total_net']:.2f}")
    y -= 0.5*cm
    c.drawRightString(16*cm, y, "IVA:")
    c.drawRightString(19*cm, y, f"€ {doc_data['total_vat']:.2f}")
    y -= 0.8*cm
    
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(16*cm, y, "TOTALE DOCUMENTO:")
    c.drawRightString(19*cm, y, f"€ {doc_data['total_gross']:.2f}")
    
    # Notes
    if doc_data.get('notes_public'):
        y -= 1.5*cm
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(2*cm, y, "Note:")
        c.drawString(2*cm, y-0.4*cm, doc_data['notes_public'][:100])

    c.save()
    return filename

