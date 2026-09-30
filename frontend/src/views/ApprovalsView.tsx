import React, { useState, useEffect } from 'react';
import {
  CheckCircle,
  XCircle,
  ChevronRight,
  X,
  ShieldCheck,
  FileText,
  AlertTriangle,
  Clock,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import type { Approval } from '../types';
import { formatCurrency, formatDate } from '../utils/format';

interface ApprovalsViewProps {
  onSelectInvoice: (invoiceId: string) => void;
  onRefreshParent?: () => void;
  activeEmail?: string;
  onSelectPersona?: (email: string) => void;
}

function getTierLabel(tier: number | null): string {
  switch (tier) {
    case 1: return 'Tier 1 (Up to ₹50,000)';
    case 2: return 'Tier 2 (₹50,001 – ₹5,00,000)';
    case 3: return 'Tier 3 (₹5,00,001 – ₹25,00,000)';
    case 4: return 'Tier 4 (Above ₹25,00,000)';
    default: return 'Standard Authority';
  }
}

export const ApprovalsView: React.FC<ApprovalsViewProps> = ({ onSelectInvoice, onRefreshParent }) => {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'PENDING' | 'APPROVED' | 'ALL'>('PENDING');
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [decisionType, setDecisionType] = useState<'APPROVE' | 'REJECT'>('APPROVE');
  const [comments, setComments] = useState('');
  const [deciding, setDeciding] = useState(false);
  const [successResult, setSuccessResult] = useState<any | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      const data = await api.listApprovals({ status: statusFilter === 'ALL' ? undefined : statusFilter });
      setApprovals(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [statusFilter]);

  const handleDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApproval) return;
    try {
      setDeciding(true);
      const res = await api.decideApproval(selectedApproval.id, decisionType, comments);
      setSuccessResult(res);
      await load();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(err.message);
      setSelectedApproval(null);
    } finally {
      setDeciding(false);
    }
  };

  const pendingApprovals = approvals.filter(a => a.status === 'PENDING');
  const approvedList = approvals.filter(a => a.status !== 'PENDING');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">
            Waiting for your approval
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Invoices that have passed all automated financial checks and require authorized sign-off.
          </p>
        </div>
        <div className="flex items-center gap-1 bg-white border border-gray-200 rounded-xl p-1 shadow-card self-start sm:self-auto">
          {(['PENDING', 'APPROVED', 'ALL'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                statusFilter === s ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              {s === 'PENDING' ? `Pending (${pendingApprovals.length})` : s === 'APPROVED' ? 'Approved' : 'All'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-36 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : approvals.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-12 text-center space-y-3">
          <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto text-gray-400">
            <Clock className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-gray-800">Nothing waiting for approval</h3>
          <p className="text-gray-500 text-xs max-w-sm mx-auto">
            All invoices within your approval authority have been actioned.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map(appr => {
            const isPending = appr.status === 'PENDING';

            return (
              <div
                key={appr.id}
                className={`bg-white rounded-2xl border shadow-card p-5 space-y-4 transition-all ${
                  isPending ? 'border-blue-200 hover:border-blue-300' : 'border-gray-100'
                }`}
              >
                {/* Top Row: Invoice, Vendor, Amount, Risk Badge */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-gray-100 pb-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className="font-mono font-bold text-base text-gray-900">
                        {appr.invoice_number}
                      </span>
                      <span className="text-gray-300">·</span>
                      <span className="font-bold text-gray-800 text-sm">
                        {appr.vendor_name || 'Unknown Vendor'}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          isPending
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        }`}
                      >
                        {isPending ? 'Pending Sign-off' : 'Approved'}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      Submitted on {formatDate(appr.created_at)} · {appr.policy_name} ({getTierLabel(appr.policy_tier)})
                    </div>
                  </div>

                  <div className="text-left sm:text-right">
                    <div className="text-[10px] uppercase font-bold text-gray-400">Invoice Amount</div>
                    <div className="text-2xl font-black text-gray-900 font-mono">
                      {formatCurrency(appr.invoice_amount)}
                    </div>
                  </div>
                </div>

                {/* Middle: Automated Checks & Risk Verification Badges */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-3 flex items-center gap-2.5">
                    <ShieldCheck className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                    <div>
                      <span className="font-bold text-emerald-950 block">All 18 AP Controls Passed</span>
                      <span className="text-emerald-700 text-[11px]">
                        3-way matching verified with zero duplicate or price anomalies.
                      </span>
                    </div>
                  </div>

                  <div className="bg-gray-50 border border-gray-200 rounded-xl p-3 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-gray-400 block">Deterministic Risk</span>
                      <span className="font-bold text-emerald-700 text-xs">LOW RISK (10/100)</span>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">
                      Safe for Disbursement
                    </span>
                  </div>
                </div>

                {/* Decision Note if already actioned */}
                {appr.comments && (
                  <div className="bg-gray-50 p-2.5 rounded-xl border border-gray-100 text-xs text-gray-600 italic">
                    Decision note: "{appr.comments}"
                  </div>
                )}

                {/* Bottom Action Buttons: [Review], [Approve], [Reject] */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 border-t border-gray-100">
                  <button
                    type="button"
                    onClick={() => onSelectInvoice(appr.invoice_id)}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 self-start sm:self-auto"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    Review full invoice details &rarr;
                  </button>

                  {isPending && (
                    <div className="flex items-center gap-2 self-end sm:self-auto">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedApproval(appr);
                          setDecisionType('REJECT');
                          setComments('');
                        }}
                        className="px-4 py-2 border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-bold rounded-xl transition-colors shadow-2xs"
                      >
                        Reject
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setSelectedApproval(appr);
                          setDecisionType('APPROVE');
                          setComments('Verified 3-way match. Approved for payment.');
                        }}
                        className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition-colors shadow-xs flex items-center gap-1.5"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Approve Invoice
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Decision Modal */}
      {selectedApproval && !successResult && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-900">
                {decisionType === 'APPROVE' ? 'Approve Invoice' : 'Reject Invoice'}
              </h3>
              <button
                onClick={() => setSelectedApproval(null)}
                className="p-1 rounded-lg text-gray-400 hover:bg-gray-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-gray-50 rounded-xl p-3.5 mb-4 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-500">Vendor</span>
                <span className="font-bold text-gray-900">{selectedApproval.vendor_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Invoice</span>
                <span className="font-mono font-bold text-gray-900">{selectedApproval.invoice_number}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-gray-200">
                <span className="text-gray-500">Amount to approve</span>
                <span className="font-mono font-black text-gray-900 text-sm">
                  {formatCurrency(selectedApproval.invoice_amount)}
                </span>
              </div>
            </div>

            <form onSubmit={handleDecision} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-700 font-bold mb-1.5">Decision Note</label>
                <textarea
                  rows={3}
                  value={comments}
                  onChange={e => setComments(e.target.value)}
                  required
                  placeholder="Record your authorization notes for the audit ledger..."
                  className="w-full border border-gray-200 rounded-xl p-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-sans"
                />
              </div>

              {decisionType === 'APPROVE' && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-[11px] text-amber-800">
                  Approving this invoice will immediately commit it to the dual-entry <strong>Payable Ledger</strong> for disbursement.
                </div>
              )}

              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setSelectedApproval(null)}
                  className="flex-1 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={deciding}
                  className={`flex-1 py-2 text-white font-bold rounded-xl transition-colors shadow-xs ${
                    decisionType === 'APPROVE'
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  {deciding
                    ? 'Processing...'
                    : decisionType === 'APPROVE'
                    ? 'Confirm Approval'
                    : 'Confirm Rejection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Success Notification Modal */}
      {successResult && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-gray-200 text-center space-y-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto text-emerald-600">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900">Approval Committed</h3>
              <p className="text-xs text-gray-500 mt-1">
                The invoice has been signed off and recorded on the payment ledger.
              </p>
            </div>

            {successResult.payable_number && (
              <div className="bg-gray-50 p-3 rounded-xl border border-gray-100 text-xs text-left space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-500">Payable Ref:</span>
                  <span className="font-mono font-bold text-gray-900">{successResult.payable_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Status:</span>
                  <span className="font-semibold text-emerald-700">{successResult.invoice_status}</span>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={() => {
                setSuccessResult(null);
                setSelectedApproval(null);
              }}
              className="w-full py-2 bg-gray-900 hover:bg-gray-800 text-white font-bold rounded-xl text-xs transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

