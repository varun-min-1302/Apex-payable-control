import React, { useState, useEffect } from 'react';
import { CreditCard, CheckCircle, Clock, X, Search, DollarSign, ArrowUpRight, ShieldCheck } from 'lucide-react';
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
      return { label: 'Payment due', className: 'bg-blue-50 text-blue-700 border-blue-200' };
    case 'PARTIALLY_PAID':
      return { label: 'Partially paid', className: 'bg-amber-50 text-amber-700 border-amber-200' };
    case 'PAID':
      return { label: 'Paid', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    case 'ON_HOLD':
      return { label: 'On hold', className: 'bg-gray-100 text-gray-700 border-gray-200' };
    case 'CANCELLED':
      return { label: 'Cancelled', className: 'bg-gray-100 text-gray-500 border-gray-200' };
    default:
      return { label: status, className: 'bg-gray-100 text-gray-600 border-gray-200' };
  }
}

export const PaymentsView: React.FC<PaymentsViewProps> = ({ onRefreshParent, onSelectInvoice }) => {
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
      const paidMsg = `Payment of ${formatCurrency(disburseAmount)} successfully recorded for ${selectedPayable.invoice_number}.`;
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
  const totalLiability = payables.reduce((sum, p) => sum + parseFloat(String(p.approved_amount || 0)), 0);
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Payments &amp; Payable Ledger</h1>
          <p className="text-sm text-gray-500 mt-1">
            Approved liabilities ready for disbursement, payment execution, and settlement history.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5" /> Immutable Ledger
          </span>
        </div>
      </div>

      {/* Success Notification */}
      {successNotice && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-emerald-800 text-sm shadow-sm animate-fade-in">
          <div className="flex items-center gap-2.5">
            <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span className="font-medium">{successNotice}</span>
          </div>
          <button onClick={() => setSuccessNotice(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-card">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Total Payable Liability</div>
          <div className="text-2xl font-bold text-gray-900 mt-1.5 font-mono">{formatCurrency(totalLiability)}</div>
          <div className="text-[11px] text-gray-400 mt-1">Total approved commitment</div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-card">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Paid to Date</div>
          <div className="text-2xl font-bold text-emerald-700 mt-1.5 font-mono">{formatCurrency(totalPaid)}</div>
          <div className="text-[11px] text-emerald-600 mt-1">Settled disbursements</div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-card">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Outstanding</div>
          <div className="text-2xl font-bold text-blue-700 mt-1.5 font-mono">{formatCurrency(totalOutstanding)}</div>
          <div className="text-[11px] text-blue-600 mt-1">Balance pending release</div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-card">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Partially Paid</div>
          <div className="text-2xl font-bold text-amber-700 mt-1.5 font-mono">{partiallyPaidCount}</div>
          <div className="text-[11px] text-amber-600 mt-1">Installments in progress</div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-card overflow-hidden">
        {/* Table Filter & Search Header */}
        <div className="p-4 border-b border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-1 overflow-x-auto">
            {(['ALL', 'OPEN', 'PARTIALLY_PAID', 'PAID'] as const).map(s => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors whitespace-nowrap ${
                  statusFilter === s ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                {s === 'ALL' ? 'All Payables' : s === 'OPEN' ? 'Payment Due' : s === 'PARTIALLY_PAID' ? 'Partial' : 'Paid'}
              </button>
            ))}
          </div>

          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search vendor or invoice..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
            />
          </div>
        </div>

        {/* Table Content */}
        {loading ? (
          <div className="p-8 space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : filteredPayables.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <CreditCard className="w-6 h-6 text-gray-400" />
            </div>
            <h3 className="text-base font-semibold text-gray-800">No payments recorded yet</h3>
            <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
              Invoices will automatically enter this ledger once approved by authorized finance managers.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50/75 border-b border-gray-100 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Invoice #</th>
                  <th className="py-3 px-4">Vendor</th>
                  <th className="py-3 px-4 text-right">Payable Amount</th>
                  <th className="py-3 px-4 text-right">Paid Amount</th>
                  <th className="py-3 px-4 text-right">Outstanding</th>
                  <th className="py-3 px-4">Due Date</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-xs">
                {filteredPayables.map(p => {
                  const badge = getPayableStatusBadge(p.status);
                  const approved = parseFloat(String(p.approved_amount || 0));
                  const remaining = parseFloat(String(p.remaining_balance || 0));
                  const paid = Math.max(0, approved - remaining);
                  const isSettled = p.status === 'PAID';

                  return (
                    <tr key={p.id} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-3.5 px-4">
                        <button
                          type="button"
                          onClick={() => onSelectInvoice && p.invoice_id && onSelectInvoice(p.invoice_id)}
                          className="font-mono font-bold text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {p.invoice_number}
                        </button>
                        <div className="text-[10px] text-gray-400 font-mono mt-0.5">{p.payable_number}</div>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-gray-900 max-w-xs truncate">
                        {p.vendor_name || 'Verified Vendor'}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-gray-900">
                        {formatCurrency(approved)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-emerald-700 font-medium">
                        {formatCurrency(paid)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-gray-900">
                        {formatCurrency(remaining)}
                      </td>
                      <td className="py-3.5 px-4 text-gray-600">
                        {formatDate(p.due_date)}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${badge.className}`}
                        >
                          {badge.label}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {!isSettled ? (
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedPayable(p);
                              setDisburseAmount(remaining);
                              setPaymentRef(`PAY-${Date.now()}`);
                              setPaymentMethod('NEFT');
                            }}
                            className="px-3 py-1.5 bg-gray-900 hover:bg-gray-800 text-white text-xs font-semibold rounded-xl transition-colors whitespace-nowrap shadow-xs"
                          >
                            Record Payment
                          </button>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold text-xs">
                            <CheckCircle className="w-3.5 h-3.5" /> Settled
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Record Payment Disbursement Modal */}
      {selectedPayable && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-modal border border-gray-200">
            <div className="flex items-center justify-between mb-4 border-b border-gray-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-gray-900">Record Payment Disbursement</h3>
                <p className="text-xs text-gray-500 mt-0.5">Execute settlement against approved liability</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedPayable(null)}
                className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-gray-50 rounded-xl p-4 mb-4 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Payable Number:</span>
                <span className="font-mono font-semibold text-gray-800">{selectedPayable.payable_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Vendor:</span>
                <span className="font-semibold text-gray-900">{selectedPayable.vendor_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Invoice:</span>
                <span className="font-mono font-semibold text-gray-800">{selectedPayable.invoice_number}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-gray-200 text-sm">
                <span className="text-gray-600 font-medium">Outstanding Balance:</span>
                <span className="font-mono font-bold text-gray-900">
                  {formatCurrency(selectedPayable.remaining_balance)}
                </span>
              </div>
            </div>

            <form onSubmit={handleDisburse} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-gray-700 font-semibold mb-1">
                  Disbursement Amount (₹)
                </label>
                <input
                  type="number"
                  value={disburseAmount}
                  onChange={e => setDisburseAmount(Number(e.target.value))}
                  required
                  min={0.01}
                  max={Number(selectedPayable.remaining_balance)}
                  step={0.01}
                  className="w-full border border-gray-200 rounded-xl px-3.5 py-2 font-mono text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-[10px] text-gray-400 mt-1 block">
                  Defaults to full outstanding balance. You can enter a partial installment amount.
                </span>
              </div>

              <div>
                <label className="block text-gray-700 font-semibold mb-1">
                  Payment Reference / UTR
                </label>
                <input
                  type="text"
                  value={paymentRef}
                  onChange={e => setPaymentRef(e.target.value)}
                  required
                  placeholder="e.g. UTR-2026-991240"
                  className="w-full border border-gray-200 rounded-xl px-3.5 py-2 font-mono text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-gray-700 font-semibold mb-1">
                  Payment Method
                </label>
                <select
                  value={paymentMethod}
                  onChange={e => setPaymentMethod(e.target.value)}
                  className="w-full border border-gray-200 rounded-xl px-3.5 py-2 text-xs font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  {['NEFT', 'RTGS', 'IMPS', 'CHEQUE', 'UPI', 'WIRE'].map(m => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>

              <div className="bg-blue-50 border border-blue-100 rounded-xl p-3 text-[11px] text-blue-800">
                Disbursement is recorded to the payments journal with an immutable audit event. The remaining payable
                balance will adjust automatically.
              </div>

              <div className="flex gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedPayable(null)}
                  className="flex-1 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={disbursing}
                  className="flex-1 py-2.5 bg-gray-900 hover:bg-gray-800 disabled:opacity-50 text-white font-bold rounded-xl text-xs transition-colors flex items-center justify-center gap-1.5 shadow-xs"
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
