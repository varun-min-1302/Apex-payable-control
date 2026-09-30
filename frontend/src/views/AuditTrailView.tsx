import React, { useState, useEffect } from 'react';
import {
  History,
  ShieldCheck,
  Search,
  Filter,
  ChevronRight,
  ChevronDown,
  User,
  Database,
  Lock
} from 'lucide-react';
import { api } from '../api/client';
import { AuditLog } from '../types';

export const AuditTrailView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState<string>('ALL');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const data = await api.listAuditLogs({
        entity_type: entityFilter === 'ALL' ? undefined : entityFilter,
        limit: 100,
      });
      setLogs(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [entityFilter]);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getActionColor = (action: string) => {
    if (action.includes('PAYABLE_CREATED')) return 'text-indigo-400 bg-indigo-950/80 border-indigo-800';
    if (action.includes('APPROV')) return 'text-emerald-400 bg-emerald-950/80 border-emerald-800';
    if (action.includes('EXCEPTION')) return 'text-rose-400 bg-rose-950/80 border-rose-800';
    if (action.includes('RUN') || action.includes('EVALUAT')) return 'text-cyan-400 bg-cyan-950/80 border-cyan-800';
    if (action.includes('PAYMENT') || action.includes('DISBURSE')) return 'text-teal-400 bg-teal-950/80 border-teal-800';
    return 'text-slate-300 bg-slate-800 border-slate-700';
  };

  const entityTypes = ['ALL', 'INVOICE', 'APPROVAL', 'PAYABLE_LEDGER', 'EXCEPTION', 'PAYMENT'];

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Immutable Audit Trail Explorer</h1>
            <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-950/80 text-purple-300 border border-purple-800">
              <Lock className="w-3 h-3" />
              <span>Tamper-Proof Trigger Enforced</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Permanent, append-only compliance record. Protected at the PostgreSQL engine level by a trigger that raises an exception on any <code className="text-rose-400">UPDATE</code> or <code className="text-rose-400">DELETE</code> statement.
          </p>
        </div>

        {/* Entity Filter */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-2 md:pb-0 bg-slate-900 p-1.5 rounded-xl border border-slate-800 self-start">
          {entityTypes.map((type) => (
            <button
              key={type}
              onClick={() => setEntityFilter(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                entityFilter === type
                  ? 'bg-indigo-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading audit trail records...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No audit events found for selected entity type.</div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {logs.map((log) => {
              const isExpanded = expandedId === log.id;
              return (
                <div key={log.id} className="p-4 hover:bg-slate-800/30 transition text-xs space-y-3">
                  <div className="flex items-center justify-between cursor-pointer" onClick={() => toggleExpand(log.id)}>
                    <div className="flex items-center space-x-3">
                      <button className="text-slate-400 hover:text-white">
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </button>
                      <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-mono font-bold border ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                      <span className="font-mono text-slate-300 font-semibold">{log.entity_type}</span>
                      <span className="font-mono text-[11px] text-slate-400">{log.entity_id}</span>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-1.5 text-slate-300 font-medium">
                        <User className="w-3.5 h-3.5 text-indigo-400" />
                        <span>{log.actor_name || 'System Engine'}</span>
                      </div>
                      <span className="font-mono text-[11px] text-slate-400">
                        {log.created_at.replace('T', ' ').split('.')[0]}
                      </span>
                    </div>
                  </div>

                  {/* Expanded JSON State Diff */}
                  {isExpanded && (
                    <div className="mt-3 pl-7 grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800/60">
                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
                        <div className="text-[10px] uppercase font-mono font-bold text-slate-400 mb-1">Previous State</div>
                        <pre className="text-[11px] font-mono text-slate-300 overflow-x-auto">
                          {log.previous_state ? JSON.stringify(log.previous_state, null, 2) : 'null (Created)'}
                        </pre>
                      </div>

                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
                        <div className="text-[10px] uppercase font-mono font-bold text-indigo-400 mb-1">New State Commited</div>
                        <pre className="text-[11px] font-mono text-emerald-300 overflow-x-auto">
                          {log.new_state ? JSON.stringify(log.new_state, null, 2) : 'null'}
                        </pre>
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
