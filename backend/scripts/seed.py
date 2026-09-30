import hashlib
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.session import SessionLocal
from database.enums import (
    TenantStatus,
    UserStatus,
    RoleCode,
    VendorStatus,
    VendorRiskStatus,
    POStatus,
    ReceiptStatus,
    InvoiceStatus,
    ExtractionStatus,
    ControlRunStatus,
    ControlCategory,
    ControlCode,
    ControlStatus,
    SeverityLevel,
    RiskSignalStatus,
    ExceptionStatus,
    ApprovalStatus,
    ApprovalDecision,
    PayableStatus,
    PaymentStatus,
)
from database.models import (
    Tenant,
    User,
    Role,
    UserRole,
    Vendor,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
    Invoice,
    InvoiceRevision,
    InvoiceItem,
    ControlRun,
    ControlResult,
    RiskSignal,
    Exception as DBException,
    ApprovalPolicy,
    Approval,
    PayableLedger,
    Payment,
    AuditLog,
)

def hash_string(val: str) -> str:
    return hashlib.sha256(val.encode("utf-8")).hexdigest()

def seed_database() -> None:
    session = SessionLocal()
    try:
        print("Starting comprehensive database seeding...")

        # -------------------------------------------------------------
        # 1. Tenant
        # -------------------------------------------------------------
        tenant = Tenant(
            name="Apex FinTech Technologies Pvt Ltd",
            slug="apex-fintech",
            status=TenantStatus.ACTIVE.value,
        )
        session.add(tenant)
        session.flush()
        tenant_id = tenant.id
        print(f"Created Tenant: {tenant.name} ({tenant.slug})")

        # -------------------------------------------------------------
        # 2. Roles
        # -------------------------------------------------------------
        roles_data = [
            (RoleCode.ADMIN.value, "System Administrator", "Full system configuration and override access"),
            (RoleCode.AP_CLERK.value, "Accounts Payable Clerk", "Uploads invoices, reviews extractions, and corrects data"),
            (RoleCode.PROCUREMENT_MANAGER.value, "Procurement Manager", "Manages purchase orders and resolves procurement exceptions"),
            (RoleCode.RECEIVING_USER.value, "Receiving / Warehouse Specialist", "Records and verifies physical goods/service receipts"),
            (RoleCode.FINANCE_MANAGER.value, "Finance Manager", "Reviews invoices and approves up to tier threshold"),
            (RoleCode.FINANCE_HEAD.value, "Head of Finance / Controller", "Authorizes high-value invoices"),
            (RoleCode.AUDITOR.value, "Internal/External Auditor", "Read-only access to audit logs and control evidence"),
        ]
        roles_map = {}
        for code, name, desc in roles_data:
            role = Role(code=code, name=name, description=desc)
            session.add(role)
            roles_map[code] = role
        session.flush()

        # -------------------------------------------------------------
        # 3. Users & UserRoles
        # -------------------------------------------------------------
        users_data = [
            ("rajesh.sharma@apexfin.in", "Rajesh Sharma", [RoleCode.ADMIN.value]),
            ("priya.nair@apexfin.in", "Priya Nair", [RoleCode.AP_CLERK.value]),
            ("amit.patel@apexfin.in", "Amit Patel", [RoleCode.AP_CLERK.value]),
            ("vikram.malhotra@apexfin.in", "Vikram Malhotra", [RoleCode.PROCUREMENT_MANAGER.value]),
            ("sneha.kulkarni@apexfin.in", "Sneha Kulkarni", [RoleCode.RECEIVING_USER.value]),
            ("ananya.rao@apexfin.in", "Ananya Rao", [RoleCode.FINANCE_MANAGER.value]),
            ("rohan.verma@apexfin.in", "Rohan Verma", [RoleCode.FINANCE_HEAD.value]),
            ("sunita.mehta@apexfin.in", "Sunita Mehta", [RoleCode.AUDITOR.value]),
            ("kavita.deshmukh@apexfin.in", "Kavita Deshmukh", [RoleCode.FINANCE_MANAGER.value]),
        ]
        users_map = {}
        for email, full_name, user_role_codes in users_data:
            user = User(
                tenant_id=tenant_id,
                email=email,
                full_name=full_name,
                status=UserStatus.ACTIVE.value,
            )
            session.add(user)
            session.flush()
            users_map[email] = user
            for r_code in user_role_codes:
                ur = UserRole(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    role_id=roles_map[r_code].id,
                )
                session.add(ur)
        session.flush()
        print(f"Created {len(users_map)} Users with role assignments.")

        # -------------------------------------------------------------
        # 4. Approval Policies
        # -------------------------------------------------------------
        policies_data = [
            ("Tier 1 - Standard Operating Invoices", Decimal("0.00"), Decimal("50000.00"), RoleCode.AP_CLERK.value, 1),
            ("Tier 2 - Managerial Authority", Decimal("50000.01"), Decimal("500000.00"), RoleCode.FINANCE_MANAGER.value, 1),
            ("Tier 3 - Executive Finance Authority", Decimal("500000.01"), Decimal("2500000.00"), RoleCode.FINANCE_HEAD.value, 1),
            ("Tier 4 - CFO / Board Authority", Decimal("2500000.01"), None, RoleCode.ADMIN.value, 1),
        ]
        approval_policies = []
        for name, min_amt, max_amt, req_role, seq in policies_data:
            pol = ApprovalPolicy(
                tenant_id=tenant_id,
                name=name,
                min_amount=min_amt,
                max_amount=max_amt,
                required_role=req_role,
                sequence_order=seq,
                requires_all_controls_pass=True,
                active=True,
            )
            session.add(pol)
            approval_policies.append(pol)
        session.flush()

        # -------------------------------------------------------------
        # 5. Vendors (10 Vendors)
        # -------------------------------------------------------------
        vendors_seed = [
            ("VEND-1001", "Tata Infotech Hardware Systems Pvt Ltd", "Tata Infotech", "27AABCT3518Q1ZV", "U72200MH1998PTC115642", "contact@tatainfotech.in", "+91-22-67891234", "Nariman Point", "Mumbai", "Maharashtra", "1234", "HDFC Bank", "HDFC0000123"),
            ("VEND-1002", "Infosys Cloud Solutions Limited", "Infosys Cloud", "29AABCI1234A1ZB", "L85110KA1981PLC013115", "billing@infosyscloud.in", "+91-80-28520261", "Electronics City", "Bengaluru", "Karnataka", "5678", "State Bank of India", "SBIN0004567"),
            ("VEND-1003", "Larsen & Toubro Facility Solutions Ltd", "L&T Facilities", "27AABCL0123F1ZY", "L99999MH1946PLC004768", "facilities@larsentoubro.in", "+91-22-67525656", "Powai", "Mumbai", "Maharashtra", "9012", "ICICI Bank", "ICIC0008910"),
            ("VEND-1004", "Reliance Digital Logistics Private Limited", "Reliance Logistics", "24AABCR4567P1ZX", "U60200GJ2005PTC046789", "ops@reliancelogistics.in", "+91-79-35002000", "GIFT City", "Gandhinagar", "Gujarat", "3456", "Axis Bank", "UTIB0001234"),
            ("VEND-1005", "Wipro Enterprise Networks Limited", "Wipro Networks", "29AABCW7890M1ZW", "L32102KA1945PLC020800", "orders@wipronetworks.in", "+91-80-28440011", "Sarjapur Road", "Bengaluru", "Karnataka", "7890", "Kotak Mahindra Bank", "KKBK0000987"),
            ("VEND-1006", "Bharti Airtel Business Services Ltd", "Airtel Business", "07AABCB2345K1ZV", "L74899DL1995PLC070609", "corporate@airtelbusiness.in", "+91-11-46666100", "Connaught Place", "New Delhi", "Delhi", "2345", "Standard Chartered", "SCBL0036001"),
            ("VEND-1007", "Godrej Workspace Furniture Limited", "Godrej Workspace", "27AABCG6789D1ZS", "L28993MH1932PLC001828", "sales@godrejworkspace.in", "+91-22-67965656", "Vikhroli", "Mumbai", "Maharashtra", "6789", "IndusInd Bank", "INDB0000055"),
            ("VEND-1008", "Blue Dart Supply Chain Express Ltd", "Blue Dart Express", "27AABCB8901L1ZT", "L61074MH1991PLC061074", "invoices@bluedart.in", "+91-22-28396444", "Andheri East", "Mumbai", "Maharashtra", "0123", "Citibank NA", "CITI0000002"),
            ("VEND-1009", "Mahindra Cyber Defense Solutions Pvt Ltd", "Mahindra CyberSec", "27AABCM3456R1ZP", "U74999MH2012PTC231456", "security@mahindracyber.in", "+91-20-66042000", "Hinjawadi", "Pune", "Maharashtra", "4567", "Yes Bank", "YESB0000001"),
            ("VEND-1010", "HCL Tech Infrastructure Services", "HCL Tech", "09AABCH5678Q1ZQ", "L74140UP1991PLC013400", "finance@hclinfra.in", "+91-120-2520701", "Sector 126", "Noida", "Uttar Pradesh", "8901", "Punjab National Bank", "PUNB0001200"),
        ]
        vendors = []
        for code, l_name, d_name, tax_id, reg_no, email, phone, addr, city, state, l4, b_name, ifsc in vendors_seed:
            v = Vendor(
                tenant_id=tenant_id,
                vendor_code=code,
                legal_name=l_name,
                display_name=d_name,
                tax_identifier=tax_id,
                registration_number=reg_no,
                email=email,
                phone=phone,
                address=addr,
                city=city,
                state=state,
                country="India",
                currency="INR",
                payment_terms_days=30,
                status=VendorStatus.ACTIVE.value,
                risk_status=VendorRiskStatus.NORMAL.value,
                bank_account_last4=l4,
                bank_account_hash=hash_string(f"BANK_ACC_SALT_{code}_{l4}"),
                bank_name=b_name,
                ifsc=ifsc,
            )
            session.add(v)
            vendors.append(v)
        session.flush()
        print(f"Created {len(vendors)} Vendors.")

        # -------------------------------------------------------------
        # 6. Purchase Orders (30 POs) & PO Items (60+ items)
        # -------------------------------------------------------------
        purchase_orders = []
        po_items_map = {} # po_id -> list of items

        proc_user = users_map["vikram.malhotra@apexfin.in"]

        products = [
            ("PRD-LT01", "ThinkPad Enterprise Laptop Core i7 32GB", Decimal("85000.00"), Decimal("0.18")),
            ("PRD-MON27", "27-inch 4K IPS Ergonomic Monitor", Decimal("22000.00"), Decimal("0.18")),
            ("PRD-SRV01", "Dell PowerEdge Rack Server Dual Xeon", Decimal("350000.00"), Decimal("0.18")),
            ("PRD-SW01", "Enterprise Cloud Firewall Annual License", Decimal("120000.00"), Decimal("0.18")),
            ("PRD-DSK01", "Ergonomic Motorized Height-Adjustable Desk", Decimal("32000.00"), Decimal("0.18")),
            ("PRD-CHR01", "High-Back Breathable Mesh Office Chair", Decimal("14000.00"), Decimal("0.18")),
            ("PRD-NET01", "Cisco Catalyst 48-Port Managed Gigabit Switch", Decimal("95000.00"), Decimal("0.18")),
            ("PRD-SEC01", "Endpoint Protection & EDR 500-Seat License", Decimal("240000.00"), Decimal("0.18")),
            ("PRD-LOG01", "Inter-City Express Air Cargo Freight Service", Decimal("45000.00"), Decimal("0.18")),
            ("PRD-MNT01", "Annual Campus Facilities HVAC Maintenance", Decimal("180000.00"), Decimal("0.18")),
        ]

        base_date = date.today() - timedelta(days=60)

        for i in range(1, 31):
            vendor = vendors[(i - 1) % len(vendors)]
            po_num = f"PO-2026-{i:04d}"
            po_d = base_date + timedelta(days=i)

            po = PurchaseOrder(
                tenant_id=tenant_id,
                vendor_id=vendor.id,
                po_number=po_num,
                po_date=po_d,
                currency="INR",
                status=POStatus.APPROVED.value,
                approval_status="APPROVED",
                payment_terms_days=30,
                subtotal=Decimal("0.00"),
                tax_total=Decimal("0.00"),
                discount_total=Decimal("0.00"),
                grand_total=Decimal("0.00"),
                notes=f"Purchase Order for {vendor.display_name} operations",
                created_by=proc_user.id,
                approved_by=users_map["rohan.verma@apexfin.in"].id,
                approved_at=datetime.combine(po_d + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
            )
            session.add(po)
            session.flush()
            purchase_orders.append(po)

            # For Scenario L (i == 12): create 1 item totalling ₹49,990.00 right below Tier 1 threshold
            if i == 12:
                prod1 = products[0]
                qty1 = Decimal("1.0000")
                price1 = Decimal("42364.41")
                tax_rate1 = Decimal("0.1800")
                line_tot1 = qty1 * price1
                tax_amt1 = (line_tot1 * tax_rate1).quantize(Decimal("0.01"))
                total1 = line_tot1 + tax_amt1

                item1 = PurchaseOrderItem(
                    tenant_id=tenant_id,
                    purchase_order_id=po.id,
                    line_number=1,
                    product_code="SRV-AUD-001",
                    description="Professional Annual Compliance Review",
                    quantity=qty1,
                    unit_of_measure="EA",
                    unit_price=price1,
                    discount_amount=Decimal("0.00"),
                    tax_rate=tax_rate1,
                    tax_amount=tax_amt1,
                    line_total=total1,
                )
                session.add(item1)
                session.flush()
                po_items_map[po.id] = [item1]

                po.subtotal = line_tot1
                po.tax_total = tax_amt1
                po.grand_total = line_tot1 + tax_amt1
                session.flush()
            else:
                # Add 2 items per PO
                prod1 = products[(i * 2) % len(products)]
                prod2 = products[(i * 2 + 1) % len(products)]

                qty1 = Decimal(f"{(i % 5 + 1) * 10}.0000") # 10, 20, 30, 40, 50
                qty2 = Decimal(f"{(i % 3 + 1) * 5}.0000")  # 5, 10, 15

                price1 = prod1[2]
                price2 = prod2[2]

                tax_rate1 = prod1[3]
                tax_rate2 = prod2[3]

                line_tot1 = qty1 * price1
                tax_amt1 = (line_tot1 * tax_rate1).quantize(Decimal("0.01"))
                total1 = line_tot1 + tax_amt1

                line_tot2 = qty2 * price2
                tax_amt2 = (line_tot2 * tax_rate2).quantize(Decimal("0.01"))
                total2 = line_tot2 + tax_amt2

                item1 = PurchaseOrderItem(
                    tenant_id=tenant_id,
                    purchase_order_id=po.id,
                    line_number=1,
                    product_code=prod1[0],
                    description=prod1[1],
                    quantity=qty1,
                    unit_of_measure="EA",
                    unit_price=price1,
                    discount_amount=Decimal("0.00"),
                    tax_rate=tax_rate1,
                    tax_amount=tax_amt1,
                    line_total=total1,
                )
                item2 = PurchaseOrderItem(
                    tenant_id=tenant_id,
                    purchase_order_id=po.id,
                    line_number=2,
                    product_code=prod2[0],
                    description=prod2[1],
                    quantity=qty2,
                    unit_of_measure="EA",
                    unit_price=price2,
                    discount_amount=Decimal("0.00"),
                    tax_rate=tax_rate2,
                    tax_amount=tax_amt2,
                    line_total=total2,
                )
                session.add_all([item1, item2])
                session.flush()
                po_items_map[po.id] = [item1, item2]

                po.subtotal = line_tot1 + line_tot2
                po.tax_total = tax_amt1 + tax_amt2
                po.grand_total = po.subtotal + po.tax_total
                session.flush()

        print(f"Created {len(purchase_orders)} Purchase Orders with {len(purchase_orders)*2} PO Line Items.")

        # -------------------------------------------------------------
        # 7. Goods Receipts (30 GRs) & Receipt Items
        # -------------------------------------------------------------
        goods_receipts = []
        gr_items_map = {} # po_id -> list of gr items
        rec_user = users_map["sneha.kulkarni@apexfin.in"]

        for i, po in enumerate(purchase_orders, start=1):
            gr_num = f"GR-2026-{i:04d}"
            gr_date = po.po_date + timedelta(days=5)

            gr = GoodsReceipt(
                tenant_id=tenant_id,
                purchase_order_id=po.id,
                receipt_number=gr_num,
                received_date=gr_date,
                status=ReceiptStatus.ACCEPTED.value,
                received_by=rec_user.id,
                notes=f"Warehouse delivery acceptance for {po.po_number}",
            )
            session.add(gr)
            session.flush()
            goods_receipts.append(gr)

            po_items = po_items_map[po.id]
            gr_items = []
            for item in po_items:
                # Normal case: accepted = received = item.quantity
                # For PO 2 (Scenario B): GR only received 80%
                rec_qty = item.quantity
                acc_qty = item.quantity
                if i == 2 and item.line_number == 1:
                    rec_qty = item.quantity * Decimal("0.80") # 80 instead of 100
                    acc_qty = rec_qty
                elif i == 6: # Scenario F (Partial receipt)
                    rec_qty = item.quantity * Decimal("0.50") # exactly half received
                    acc_qty = rec_qty

                gri = GoodsReceiptItem(
                    tenant_id=tenant_id,
                    goods_receipt_id=gr.id,
                    purchase_order_item_id=item.id,
                    received_quantity=rec_qty,
                    accepted_quantity=acc_qty,
                    rejected_quantity=Decimal("0.0000"),
                    notes="Verified physical condition and serial numbers",
                )
                session.add(gri)
                gr_items.append(gri)
            session.flush()
            gr_items_map[po.id] = gr_items

        print(f"Created {len(goods_receipts)} Goods Receipts with items.")

        # -------------------------------------------------------------
        # 8. Invoices (40 Invoices covering Scenarios A through O)
        # -------------------------------------------------------------
        ap_clerk = users_map["priya.nair@apexfin.in"]
        fin_mgr = users_map["ananya.rao@apexfin.in"]
        fin_head = users_map["rohan.verma@apexfin.in"]

        invoices = []

        for i in range(1, 41):
            po = purchase_orders[(i - 1) % len(purchase_orders)]
            vendor = po.vendor
            inv_num = f"INV-2026-{i:04d}"
            inv_date = po.po_date + timedelta(days=7)
            due_date = inv_date + timedelta(days=vendor.payment_terms_days)
            doc_hash = hash_string(f"DOCUMENT_CONTENT_{inv_num}_{tenant_id}")

            status = InvoiceStatus.AWAITING_APPROVAL.value
            ext_status = ExtractionStatus.COMPLETED.value
            ext_conf = Decimal("98.50")

            # Check special scenarios:
            if i == 1: # Scenario A: Perfect Clean Invoice
                status = InvoiceStatus.APPROVED.value
            elif i == 2: # Scenario B: Quantity Mismatch (Invoice claims 100, receipt was 80)
                status = InvoiceStatus.EXCEPTION.value
            elif i == 3: # Scenario C: Price Mismatch (Invoice charges higher price)
                status = InvoiceStatus.EXCEPTION.value
            elif i == 4: # Scenario D: PO does not exist
                status = InvoiceStatus.EXCEPTION.value
            elif i == 5: # Scenario E: Vendor mismatch
                status = InvoiceStatus.EXCEPTION.value
            elif i == 6: # Scenario F: Partial receipt (PO 100, GR 50, Invoice 50)
                status = InvoiceStatus.AWAITING_APPROVAL.value
            elif i == 7: # Scenario G: Exact duplicate of Invoice 1
                status = InvoiceStatus.EXCEPTION.value
                doc_hash = hash_string(f"DOCUMENT_CONTENT_INV-2026-0001_{tenant_id}") # identical hash!
            elif i == 8: # Scenario H: Semantic duplicate of Invoice 6
                status = InvoiceStatus.EXCEPTION.value
            elif i == 9: # Scenario I: Tax mismatch
                status = InvoiceStatus.EXCEPTION.value
            elif i == 10: # Scenario J: Total calculation mismatch
                status = InvoiceStatus.EXCEPTION.value
            elif i == 11: # Scenario K: Bank details mismatch
                status = InvoiceStatus.EXCEPTION.value
            elif i == 12: # Scenario L: Invoice close to approval threshold
                status = InvoiceStatus.AWAITING_APPROVAL.value
            elif i == 13: # Scenario M: Corrected invoice with Revision 2
                status = InvoiceStatus.APPROVED.value
            elif i == 14: # Scenario N: Approved -> Payable -> Partially Paid
                status = InvoiceStatus.PAYABLE_CREATED.value
            elif i == 15: # Scenario O: Rejected invoice
                status = InvoiceStatus.REJECTED.value
            elif i > 35:
                status = InvoiceStatus.PAID.value
            elif i > 30:
                status = InvoiceStatus.PAYABLE_CREATED.value

            inv = Invoice(
                tenant_id=tenant_id,
                vendor_id=vendors[(i + 1) % len(vendors)].id if i == 5 else vendor.id, # Scenario E: different vendor!
                purchase_order_id=None if i == 4 else po.id, # Scenario D: no PO!
                invoice_number=inv_num,
                invoice_date=inv_date,
                due_date=due_date,
                currency="INR",
                status=status,
                source_type="UPLOAD",
                source_file_name=f"{inv_num}.pdf",
                source_file_url=f"s3://ap-invoices/{tenant.slug}/{inv_num}.pdf",
                document_hash=doc_hash,
                extraction_status=ext_status,
                extraction_confidence=ext_conf,
                submitted_by=ap_clerk.id,
            )
            session.add(inv)
            session.flush()
            invoices.append(inv)

            # Revision 1
            po_items = po_items_map[po.id]
            rev1_subtotal = Decimal("0.00")
            rev1_tax = Decimal("0.00")

            rev = InvoiceRevision(
                tenant_id=tenant_id,
                invoice_id=inv.id,
                revision_number=1,
                invoice_number=inv_num,
                invoice_date=inv_date,
                due_date=due_date,
                currency="INR",
                subtotal=Decimal("0.00"),
                discount_total=Decimal("0.00"),
                tax_total=Decimal("0.00"),
                grand_total=Decimal("0.00"),
                vendor_name_as_submitted=vendor.legal_name,
                vendor_tax_id_as_submitted=vendor.tax_identifier,
                bank_account_last4="9999" if i == 11 else vendor.bank_account_last4, # Scenario K: mismatched bank!
                bank_account_hash=hash_string("FAKE_BANK_ACC_9999") if i == 11 else vendor.bank_account_hash,
                extraction_method="AI_OCR_PARSE",
                extraction_confidence=ext_conf,
                raw_extracted_data={"ocr_confidence": 0.985, "vendor": vendor.display_name, "raw_total": str(po.grand_total)},
                submitted_at=datetime.combine(inv_date, datetime.min.time(), tzinfo=timezone.utc),
                submitted_by=ap_clerk.id,
            )
            session.add(rev)
            session.flush()

            # Link revision to invoice
            inv.current_revision_id = rev.id

            # Add invoice items for Revision 1
            for p_item in po_items:
                item_qty = p_item.quantity
                item_price = p_item.unit_price
                item_tax_rate = p_item.tax_rate

                if i == 3 and p_item.line_number == 1: # Scenario C: Price mismatch (charged higher)
                    item_price = item_price + Decimal("2000.00")
                elif i == 6: # Scenario F: Partial receipt billing
                    item_qty = p_item.quantity * Decimal("0.50")
                elif i == 9: # Scenario I: Tax mismatch (12% instead of 18%)
                    item_tax_rate = Decimal("0.1200")
                elif i == 12 and p_item.line_number == 1: # Scenario L: Close to threshold (e.g. 49,990)
                    item_qty = Decimal("1.0000")
                    item_price = Decimal("42364.41")
                    item_tax_rate = Decimal("0.1800")

                line_sub = (item_qty * item_price).quantize(Decimal("0.01"))
                line_tax = (line_sub * item_tax_rate).quantize(Decimal("0.01"))
                line_tot = line_sub + line_tax

                inv_item = InvoiceItem(
                    tenant_id=tenant_id,
                    invoice_revision_id=rev.id,
                    line_number=p_item.line_number,
                    product_code=p_item.product_code,
                    description=p_item.description,
                    quantity=item_qty,
                    unit_of_measure=p_item.unit_of_measure,
                    unit_price=item_price,
                    discount_amount=Decimal("0.00"),
                    tax_rate=item_tax_rate,
                    tax_amount=line_tax,
                    line_total=line_tot,
                )
                session.add(inv_item)
                rev1_subtotal += line_sub
                rev1_tax += line_tax

            rev.subtotal = rev1_subtotal
            rev.tax_total = rev1_tax
            # Scenario I: Tax calculation mismatch (claimed ₹15,000 vs calculated tax)
            if i == 9:
                rev.tax_total = Decimal("15000.00")

            # Scenario J: Header total mismatch (add ₹7,000 artificial discrepancy)
            if i == 10:
                rev.grand_total = rev.subtotal + rev.tax_total + Decimal("7000.00")
            else:
                rev.grand_total = rev.subtotal + rev.tax_total

            session.flush()

            # ---------------------------------------------------------
            # Revision 2 for Scenario M (Corrected invoice)
            # ---------------------------------------------------------
            target_rev = rev
            if i == 13:
                rev2 = InvoiceRevision(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    revision_number=2,
                    invoice_number=inv_num,
                    invoice_date=inv_date + timedelta(days=2),
                    due_date=due_date + timedelta(days=2),
                    currency="INR",
                    subtotal=po.subtotal,
                    discount_total=Decimal("0.00"),
                    tax_total=po.tax_total,
                    grand_total=po.grand_total,
                    vendor_name_as_submitted=vendor.legal_name,
                    vendor_tax_id_as_submitted=vendor.tax_identifier,
                    bank_account_last4=vendor.bank_account_last4,
                    bank_account_hash=vendor.bank_account_hash,
                    extraction_method="AI_OCR_PARSE",
                    extraction_confidence=Decimal("99.50"),
                    raw_extracted_data={"ocr_confidence": 0.995, "corrected": True},
                    submitted_at=datetime.combine(inv_date + timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc),
                    submitted_by=ap_clerk.id,
                )
                session.add(rev2)
                session.flush()
                inv.current_revision_id = rev2.id
                target_rev = rev2

                # Add items matching PO perfectly
                for p_item in po_items:
                    line_sub = (p_item.quantity * p_item.unit_price).quantize(Decimal("0.01"))
                    line_tax = (line_sub * p_item.tax_rate).quantize(Decimal("0.01"))
                    ii = InvoiceItem(
                        tenant_id=tenant_id,
                        invoice_revision_id=rev2.id,
                        line_number=p_item.line_number,
                        product_code=p_item.product_code,
                        description=p_item.description,
                        quantity=p_item.quantity,
                        unit_of_measure=p_item.unit_of_measure,
                        unit_price=p_item.unit_price,
                        discount_amount=Decimal("0.00"),
                        tax_rate=p_item.tax_rate,
                        tax_amount=line_tax,
                        line_total=line_sub + line_tax,
                    )
                    session.add(ii)
                session.flush()

            # ---------------------------------------------------------
            # Control Run & Control Results
            # ---------------------------------------------------------
            c_run = ControlRun(
                tenant_id=tenant_id,
                invoice_id=inv.id,
                invoice_revision_id=target_rev.id,
                run_number=1 if i != 13 else 2,
                status=ControlRunStatus.PASSED.value if status in [InvoiceStatus.APPROVED.value, InvoiceStatus.AWAITING_APPROVAL.value, InvoiceStatus.PAYABLE_CREATED.value, InvoiceStatus.PAID.value] else ControlRunStatus.FAILED.value,
                ruleset_version="v1.0.0",
                started_at=datetime.now(timezone.utc) - timedelta(hours=2),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=2) + timedelta(seconds=12),
                triggered_by=ap_clerk.id,
            )
            session.add(c_run)
            session.flush()

            # Helper to create control result
            def make_res(code, cat, c_status, sev, exp, act, var_v=None, var_p=None, msg="Validation completed"):
                res = ControlResult(
                    tenant_id=tenant_id,
                    control_run_id=c_run.id,
                    invoice_id=inv.id,
                    control_code=code,
                    control_category=cat,
                    status=c_status,
                    severity=sev,
                    expected_value=exp,
                    actual_value=act,
                    variance_value=var_v,
                    variance_percentage=var_p,
                    evidence={"evaluated_rule": f"RULE_{code}_v1", "source": "3way_engine"},
                    message=msg,
                    rule_version="v1.0.0",
                    evaluated_at=datetime.now(timezone.utc),
                )
                session.add(res)
                return res

            # Core deterministic controls
            v_res = make_res(ControlCode.VENDOR_EXISTS.value, ControlCategory.VENDOR.value, ControlStatus.PASS.value, SeverityLevel.INFO.value, {"vendor_code": vendor.vendor_code}, {"vendor_code": vendor.vendor_code})
            
            po_status = ControlStatus.FAIL.value if i == 4 else ControlStatus.PASS.value
            po_res = make_res(ControlCode.PO_EXISTS.value, ControlCategory.PROCUREMENT.value, po_status, SeverityLevel.CRITICAL.value if i == 4 else SeverityLevel.INFO.value, {"po_required": True}, {"po_found": i != 4}, msg="Purchase order not found in system" if i == 4 else "PO verified")

            po_vend_status = ControlStatus.FAIL.value if i == 5 else ControlStatus.PASS.value
            make_res(ControlCode.PO_VENDOR_MATCH.value, ControlCategory.PROCUREMENT.value, po_vend_status, SeverityLevel.HIGH.value if i == 5 else SeverityLevel.INFO.value, {"vendor_id": str(po.vendor_id)}, {"vendor_id": str(inv.vendor_id)}, msg="Vendor mismatch between invoice and PO" if i == 5 else "Vendor matches PO")

            qty_status = ControlStatus.FAIL.value if i == 2 else ControlStatus.PASS.value
            qty_res = make_res(ControlCode.QUANTITY_MATCH.value, ControlCategory.RECEIPT.value, qty_status, SeverityLevel.HIGH.value if i == 2 else SeverityLevel.INFO.value, {"accepted_qty": 80.0} if i == 2 else {"accepted_qty": 100.0}, {"invoiced_qty": 100.0}, Decimal("20.00") if i == 2 else Decimal("0.00"), Decimal("25.0000") if i == 2 else Decimal("0.0000"), msg="Invoiced quantity exceeds accepted goods receipt" if i == 2 else "Quantity within tolerance")

            price_status = ControlStatus.FAIL.value if i == 3 else ControlStatus.PASS.value
            price_res = make_res(ControlCode.PRICE_MATCH.value, ControlCategory.FINANCIAL.value, price_status, SeverityLevel.HIGH.value if i == 3 else SeverityLevel.INFO.value, {"po_unit_price": str(po_items[0].unit_price)}, {"inv_unit_price": str(po_items[0].unit_price + Decimal("2000.00")) if i == 3 else str(po_items[0].unit_price)}, Decimal("2000.00") if i == 3 else Decimal("0.00"), Decimal("4.0000") if i == 3 else Decimal("0.0000"), msg="Unit price higher than agreed PO contract price" if i == 3 else "Price matches PO")

            tax_status = ControlStatus.FAIL.value if i == 9 else ControlStatus.PASS.value
            make_res(ControlCode.TAX_VALIDATION.value, ControlCategory.FINANCIAL.value, tax_status, SeverityLevel.MEDIUM.value if i == 9 else SeverityLevel.INFO.value, {"expected_tax_rate": "18.00%"}, {"actual_tax_rate": "12.00%" if i == 9 else "18.00%"}, msg="Tax rate mismatch against standard HSN schedule" if i == 9 else "Tax mathematically validated")

            tot_status = ControlStatus.FAIL.value if i == 10 else ControlStatus.PASS.value
            make_res(ControlCode.TOTAL_VALIDATION.value, ControlCategory.FINANCIAL.value, tot_status, SeverityLevel.CRITICAL.value if i == 10 else SeverityLevel.INFO.value, {"calculated_total": str(rev.subtotal + rev.tax_total)}, {"header_total": str(rev.grand_total)}, Decimal("7000.00") if i == 10 else Decimal("0.00"), msg="Invoice header grand total does not match line item sum" if i == 10 else "Header total mathematically matches line totals")

            dup_exact_status = ControlStatus.FAIL.value if i == 7 else ControlStatus.PASS.value
            dup_res = make_res(ControlCode.DUPLICATE_EXACT.value, ControlCategory.DUPLICATE.value, dup_exact_status, SeverityLevel.CRITICAL.value if i == 7 else SeverityLevel.INFO.value, {"hash_collision": False}, {"hash_collision": i == 7}, msg="Exact document hash collision detected with INV-2026-0001" if i == 7 else "No exact hash duplicate found")

            dup_sem_status = ControlStatus.WARNING.value if i == 8 else ControlStatus.PASS.value
            make_res(ControlCode.DUPLICATE_SEMANTIC.value, ControlCategory.DUPLICATE.value, dup_sem_status, SeverityLevel.MEDIUM.value if i == 8 else SeverityLevel.INFO.value, {"similarity_threshold": 0.85}, {"computed_similarity": 0.94 if i == 8 else 0.12}, msg="High semantic line-item similarity with historical invoice INV-2026-0006" if i == 8 else "Semantic similarity within safe bounds")

            bank_status = ControlStatus.FAIL.value if i == 11 else ControlStatus.PASS.value
            bank_res = make_res(ControlCode.BANK_DETAILS_MATCH.value, ControlCategory.SECURITY.value, bank_status, SeverityLevel.CRITICAL.value if i == 11 else SeverityLevel.INFO.value, {"expected_last4": vendor.bank_account_last4}, {"actual_last4": "9999" if i == 11 else vendor.bank_account_last4}, msg="Invoice remittance bank details do not match vendor master record" if i == 11 else "Bank destination account verified")

            session.flush()

            # ---------------------------------------------------------
            # Risk Signals & Exceptions for deliberate failure cases
            # ---------------------------------------------------------
            if i == 2: # Scenario B: Quantity Mismatch
                exc = DBException(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    control_result_id=qty_res.id,
                    exception_code="QUANTITY_MISMATCH",
                    title="Invoiced quantity exceeds accepted goods receipt",
                    description="Invoice claims 100 units while warehouse goods receipt GR-2026-0002 accepted only 80 units.",
                    severity=SeverityLevel.HIGH.value,
                    status=ExceptionStatus.OPEN.value,
                    assigned_to=users_map["sneha.kulkarni@apexfin.in"].id,
                )
                session.add(exc)
            elif i == 3: # Scenario C: Price Mismatch
                exc = DBException(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    control_result_id=price_res.id,
                    exception_code="PRICE_MISMATCH",
                    title="Unit price discrepancy on line item 1",
                    description="Invoiced unit price is ₹2,000 higher than PO unit price.",
                    severity=SeverityLevel.HIGH.value,
                    status=ExceptionStatus.IN_REVIEW.value,
                    assigned_to=proc_user.id,
                )
                session.add(exc)
            elif i == 4: # Scenario D: PO not found
                exc = DBException(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    control_result_id=po_res.id,
                    exception_code="PO_NOT_FOUND",
                    title="No approved Purchase Order associated with invoice",
                    description="The invoice did not reference a valid purchase order in the tenant database.",
                    severity=SeverityLevel.CRITICAL.value,
                    status=ExceptionStatus.OPEN.value,
                    assigned_to=proc_user.id,
                )
                session.add(exc)
            elif i == 7: # Scenario G: Exact Duplicate
                exc = DBException(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    control_result_id=dup_res.id,
                    exception_code="DUPLICATE_INVOICE",
                    title="Identical invoice document checksum detected",
                    description="Exact binary hash collision with previously approved invoice INV-2026-0001.",
                    severity=SeverityLevel.CRITICAL.value,
                    status=ExceptionStatus.OPEN.value,
                    assigned_to=ap_clerk.id,
                )
                sig = RiskSignal(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    control_result_id=dup_res.id,
                    signal_code="DUPLICATE_SUSPECTED",
                    category="DUPLICATE",
                    severity=SeverityLevel.CRITICAL.value,
                    score=Decimal("100.00"),
                    confidence=Decimal("99.90"),
                    description="Exact document SHA-256 match with INV-2026-0001",
                    evidence={"matching_invoice": "INV-2026-0001"},
                    status=RiskSignalStatus.ACTIVE.value,
                )
                session.add_all([exc, sig])
            elif i == 8: # Scenario H: Semantic Duplicate
                sig = RiskSignal(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    signal_code="SEMANTIC_SIMILARITY",
                    category="DUPLICATE",
                    severity=SeverityLevel.MEDIUM.value,
                    score=Decimal("88.00"),
                    confidence=Decimal("85.00"),
                    description="Line items and amount are 94% similar to INV-2026-0006 submitted 3 days prior.",
                    evidence={"reference_invoice": "INV-2026-0006", "cosine_similarity": 0.94},
                    status=RiskSignalStatus.ACTIVE.value,
                )
                session.add(sig)
            elif i == 11: # Scenario K: Bank Details Mismatch
                exc = DBException(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    control_result_id=bank_res.id,
                    exception_code="BANK_DETAILS_MISMATCH",
                    title="Remittance account mismatch — mandatory payment hold",
                    description="Invoice specifies account ending in 9999; verified vendor master account ends in 1234.",
                    severity=SeverityLevel.CRITICAL.value,
                    status=ExceptionStatus.OPEN.value,
                    assigned_to=fin_mgr.id,
                )
                sig = RiskSignal(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    control_result_id=bank_res.id,
                    signal_code="BANK_ACCOUNT_MISMATCH",
                    category="SECURITY",
                    severity=SeverityLevel.CRITICAL.value,
                    score=Decimal("95.00"),
                    confidence=Decimal("99.00"),
                    description="Unregistered bank account listed on invoice remittance header",
                    evidence={"expected_account": "XXXX-1234", "submitted_account": "XXXX-9999"},
                    status=RiskSignalStatus.ACTIVE.value,
                )
                session.add_all([exc, sig])
            elif i == 12: # Scenario L: Threshold Proximity
                sig = RiskSignal(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    signal_code="THRESHOLD_PROXIMITY",
                    category="APPROVAL",
                    severity=SeverityLevel.LOW.value,
                    score=Decimal("45.00"),
                    confidence=Decimal("90.00"),
                    description="Invoice total ₹49,990 is within 1% of the ₹50,000 Tier 1 approval ceiling.",
                    evidence={"invoice_amount": "49990.00", "threshold": "50000.00"},
                    status=RiskSignalStatus.ACTIVE.value,
                )
                session.add(sig)

            # ---------------------------------------------------------
            # Approvals for Approved / Payable / Paid / Rejected Invoices
            # ---------------------------------------------------------
            if status in [InvoiceStatus.APPROVED.value, InvoiceStatus.PAYABLE_CREATED.value, InvoiceStatus.PAID.value]:
                pol = approval_policies[1] # Tier 2
                appr = Approval(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    approval_policy_id=pol.id,
                    sequence_order=1,
                    approver_user_id=fin_mgr.id,
                    status=ApprovalStatus.APPROVED.value,
                    decision=ApprovalDecision.APPROVE.value,
                    comments="Verified 3-way match evidence and valid vendor tax credentials. Approved for payment.",
                    decided_at=datetime.combine(inv_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
                )
                session.add(appr)
            elif status == InvoiceStatus.REJECTED.value: # Scenario O
                pol = approval_policies[1]
                appr = Approval(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    approval_policy_id=pol.id,
                    sequence_order=1,
                    approver_user_id=fin_mgr.id,
                    status=ApprovalStatus.REJECTED.value,
                    decision=ApprovalDecision.REJECT.value,
                    comments="Invoice rejected: Unapproved procurement variance and vendor terms breach.",
                    decided_at=datetime.combine(inv_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
                )
                session.add(appr)

            # ---------------------------------------------------------
            # Payable Ledger & Payments
            # ---------------------------------------------------------
            if status in [InvoiceStatus.PAYABLE_CREATED.value, InvoiceStatus.PAID.value]:
                pay_status = PayableStatus.PAID.value if status == InvoiceStatus.PAID.value else (PayableStatus.PARTIALLY_PAID.value if i == 14 else PayableStatus.OPEN.value)
                pay_num = f"PAY-2026-{i:04d}"

                pay = PayableLedger(
                    tenant_id=tenant_id,
                    invoice_id=inv.id,
                    invoice_revision_id=target_rev.id,
                    vendor_id=vendor.id,
                    payable_number=pay_num,
                    approved_amount=target_rev.grand_total,
                    currency="INR",
                    due_date=due_date,
                    status=pay_status,
                    approved_at=datetime.combine(inv_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
                )
                session.add(pay)
                session.flush()

                # Add payments if paid or partially paid
                if status == InvoiceStatus.PAID.value:
                    pmt = Payment(
                        tenant_id=tenant_id,
                        payable_id=pay.id,
                        payment_reference=f"NEFT-{inv_num}-FULL",
                        payment_date=due_date - timedelta(days=2),
                        amount=target_rev.grand_total,
                        currency="INR",
                        status=PaymentStatus.COMPLETED.value,
                        payment_method="NEFT",
                    )
                    session.add(pmt)
                elif i == 14: # Scenario N: Partially paid
                    half_amt = (target_rev.grand_total / Decimal("2")).quantize(Decimal("0.01"))
                    pmt = Payment(
                        tenant_id=tenant_id,
                        payable_id=pay.id,
                        payment_reference=f"NEFT-{inv_num}-PARTIAL",
                        payment_date=due_date - timedelta(days=5),
                        amount=half_amt,
                        currency="INR",
                        status=PaymentStatus.COMPLETED.value,
                        payment_method="NEFT",
                    )
                    session.add(pmt)

            # ---------------------------------------------------------
            # Audit Logs
            # ---------------------------------------------------------
            audit_events = [
                ("INVOICE_UPLOADED", ap_clerk.id, None, {"status": "RECEIVED"}),
                ("CONTROL_RUN_COMPLETED", None, {"status": "VALIDATING"}, {"status": inv.status}),
            ]
            if status in [InvoiceStatus.APPROVED.value, InvoiceStatus.PAYABLE_CREATED.value, InvoiceStatus.PAID.value]:
                audit_events.append(("INVOICE_APPROVED", fin_mgr.id, {"status": "AWAITING_APPROVAL"}, {"status": "APPROVED"}))
            if status in [InvoiceStatus.PAYABLE_CREATED.value, InvoiceStatus.PAID.value]:
                audit_events.append(("PAYABLE_CREATED", fin_mgr.id, {"status": "APPROVED"}, {"status": "PAYABLE_CREATED"}))
            if status == InvoiceStatus.REJECTED.value:
                audit_events.append(("INVOICE_REJECTED", fin_mgr.id, {"status": "AWAITING_APPROVAL"}, {"status": "REJECTED"}))

            for act, actor_id, prev_s, new_s in audit_events:
                a_log = AuditLog(
                    tenant_id=tenant_id,
                    actor_user_id=actor_id,
                    action=act,
                    entity_type="INVOICE",
                    entity_id=inv.id,
                    request_id=f"REQ-{uuid.uuid4().hex[:8]}",
                    correlation_id=f"CORR-{inv_num}",
                    previous_state=prev_s,
                    new_state=new_s,
                    metadata_json={"invoice_number": inv_num, "source": "seed_pipeline"},
                    ip_address="192.168.1.100",
                    user_agent="AP-Control-Engine/1.0",
                )
                session.add(a_log)

            session.flush()

        session.commit()
        print("Database seeding completed successfully!")
        print("Summary of seeded entities:")
        print(f"  - Tenant: 1")
        print(f"  - Roles: {len(roles_map)}")
        print(f"  - Users: {len(users_map)}")
        print(f"  - Vendors: {len(vendors)}")
        print(f"  - Purchase Orders: {len(purchase_orders)}")
        print(f"  - Goods Receipts: {len(goods_receipts)}")
        print(f"  - Invoices: {len(invoices)}")
        print(f"  - Approval Policies: {len(approval_policies)}")

    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
