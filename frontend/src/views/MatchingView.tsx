import React, { useState, useEffect } from 'react';
import {
  Scale,
  Search,
} from 'lucide-react';
import { api } from '../api/client';
import { InvoiceSummary } from '../types';
import { formatCurrency, formatDate } from '../utils/format';

interface MatchingViewProps {
  onSelectInvoice: (invoiceId: string) => void;
}

export const MatchingView: React.FC<MatchingViewProps> = ({ onSelectInvoice }) => {
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    api.listInvoices()
      .then(setInvoices)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = invoices.filter(inv => 
    inv.invoice_number.toLowerCase().includes(search.toLowerCase()) ||
    (inv.vendor_name && inv.vendor_name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">3-Way Match & Deterministic Control Center</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Automated verification comparing Purchase Order contract terms, Warehouse Goods Receipts, and Invoiced line items.
          </p>
        </div>

        <div className="relative shrink-0">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search invoice or vendor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 bg-surface border border-border rounded-xl text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary w-64"
          />
        </div>
      </div>

      {/* Rules Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card p-5 rounded-2xl border border-border shadow-card space-y-2">
          <div className="flex items-center space-x-2 text-primary font-bold text-xs uppercase font-mono">
            <Scale className="w-4 h-4" />
            <span>Quantity Match Rule</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Invoiced quantity cannot exceed accepted warehouse quantity: <code className="text-amber-600 dark:text-amber-400 font-mono">Qty_inv ≤ Qty_rec</code>. Rejects over-invoicing and enforces zero unauthorized tolerances.
          </p>
        </div>

        <div className="bg-card p-5 rounded-2xl border border-border shadow-card space-y-2">
          <div className="flex items-center space-x-2 text-primary font-bold text-xs uppercase font-mono">
            <Scale className="w-4 h-4" />
            <span>Price Match Rule</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Invoiced unit price must match approved PO line price: <code className="text-amber-600 dark:text-amber-400 font-mono">Price_inv ≤ Price_po</code>. Flags price inflation exceptions automatically.
          </p>
        </div>

        <div className="bg-card p-5 rounded-2xl border border-border shadow-card space-y-2">
          <div className="flex items-center space-x-2 text-primary font-bold text-xs uppercase font-mono">
            <Scale className="w-4 h-4" />
            <span>Bank & Duplicate Rules</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            SHA-256 binary hash collision matching and destination bank fingerprinting prevents duplicate invoice fraud and rogue account transfers.
          </p>
        </div>
      </div>

      {/* Invoice Inspection Directory */}
      <div className="bg-card rounded-2xl border border-border shadow-card overflow-hidden">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-sm font-bold text-foreground">Select Invoice to Inspect 3-Way Match & 18 Rules</h2>
          <span className="text-xs text-muted-foreground font-mono">{filtered.length} Invoices Available</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-muted-foreground text-xs">Loading invoices...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-surface-muted border-b border-border text-[11px] font-semibold uppercase text-muted-foreground tracking-wider">
                  <th className="py-3 px-4">Invoice #</th>
                  <th className="py-3 px-4">Vendor</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Inspection Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((inv) => (
                  <tr key={inv.id} className="hover:bg-muted/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-primary">{inv.invoice_number}</td>
                    <td className="py-3 px-4 font-semibold text-foreground">{inv.vendor_name}</td>
                    <td className="py-3 px-4 font-mono text-muted-foreground">{inv.invoice_date ? formatDate(inv.invoice_date) : '—'}</td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-foreground">{formatCurrency(inv.grand_total)}</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-muted text-muted-foreground border border-border">
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onSelectInvoice(inv.id)}
                        className="px-3.5 py-1.5 bg-primary hover:opacity-90 text-primary-foreground font-semibold text-xs rounded-xl shadow-xs transition-colors"
                      >
                        Inspect Rules
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
};
