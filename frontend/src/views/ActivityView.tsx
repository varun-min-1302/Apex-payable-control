import React, { useState, useEffect } from 'react';
import {
  Activity,
  ChevronDown,
  ChevronRight,
  User,
  ShieldCheck,
  ShieldAlert,
  CreditCard,
  FileText,
  Clock,
  CheckCircle,
  AlertTriangle,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import type { AuditLog } from '../types';
import { formatDateTime } from '../utils/format';

export const ActivityView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState<string>('ALL');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await api.listAuditLogs({
          entity_type: entityFilter === 'ALL' ? undefined : entityFilter,
          limit: 100
        });
        setLogs(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [entityFilter]);

  function humanAction(action: string, entityType: string): string {
    if (action.includes('PAYABLE_CREATED')) return 'Invoice approved for payment';
    if (action.includes('APPROVED')) return 'Invoice approved by manager';
    if (action.includes('REJECTED')) return 'Invoice rejected';
    if (action.includes('EXCEPTION_RESOLVED')) return 'Discrepancy resolved';
    if (action.includes('EXCEPTION')) return 'Discrepancy / Exception flagged';
    if (action.includes('CONTROL_RUN') || action.includes('EVALUAT')) return '18 automated controls evaluated';
    if (action.includes('PAYMENT') || action.includes('DISBURSE')) return 'Disbursement recorded to ledger';
    if (action.includes('INVOICE_CREATED') || action.includes('INTAKE')) return 'Invoice document ingested';
    if (action.includes('EXTRACTION') || action.includes('AI')) return 'Gemini AI document extraction';
    if (action.includes('STATUS_CHANGED')) return `${entityType} status updated`;
    return action.replace(/_/g, ' ').toLowerCase().replace(/^./, c => c.toUpperCase());
  }

  function getActionBadge(action: string) {
    if (action.includes('PAYABLE_CREATED') || action.includes('APPROVED')) {
      return { dot: 'bg-emerald-500', icon: CheckCircle, className: 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10' };
    }
    if (action.includes('REJECTED') || action.includes('EXCEPTION')) {
      return { dot: 'bg-amber-500', icon: AlertTriangle, className: 'text-amber-600 dark:text-amber-400 bg-amber-500/10' };
    }
    if (action.includes('PAYMENT') || action.includes('DISBURSE')) {
      return { dot: 'bg-blue-500', icon: CreditCard, className: 'text-blue-600 dark:text-blue-400 bg-blue-500/10' };
    }
    if (action.includes('CONTROL') || action.includes('EVALUAT')) {
      return { dot: 'bg-indigo-500', icon: ShieldCheck, className: 'text-indigo-600 dark:text-indigo-400 bg-indigo-500/10' };
    }
    if (action.includes('EXTRACTION') || action.includes('AI')) {
      return { dot: 'bg-purple-500', icon: Sparkles, className: 'text-purple-600 dark:text-purple-400 bg-purple-500/10' };
    }
    return { dot: 'bg-muted-foreground', icon: FileText, className: 'text-muted-foreground bg-muted' };
  }

  const entityTypes = [
    { type: 'ALL', label: 'All Activity' },
    { type: 'INVOICE', label: 'Invoices' },
    { type: 'APPROVAL', label: 'Approvals' },
    { type: 'PAYABLE_LEDGER', label: 'Payments' },
    { type: 'EXCEPTION', label: 'Exceptions' },
    { type: 'PAYMENT', label: 'Disbursements' },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            Activity
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Every important invoice, control, approval, and payment action recorded on the immutable audit trail.
          </p>
        </div>

        {/* Entity Filter Pills */}
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-full border border-border/60 self-start sm:self-auto overflow-x-auto">
          {entityTypes.map(item => (
            <button
              key={item.type}
              onClick={() => setEntityFilter(item.type)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap ${
                entityFilter === item.type
                  ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Timeline List */}
      <div className="bg-card text-card-foreground rounded-[22px] border border-border/80 shadow-card overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />
            ))}
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground text-xs space-y-2">
            <Activity className="w-8 h-8 text-muted-foreground/60 mx-auto" />
            <p className="font-semibold text-foreground">No audit activity found</p>
            <p>Try switching to another entity filter.</p>
          </div>
        ) : (
          <div className="divide-y divide-border/60">
            {logs.map(log => {
              const isExpanded = expandedId === log.id;
              const badge = getActionBadge(log.action);
              const Icon = badge.icon;

              return (
                <div key={log.id} className="transition-colors">
                  <div
                    className="p-4 sm:p-5 flex items-center gap-3.5 hover:bg-muted/30 cursor-pointer"
                    onClick={() => setExpandedId(isExpanded ? null : log.id)}
                  >
                    {/* Event Icon Circle */}
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${badge.className}`}>
                      <Icon className="w-4 h-4" />
                    </div>

                    {/* Event Title & Metadata */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-foreground text-xs sm:text-sm">
                          {humanAction(log.action, log.entity_type)}
                        </span>
                        <span className="text-[10px] font-mono font-bold text-muted-foreground bg-muted/60 px-2 py-0.5 rounded-md">
                          {log.entity_type}
                        </span>
                      </div>

                      <div className="text-xs text-muted-foreground mt-0.5 flex items-center gap-3">
                        {log.actor_name && (
                          <span className="flex items-center gap-1 font-medium text-foreground">
                            <User className="w-3 h-3 text-muted-foreground" />
                            {log.actor_name}
                          </span>
                        )}
                        <span>{formatDateTime(log.created_at)}</span>
                      </div>
                    </div>

                    {/* Chevron to expand */}
                    <button className="p-1 text-muted-foreground hover:text-foreground">
                      {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Expandable Technical Audit Proof Diff */}
                  {isExpanded && (
                    <div className="px-5 pb-5 pt-2 bg-muted/20 border-t border-border/60 space-y-3">
                      <div className="text-[11px] font-mono text-muted-foreground flex flex-wrap gap-x-4 gap-y-1">
                        <span><strong className="text-foreground">Action:</strong> {log.action}</span>
                        <span><strong className="text-foreground">Target ID:</strong> {log.entity_id}</span>
                        {log.correlation_id && (
                          <span><strong className="text-foreground">Correlation:</strong> {log.correlation_id}</span>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                        <div className="bg-card p-3 rounded-xl border border-border/80">
                          <div className="text-[10px] font-bold text-muted-foreground uppercase mb-1">
                            Previous State
                          </div>
                          <pre className="text-[11px] text-muted-foreground overflow-x-auto whitespace-pre-wrap break-all max-h-48">
                            {log.previous_state ? JSON.stringify(log.previous_state, null, 2) : 'null (Initial Record Creation)'}
                          </pre>
                        </div>

                        <div className="bg-card p-3 rounded-xl border border-border/80">
                          <div className="text-[10px] font-bold text-primary uppercase mb-1">
                            New State
                          </div>
                          <pre className="text-[11px] text-foreground overflow-x-auto whitespace-pre-wrap break-all max-h-48">
                            {log.new_state ? JSON.stringify(log.new_state, null, 2) : 'null'}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
};
