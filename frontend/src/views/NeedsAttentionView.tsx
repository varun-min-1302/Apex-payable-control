import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, ChevronRight, X, ArrowRight, ShieldAlert, FileText, Check } from 'lucide-react';
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
      return { label: 'Critical', className: 'bg-red-100 text-red-800 border-red-200' };
    case 'HIGH':
      return { label: 'High', className: 'bg-orange-100 text-orange-800 border-orange-200' };
    case 'MEDIUM':
      return { label: 'Medium', className: 'bg-amber-100 text-amber-800 border-amber-200' };
    default:
      return { label: 'Low', className: 'bg-blue-100 text-blue-800 border-blue-200' };
  }
}

export const NeedsAttentionView: React.FC<NeedsAttentionViewProps> = ({ onSelectInvoice, onRefreshParent }) => {
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
      alert('Please provide a reason.');
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
      alert(err.message);
    } finally {
      setResolving(false);
    }
  };

  const openExceptions = exceptions.filter(e => e.status === 'OPEN');
  const resolvedExceptions = exceptions.filter(e => e.status !== 'OPEN');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Needs Attention</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Invoices with verified exceptions that must be addressed before payment approval.
          </p>
        </div>
        <div className="flex items-center gap-1 bg-white border border-gray-200 rounded-xl p-1 shadow-card self-start sm:self-auto">
          {(['OPEN', 'RESOLVED', 'ALL'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                statusFilter === s ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              {s === 'OPEN' ? `Active (${openExceptions.length})` : s === 'RESOLVED' ? 'Resolved' : 'All'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : exceptions.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-12 text-center space-y-3">
          <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto text-emerald-600">
            <CheckCircle className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-gray-800">All clear</h3>
          <p className="text-gray-500 text-xs max-w-sm mx-auto">
            {statusFilter === 'OPEN'
              ? 'No invoices currently need your attention. All verified invoices are progressing normally.'
              : 'No records found for this filter.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Active Exceptions List */}
          {statusFilter !== 'RESOLVED' && openExceptions.length > 0 && (
            <div className="space-y-3">
              {openExceptions.map(exc => {
                const sev = getSeverityBadge(exc.severity);
                return (
                  <div
                    key={exc.id}
                    className="bg-white rounded-2xl border border-amber-200/80 shadow-card p-5 space-y-4 hover:border-amber-300 transition-all"
                  >
                    {/* Top Row: Invoice, Vendor, Severity */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono font-bold text-base text-gray-900">
                          {exc.invoice_number}
                        </span>
                        <span className="text-gray-300">·</span>
                        <span className="font-semibold text-gray-800 text-sm">
                          {exc.vendor_name || 'Unknown Vendor'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border uppercase ${sev.className}`}>
                          {sev.label} Severity
                        </span>
                        <span className="text-gray-400 text-xs">Flagged {formatDate(exc.created_at)}</span>
                      </div>
                    </div>

                    {/* Middle Section: Issue Title & Structured Content */}
                    <div className="space-y-2.5">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-amber-500" />
                        <h3 className="text-sm font-bold text-gray-900">
                          {humanExceptionCode(exc.exception_code)}
                        </h3>
                      </div>

                      {/* What Happened */}
                      <div className="bg-gray-50 p-3 rounded-xl border border-gray-100 text-xs space-y-1">
                        <span className="text-gray-400 font-bold uppercase text-[10px] block">
                          What happened
                        </span>
                        <p className="text-gray-800 leading-relaxed font-medium">
                          {exceptionWhatHappened(exc.exception_code)}
                        </p>
                      </div>

                      {/* Two Column: Why It Matters & Recommended Action */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div className="bg-amber-50/60 p-3 rounded-xl border border-amber-100">
                          <span className="text-amber-800 font-bold uppercase text-[10px] block flex items-center gap-1">
                            <ShieldAlert className="w-3 h-3 text-amber-600" />
                            Why it matters
                          </span>
                          <p className="text-gray-700 mt-1 leading-relaxed">
                            {exceptionWhatHappened(exc.exception_code)}
                          </p>
                        </div>

                        <div className="bg-blue-50/60 p-3 rounded-xl border border-blue-100">
                          <span className="text-blue-800 font-bold uppercase text-[10px] block flex items-center gap-1">
                            <ArrowRight className="w-3 h-3 text-blue-600" />
                            Recommended action
                          </span>
                          <p className="text-gray-700 mt-1 leading-relaxed">
                            {exceptionWhatToDo(exc.exception_code)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                      <details className="text-xs">
                        <summary className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide cursor-pointer hover:text-gray-600">
                          Technical details
                        </summary>
                        <div className="mt-1.5 p-2 bg-gray-50 rounded-lg text-[11px] font-mono text-gray-600 space-y-0.5 border border-gray-100">
                          <div><span className="text-gray-400">Rule:</span> {exc.exception_code}</div>
                          <div><span className="text-gray-400">ID:</span> {exc.id}</div>
                        </div>
                      </details>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => onSelectInvoice(exc.invoice_id)}
                          className="px-3.5 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-semibold rounded-xl transition-colors flex items-center gap-1"
                        >
                          <FileText className="w-3.5 h-3.5" />
                          Review Invoice
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedException(exc);
                            setResolutionAction('RESOLVE');
                            setResolutionReason('');
                          }}
                          className="px-4 py-1.5 bg-gray-900 hover:bg-gray-800 text-white text-xs font-semibold rounded-xl transition-colors shadow-2xs"
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

          {/* Resolved Exceptions */}
          {statusFilter !== 'OPEN' && resolvedExceptions.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                Resolved Issues ({resolvedExceptions.length})
              </h2>
              {resolvedExceptions.map(exc => (
                <div key={exc.id} className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 opacity-80">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-emerald-50 rounded-xl flex items-center justify-center flex-shrink-0 text-emerald-600">
                        <Check className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="font-bold text-gray-800 text-sm">{exc.vendor_name || 'Unknown Vendor'}</div>
                        <div className="text-xs text-gray-400 font-mono mt-0.5">
                          {exc.invoice_number} · {humanExceptionCode(exc.exception_code)} · Resolved
                        </div>
                        {exc.resolution_reason && (
                          <div className="text-xs text-gray-600 mt-1 italic">
                            Resolution note: "{exc.resolution_reason}"
                          </div>
                        )}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => onSelectInvoice(exc.invoice_id)}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                    >
                      View Invoice &rarr;
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Resolution Modal */}
      {selectedException && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-900">Resolve Exception</h3>
              <button
                onClick={() => setSelectedException(null)}
                className="p-1 rounded-lg text-gray-400 hover:bg-gray-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-gray-50 rounded-xl p-3.5 mb-4 text-xs space-y-1">
              <div className="font-bold text-gray-900">{selectedException.vendor_name}</div>
              <div className="text-gray-500 font-mono">{selectedException.invoice_number}</div>
              <div className="text-gray-700 mt-1">{exceptionWhatHappened(selectedException.exception_code)}</div>
            </div>

            <form onSubmit={handleResolve} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-700 font-bold mb-1.5">Action</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['RESOLVE', 'WAIVE'] as const).map(action => (
                    <button
                      key={action}
                      type="button"
                      onClick={() => setResolutionAction(action)}
                      className={`py-2 rounded-xl text-xs font-semibold transition-colors border ${
                        resolutionAction === action
                          ? 'bg-gray-900 text-white border-gray-900'
                          : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {action === 'RESOLVE' ? 'Mark as Fixed' : 'Waive / Accept Risk'}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-gray-700 font-bold mb-1.5">
                  Resolution Note <span className="text-gray-400 font-normal">(Required for audit trail)</span>
                </label>
                <textarea
                  rows={3}
                  value={resolutionReason}
                  onChange={e => setResolutionReason(e.target.value)}
                  required
                  placeholder="Explain why this issue is resolved or waived..."
                  className="w-full border border-gray-200 rounded-xl p-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-sans"
                />
              </div>

              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setSelectedException(null)}
                  className="flex-1 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resolving}
                  className="flex-1 py-2 bg-gray-900 hover:bg-gray-800 disabled:opacity-50 text-white font-bold rounded-xl transition-colors"
                >
                  {resolving ? 'Saving...' : 'Confirm Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};


