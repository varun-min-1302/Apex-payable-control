import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  CheckCircle,
  Clock,
  X,
  Search,
  DollarSign,
  ShieldCheck,
  Building,
  ArrowRight,
  TrendingUp,
  Percent
} from 'lucide-react';
import { api } from '../api/client';
import type { PayableLedger } from '../types';
import { formatCurrency, formatDate } from '../utils/format';

interface PaymentsViewProps {
  onRefreshParent?: () => void;
  onSelectInvoice?: (invoiceId: string) => void;
}

function getPayableStatusBadge(status: string): { label: string; className: string } {
  switch (status) {
    case 'OPEN':
      return { label: 'Payment Due', className: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20' };
    case 'PARTIALLY_PAID':
      return { label: 'Partially Paid', className: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20' };
    case 'PAID':
      return { label: 'Paid in Full', className: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' };
    case 'ON_HOLD':
      return { label: 'On Hold', className: 'bg-muted text-muted-foreground border border-border' };
    case 'CANCELLED':
      return { label: 'Cancelled', className: 'bg-muted text-muted-foreground border border-border' };
    default:
      return { label: status, className: 'bg-muted text-muted-foreground border border-border' };
  }
}

export const PaymentsView: React.FC<PaymentsViewProps> = ({
  onRefreshParent,
  onSelectInvoice
}) => {
  const [payables, setPayables] = useState<PayableLedger[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'OPEN' | 'PARTIALLY_PAID' | 'PAID'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPayable, setSelectedPayable] = useState<PayableLedger | null>(null);
  const [disburseAmount, setDisburseAmount] = useState<number>(0);
  const [paymentRef, setPaymentRef] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<string>('NEFT');
  const [disbursing, setDisbursing] = useState(false);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      const data = await api.listPayables({ status: statusFilter === 'ALL' ? undefined : statusFilter });
      setPayables(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [statusFilter]);

  const handleDisburse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPayable || disburseAmount <= 0) {
      alert('Amount must be greater than zero.');
      return;
    }
    try {
      setDisbursing(true);
      await api.recordDisbursement(selectedPayable.id, disburseAmount, paymentRef, paymentMethod);
      const paidMsg = `Settlement of ${formatCurrency(disburseAmount)} successfully recorded for ${selectedPayable.invoice_number}.`;
      setSelectedPayable(null);
      setSuccessNotice(paidMsg);
      setTimeout(() => setSuccessNotice(null), 5000);
      await load();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(err.message || 'Payment recording failed');
    } finally {
      setDisbursing(false);
    }
  };

  // Filter by search query
  const filteredPayables = payables.filter(p => {
    const q = searchQuery.toLowerCase();
    return (
      (p.invoice_number || '').toLowerCase().includes(q) ||
      (p.vendor_name || '').toLowerCase().includes(q) ||
      (p.payable_number || '').toLowerCase().includes(q)
    );
  });

  // KPI Calculations
  const totalApproved = payables.reduce((sum, p) => sum + parseFloat(String(p.approved_amount || 0)), 0);
  const totalOutstanding = payables
    .filter(p => p.status === 'OPEN' || p.status === 'PARTIALLY_PAID')
    .reduce((sum, p) => sum + parseFloat(String(p.remaining_balance || 0)), 0);
  const totalPaid = payables.reduce((sum, p) => {
    const approved = parseFloat(String(p.approved_amount || 0));
    const remaining = parseFloat(String(p.remaining_balance || 0));
    return sum + Math.max(0, approved - remaining);
  }, 0);
  const partiallyPaidCount = payables.filter(p => p.status === 'PARTIALLY_PAID').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            Payments
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Track approved payable obligations and payment status.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-3.5 h-3.5" /> Immutable Settlement Ledger
          </span>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successNotice && (
        <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-between text-emerald-700 dark:text-emerald-300 text-xs shadow-xs animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            <span className="font-medium">{successNotice}</span>
          </div>
          <button onClick={() => setSuccessNotice(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 2. 4 KPI Cards as specified in Section 14 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Approved for Payment */}
        <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-5 shadow-card">
          <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Approved for Payment
          </div>
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-1">
            {formatCurrency(totalApproved)}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            Total authorized obligations
          </div>
        </div>

        {/* Outstanding */}
        <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-5 shadow-card">
          <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Outstanding
          </div>
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-blue-600 dark:text-blue-400 mt-1">
            {formatCurrency(totalOutstanding)}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            Awaiting disbursement
          </div>
        </div>

        {/* Paid */}
        <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-5 shadow-card">
          <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Paid
          </div>
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400 mt-1">
            {formatCurrency(totalPaid)}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            Settled disbursements
          </div>
        </div>

        {/* Partially Paid */}
        <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-5 shadow-card">
          <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Partially Paid
          </div>
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-amber-600 dark:text-amber-400 mt-1 flex items-baseline gap-1.5">
            <span>{partiallyPaidCount}</span>
            <span className="text-xs font-medium text-muted-foreground">Invoices</span>
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            Active milestone schedules
          </div>
        </div>

      </div>

      {/* 3. Search and Status Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-full border border-border/60 self-start sm:self-auto">
          {(['ALL', 'OPEN', 'PARTIALLY_PAID', 'PAID'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                statusFilter === s
                  ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {s === 'ALL' ? 'All Payables' : s === 'OPEN' ? 'Due' : s === 'PARTIALLY_PAID' ? 'Partial' : 'Paid'}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search payable # or vendor..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-8 pr-3 py-1.5 bg-muted/50 border border-border rounded-xl text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary w-60"
          />
        </div>
      </div>

      {/* 4. Payables List with Visual Progress Bars */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-44 bg-muted rounded-[22px] animate-pulse" />
          ))}
        </div>
      ) : filteredPayables.length === 0 ? (
        <div className="bg-card text-card-foreground rounded-[22px] border border-border/80 shadow-card p-12 text-center space-y-3">
          <div className="w-14 h-14 bg-muted text-muted-foreground rounded-2xl flex items-center justify-center mx-auto">
            <CreditCard className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-foreground">No payables found</h3>
          <p className="text-muted-foreground text-xs max-w-sm mx-auto">
            Approved invoices will appear in this ledger once they receive managerial authorization.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPayables.map(p => {
            const approvedAmt = parseFloat(String(p.approved_amount || 0));
            const remainingAmt = parseFloat(String(p.remaining_balance || 0));
            const paidAmt = Math.max(0, approvedAmt - remainingAmt);
            const progressPercent = approvedAmt > 0 ? Math.min(100, Math.round((paidAmt / approvedAmt) * 100)) : 0;
            const badge = getPayableStatusBadge(p.status);

            return (
              <div
                key={p.id}
                className="bg-card text-card-foreground rounded-[22px] border border-border/80 shadow-card p-6 space-y-4 hover:border-primary/40 transition-all"
              >
                {/* Header: Payable ID, Invoice #, Vendor, Status Badge */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-border/60 pb-3">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono font-bold text-sm text-foreground bg-muted/60 px-2 py-0.5 rounded-md">
                        {p.payable_number}
                      </span>
                      <span className="text-muted-foreground">·</span>
                      <span className="font-mono font-bold text-primary text-sm">
                        {p.invoice_number}
                      </span>
                      <span className="text-muted-foreground">·</span>
                      <span className="font-semibold text-foreground text-sm">
                        {p.vendor_name || 'Vendor'}
                      </span>
                    </div>

                    <div className="text-xs text-muted-foreground mt-1">
                      Due Date: <span className="text-foreground font-medium">{formatDate(p.due_date)}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${badge.className}`}>
                      {badge.label}
                    </span>
                  </div>
                </div>

                {/* Financial Summary & Visual Progress */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-muted/30 p-4 rounded-xl border border-border/60">
                  <div>
                    <div className="text-[10px] font-bold text-muted-foreground uppercase">Approved Total</div>
                    <div className="text-lg font-extrabold font-mono text-foreground mt-0.5">
                      {formatCurrency(approvedAmt)}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] font-bold text-muted-foreground uppercase">Settled to Date</div>
                    <div className="text-lg font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">
                      {formatCurrency(paidAmt)}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] font-bold text-muted-foreground uppercase">Outstanding Balance</div>
                    <div className="text-lg font-extrabold font-mono text-blue-600 dark:text-blue-400 mt-0.5">
                      {formatCurrency(remainingAmt)}
                    </div>
                  </div>
                </div>

                {/* Visual Progress Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[11px] font-medium text-muted-foreground">
                    <span>Payment Completion</span>
                    <span className="font-mono">{progressPercent}%</span>
                  </div>
                  <div className="w-full bg-muted/80 h-2 rounded-full overflow-hidden flex">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>

                {/* Footer: Action to record payment */}
                <div className="pt-2 flex items-center justify-between gap-3">
                  <div className="text-xs text-muted-foreground">
                    {p.payments && p.payments.length > 0
                      ? `${p.payments.length} disbursement${p.payments.length > 1 ? 's' : ''} recorded`
                      : 'No payments recorded yet'}
                  </div>

                  {(p.status === 'OPEN' || p.status === 'PARTIALLY_PAID') && (
                    <button
                      onClick={() => {
                        setSelectedPayable(p);
                        setDisburseAmount(parseFloat(String(p.remaining_balance)));
                        setPaymentRef(`TXN-${Date.now().toString().slice(-6)}`);
                        setPaymentMethod('NEFT');
                      }}
                      className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl text-xs transition-all shadow-xs flex items-center gap-1.5"
                    >
                      <CreditCard className="w-3.5 h-3.5" />
                      Record Payment
                    </button>
                  )}
                </div>

              </div>
            );
          })}
        </div>
      )}

      {/* Record Payment Modal */}
      {selectedPayable && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-popover text-popover-foreground rounded-[24px] max-w-md w-full p-6 shadow-modal border border-border space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="text-base font-bold text-foreground">Record Disbursement</h3>
              <button
                onClick={() => setSelectedPayable(null)}
                className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-muted/50 p-3.5 rounded-xl border border-border text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Payable Reference:</span>
                <span className="font-mono font-semibold text-foreground">{selectedPayable.payable_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Vendor:</span>
                <span className="font-semibold text-foreground">{selectedPayable.vendor_name}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-border">
                <span className="text-muted-foreground">Remaining Balance:</span>
                <span className="font-mono font-bold text-sm text-foreground">
                  {formatCurrency(selectedPayable.remaining_balance)}
                </span>
              </div>
            </div>

            <form onSubmit={handleDisburse} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase mb-1">
                  Disbursement Amount (₹) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={disburseAmount}
                  onChange={e => setDisburseAmount(Number(e.target.value))}
                  required
                  min={0.01}
                  step={0.01}
                  className="w-full bg-muted/40 border border-border rounded-xl px-3 py-2 text-xs font-mono font-bold text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase mb-1">
                  Payment Method
                </label>
                <div className="grid grid-cols-4 gap-1.5">
                  {['NEFT', 'RTGS', 'UPI', 'CHEQUE'].map(method => (
                    <button
                      key={method}
                      type="button"
                      onClick={() => setPaymentMethod(method)}
                      className={`py-1.5 rounded-xl text-xs font-semibold transition-all border ${
                        paymentMethod === method
                          ? 'bg-foreground text-background font-bold'
                          : 'bg-card text-muted-foreground border-border hover:bg-muted'
                      }`}
                    >
                      {method}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase mb-1">
                  Bank Reference / UTR Number
                </label>
                <input
                  type="text"
                  value={paymentRef}
                  onChange={e => setPaymentRef(e.target.value)}
                  placeholder="e.g. UTR-982341908234"
                  className="w-full bg-muted/40 border border-border rounded-xl px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="flex gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedPayable(null)}
                  className="flex-1 py-2 bg-card hover:bg-muted text-muted-foreground font-semibold rounded-xl text-xs border border-border transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={disbursing}
                  className="flex-1 py-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl text-xs transition-colors shadow-xs disabled:opacity-50"
                >
                  {disbursing ? 'Recording...' : 'Confirm Disbursement'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
