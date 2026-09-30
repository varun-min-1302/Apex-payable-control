import React, { useState, useEffect } from 'react';
import { Activity, ChevronDown, ChevronRight, User } from 'lucide-react';
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
        const data = await api.listAuditLogs({ entity_type: entityFilter === 'ALL' ? undefined : entityFilter, limit: 100 });
        setLogs(data);
      } catch (err) { console.error(err); } finally { setLoading(false); }
    };
    load();
  }, [entityFilter]);

  function humanAction(action: string, entityType: string): string {
    if (action.includes('PAYABLE_CREATED')) return 'Invoice approved for payment';
    if (action.includes('APPROVED')) return 'Invoice approved';
    if (action.includes('REJECTED')) return 'Invoice rejected';
    if (action.includes('EXCEPTION_RESOLVED')) return 'Issue resolved';
    if (action.includes('EXCEPTION')) return 'Issue flagged';
    if (action.includes('CONTROL_RUN') || action.includes('EVALUAT')) return 'Automated checks completed';
    if (action.includes('PAYMENT') || action.includes('DISBURSE')) return 'Payment recorded';
    if (action.includes('INVOICE_CREATED')) return 'Invoice received';
    if (action.includes('STATUS_CHANGED')) return `${entityType} status updated`;
    return action.replace(/_/g, ' ').toLowerCase().replace(/^./, c => c.toUpperCase());
  }

  function getActionDot(action: string): string {
    if (action.includes('PAYABLE_CREATED') || action.includes('APPROVED')) return 'bg-green-500';
    if (action.includes('REJECTED') || action.includes('EXCEPTION')) return 'bg-amber-500';
    if (action.includes('PAYMENT') || action.includes('DISBURSE')) return 'bg-blue-500';
    if (action.includes('RUN') || action.includes('EVALUAT')) return 'bg-cyan-500';
    return 'bg-gray-400';
  }

  const entityTypes = ['ALL', 'INVOICE', 'APPROVAL', 'PAYABLE_LEDGER', 'EXCEPTION', 'PAYMENT'];
  const entityLabels: Record<string, string> = { ALL: 'All activity', INVOICE: 'Invoices', APPROVAL: 'Approvals', PAYABLE_LEDGER: 'Payments', EXCEPTION: 'Issues', PAYMENT: 'Disbursements' };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Activity</h1>
          <p className="text-gray-500 mt-1">A record of everything that has happened on this platform.</p>
        </div>
      </div>

      <div className="flex items-center gap-1 bg-white border border-gray-200 rounded-xl p-1 shadow-card overflow-x-auto">
        {entityTypes.map(type => (
          <button key={type} onClick={() => setEntityFilter(type)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
              entityFilter === type ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-800'
            }`}>
            {entityLabels[type] || type}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-2">{[...Array(8)].map((_, i) => <div key={i} className="h-14 bg-gray-100 rounded-xl animate-pulse" />)}</div>
      ) : logs.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-12 text-center">
          <Activity className="w-8 h-8 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No activity found for this filter.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card divide-y divide-gray-100">
          {logs.map(log => {
            const isExpanded = expandedId === log.id;
            return (
              <div key={log.id}>
                <div
                  className="px-5 py-4 flex items-center gap-4 hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => setExpandedId(isExpanded ? null : log.id)}
                >
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${getActionDot(log.action)}`} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900">{humanAction(log.action, log.entity_type)}</div>
                    <div className="text-sm text-gray-400 mt-0.5 flex items-center gap-2">
                      {log.actor_name && <span className="flex items-center gap-1"><User className="w-3 h-3" />{log.actor_name}</span>}
                      <span>{formatDateTime(log.created_at)}</span>
                    </div>
                  </div>
                  <button className="text-gray-400 flex-shrink-0">
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                </div>
                {isExpanded && (
                  <div className="px-5 pb-4 bg-gray-50 border-t border-gray-100">
                    <details className="mt-3">
                      <summary className="text-xs font-semibold text-gray-400 uppercase tracking-wide cursor-pointer hover:text-gray-600">Technical details</summary>
                      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="bg-white rounded-xl border border-gray-200 p-3">
                          <div className="text-xs font-mono font-bold text-gray-400 mb-2 uppercase">Previous state</div>
                          <pre className="text-xs font-mono text-gray-600 overflow-x-auto whitespace-pre-wrap break-all">
                            {log.previous_state ? JSON.stringify(log.previous_state, null, 2) : 'null (initial creation)'}
                          </pre>
                        </div>
                        <div className="bg-white rounded-xl border border-gray-200 p-3">
                          <div className="text-xs font-mono font-bold text-blue-500 mb-2 uppercase">New state</div>
                          <pre className="text-xs font-mono text-gray-600 overflow-x-auto whitespace-pre-wrap break-all">
                            {log.new_state ? JSON.stringify(log.new_state, null, 2) : 'null'}
                          </pre>
                        </div>
                      </div>
                      <div className="mt-2 text-xs font-mono text-gray-400">
                        <span className="font-semibold">Action:</span> {log.action} ·
                        <span className="font-semibold ml-2">Entity:</span> {log.entity_type} ·
                        <span className="font-semibold ml-2">ID:</span> {log.entity_id}
                        {log.correlation_id && <><span className="font-semibold ml-2">Correlation:</span> {log.correlation_id}</>}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
