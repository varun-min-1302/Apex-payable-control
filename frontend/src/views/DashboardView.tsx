import React, { useState, useEffect } from 'react';
import {
  FileText,
  Clock,
  AlertTriangle,
  Landmark,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  ShieldAlert,
  Search,
  CheckSquare
} from 'lucide-react';
import { api } from '../api/client';
import { DashboardKPIs, ScenarioItem } from '../types';
import { NavTab } from '../components/Sidebar';

interface DashboardViewProps {
  onNavigateTab: (tab: NavTab) => void;
  onSelectInvoice: (invoiceId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigateTab, onSelectInvoice }) => {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [scenarioFilter, setScenarioFilter] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [kpisData, scenariosData] = await Promise.all([
        api.getDashboardKPIs(),
        api.getScenarios(),
      ]);
      setKpis(kpisData);
      setScenarios(scenariosData.scenarios);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatCurrency = (val: string | number | undefined) => {
    if (val === undefined || val === null) return '₹0.00';
    const num = typeof val === 'string' ? parseFloat(val) : val;
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(num);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-400 dark:border-emerald-800">APPROVED</span>;
      case 'PAYABLE_CREATED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/80 dark:text-indigo-400 dark:border-indigo-800">PAYABLE CREATED</span>;
      case 'PAID':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-100 text-teal-700 border border-teal-200 dark:bg-teal-950/80 dark:text-teal-400 dark:border-teal-800">PAID</span>;
      case 'AWAITING_APPROVAL':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200 dark:bg-amber-950/80 dark:text-amber-400 dark:border-amber-800">AWAITING APPROVAL</span>;
      case 'EXCEPTION':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-700 border border-rose-200 dark:bg-rose-950/80 dark:text-rose-400 dark:border-rose-800">EXCEPTION</span>;
      case 'REJECTED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700">REJECTED</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700">{status}</span>;
    }
  };

  const filteredScenarios = scenarios.filter(s => 
    s.scenario_code.toLowerCase().includes(scenarioFilter.toLowerCase()) ||
    s.scenario_name.toLowerCase().includes(scenarioFilter.toLowerCase()) ||
    s.invoice_number.toLowerCase().includes(scenarioFilter.toLowerCase()) ||
    s.vendor_name.toLowerCase().includes(scenarioFilter.toLowerCase())
  );

  return (
    <div className="space-y-8">
      
      {/* Top Banner / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-gray-50 via-indigo-50/40 to-gray-50 dark:from-slate-900 dark:via-indigo-950/40 dark:to-slate-900 p-6 rounded-2xl border border-gray-200 dark:border-slate-800 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">Executive AP Control Center</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
            Real-time financial governance, deterministic 3-way matching, and exception authorization across 15 deliberate business scenarios.
          </p>
        </div>
        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => onNavigateTab('invoices')}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl shadow-lg shadow-indigo-600/20 transition flex items-center space-x-2"
          >
            <span>Ingest Invoice</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => onNavigateTab('approvals')}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-200 text-sm font-medium rounded-xl border border-gray-200 dark:border-slate-700 transition flex items-center space-x-2"
          >
            <CheckSquare className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Golden Tx Approvals</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        
        {/* Total Invoices */}
        <div className="bg-white dark:bg-slate-900/80 p-5 rounded-2xl border border-gray-200 dark:border-slate-800/90 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400">Total Invoices</span>
            <div className="p-2 rounded-xl bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-500/20">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-gray-900 dark:text-white font-mono">
            {kpis ? kpis.total_invoices : '—'}
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-slate-400">Master ingestion log</div>
        </div>

        {/* 3-Way Match Pass Rate */}
        <div className="bg-white dark:bg-slate-900/80 p-5 rounded-2xl border border-gray-200 dark:border-slate-800/90 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400">3-Way Match Rate</span>
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">
            {kpis ? `${kpis.three_way_match_pass_rate_percentage}%` : '—'}
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-slate-400">Automated pass rate</div>
        </div>

        {/* Awaiting Approval */}
        <div className="bg-white dark:bg-slate-900/80 p-5 rounded-2xl border border-gray-200 dark:border-slate-800/90 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400">Awaiting Sign-off</span>
            <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-100 dark:border-amber-500/20">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-amber-600 dark:text-amber-400 font-mono">
            {kpis ? kpis.awaiting_approval : '—'}
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-slate-400">Awaiting manager approval</div>
        </div>

        {/* Open Exceptions */}
        <div className="bg-white dark:bg-slate-900/80 p-5 rounded-2xl border border-gray-200 dark:border-slate-800/90 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400">Open Exceptions</span>
            <div className="p-2 rounded-xl bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-100 dark:border-rose-500/20">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-rose-600 dark:text-rose-400 font-mono">
            {kpis ? kpis.open_exceptions : '—'}
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-slate-400">Requires review / waiver</div>
        </div>

        {/* Total Payable Liability */}
        <div className="bg-white dark:bg-slate-900/80 p-5 rounded-2xl border border-gray-200 dark:border-slate-800/90 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400">Payable Liabilities</span>
            <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-500/20">
              <Landmark className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-xl font-bold text-indigo-700 dark:text-indigo-300 font-mono truncate">
            {kpis ? formatCurrency(kpis.total_payable_liability) : '—'}
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-slate-400">Committed general liability</div>
        </div>

        {/* Total Disbursed */}
        <div className="bg-white dark:bg-slate-900/80 p-5 rounded-2xl border border-gray-200 dark:border-slate-800/90 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400">Disbursed Funds</span>
            <div className="p-2 rounded-xl bg-teal-50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-100 dark:border-teal-500/20">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-xl font-bold text-teal-700 dark:text-teal-300 font-mono truncate">
            {kpis ? formatCurrency(kpis.total_disbursed_amount) : '—'}
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-slate-400">Completed payments</div>
        </div>

      </div>

      {/* Finathon Core Demo Matrix: Scenarios A through O */}
      <div className="bg-white dark:bg-slate-900/90 rounded-2xl border border-gray-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white tracking-tight">Finathon Control Evaluation Matrix</h2>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">
                15 Scenarios (A – O)
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
              Deliberate benchmark dataset testing 3-way matching, fraud flags, arithmetic accuracy, bank account hashing, duplicate checksums, and managerial approvals.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Filter scenarios..."
                value={scenarioFilter}
                onChange={(e) => setScenarioFilter(e.target.value)}
                className="pl-9 pr-4 py-1.5 bg-gray-50 dark:bg-slate-800/80 border border-gray-200 dark:border-slate-700 rounded-xl text-xs text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-400 focus:outline-none focus:border-indigo-500 w-60"
              />
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 dark:bg-slate-950/60 border-b border-gray-200 dark:border-slate-800 text-[11px] font-mono uppercase tracking-wider text-gray-500 dark:text-slate-400">
                <th className="py-3 px-4">Code</th>
                <th className="py-3 px-4">Scenario Name</th>
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Vendor</th>
                <th className="py-3 px-4 text-right">Grand Total</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4">Signals &amp; Exceptions</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-800/60 text-xs">
              {filteredScenarios.map((sc) => (
                <tr key={sc.scenario_code} className="hover:bg-gray-50 dark:hover:bg-slate-800/40 transition">
                  <td className="py-3.5 px-4 font-mono font-bold text-indigo-600 dark:text-indigo-400 whitespace-nowrap">
                    {sc.scenario_code}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-gray-800 dark:text-slate-200">{sc.scenario_name}</div>
                    <div className="text-[11px] text-gray-500 dark:text-slate-400 line-clamp-1 mt-0.5">{sc.summary}</div>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-gray-700 dark:text-slate-300 whitespace-nowrap">
                    {sc.invoice_number}
                  </td>
                  <td className="py-3.5 px-4 text-gray-700 dark:text-slate-300 font-medium whitespace-nowrap">
                    {sc.vendor_name}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-semibold text-gray-800 dark:text-slate-200 whitespace-nowrap">
                    {formatCurrency(sc.grand_total)}
                  </td>
                  <td className="py-3.5 px-4 text-center whitespace-nowrap">
                    {getStatusBadge(sc.current_status)}
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {sc.has_exceptions ? (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800/80">
                          <AlertTriangle className="w-3 h-3" />
                          <span>Exception</span>
                        </span>
                      ) : null}
                      {sc.has_risk_signals ? (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/80">
                          <ShieldAlert className="w-3 h-3" />
                          <span>Risk Signal</span>
                        </span>
                      ) : null}
                      {!sc.has_exceptions && !sc.has_risk_signals ? (
                        <span className="text-[11px] text-gray-400 dark:text-slate-400 font-mono">Clean Pass</span>
                      ) : null}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={() => onSelectInvoice(sc.invoice_id)}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs border border-indigo-500/40 transition shadow-sm"
                    >
                      Inspect 3-Way Match
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
