import React, { useState, useEffect } from 'react';
import {
  Building2,
  FileSpreadsheet,
  PackageCheck,
  CheckCircle,
  ShieldCheck,
  Search
} from 'lucide-react';
import { api } from '../api/client';
import type { Vendor, PurchaseOrder, GoodsReceipt } from '../types';
import { formatCurrency, formatDate } from '../utils/format';

export const ProcurementView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'vendors' | 'pos' | 'receipts'>('vendors');
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [receipts, setReceipts] = useState<GoodsReceipt[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.listVendors(),
      api.listPurchaseOrders(),
      api.listGoodsReceipts(),
    ])
      .then(([v, p, r]) => {
        setVendors(v);
        setPos(p);
        setReceipts(r);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const vendorMap = new Map<string, string>(
    vendors.map(v => [v.id, v.legal_name || v.display_name || v.vendor_code])
  );
  const poMap = new Map<string, PurchaseOrder>(
    pos.map(p => [p.id, p])
  );

  const filteredVendors = vendors.filter(v =>
    (v.legal_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (v.display_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (v.vendor_code || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (v.tax_identifier || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredPos = pos.filter(p => {
    const vName = vendorMap.get(p.vendor_id) || (p as any).vendor_name || '';
    return (
      (p.po_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      vName.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const filteredReceipts = receipts.filter(r => {
    const po = poMap.get(r.purchase_order_id);
    const poNum = po?.po_number || (r as any).po_number || '';
    const vName = (po ? vendorMap.get(po.vendor_id) : null) || (r as any).vendor_name || '';
    return (
      (r.receipt_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      vName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      poNum.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            Vendors &amp; Orders
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Verified vendor identities, purchase commitments, and physical goods receipts.
          </p>
        </div>

        {/* Tab Switcher Pills */}
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-full border border-border/60 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('vendors')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'vendors'
                ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Vendors ({vendors.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('pos')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'pos'
                ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Purchase Orders ({pos.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('receipts')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'receipts'
                ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <PackageCheck className="w-3.5 h-3.5" />
            <span>Goods Receipts ({receipts.length})</span>
          </button>
        </div>
      </div>

      {/* 2. Search & Filter Bar */}
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder={`Search ${activeTab === 'vendors' ? 'vendors by name or tax ID...' : activeTab === 'pos' ? 'orders by PO # or vendor...' : 'receipts by #...'}`}
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-8 pr-3 py-1.5 bg-muted/50 border border-border rounded-xl text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary w-full"
          />
        </div>

        <div className="text-xs text-muted-foreground">
          Showing {activeTab === 'vendors' ? filteredVendors.length : activeTab === 'pos' ? filteredPos.length : filteredReceipts.length} records
        </div>
      </div>

      {/* 3. Table / Modular Card Presentation */}
      <div className="bg-card text-card-foreground rounded-[22px] border border-border/80 shadow-card overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            
            {/* VENDORS TAB */}
            {activeTab === 'vendors' && (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-muted/30 border-b border-border/60 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Legal Vendor Name</th>
                    <th className="py-3 px-4">Tax Identifier (GSTIN)</th>
                    <th className="py-3 px-4">Verification Proofs</th>
                    <th className="py-3 px-4">Bank Remittance</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredVendors.map(vendor => (
                    <tr key={vendor.id} className="hover:bg-muted/40 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-primary">
                        {vendor.vendor_code}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-foreground">
                        {vendor.legal_name || vendor.display_name || vendor.vendor_code}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">
                        {vendor.tax_identifier || '—'}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            <CheckCircle className="w-3 h-3" /> Vendor Verified
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            <CheckCircle className="w-3 h-3" /> Tax ID Match
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                            <ShieldCheck className="w-3 h-3" /> Bank Verified
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-muted-foreground">
                        {vendor.bank_account_last4 ? (
                          <span>•••• {vendor.bank_account_last4} ({vendor.ifsc || vendor.bank_name || 'Bank'})</span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                          {vendor.status || 'ACTIVE'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* PURCHASE ORDERS TAB */}
            {activeTab === 'pos' && (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-muted/30 border-b border-border/60 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    <th className="py-3 px-4">PO Number</th>
                    <th className="py-3 px-4">Vendor</th>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4 text-right">Committed Value</th>
                    <th className="py-3 px-4 text-center">Line Items</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredPos.map(order => {
                    const vendorName = vendorMap.get(order.vendor_id) || (order as any).vendor_name || 'Vendor';
                    return (
                      <tr key={order.id} className="hover:bg-muted/40 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-bold text-primary">
                          {order.po_number}
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-foreground">
                          {vendorName}
                        </td>
                        <td className="py-3.5 px-4 text-muted-foreground">
                          {formatDate(order.po_date)}
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-bold text-foreground">
                          {formatCurrency(order.grand_total)}
                        </td>
                        <td className="py-3.5 px-4 text-center text-muted-foreground font-mono">
                          {order.items ? order.items.length : 1} items
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            {order.status || 'APPROVED'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}

            {/* GOODS RECEIPTS TAB */}
            {activeTab === 'receipts' && (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-muted/30 border-b border-border/60 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    <th className="py-3 px-4">Receipt #</th>
                    <th className="py-3 px-4">PO Reference</th>
                    <th className="py-3 px-4">Vendor</th>
                    <th className="py-3 px-4">Received Date</th>
                    <th className="py-3 px-4 text-center">Received Units</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredReceipts.map(rcpt => {
                    const po = poMap.get(rcpt.purchase_order_id);
                    const poNum = po?.po_number || (rcpt as any).po_number || '—';
                    const vendorName = (po ? vendorMap.get(po.vendor_id) : null) || (rcpt as any).vendor_name || 'Vendor';
                    const totalUnits = rcpt.items
                      ? rcpt.items.reduce((s, i) => s + (Number(i.received_quantity) || 0), 0)
                      : null;
                    return (
                      <tr key={rcpt.id} className="hover:bg-muted/40 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-bold text-primary">
                          {rcpt.receipt_number}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-muted-foreground">
                          {poNum}
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-foreground">
                          {vendorName}
                        </td>
                        <td className="py-3.5 px-4 text-muted-foreground">
                          {formatDate(rcpt.received_date)}
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono font-semibold text-foreground">
                          {totalUnits !== null ? `${totalUnits} units` : '—'}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                            {rcpt.status || 'VERIFIED'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}

          </div>
        )}
      </div>

    </div>
  );
};
