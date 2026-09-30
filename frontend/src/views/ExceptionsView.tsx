import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Filter,
  UserCheck,
  Calendar,
  MessageSquare,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { APException } from '../types';

interface ExceptionsViewProps {
  onSelectInvoice: (invoiceId: string) => void;
  onRefreshParent?: () => void;
}

export const ExceptionsView: React.FC<ExceptionsViewProps> = ({ onSelectInvoice, onRefreshParent }) => {
  const [exceptions, setExceptions] = useState<APException[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'OPEN' | 'RESOLVED'>('OPEN');
  
  // Resolution Modal State
  const [selectedException, setSelectedException] = useState<APException | null>(null);
  const [resolutionAction, setResolutionAction] = useState<'RESOLVE' | 'WAIVE'>('RESOLVE');
  const [resolutionReason, setResolutionReason] = useState('');
  const [resolving, setResolving] = useState(false);

  const loadExceptions = async () => {
    try {
      setLoading(true);
      const data = await api.listExceptions({
        status: statusFilter === 'ALL' ? undefined : statusFilter,
      });
      setExceptions(data);
    } catch (err) {
      console.error('Failed to load exceptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExceptions();
  }, [statusFilter]);

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedException || !resolutionReason.trim()) {
      alert('Please provide a mandatory audit justification.');
      return;
    }

    try {
      setResolving(true);
      await api.resolveException(selectedException.id, resolutionAction, resolutionReason);
      setSelectedException(null);
      setResolutionReason('');
      await loadExceptions();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(`Resolution Error: ${err.message}`);
    } finally {
      setResolving(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950/80 text-rose-400 border border-rose-800">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-orange-950/80 text-orange-400 border border-orange-800">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950/80 text-amber-400 border border-amber-800">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700">LOW</span>;
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Exceptions Resolution Center</h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic control failures halting invoice progression. Requires authorized managerial review or waiver with immutable audit justification.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-2 bg-slate-900 p-1.5 rounded-xl border border-slate-800 self-start">
          <button
            onClick={() => setStatusFilter('OPEN')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              statusFilter === 'OPEN'
                ? 'bg-rose-600 text-white font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Active Open
          </button>
          <button
            onClick={() => setStatusFilter('RESOLVED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              statusFilter === 'RESOLVED'
                ? 'bg-indigo-600 text-white font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Resolved & Waived
          </button>
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              statusFilter === 'ALL'
                ? 'bg-slate-700 text-white font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            All Exceptions
          </button>
        </div>
      </div>

      {/* Exceptions Grid / Cards */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">Loading exceptions...</div>
      ) : exceptions.length === 0 ? (
        <div className="bg-slate-900/60 p-12 rounded-2xl border border-slate-800 text-center space-y-3">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-200">Zero Open Exceptions</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            All deterministic control runs have passed or have been resolved by management. Invoices can proceed to managerial approval.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {exceptions.map((exc) => (
            <div
              key={exc.id}
              className={`p-5 rounded-2xl border transition space-y-4 ${
                exc.status === 'OPEN'
                  ? 'bg-slate-900/90 border-slate-800 hover:border-slate-700 shadow-lg'
                  : 'bg-slate-900/40 border-slate-800/60 opacity-80'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    {getSeverityBadge(exc.severity)}
                    <span className="font-mono text-xs font-semibold text-indigo-400">{exc.exception_code}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                      exc.status === 'OPEN' ? 'bg-rose-950 text-rose-300' : 'bg-emerald-950 text-emerald-300'
                    }`}>
                      {exc.status}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-white mt-1">{exc.title}</h3>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                {exc.description}
              </p>

              <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 font-mono">
                <div>Invoice: <strong className="text-slate-200">{exc.invoice_number || 'N/A'}</strong></div>
                <div>Vendor: <span className="text-slate-200 truncate">{exc.vendor_name || 'N/A'}</span></div>
                <div>Assigned: <span className="text-slate-300">{exc.assigned_to_name || 'Procurement Mgr'}</span></div>
                <div>Logged: <span className="text-slate-400">{exc.created_at.split('T')[0]}</span></div>
              </div>

              {exc.resolution_reason && (
                <div className="bg-emerald-950/30 p-2.5 rounded-xl border border-emerald-900/50 text-[11px] text-emerald-300 space-y-1">
                  <span className="font-semibold uppercase tracking-wider text-[10px]">Resolution Justification:</span>
                  <div>{exc.resolution_reason}</div>
                </div>
              )}

              <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
                <button
                  onClick={() => onSelectInvoice(exc.invoice_id)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center space-x-1"
                >
                  <span>Inspect 3-Way Match</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                {exc.status === 'OPEN' && (
                  <button
                    onClick={() => {
                      setSelectedException(exc);
                      setResolutionAction('RESOLVE');
                      setResolutionReason('Vendor submitted authorized credit note.');
                    }}
                    className="px-3.5 py-1.5 bg-emerald-600/90 hover:bg-emerald-600 text-white text-xs font-semibold rounded-xl shadow-sm transition"
                  >
                    Resolve / Waive
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Resolve / Waive Exception */}
      {selectedException && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>Resolve Control Exception</span>
              </h3>
              <button
                onClick={() => setSelectedException(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleResolveSubmit} className="space-y-4 text-xs">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                <div className="font-mono text-[11px] text-indigo-400">{selectedException.exception_code}</div>
                <div className="font-bold text-slate-100">{selectedException.title}</div>
                <div className="text-slate-400 text-[11px]">Invoice: {selectedException.invoice_number}</div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Resolution Action</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setResolutionAction('RESOLVE')}
                    className={`py-2 px-3 rounded-xl font-medium transition ${
                      resolutionAction === 'RESOLVE'
                        ? 'bg-emerald-600 text-white font-semibold'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    RESOLVE (Fixed)
                  </button>
                  <button
                    type="button"
                    onClick={() => setResolutionAction('WAIVE')}
                    className={`py-2 px-3 rounded-xl font-medium transition ${
                      resolutionAction === 'WAIVE'
                        ? 'bg-amber-600 text-white font-semibold'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    WAIVE (Tolerated)
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  Mandatory Audit Justification Reason *
                </label>
                <textarea
                  rows={3}
                  value={resolutionReason}
                  onChange={(e) => setResolutionReason(e.target.value)}
                  placeholder="Explain why this exception is resolved or waived (e.g. credit note number, approved receiving memo)..."
                  required
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-white text-xs focus:outline-none focus:border-indigo-500"
                />
                <p className="text-[10px] text-slate-400 mt-1">
                  This justification will be permanently written to the immutable audit trail.
                </p>
              </div>

              <div className="pt-2 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setSelectedException(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resolving}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-lg shadow-emerald-600/20"
                >
                  {resolving ? 'Recording Resolution...' : 'Commit Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
