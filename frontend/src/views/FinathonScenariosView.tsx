import React, { useState, useEffect } from 'react';
import { Search, AlertTriangle, ShieldAlert, FlaskConical } from 'lucide-react';
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
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
              <FlaskConical className="w-4 h-4 text-indigo-600" />
            </div>
            <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">Finathon Demo</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Scenarios A – O</h1>
          <p className="text-gray-500 mt-1">
            15 deliberate test scenarios covering 3-way matching, fraud detection, duplicates, arithmetic validation, and approval workflows.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-100">
            {scenarios.length} scenarios
          </span>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
            <input type="text" placeholder="Filter scenarios..." value={filter} onChange={e => setFilter(e.target.value)}
              className="pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full" />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-gray-400">Loading scenarios...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100 text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Scenario</th>
                  <th className="py-3 px-4">Invoice #</th>
                  <th className="py-3 px-4">Vendor</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4">Flags</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map(sc => {
                  const sc_colors = getStatusColor(sc.current_status);
                  return (
                    <tr key={sc.scenario_code} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-mono font-bold text-indigo-600 text-sm">{sc.scenario_code}</span>
                      </td>
                      <td className="py-3 px-4 max-w-xs">
                        <div className="font-medium text-gray-800 text-sm">{sc.scenario_name}</div>
                        <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">{sc.summary}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-mono text-xs text-gray-600">{sc.invoice_number}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-sm text-gray-700">{sc.vendor_name}</span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="font-mono font-semibold text-gray-800 text-sm">{formatCurrency(sc.grand_total)}</span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${sc_colors.bg} ${sc_colors.text}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${sc_colors.dot}`} />
                          {humanStatus(sc.current_status)}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          {sc.has_exceptions && (
                            <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-100">
                              <AlertTriangle className="w-3 h-3" /> Issue
                            </span>
                          )}
                          {sc.has_risk_signals && (
                            <span className="flex items-center gap-1 text-xs text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full border border-orange-100">
                              <ShieldAlert className="w-3 h-3" /> Risk
                            </span>
                          )}
                          {!sc.has_exceptions && !sc.has_risk_signals && (
                            <span className="text-xs text-green-600 font-medium">Clean</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button onClick={() => onSelectInvoice(sc.invoice_id)}
                          className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-lg border border-indigo-100 transition-colors">
                          Inspect
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
