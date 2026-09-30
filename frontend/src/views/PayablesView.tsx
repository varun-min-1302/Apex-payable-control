import React, { useState, useEffect } from 'react';
import {
  Landmark,
  DollarSign,
  Calendar,
  CheckCircle2,
  Clock,
  ArrowRight,
  CreditCard,
  Building,
  Layers,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import { PayableLedger, Payment } from '../types';

interface PayablesViewProps {
  onRefreshParent?: () => void;
}

export const PayablesView: React.FC<PayablesViewProps> = ({ onRefreshParent }) => {
  const [payables, setPayables] = useState<PayableLedger[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'OPEN' | 'PARTIALLY_PAID' | 'PAID'>('ALL');

  // Disbursement Modal State
  const [selectedPayable, setSelectedPayable] = useState<PayableLedger | null>(null);
  const [disburseAmount, setDisburseAmount] = useState<number>(0);
  const [paymentRef, setPaymentRef] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<string>('NEFT');
  const [disbursing, setDisbursing] = useState<boolean>(false);
  const [viewHistoryPayable, setViewHistoryPayable] = useState<PayableLedger | null>(null);

  const loadPayables = async () => {
    try {
      setLoading(true);
      const data = await api.listPayables({
        status: statusFilter === 'ALL' ? undefined : statusFilter,
      });
      setPayables(data);
    } catch (err) {
      console.error('Failed to load payables:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayables();
  }, [statusFilter]);

  const handleDisburseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPayable || disburseAmount <= 0) {
      alert('Disbursement amount must be greater than zero.');
      return;
    }

    try {
      setDisbursing(true);
      await api.recordDisbursement(
        selectedPayable.id,
        disburseAmount,
        paymentRef,
        paymentMethod
      );
      setSelectedPayable(null);
      await loadPayables();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(`Disbursement Error: ${err.message}`);
    } finally {
      setDisbursing(false);
    }
  };

  const formatCurrency = (val: string | number | undefined) => {
    if (val === undefined || val === null) return '₹0.00';
    const num = typeof val === 'string' ? parseFloat(val) : val;
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(num);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/80 dark:text-indigo-400 dark:border-indigo-800">OPEN</span>;
      case 'PARTIALLY_PAID':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200 dark:bg-amber-950/80 dark:text-amber-400 dark:border-amber-800">PARTIALLY PAID</span>;
      case 'PAID':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-400 dark:border-emerald-800">FULLY SETTLED</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700">{status}</span>;
    }
  };

  const totalCommitted = payables.reduce((acc, p) => acc + Number(p.approved_amount || 0), 0);
  const totalPaid = payables.reduce((acc, p) => acc + Number(p.paid_amount || 0), 0);
  const totalOutstanding = payables
    .filter(p => p.status === 'OPEN' || p.status === 'PARTIALLY_PAID')
    .reduce((acc, p) => acc + Number(p.remaining_balance || 0), 0);

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">General Liability Ledger &amp; Disbursements</h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Committed legal payment obligations created solely via authorized approval decisions with complete payment disbursement records.
          </p>
        </div>

        {/* Status Filters */}
        <div className="flex items-center space-x-2 bg-gray-100 dark:bg-[#1a1a1a] p-1.5 rounded-xl border border-gray-200 dark:border-[#333] self-start">
          {(['ALL', 'OPEN', 'PARTIALLY_PAID', 'PAID'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                statusFilter === st
                  ? 'bg-indigo-600 text-white font-semibold'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Aggregate Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-[#0c0c0c] p-5 rounded-2xl border border-gray-200 dark:border-[#222] shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total Approved Liabilities</span>
          <div className="text-2xl font-bold text-gray-900 dark:text-white font-mono mt-1">
            {formatCurrency(totalCommitted)}
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">Committed obligations</span>
        </div>

        <div className="bg-white dark:bg-[#0c0c0c] p-5 rounded-2xl border border-gray-200 dark:border-[#222] shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Outstanding Liability Due</span>
          <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 font-mono mt-1">
            {formatCurrency(totalOutstanding)}
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">Awaiting disbursement</span>
        </div>

        <div className="bg-white dark:bg-[#0c0c0c] p-5 rounded-2xl border border-gray-200 dark:border-[#222] shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total Settled Disbursements</span>
          <div className="text-2xl font-bold text-teal-600 dark:text-teal-400 font-mono mt-1">
            {formatCurrency(totalPaid)}
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">Completed payments</span>
        </div>
      </div>

      {/* Payables Ledger Table */}
      <div className="bg-white dark:bg-[#0c0c0c] rounded-2xl border border-gray-200 dark:border-[#222] shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-500 dark:text-gray-400 text-xs">Loading payable obligations...</div>
        ) : payables.length === 0 ? (
          <div className="p-12 text-center text-gray-500 dark:text-gray-400 text-xs">No payable obligations found matching filter.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-gray-50 dark:bg-[#111] border-b border-gray-200 dark:border-[#222] text-[11px] font-mono uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  <th className="py-3 px-4">Payable #</th>
                  <th className="py-3 px-4">Invoice #</th>
                  <th className="py-3 px-4">Vendor</th>
                  <th className="py-3 px-4">Due Date</th>
                  <th className="py-3 px-4 text-right">Approved Amount</th>
                  <th className="py-3 px-4 text-right">Paid Amount</th>
                  <th className="py-3 px-4 text-right">Remaining Balance</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-[#222]">
                {payables.map((p) => {
                  const isSettled = p.status === 'PAID';
                  return (
                    <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-[#1a1a1a] transition">
                      <td className="py-3.5 px-4 font-mono font-bold text-indigo-600 dark:text-indigo-400 whitespace-nowrap">
                        {p.payable_number}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-gray-700 dark:text-gray-300 whitespace-nowrap">
                        {p.invoice_number || 'N/A'}
                      </td>
                      <td className="py-3.5 px-4 font-medium text-gray-800 dark:text-gray-200 whitespace-nowrap">
                        {p.vendor_name || 'Vendor'}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-gray-600 dark:text-gray-300 whitespace-nowrap">
                        {p.due_date}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-gray-900 dark:text-gray-100 whitespace-nowrap">
                        {formatCurrency(p.approved_amount)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-teal-600 dark:text-teal-400 whitespace-nowrap">
                        {formatCurrency(p.paid_amount)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-amber-600 dark:text-amber-300 whitespace-nowrap">
                        {formatCurrency(p.remaining_balance)}
                      </td>
                      <td className="py-3.5 px-4 text-center whitespace-nowrap">
                        {getStatusBadge(p.status)}
                      </td>
                      <td className="py-3.5 px-4 text-right whitespace-nowrap space-x-2">
                        <button
                          onClick={() => setViewHistoryPayable(p)}
                          className="px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-[#1a1a1a] hover:bg-gray-200 dark:hover:bg-[#2a2a2a] text-gray-600 dark:text-gray-300 text-xs transition border border-gray-200 dark:border-[#333]"
                        >
                          Payments ({p.payments?.length || 0})
                        </button>
                        
                        {!isSettled && (
                          <button
                            onClick={() => {
                              setSelectedPayable(p);
                              setDisburseAmount(Number(p.remaining_balance));
                              setPaymentRef(`NEFT-${Math.floor(100000 + Math.random() * 900000)}`);
                            }}
                            className="px-3 py-1 bg-teal-600 hover:bg-teal-700 text-white font-medium text-xs rounded-lg shadow-sm transition"
                          >
                            Disburse
                          </button>
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

      {/* Modal: Record Financial Disbursement */}
      {selectedPayable && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111] border border-gray-200 dark:border-[#333] rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-[#222] pb-3">
              <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center space-x-2">
                <CreditCard className="w-5 h-5 text-teal-500" />
                <span>Execute Financial Disbursement</span>
              </h3>
              <button
                onClick={() => setSelectedPayable(null)}
                className="text-gray-400 hover:text-gray-700 dark:hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleDisburseSubmit} className="space-y-4 text-xs">
              <div className="bg-gray-50 dark:bg-[#080808] p-4 rounded-xl border border-gray-200 dark:border-[#222] space-y-2 font-mono">
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Payable #:</span>
                  <span className="font-bold text-indigo-600 dark:text-indigo-400">{selectedPayable.payable_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Vendor:</span>
                  <span className="text-gray-700 dark:text-gray-200">{selectedPayable.vendor_name}</span>
                </div>
                <div className="flex justify-between border-t border-gray-200 dark:border-[#222] pt-2">
                  <span className="text-gray-500 dark:text-gray-400">Remaining Due:</span>
                  <span className="font-bold text-amber-600 dark:text-amber-400 text-sm">{formatCurrency(selectedPayable.remaining_balance)}</span>
                </div>
              </div>

              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-medium mb-1">Disbursement Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  max={Number(selectedPayable.remaining_balance)}
                  value={disburseAmount}
                  onChange={(e) => setDisburseAmount(Number(e.target.value))}
                  required
                  className="w-full bg-white dark:bg-[#1a1a1a] border border-gray-200 dark:border-[#333] rounded-xl px-3 py-2 text-gray-900 dark:text-white font-mono text-xs focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-medium mb-1">Payment Reference Number</label>
                <input
                  type="text"
                  value={paymentRef}
                  onChange={(e) => setPaymentRef(e.target.value)}
                  placeholder="e.g. UTR / NEFT reference number"
                  required
                  className="w-full bg-white dark:bg-[#1a1a1a] border border-gray-200 dark:border-[#333] rounded-xl px-3 py-2 text-gray-900 dark:text-white font-mono text-xs focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-medium mb-1">Payment Rail</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full bg-white dark:bg-[#1a1a1a] border border-gray-200 dark:border-[#333] rounded-xl px-3 py-2 text-gray-900 dark:text-white text-xs focus:outline-none focus:border-teal-500"
                >
                  <option value="NEFT">NEFT (National Electronic Funds Transfer)</option>
                  <option value="RTGS">RTGS (Real Time Gross Settlement)</option>
                  <option value="IMPS">IMPS (Immediate Payment Service)</option>
                  <option value="WIRE">International Wire Transfer</option>
                </select>
              </div>

              <div className="pt-2 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setSelectedPayable(null)}
                  className="px-4 py-2 bg-gray-100 dark:bg-[#1a1a1a] hover:bg-gray-200 dark:hover:bg-[#2a2a2a] text-gray-700 dark:text-gray-300 rounded-xl border border-gray-200 dark:border-[#333]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={disbursing}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-bold rounded-xl shadow-lg shadow-teal-600/20"
                >
                  {disbursing ? 'Processing Payment...' : 'Record Payment Disbursement'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: View Payment History */}
      {viewHistoryPayable && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111] border border-gray-200 dark:border-[#333] rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-[#222] pb-3">
              <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center space-x-2">
                <Clock className="w-5 h-5 text-indigo-500" />
                <span>Disbursement History ({viewHistoryPayable.payable_number})</span>
              </h3>
              <button
                onClick={() => setViewHistoryPayable(null)}
                className="text-gray-400 hover:text-gray-700 dark:hover:text-white"
              >
                ✕
              </button>
            </div>

            {viewHistoryPayable.payments?.length === 0 ? (
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center py-6">No disbursements recorded yet.</p>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {viewHistoryPayable.payments.map((pm) => (
                  <div key={pm.id} className="bg-gray-50 dark:bg-[#080808] p-3 rounded-xl border border-gray-200 dark:border-[#222] flex justify-between items-center text-xs">
                    <div>
                      <div className="font-mono font-bold text-teal-600 dark:text-teal-400">{pm.payment_reference}</div>
                      <div className="text-[11px] text-gray-500 dark:text-gray-400">{pm.payment_method} • {pm.payment_date}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono font-bold text-gray-900 dark:text-white">{formatCurrency(pm.amount)}</div>
                      <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400">{pm.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setViewHistoryPayable(null)}
                className="px-4 py-2 bg-gray-100 dark:bg-[#1a1a1a] hover:bg-gray-200 dark:hover:bg-[#2a2a2a] text-gray-700 dark:text-gray-200 rounded-xl text-xs border border-gray-200 dark:border-[#333]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
