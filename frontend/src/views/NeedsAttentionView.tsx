import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  CheckCircle,
  ChevronRight,
  X,
  ArrowRight,
  ShieldAlert,
  FileText,
  Check,
  RotateCcw,
  Sliders,
  DollarSign
} from 'lucide-react';
import { api } from '../api/client';
import type { APException } from '../types';
import { formatDate } from '../utils/format';
import { exceptionWhatHappened, exceptionWhatToDo } from '../utils/labels';
import { humanExceptionCode } from '../utils/format';

interface NeedsAttentionViewProps {
  onSelectInvoice: (invoiceId: string) => void;
  onRefreshParent?: () => void;
  activeEmail?: string;
  onSelectPersona?: (email: string) => void;
}

function getSeverityBadge(sev: string): { label: string; className: string } {
  switch (sev?.toUpperCase()) {
    case 'CRITICAL':
      return { label: 'Critical', className: 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20' };
    case 'HIGH':
      return { label: 'High', className: 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20' };
    case 'MEDIUM':
      return { label: 'Medium', className: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20' };
    default:
      return { label: 'Low', className: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20' };
  }
}

export const NeedsAttentionView: React.FC<NeedsAttentionViewProps> = ({
  onSelectInvoice,
  onRefreshParent,
}) => {
  const [exceptions, setExceptions] = useState<APException[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'OPEN' | 'RESOLVED' | 'ALL'>('OPEN');
  const [selectedException, setSelectedException] = useState<APException | null>(null);
  const [resolutionAction, setResolutionAction] = useState<'RESOLVE' | 'WAIVE'>('RESOLVE');
  const [resolutionReason, setResolutionReason] = useState('');
  const [resolving, setResolving] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      const data = await api.listExceptions({ status: statusFilter === 'ALL' ? undefined : statusFilter });
      setExceptions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [statusFilter]);

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedException || !resolutionReason.trim()) {
      alert('Please provide an audit justification note.');
      return;
    }
    try {
      setResolving(true);
      await api.resolveException(selectedException.id, resolutionAction, resolutionReason);
      setSelectedException(null);
      setResolutionReason('');
      await load();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(err.message || 'Failed to record exception resolution.');
    } finally {
      setResolving(false);
    }
  };

  const openExceptions = exceptions.filter(e => e.status === 'OPEN');
  const resolvedExceptions = exceptions.filter(e => e.status !== 'OPEN');

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            Needs Attention
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Invoices that require action before they can become payable.
          </p>
        </div>

        {/* Filter Switcher */}
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-full border border-border/60 self-start sm:self-auto">
          {(['OPEN', 'RESOLVED', 'ALL'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                statusFilter === s
                  ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {s === 'OPEN' ? `Active (${openExceptions.length})` : s === 'RESOLVED' ? `Resolved (${resolvedExceptions.length})` : 'All'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-44 bg-muted rounded-[22px] animate-pulse" />
          ))}
        </div>
      ) : exceptions.length === 0 ? (
        <div className="bg-card text-card-foreground rounded-[22px] border border-border/80 shadow-card p-12 text-center space-y-3">
          <div className="w-14 h-14 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center mx-auto">
            <CheckCircle className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-foreground">All clear</h3>
          <p className="text-muted-foreground text-xs max-w-sm mx-auto">
            {statusFilter === 'OPEN'
              ? 'No invoices currently need your attention. All verified invoices are progressing normally.'
              : 'No records found for this filter.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          
          {/* Active Exceptions List */}
          {statusFilter !== 'RESOLVED' && openExceptions.length > 0 && (
            <div className="space-y-4">
              {openExceptions.map(exc => {
                const sev = getSeverityBadge(exc.severity);
                return (
                  <div
                    key={exc.id}
                    className="bg-card text-card-foreground rounded-[22px] border border-amber-300/80 dark:border-amber-900/60 shadow-card p-5 space-y-4 hover:border-amber-400 transition-all"
                  >
                    {/* Header: Invoice #, Vendor, Severity Badge */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-3">
                      <div className="flex items-center gap-2.5 flex-wrap">
                        <span className="font-mono font-bold text-base text-primary">
                          {exc.invoice_number}
                        </span>
                        <span className="text-muted-foreground">·</span>
                        <span className="font-semibold text-foreground text-sm">
                          {exc.vendor_name || 'Unknown Vendor'}
                        </span>
                        <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${sev.className}`}>
                          {sev.label} Severity
                        </span>
                      </div>

                      <div className="text-[11px] text-muted-foreground">
                        Flagged {formatDate(exc.created_at)}
                      </div>
                    </div>

                    {/* Discrepancy Metric Cards (Quantity / Price Variance) */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                      <div className="p-3 bg-muted/40 rounded-xl border border-border/60">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase">Discrepancy</div>
                        <div className="text-xs font-bold text-amber-600 dark:text-amber-400 mt-1">
                          {humanExceptionCode(exc.exception_code)}
                        </div>
                      </div>

                      <div className="p-3 bg-muted/40 rounded-xl border border-border/60">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase">Invoice Value</div>
                        <div className="text-xs font-bold font-mono text-foreground mt-1">
                          120 Units
                        </div>
                      </div>

                      <div className="p-3 bg-muted/40 rounded-xl border border-border/60">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase">Verified Value</div>
                        <div className="text-xs font-bold font-mono text-foreground mt-1">
                          100 Units
                        </div>
                      </div>

                      <div className="p-3 bg-red-500/10 rounded-xl border border-red-500/20">
                        <div className="text-[10px] font-bold text-red-600 dark:text-red-400 uppercase">Variance</div>
                        <div className="text-xs font-extrabold font-mono text-red-600 dark:text-red-400 mt-1">
                          +20 Units (+16.7%)
                        </div>
                      </div>
                    </div>

                    {/* Plain Language Explanation: What Happened & What to Do */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs bg-muted/30 p-3.5 rounded-xl border border-border/60">
                      <div>
                        <span className="font-bold text-foreground block mb-0.5">What happened</span>
                        <span className="text-muted-foreground leading-relaxed">
                          {exceptionWhatHappened(exc.exception_code)}
                        </span>
                      </div>
                      <div>
                        <span className="font-bold text-foreground block mb-0.5">Recommended action</span>
                        <span className="text-muted-foreground leading-relaxed">
                          {exceptionWhatToDo(exc.exception_code)}
                        </span>
                      </div>
                    </div>

                    {/* Action Footer */}
                    <div className="pt-2 flex items-center justify-between gap-3">
                      <button
                        onClick={() => onSelectInvoice(exc.invoice_id)}
                        className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                      >
                        Inspect Full Invoice Details <ChevronRight className="w-3.5 h-3.5" />
                      </button>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setSelectedException(exc);
                            setResolutionAction('WAIVE');
                            setResolutionReason('');
                          }}
                          className="px-3 py-1.5 bg-card hover:bg-muted text-muted-foreground hover:text-foreground text-xs font-medium rounded-xl border border-border transition-colors"
                        >
                          Waive Discrepancy
                        </button>
                        <button
                          onClick={() => {
                            setSelectedException(exc);
                            setResolutionAction('RESOLVE');
                            setResolutionReason('');
                          }}
                          className="px-3.5 py-1.5 bg-foreground text-background dark:bg-card dark:text-foreground hover:opacity-90 text-xs font-semibold rounded-xl transition-all shadow-xs"
                        >
                          Resolve Issue
                        </button>
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>
          )}

          {/* Resolved Exceptions List */}
          {statusFilter !== 'OPEN' && resolvedExceptions.length > 0 && (
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                Resolved Exceptions ({resolvedExceptions.length})
              </h3>
              {resolvedExceptions.map(exc => (
                <div
                  key={exc.id}
                  className="bg-card text-card-foreground rounded-[20px] border border-border/80 shadow-card p-4 opacity-80 space-y-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      <span className="font-mono font-bold text-foreground">{exc.invoice_number}</span>
                      <span className="text-muted-foreground">·</span>
                      <span className="font-semibold text-foreground">{exc.vendor_name}</span>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      RESOLVED
                    </span>
                  </div>
                  {exc.resolution_reason && (
                    <p className="text-xs text-muted-foreground italic pl-6">
                      Audit Note: &ldquo;{exc.resolution_reason}&rdquo;
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

        </div>
      )}

      {/* Resolution Modal */}
      {selectedException && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-popover text-popover-foreground rounded-[24px] max-w-md w-full p-6 shadow-modal border border-border space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="text-base font-bold text-foreground">Record Exception Resolution</h3>
              <button
                onClick={() => setSelectedException(null)}
                className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-muted/50 p-3 rounded-xl border border-border text-xs space-y-1">
              <div className="font-bold text-foreground">
                {selectedException.invoice_number} · {selectedException.vendor_name}
              </div>
              <div className="text-muted-foreground">
                Issue: {humanExceptionCode(selectedException.exception_code)}
              </div>
            </div>

            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase mb-1.5">Action</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setResolutionAction('RESOLVE')}
                    className={`py-2 rounded-xl text-xs font-semibold transition-all border ${
                      resolutionAction === 'RESOLVE'
                        ? 'bg-foreground text-background font-bold'
                        : 'bg-card text-muted-foreground border-border hover:bg-muted'
                    }`}
                  >
                    Mark as Resolved
                  </button>
                  <button
                    type="button"
                    onClick={() => setResolutionAction('WAIVE')}
                    className={`py-2 rounded-xl text-xs font-semibold transition-all border ${
                      resolutionAction === 'WAIVE'
                        ? 'bg-foreground text-background font-bold'
                        : 'bg-card text-muted-foreground border-border hover:bg-muted'
                    }`}
                  >
                    Waive Discrepancy
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase mb-1.5">
                  Audit Justification Note <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  value={resolutionReason}
                  onChange={e => setResolutionReason(e.target.value)}
                  required
                  placeholder="Explain why this issue is resolved or waived for permanent audit compliance..."
                  className="w-full bg-muted/40 border border-border rounded-xl p-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                />
              </div>

              <div className="flex gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedException(null)}
                  className="flex-1 py-2 bg-card hover:bg-muted text-muted-foreground font-semibold rounded-xl text-xs border border-border transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resolving}
                  className="flex-1 py-2 bg-primary hover:bg-primary/90 disabled:opacity-50 text-primary-foreground font-semibold rounded-xl text-xs transition-colors shadow-xs"
                >
                  {resolving ? 'Recording...' : 'Confirm Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
