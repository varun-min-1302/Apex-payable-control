import React, { useState, useEffect } from 'react';
import { Search, AlertTriangle, ShieldAlert, FlaskConical, ChevronRight } from 'lucide-react';
import { api } from '../api/client';
import type { ScenarioItem } from '../types';
import { formatCurrency, humanStatus, getStatusColor } from '../utils/format';

interface FinathonScenariosViewProps {
  onSelectInvoice: (invoiceId: string) => void;
}

export const FinathonScenariosView: React.FC<FinathonScenariosViewProps> = ({ onSelectInvoice }) => {
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    api.getScenarios()
      .then(data => { setScenarios(data.scenarios); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const filtered = scenarios.filter(s =>
    s.scenario_code.toLowerCase().includes(filter.toLowerCase()) ||
    s.scenario_name.toLowerCase().includes(filter.toLowerCase()) ||
    s.invoice_number.toLowerCase().includes(filter.toLowerCase()) ||
    s.vendor_name.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-primary/10 text-primary border border-primary/20">
              Deterministic Verification Matrix
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            Scenarios A through O
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            15 deliberate test scenarios covering 3-way matching, fraud detection, duplicate screening, and approval workflows.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20">
            {scenarios.length} Scenarios Loaded
          </span>
        </div>
      </div>

      <div className="bg-card text-card-foreground rounded-[22px] border border-border/80 shadow-card overflow-hidden">
        <div className="p-4 border-b border-border/60 flex items-center justify-between gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter scenarios by code or title..."
              value={filter}
              onChange={e => setFilter(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-muted/50 border border-border rounded-xl text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary w-full"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-muted-foreground text-xs">Loading scenarios matrix...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-muted/30 border-b border-border/60 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Scenario Name</th>
                  <th className="py-3 px-4">Invoice #</th>
                  <th className="py-3 px-4">Vendor</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Flags</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filtered.map(sc => {
                  const sc_colors = getStatusColor(sc.current_status);
                  return (
                    <tr key={sc.scenario_code} className="hover:bg-muted/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <span className="font-mono font-bold text-primary text-xs">{sc.scenario_code}</span>
                      </td>
                      <td className="py-3.5 px-4 max-w-xs">
                        <div className="font-semibold text-foreground text-xs">{sc.scenario_name}</div>
                        <div className="text-[11px] text-muted-foreground mt-0.5 line-clamp-1">{sc.summary}</div>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">
                        {sc.invoice_number}
                      </td>
                      <td className="py-3.5 px-4 text-foreground font-medium">
                        {sc.vendor_name}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-foreground">
                        {formatCurrency(sc.grand_total)}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium ${sc_colors.bg} ${sc_colors.text}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${sc_colors.dot}`} />
                          {humanStatus(sc.current_status)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <div className="flex items-center justify-center gap-1">
                          {sc.has_exceptions && (
                            <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full">
                              Issue
                            </span>
                          )}
                          {sc.has_risk_signals && (
                            <span className="text-[10px] font-bold text-orange-600 dark:text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded-full">
                              Risk
                            </span>
                          )}
                          {!sc.has_exceptions && !sc.has_risk_signals && (
                            <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                              Clean
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => onSelectInvoice(sc.invoice_id)}
                          className="px-2.5 py-1 text-primary hover:bg-primary/10 rounded-lg text-xs font-semibold transition-colors"
                        >
                          Inspect →
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
