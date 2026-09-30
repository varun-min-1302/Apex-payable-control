import React, { useState, useEffect } from 'react';
import {
  Building2,
  FileSpreadsheet,
  PackageCheck,
} from 'lucide-react';
import { api } from '../api/client';
import { Vendor, PurchaseOrder, GoodsReceipt } from '../types';
import { formatCurrency, formatDate } from '../utils/format';

export const ProcurementView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'vendors' | 'pos' | 'receipts'>('vendors');
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [receipts, setReceipts] = useState<GoodsReceipt[]>([]);
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

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Procurement Master Records</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Baseline master data including verified vendor identities, approved purchase orders, and warehouse physical goods receipts.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 bg-surface border border-border p-1 rounded-xl shadow-card self-start">
          <button
            onClick={() => setActiveTab('vendors')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1.5 ${
              activeTab === 'vendors'
                ? 'bg-primary text-primary-foreground font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>Vendors ({vendors.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('pos')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1.5 ${
              activeTab === 'pos'
                ? 'bg-primary text-primary-foreground font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Purchase Orders ({pos.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('receipts')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1.5 ${
              activeTab === 'receipts'
                ? 'bg-primary text-primary-foreground font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            }`}
          >
            <PackageCheck className="w-4 h-4" />
            <span>Goods Receipts ({receipts.length})</span>
          </button>
        </div>
      </div>

      {/* Body Content */}
      <div className="bg-card rounded-2xl border border-border shadow-card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-muted-foreground text-sm">Loading procurement records...</div>
        ) : (
          <div className="overflow-x-auto">
            
            {/* VENDORS TABLE */}
            {activeTab === 'vendors' && (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-surface-muted border-b border-border text-[11px] font-semibold uppercase text-muted-foreground tracking-wider">
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Legal Name</th>
                    <th className="py-3 px-4">Tax Identifier (GSTIN)</th>
                    <th className="py-3 px-4">Terms</th>
                    <th className="py-3 px-4">Bank Destination</th>
                    <th className="py-3 px-4">Masked Account</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {vendors.map((v) => (
                    <tr key={v.id} className="hover:bg-muted/50 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-primary whitespace-nowrap">{v.vendor_code}</td>
                      <td className="py-3.5 px-4 font-semibold text-foreground">{v.legal_name}</td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">{v.tax_identifier}</td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">Net {v.payment_terms_days} Days</td>
                      <td className="py-3.5 px-4 text-foreground">{v.bank_name || 'HDFC Bank'}</td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">•••• •••• •••• {v.bank_account_last4 || '0000'}</td>
                      <td className="py-3.5 px-4 text-center">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide ${
                          v.status === 'ACTIVE'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-400 dark:border-emerald-800'
                            : 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-400 dark:border-rose-800'
                        }`}>
                          {v.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* PURCHASE ORDERS TABLE */}
            {activeTab === 'pos' && (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-surface-muted border-b border-border text-[11px] font-semibold uppercase text-muted-foreground tracking-wider">
                    <th className="py-3 px-4">PO Number</th>
                    <th className="py-3 px-4">Order Date</th>
                    <th className="py-3 px-4">Items Count</th>
                    <th className="py-3 px-4 text-right">Subtotal</th>
                    <th className="py-3 px-4 text-right">Tax Total</th>
                    <th className="py-3 px-4 text-right">Grand Total</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {pos.map((p) => (
                    <tr key={p.id} className="hover:bg-muted/50 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-primary whitespace-nowrap">{p.po_number}</td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">{p.po_date ? formatDate(p.po_date) : '—'}</td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">{p.items?.length || 1} line(s)</td>
                      <td className="py-3.5 px-4 text-right font-mono text-muted-foreground">{formatCurrency(p.subtotal)}</td>
                      <td className="py-3.5 px-4 text-right font-mono text-muted-foreground">{formatCurrency(p.tax_total)}</td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-foreground">{formatCurrency(p.grand_total)}</td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-400 dark:border-emerald-800">
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* GOODS RECEIPTS TABLE */}
            {activeTab === 'receipts' && (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-surface-muted border-b border-border text-[11px] font-semibold uppercase text-muted-foreground tracking-wider">
                    <th className="py-3 px-4">Receipt Number</th>
                    <th className="py-3 px-4">Received Date</th>
                    <th className="py-3 px-4">Items Received</th>
                    <th className="py-3 px-4">Notes</th>
                    <th className="py-3 px-4 text-center">Receipt Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {receipts.map((r) => (
                    <tr key={r.id} className="hover:bg-muted/50 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-primary whitespace-nowrap">{r.receipt_number}</td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">{r.received_date ? formatDate(r.received_date) : '—'}</td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">{r.items?.length || 1} item line(s)</td>
                      <td className="py-3.5 px-4 text-muted-foreground">{r.notes || 'Warehouse inspection verified'}</td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-400 dark:border-emerald-800">
                          {r.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

          </div>
        )}
      </div>

    </div>
  );
};
