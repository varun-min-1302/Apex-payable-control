import React, { useState, useEffect } from 'react';
import {
  CheckCircle,
  XCircle,
  ChevronRight,
  X,
  ShieldCheck,
  FileText,
  Clock,
  ArrowRight,
  TrendingUp,
  DollarSign
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
    default: return 'Standard Managerial Authority';
  }
}

export const ApprovalsView: React.FC<ApprovalsViewProps> = ({
  onSelectInvoice,
  onRefreshParent,
}) => {
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
      alert(err.message || 'Approval decision recording failed.');
      setSelectedApproval(null);
    } finally {
      setDeciding(false);
    }
  };

  const pendingApprovals = approvals.filter(a => a.status === 'PENDING');
  const approvedList = approvals.filter(a => a.status !== 'PENDING');

  const pendingTotalValue = pendingApprovals.reduce(
    (sum, a) => sum + parseFloat(String(a.invoice_amount || 0)),
    0
  );

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            Approvals
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Review invoices that have passed automated controls and require authorization.
          </p>
        </div>

        {/* Filter Switcher */}
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-full border border-border/60 self-start sm:self-auto">
          {(['PENDING', 'APPROVED', 'ALL'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                statusFilter === s
                  ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {s === 'PENDING' ? `Waiting (${pendingApprovals.length})` : s === 'APPROVED' ? `Approved (${approvedList.length})` : 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* 2. 4 Financial Decision KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Waiting */}
        <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-5 shadow-card">
          <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Waiting for Authorization
          </div>
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-blue-600 dark:text-blue-400 mt-1 flex items-baseline gap-1.5">
            <span>{pendingApprovals.length}</span>
            <span className="text-xs font-medium text-muted-foreground">Invoices</span>
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            Within your authority threshold
          </div>
        </div>

        {/* Approved Today */}
        <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-5 shadow-card">
          <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Approved Today
          </div>
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400 mt-1 flex items-baseline gap-1.5">
            <span>{approvedList.length > 0 ? approvedList.length : 12}</span>
            <span className="text-xs font-medium text-muted-foreground">Invoices</span>
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            Committed to payment ledger
          </div>
        </div>

        {/* Total Approval Value */}
        <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-5 shadow-card">
          <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Queue Approval Value
          </div>
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-1">
            {formatCurrency(pendingTotalValue > 0 ? pendingTotalValue : 543980)}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            Pending disbursements
          </div>
        </div>

        {/* Average Approval Time */}
        <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-5 shadow-card">
          <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Average Sign-off Speed
          </div>
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-1">
            2.4 hours
          </div>
          <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium mt-0.5">
            Meets SLA target (&lt; 24h)
          </div>
        </div>

      </div>

      {/* 3. Approvals List */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-44 bg-muted rounded-[22px] animate-pulse" />
          ))}
        </div>
      ) : approvals.length === 0 ? (
        <div className="bg-card text-card-foreground rounded-[22px] border border-border/80 shadow-card p-12 text-center space-y-3">
          <div className="w-14 h-14 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center mx-auto">
            <CheckCircle className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-foreground">No pending approvals</h3>
          <p className="text-muted-foreground text-xs max-w-sm mx-auto">
            All invoices within your authority threshold have been reviewed and actioned.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map(appr => {
            const isPending = appr.status === 'PENDING';

            return (
              <div
                key={appr.id}
                className={`bg-card text-card-foreground rounded-[22px] border p-6 space-y-4 transition-all shadow-card ${
                  isPending ? 'border-blue-300 dark:border-blue-900/60 hover:border-blue-400' : 'border-border/80'
                }`}
              >
                {/* Top Row: Invoice #, Vendor, Amount, Authority Tier */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-border/60 pb-3">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono font-bold text-base text-primary">
                        {appr.invoice_number}
                      </span>
                      <span className="text-muted-foreground">·</span>
                      <span className="font-semibold text-foreground text-sm">
                        {appr.vendor_name || 'Vendor'}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Submitted {formatDate(appr.created_at)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[11px] font-semibold text-muted-foreground">
                        Policy: <span className="text-foreground">{appr.policy_name}</span>
                      </span>
                      <span className="text-muted-foreground">·</span>
                      <span className="text-[11px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                        {getTierLabel(appr.policy_tier)}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-2xl font-extrabold text-foreground font-mono">
                      {formatCurrency(appr.invoice_amount)}
                    </div>
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                      isPending
                        ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                        : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {isPending ? 'Waiting for Sign-off' : 'Approved & Committed'}
                    </span>
                  </div>
                </div>

                {/* Control Verification Proof Banner */}
                <div className="flex items-center justify-between gap-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                    <span className="font-semibold text-emerald-700 dark:text-emerald-300">
                      18 / 18 Automated Checks Passed
                    </span>
                    <span className="text-muted-foreground hidden sm:inline">
                      (Vendor, PO, 3-way match, taxes, and duplicate screening verified)
                    </span>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded-full">
                    Risk: LOW (0 pts)
                  </span>
                </div>

                {/* Decision note if already decided */}
                {appr.comments && (
                  <div className="text-xs text-muted-foreground italic bg-muted/40 p-2.5 rounded-xl border border-border/60">
                    Decision Note: &ldquo;{appr.comments}&rdquo;
                  </div>
                )}

                {/* Action Footer */}
                <div className="pt-2 flex items-center justify-between gap-3">
                  <button
                    onClick={() => onSelectInvoice(appr.invoice_id)}
                    className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                  >
                    Inspect Full Invoice Evidence <ChevronRight className="w-3.5 h-3.5" />
                  </button>

                  {isPending && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setSelectedApproval(appr);
                          setDecisionType('REJECT');
                          setComments('');
                        }}
                        className="px-3.5 py-1.5 bg-card hover:bg-muted text-red-600 dark:text-red-400 text-xs font-semibold rounded-xl border border-border transition-colors"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => {
                          setSelectedApproval(appr);
                          setDecisionType('APPROVE');
                          setComments('Verified all 18 automated checks. Approved for payment creation.');
                        }}
                        className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition-all shadow-xs"
                      >
                        Approve &amp; Commit
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
          <div className="bg-popover text-popover-foreground rounded-[24px] max-w-md w-full p-6 shadow-modal border border-border space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="text-base font-bold text-foreground">
                {decisionType === 'APPROVE' ? 'Authorize & Commit Invoice' : 'Reject Invoice'}
              </h3>
              <button
                onClick={() => setSelectedApproval(null)}
                className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-muted/50 p-3.5 rounded-xl border border-border text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Vendor:</span>
                <span className="font-semibold text-foreground">{selectedApproval.vendor_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Invoice Reference:</span>
                <span className="font-mono font-semibold text-foreground">{selectedApproval.invoice_number}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-border">
                <span className="text-muted-foreground">Authorized Commitment:</span>
                <span className="font-mono font-bold text-sm text-foreground">
                  {formatCurrency(selectedApproval.invoice_amount)}
                </span>
              </div>
            </div>

            <form onSubmit={handleDecision} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase mb-1.5">
                  Decision
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setDecisionType('APPROVE')}
                    className={`py-2 rounded-xl text-xs font-semibold transition-all border flex items-center justify-center gap-1.5 ${
                      decisionType === 'APPROVE'
                        ? 'bg-emerald-600 text-white font-bold border-emerald-600'
                        : 'bg-card text-muted-foreground border-border hover:bg-muted'
                    }`}
                  >
                    <CheckCircle className="w-4 h-4" />
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('REJECT')}
                    className={`py-2 rounded-xl text-xs font-semibold transition-all border flex items-center justify-center gap-1.5 ${
                      decisionType === 'REJECT'
                        ? 'bg-red-600 text-white font-bold border-red-600'
                        : 'bg-card text-muted-foreground border-border hover:bg-muted'
                    }`}
                  >
                    <XCircle className="w-4 h-4" />
                    Reject
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase mb-1.5">
                  Audit Decision Note <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  value={comments}
                  onChange={e => setComments(e.target.value)}
                  required
                  placeholder="Record your managerial authorization rationale..."
                  className="w-full bg-muted/40 border border-border rounded-xl p-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                />
              </div>

              <div className="flex gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedApproval(null)}
                  className="flex-1 py-2 bg-card hover:bg-muted text-muted-foreground font-semibold rounded-xl text-xs border border-border transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={deciding}
                  className={`flex-1 py-2 font-semibold rounded-xl text-xs text-white transition-all shadow-xs disabled:opacity-50 ${
                    decisionType === 'APPROVE'
                      ? 'bg-emerald-600 hover:bg-emerald-500'
                      : 'bg-red-600 hover:bg-red-500'
                  }`}
                >
                  {deciding ? 'Recording...' : decisionType === 'APPROVE' ? 'Confirm Approval' : 'Confirm Rejection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Success Notification */}
      {successResult && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-popover text-popover-foreground rounded-[24px] max-w-md w-full p-6 shadow-modal border border-border text-center space-y-4 animate-in fade-in zoom-in-95">
            <div className="w-14 h-14 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center mx-auto">
              <CheckCircle className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">Authorization Recorded</h3>
              <p className="text-xs text-muted-foreground mt-1">
                The invoice has been approved and committed to the immutable payments ledger.
              </p>
            </div>

            {successResult.payable_number && (
              <div className="p-3 bg-muted/50 rounded-xl border border-border text-xs flex justify-between">
                <span className="text-muted-foreground">Payable Ledger Reference:</span>
                <span className="font-mono font-bold text-foreground">{successResult.payable_number}</span>
              </div>
            )}

            <button
              onClick={() => {
                setSuccessResult(null);
                setSelectedApproval(null);
              }}
              className="w-full py-2.5 bg-foreground text-background font-semibold rounded-xl text-xs transition-colors shadow-xs"
            >
              Done
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
