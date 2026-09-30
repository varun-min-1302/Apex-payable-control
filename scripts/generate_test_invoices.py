import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image, ImageDraw

out_dir = os.path.abspath('sample_invoices')
os.makedirs(out_dir, exist_ok=True)

def build_pdf(filename, inv_data):
    filepath = os.path.join(out_dir, filename)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    meta_label = ParagraphStyle('MetaLabel', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.HexColor('#64748b'))
    meta_val = ParagraphStyle('MetaVal', fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#0f172a'))
    hdr_style = ParagraphStyle('Hdr', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor('#ffffff'))
    cell_style = ParagraphStyle('Cell', fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#334155'))
    cell_right = ParagraphStyle('CellR', fontName='Helvetica', fontSize=9, leading=12, alignment=2, textColor=colors.HexColor('#0f172a'))
    
    story = []
    
    v_name = inv_data['vendor_name']
    v_tax = inv_data['vendor_tax_id']
    inv_num = inv_data['invoice_number']
    po_num = inv_data['po_number']
    dt = inv_data['date']
    due_dt = inv_data['due_date']
    
    # Header block
    left_header = f"<b><font size='12'>{v_name}</font></b><br/><font size='8' color='#64748b'>Registered Supplier & Vendor Services<br/>GSTIN / Tax ID: <b>{v_tax}</b></font>"
    right_header = f"<b><font size='14' color='#2563eb'>TAX INVOICE</font></b><br/><font size='10' color='#0f172a'><b>{inv_num}</b></font><br/><font size='8' color='#64748b'>Invoice Date: {dt}<br/>Payment Due: {due_dt}</font>"
    
    header_table = Table(
        [[Paragraph(left_header, meta_val), Paragraph(right_header, ParagraphStyle('HdrR', alignment=2, leading=14))]],
        colWidths=[330, 210]
    )
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#cbd5e1'), spaceAfter=12))
    
    # Bill To & PO Info
    billed_to = "Apex FinTech Technologies India Pvt Ltd<br/>SEZ Campus, Bandra Kurla Complex<br/>Mumbai, Maharashtra - 400051<br/>GSTIN: 27AABCA9999Z1Z1"
    po_details = f"Purchase Order Ref: <b>{po_num}</b><br/>Payment Terms: Net 30 Days<br/>Remittance Bank: <b>{inv_data['bank_name']}</b><br/>Account Number: <b>{inv_data['bank_ac']}</b><br/>IFSC: <b>{inv_data['bank_ifsc']}</b>"
    
    bill_data = [
        [Paragraph('<b>BILLED TO (BUYER):</b>', meta_label), Paragraph('<b>PURCHASE ORDER & REMITTANCE:</b>', meta_label)],
        [Paragraph(billed_to, meta_val), Paragraph(po_details, meta_val)]
    ]
    t_bill = Table(bill_data, colWidths=[270, 270])
    t_bill.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t_bill)
    story.append(Spacer(1, 14))
    
    # Items Table
    item_rows = [[
        Paragraph('Item Description', hdr_style),
        Paragraph('Qty', ParagraphStyle('HQ', parent=hdr_style, alignment=1)),
        Paragraph('Unit Price (₹)', ParagraphStyle('HUP', parent=hdr_style, alignment=2)),
        Paragraph('Tax', ParagraphStyle('HT', parent=hdr_style, alignment=1)),
        Paragraph('Line Total (₹)', ParagraphStyle('HTOT', parent=hdr_style, alignment=2))
    ]]
    
    for it in inv_data['items']:
        p_price = f"{it['price']:,.2f}"
        p_total = f"{it['total']:,.2f}"
        item_rows.append([
            Paragraph(it['desc'], cell_style),
            Paragraph(str(it['qty']), ParagraphStyle('CQ', parent=cell_style, alignment=1)),
            Paragraph(p_price, cell_right),
            Paragraph('18%', ParagraphStyle('CT', parent=cell_style, alignment=1)),
            Paragraph(p_total, cell_right)
        ])
    
    t_items = Table(item_rows, colWidths=[240, 45, 90, 45, 120])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ffffff')),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 14))
    
    # Totals Table
    s_sub = f"₹ {inv_data['subtotal']:,.2f}"
    s_cgst = f"₹ {inv_data['cgst']:,.2f}"
    s_sgst = f"₹ {inv_data['sgst']:,.2f}"
    s_grand = f"₹ {inv_data['grand_total']:,.2f}"
    
    totals_rows = [
        [Paragraph('Taxable Subtotal:', meta_label), Paragraph(s_sub, cell_right)],
        [Paragraph('CGST (9%):', meta_label), Paragraph(s_cgst, cell_right)],
        [Paragraph('SGST (9%):', meta_label), Paragraph(s_sgst, cell_right)],
        [Paragraph('<b>Grand Total:</b>', ParagraphStyle('GT', parent=meta_label, fontSize=11, textColor=colors.HexColor('#0f172a'))),
         Paragraph(f'<b>{s_grand}</b>', ParagraphStyle('GTR', parent=cell_right, fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#1d4ed8')))]
    ]
    t_totals = Table(totals_rows, colWidths=[130, 130])
    t_totals.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEABOVE', (0,3), (-1,3), 1, colors.HexColor('#0f172a'))
    ]))
    
    layout_totals = Table([['', t_totals]], colWidths=[280, 260])
    story.append(layout_totals)
    story.append(Spacer(1, 20))
    
    footer_p = Paragraph(
        '<font size="7" color="#94a3b8">Computer-generated commercial tax invoice pursuant to GST provisions. Valid without physical signature when remitted electronically.</font>',
        ParagraphStyle('Foot', alignment=1)
    )
    story.append(footer_p)
    
    doc.build(story)
    print(f"Generated PDF: {filepath}")

def build_png(filename, inv_data):
    filepath = os.path.join(out_dir, filename)
    img = Image.new('RGB', (1000, 1250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(0, 0), (1000, 15)], fill=(37, 99, 235))
    draw.text((60, 50), inv_data['vendor_name'].upper(), fill=(15, 23, 42))
    draw.text((60, 80), f"GSTIN: {inv_data['vendor_tax_id']} | Corporate Office: Bandra West, Mumbai 400050", fill=(100, 116, 139))
    
    draw.text((680, 50), "TAX INVOICE", fill=(37, 99, 235))
    draw.text((680, 80), f"Invoice #: {inv_data['invoice_number']}", fill=(15, 23, 42))
    draw.text((680, 105), f"Date: {inv_data['date']}", fill=(100, 116, 139))
    draw.text((680, 130), f"PO Ref: {inv_data['po_number']}", fill=(15, 23, 42))
    
    draw.line((60, 170, 940, 170), fill=(226, 232, 240), width=2)
    
    draw.text((60, 190), "Billed To: Apex FinTech Technologies India Pvt Ltd", fill=(15, 23, 42))
    draw.text((60, 215), "Address: BKC Financial District, Mumbai, MH 400051", fill=(100, 116, 139))
    draw.text((60, 240), "GSTIN: 27AABCA9999Z1Z1 | Currency: INR", fill=(100, 116, 139))
    
    draw.rectangle([(60, 290), (940, 330)], fill=(15, 23, 42))
    draw.text((80, 303), "Item Description", fill=(255, 255, 255))
    draw.text((540, 303), "Qty", fill=(255, 255, 255))
    draw.text((620, 303), "Unit Price", fill=(255, 255, 255))
    draw.text((770, 303), "Tax", fill=(255, 255, 255))
    draw.text((840, 303), "Amount (INR)", fill=(255, 255, 255))
    
    y = 350
    for it in inv_data['items']:
        draw.text((80, y), it['desc'], fill=(15, 23, 42))
        draw.text((545, y), str(it['qty']), fill=(15, 23, 42))
        draw.text((620, y), f"{it['price']:,.2f}", fill=(15, 23, 42))
        draw.text((770, y), "18%", fill=(15, 23, 42))
        draw.text((840, y), f"{it['total']:,.2f}", fill=(15, 23, 42))
        y += 40
        draw.line((60, y, 940, y), fill=(241, 245, 249), width=1)
        y += 15
        
    draw.line((60, y + 10, 940, y + 10), fill=(226, 232, 240), width=2)
    
    draw.text((60, y + 40), "Remittance & Bank Details:", fill=(15, 23, 42))
    draw.text((60, y + 65), f"Beneficiary: {inv_data['vendor_name']}", fill=(100, 116, 139))
    draw.text((60, y + 90), f"Bank Name: {inv_data['bank_name']}", fill=(100, 116, 139))
    draw.text((60, y + 115), f"Account Number: {inv_data['bank_ac']}", fill=(100, 116, 139))
    draw.text((60, y + 140), f"IFSC Code: {inv_data['bank_ifsc']}", fill=(100, 116, 139))
    
    draw.text((650, y + 40), f"Subtotal:             INR {inv_data['subtotal']:,.2f}", fill=(71, 85, 105))
    draw.text((650, y + 70), f"CGST (9%):          INR  {inv_data['cgst']:,.2f}", fill=(71, 85, 105))
    draw.text((650, y + 100), f"SGST (9%):          INR  {inv_data['sgst']:,.2f}", fill=(71, 85, 105))
    draw.line((650, y + 125, 940, y + 125), fill=(15, 23, 42), width=2)
    draw.text((650, y + 140), f"GRAND TOTAL:   INR {inv_data['grand_total']:,.2f}", fill=(37, 99, 235))
    
    img.save(filepath, format='PNG')
    print(f"Generated PNG: {filepath}")

# 1. Clean Matching Invoice
inv1 = {
    'vendor_name': 'Infosys Cloud Solutions Limited',
    'vendor_tax_id': '29AABCI1234A1ZB',
    'invoice_number': 'INV-TEST-2026-001',
    'po_number': 'PO-2026-0002',
    'date': '2026-09-30',
    'due_date': '2026-10-30',
    'bank_name': 'HDFC Bank Limited',
    'bank_ac': '50200012345678',
    'bank_ifsc': 'HDFC0001234',
    'items': [
        {'desc': 'Ergonomic Motorized Height-Adjustable Desk', 'qty': 10, 'price': 32000.0, 'total': 320000.0},
        {'desc': 'High-Back Breathable Mesh Office Chair', 'qty': 5, 'price': 14000.0, 'total': 70000.0}
    ],
    'subtotal': 390000.0,
    'cgst': 35100.0,
    'sgst': 35100.0,
    'grand_total': 460200.0
}
build_pdf('01_clean_matching_invoice.pdf', inv1)
build_png('01_clean_matching_invoice.png', inv1)

# 2. Quantity Variance Invoice
inv2 = {
    'vendor_name': 'Tata Infotech Hardware Systems Pvt Ltd',
    'vendor_tax_id': '27AABCT3518Q1ZV',
    'invoice_number': 'INV-TEST-2026-002',
    'po_number': 'PO-2026-0001',
    'date': '2026-09-30',
    'due_date': '2026-10-30',
    'bank_name': 'State Bank of India',
    'bank_ac': '300123456789',
    'bank_ifsc': 'SBIN0001234',
    'items': [
        {'desc': 'Dell PowerEdge Rack Server Dual Xeon', 'qty': 25, 'price': 350000.0, 'total': 8750000.0}
    ],
    'subtotal': 8750000.0,
    'cgst': 787500.0,
    'sgst': 787500.0,
    'grand_total': 10325000.0
}
build_pdf('02_quantity_variance_invoice.pdf', inv2)
build_png('02_quantity_variance_invoice.png', inv2)

# 3. Price Variance Invoice
inv3 = {
    'vendor_name': 'Larsen & Toubro Facility Solutions Ltd',
    'vendor_tax_id': '27AABCL0123F1ZY',
    'invoice_number': 'INV-TEST-2026-003',
    'po_number': 'PO-2026-0003',
    'date': '2026-09-30',
    'due_date': '2026-10-30',
    'bank_name': 'ICICI Bank',
    'bank_ac': '001105001234',
    'bank_ifsc': 'ICIC0000011',
    'items': [
        {'desc': 'Cisco Catalyst 48-Port Managed Gigabit Switch', 'qty': 10, 'price': 115000.0, 'total': 1150000.0}
    ],
    'subtotal': 1150000.0,
    'cgst': 103500.0,
    'sgst': 103500.0,
    'grand_total': 1357000.0
}
build_pdf('03_price_variance_invoice.pdf', inv3)
build_png('03_price_variance_invoice.png', inv3)

print("All sample invoices successfully created.")
