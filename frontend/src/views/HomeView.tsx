import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  ArrowRight,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  TrendingUp,
  FileText,
  CreditCard,
  AlertTriangle,
  Building2,
  Receipt,
  Layers,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import type { DashboardKPIs, APException, Approval, DashboardControlHealth, DashboardRiskOverview } from '../types';
import { formatCurrency, formatDate } from '../utils/format';
import { exceptionWhatHappened } from '../utils/labels';
import { humanExceptionCode } from '../utils/format';
import type { NavTab } from '../components/Sidebar';

interface HomeViewProps {
  onNavigateTab: (tab: NavTab) => void;
  onSelectInvoice: (invoiceId: string) => void;
  activeEmail: string;
}

export const HomeView: React.FC<HomeViewProps> = ({ onNavigateTab, onSelectInvoice, activeEmail }) => {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [controlHealth, setControlHealth] = useState<DashboardControlHealth | null>(null);
  const [riskOverview, setRiskOverview] = useState<DashboardRiskOverview | null>(null);
  const [exceptions, setExceptions] = useState<APException[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [visibleExceptionsCount, setVisibleExceptionsCount] = useState<number>(0);
  const [visibleApprovalsCount, setVisibleApprovalsCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [kpisData, excData, appData, healthData, riskData] = await Promise.all([
          api.getDashboardKPIs(),
          api.listExceptions({ status: 'OPEN' }),
          api.listApprovals({ status: 'PENDING' }),
          api.getDashboardControlHealth().catch(() => null),
          api.getDashboardRiskOverview().catch(() => null),
        ]);
        setKpis(kpisData);
        setExceptions(excData.slice(0, 3));
        setApprovals(appData.slice(0, 3));
        setVisibleExceptionsCount(excData.length);
        setVisibleApprovalsCount(appData.length);
        setControlHealth(healthData);
        setRiskOverview(riskData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [activeEmail]);

  const atRiskCount = (riskOverview?.critical_count || 0) + (riskOverview?.high_count || 0);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* 1. Header Banner */}
      <div className="pt-2 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-brand-50 text-brand-700 border border-brand-200">
              Executive AP Intelligence
            </span>
            <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Live Verification
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">
            Accounts Payable Control Center
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Know what can be paid, what needs attention, and why.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigateTab('simulator')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white text-xs font-semibold rounded-xl transition-all shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Open AP Simulator
          </button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-100 rounded-2xl animate-pulse" />
            ))}
          </div>
          <div className="h-44 bg-gray-100 rounded-2xl animate-pulse" />
          <div className="h-44 bg-gray-100 rounded-2xl animate-pulse" />
        </div>
      ) : (
        <>
          {/* 2. Primary 6 KPI Cards (All Clickable) */}
          {kpis && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {/* 1. Total Invoices */}
              <div
                onClick={() => onNavigateTab('invoices')}
                className="bg-white rounded-2xl border border-gray-100 p-4 shadow-card hover:shadow-card-hover transition-all cursor-pointer group"
              >
                <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Invoices</div>
                <div className="text-2xl font-extrabold text-gray-900 mt-1">{kpis.total_invoices}</div>
                <div className="text-[10px] text-gray-400 mt-1 flex items-center gap-1 group-hover:text-blue-600 transition-colors">
                  View all <ArrowRight className="w-3 h-3" />
                </div>
              </div>

              {/* 2. Needs Attention */}
              <div
                onClick={() => onNavigateTab('attention')}
                className={`bg-white rounded-2xl border p-4 shadow-card hover:shadow-card-hover transition-all cursor-pointer group ${
                  visibleExceptionsCount > 0 ? 'border-amber-200 bg-amber-50/50' : 'border-gray-100'
                }`}
              >
                <div className="text-[11px] font-bold text-amber-800 uppercase tracking-wider">Needs Attention</div>
                <div className="text-2xl font-extrabold text-amber-900 mt-1">{visibleExceptionsCount}</div>
                <div className="text-[10px] text-amber-700 mt-1 flex items-center gap-1 font-medium">
                  {visibleExceptionsCount > 0 ? 'Action required' : 'All clear'} <ArrowRight className="w-3 h-3" />
                </div>
              </div>

              {/* 3. Awaiting Approval */}
              <div
                onClick={() => onNavigateTab('approvals')}
                className={`bg-white rounded-2xl border p-4 shadow-card hover:shadow-card-hover transition-all cursor-pointer group ${
                  visibleApprovalsCount > 0 ? 'border-blue-200 bg-blue-50/50' : 'border-gray-100'
                }`}
              >
                <div className="text-[11px] font-bold text-blue-800 uppercase tracking-wider">Awaiting Approval</div>
                <div className="text-2xl font-extrabold text-blue-900 mt-1">{visibleApprovalsCount}</div>
                <div className="text-[10px] text-blue-700 mt-1 flex items-center gap-1 font-medium">
                  {visibleApprovalsCount > 0 ? 'Sign off now' : 'Queue clear'} <ArrowRight className="w-3 h-3" />
                </div>
              </div>

              {/* 4. Approved for Payment */}
              <div
                onClick={() => onNavigateTab('payments')}
                className="bg-white rounded-2xl border border-gray-100 p-4 shadow-card hover:shadow-card-hover transition-all cursor-pointer group"
              >
                <div className="text-[11px] font-bold text-indigo-700 uppercase tracking-wider truncate" title="Approved for Payment">
                  Approved
                </div>
                <div className="text-2xl font-extrabold text-indigo-900 mt-1">{kpis.payable_created}</div>
                <div className="text-[10px] text-indigo-600 mt-1 flex items-center gap-1 group-hover:text-indigo-800 transition-colors">
                  Ready to pay <ArrowRight className="w-3 h-3" />
                </div>
              </div>

              {/* 5. Paid */}
              <div
                onClick={() => onNavigateTab('payments')}
                className="bg-white rounded-2xl border border-gray-100 p-4 shadow-card hover:shadow-card-hover transition-all cursor-pointer group"
              >
                <div className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Paid</div>
                <div className="text-2xl font-extrabold text-emerald-800 mt-1">{kpis.paid_invoices}</div>
                <div className="text-[10px] text-emerald-600 mt-1 flex items-center gap-1">
                  {formatCurrency(kpis.total_disbursed_amount)}
                </div>
              </div>

              {/* 6. At Risk */}
              <div
                onClick={() => onNavigateTab('invoices')}
                className={`bg-white rounded-2xl border p-4 shadow-card hover:shadow-card-hover transition-all cursor-pointer group ${
                  atRiskCount > 0 ? 'border-red-200 bg-red-50/50' : 'border-gray-100'
                }`}
              >
                <div className="text-[11px] font-bold text-red-800 uppercase tracking-wider">At Risk</div>
                <div className="text-2xl font-extrabold text-red-900 mt-1">{atRiskCount}</div>
                <div className="text-[10px] text-red-700 mt-1 font-semibold flex items-center gap-1">
                  High/Critical <ArrowRight className="w-3 h-3" />
                </div>
              </div>
            </div>
          )}

          {/* 3. Executive Control Overview (Section 4) */}
          {controlHealth && (
            <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-card space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4">
                <div>
                  <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-indigo-600" />
                    Control Overview
                  </h2>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Deterministic verification status across all {controlHealth.total_checks_evaluated} automated checks evaluated.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-green-50 text-green-800 border border-green-200 rounded-xl text-xs font-bold">
                    {controlHealth.overall_pass_rate_percentage}% Overall Pass Rate
                  </span>
                </div>
              </div>

              {/* 6 Control Category Tiles */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {controlHealth.categories.map(cat => {
                  const hasIssues = cat.failed_count > 0;
                  return (
                    <div
                      key={cat.category}
                      onClick={() => onNavigateTab('attention')}
                      className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                        hasIssues
                          ? 'bg-amber-50/50 border-amber-200 hover:border-amber-300'
                          : 'bg-gray-50 border-gray-100 hover:border-gray-200'
                      }`}
                    >
                      <div>
                        <div className="text-xs font-bold text-gray-800 truncate" title={cat.name}>
                          {cat.name.replace(/ Integrity| Prevention| & Tax| & Fraud Signals/, '')}
                        </div>
                        <div className="text-xl font-extrabold text-gray-900 mt-1">
                          {cat.pass_rate_percentage}%
                        </div>
                      </div>

                      <div className="mt-2.5 pt-2 border-t border-gray-200/50 text-[10px] space-y-0.5">
                        <div className="flex justify-between text-gray-500">
                          <span>Evaluated:</span>
                          <span className="font-semibold text-gray-700">{cat.total_checks}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Issues:</span>
                          <span className={`font-bold ${hasIssues ? 'text-red-700' : 'text-emerald-700'}`}>
                            {cat.failed_count}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 4. Risk Overview & Top Risk Drivers (Section 5) */}
          {riskOverview && (
            <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-card space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4">
                <div>
                  <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-indigo-600" />
                    Risk Overview
                  </h2>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Deterministic risk scores and active risk drivers across {riskOverview.total_evaluated} evaluated invoices.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-indigo-50 text-indigo-800 border border-indigo-200 rounded-xl text-xs font-bold">
                    Avg Risk Score: {riskOverview.average_risk_score} / 100
                  </span>
                </div>
              </div>

              {/* 4 Risk Distribution Tiles (Clickable) */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div
                  onClick={() => onNavigateTab('attention')}
                  className="bg-red-50/70 border border-red-200/80 rounded-xl p-3.5 flex flex-col justify-between cursor-pointer hover:border-red-300 transition-all shadow-xs"
                >
                  <div className="text-[11px] font-bold text-red-800 uppercase tracking-wider">Critical</div>
                  <div className="text-2xl font-black text-red-900 mt-1">{riskOverview.critical_count}</div>
                  <div className="text-[10px] text-red-700 mt-1 font-medium">Score &ge; 75 (Immediate block)</div>
                </div>

                <div
                  onClick={() => onNavigateTab('attention')}
                  className="bg-orange-50/70 border border-orange-200/80 rounded-xl p-3.5 flex flex-col justify-between cursor-pointer hover:border-orange-300 transition-all shadow-xs"
                >
                  <div className="text-[11px] font-bold text-orange-800 uppercase tracking-wider">High</div>
                  <div className="text-2xl font-black text-orange-900 mt-1">{riskOverview.high_count}</div>
                  <div className="text-[10px] text-orange-700 mt-1 font-medium">Score 50–74 (Elevated risk)</div>
                </div>

                <div
                  onClick={() => onNavigateTab('invoices')}
                  className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5 flex flex-col justify-between cursor-pointer hover:border-amber-300 transition-all shadow-xs"
                >
                  <div className="text-[11px] font-bold text-amber-800 uppercase tracking-wider">Medium</div>
                  <div className="text-2xl font-black text-amber-900 mt-1">{riskOverview.medium_count}</div>
                  <div className="text-[10px] text-amber-700 mt-1 font-medium">Score 25–49 (Warnings)</div>
                </div>

                <div
                  onClick={() => onNavigateTab('invoices')}
                  className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-3.5 flex flex-col justify-between cursor-pointer hover:border-emerald-300 transition-all shadow-xs"
                >
                  <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">Low</div>
                  <div className="text-2xl font-black text-emerald-900 mt-1">{riskOverview.low_count}</div>
                  <div className="text-[10px] text-emerald-700 mt-1 font-medium">Score 0–24 (Normal tolerance)</div>
                </div>
              </div>

              {/* Two Column Grid: Top Risk Drivers & Highest Risk Invoices (All Clickable) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                {/* Left: Top Risk Drivers */}
                <div className="bg-gray-50/80 border border-gray-100 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-800 flex items-center gap-1.5 uppercase tracking-wide">
                      <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                      Top Risk Drivers
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">By Frequency</span>
                  </div>

                  {riskOverview.top_risk_drivers.length === 0 ? (
                    <div className="text-xs text-gray-500 py-4 text-center">No active risk drivers detected.</div>
                  ) : (
                    <div className="space-y-2.5">
                      {riskOverview.top_risk_drivers.map(driver => (
                        <div
                          key={driver.driver_code}
                          onClick={() => onNavigateTab('attention')}
                          className="space-y-1 p-2 rounded-lg hover:bg-white transition-colors cursor-pointer"
                        >
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-semibold text-gray-800 truncate" title={driver.title}>
                              {driver.title}
                            </span>
                            <span className="font-mono text-gray-500 text-[11px] flex-shrink-0 ml-2">
                              {driver.invoice_count} inv ({driver.percentage}%)
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-indigo-600 h-full rounded-full"
                              style={{ width: `${Math.min(driver.percentage, 100)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right: Highest Risk Invoices */}
                <div className="bg-gray-50/80 border border-gray-100 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-800 flex items-center gap-1.5 uppercase tracking-wide">
                      <ShieldAlert className="w-3.5 h-3.5 text-red-600" />
                      Highest Risk Invoices
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">Action Required</span>
                  </div>

                  {riskOverview.highest_risk_invoices.length === 0 ? (
                    <div className="text-xs text-gray-500 py-4 text-center">Zero high-risk invoices currently open.</div>
                  ) : (
                    <div className="space-y-2">
                      {riskOverview.highest_risk_invoices.slice(0, 4).map(inv => {
                        const scoreBadge =
                          inv.risk_level === 'CRITICAL'
                            ? 'bg-red-100 text-red-800 border-red-200'
                            : inv.risk_level === 'HIGH'
                            ? 'bg-orange-100 text-orange-800 border-orange-200'
                            : 'bg-amber-100 text-amber-800 border-amber-200';

                        return (
                          <div
                            key={inv.invoice_id}
                            className="bg-white p-2.5 rounded-lg border border-gray-200 flex items-center justify-between gap-2 hover:border-gray-300 transition-colors"
                          >
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-xs text-gray-900 truncate">
                                  {inv.invoice_number}
                                </span>
                                <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full border ${scoreBadge}`}>
                                  {inv.risk_score} pts · {inv.risk_level}
                                </span>
                              </div>
                              <div className="text-[11px] text-gray-500 truncate mt-0.5">
                                {inv.vendor_name} · {formatCurrency(inv.grand_total)}
                              </div>
                            </div>

                            <button
                              type="button"
                              onClick={() => onSelectInvoice(inv.invoice_id)}
                              className="px-2.5 py-1 text-[11px] font-semibold text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors flex-shrink-0"
                            >
                              Inspect
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 5. Needs Attention Preview */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Needs your attention</h2>
                <p className="text-xs text-gray-500 mt-0.5">Invoices with issues that must be resolved before payment.</p>
              </div>
              {exceptions.length > 0 && (
                <button
                  onClick={() => onNavigateTab('attention')}
                  className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
                >
                  See all {visibleExceptionsCount} <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {exceptions.length === 0 ? (
              <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-card flex items-center gap-4">
                <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <div className="font-semibold text-gray-800 text-sm">All clear</div>
                  <div className="text-xs text-gray-500 mt-0.5">No invoices currently need your attention.</div>
                </div>
              </div>
            ) : (
              <div className="space-y-2.5">
                {exceptions.map(exc => (
                  <div
                    key={exc.id}
                    className="bg-white rounded-2xl border border-amber-100 shadow-card p-4 flex items-start justify-between gap-4"
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 border border-amber-200/60">
                        <AlertCircle className="w-4 h-4 text-amber-600" />
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold text-gray-900 text-sm">{exc.vendor_name || 'Unknown Vendor'}</div>
                        <div className="text-xs text-gray-500">
                          {exc.invoice_number} · <span className="text-amber-700 font-semibold">{humanExceptionCode(exc.exception_code)}</span>
                        </div>
                        <div className="text-xs text-gray-600 mt-1">{exceptionWhatHappened(exc.exception_code)}</div>
                      </div>
                    </div>
                    <button
                      onClick={() => onSelectInvoice(exc.invoice_id)}
                      className="flex-shrink-0 flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 whitespace-nowrap bg-blue-50/60 px-3 py-1.5 rounded-lg border border-blue-100"
                    >
                      Review <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 6. Waiting for Approval Preview */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Waiting for your approval</h2>
                <p className="text-xs text-gray-500 mt-0.5">Invoices that have passed all checks and need your sign-off.</p>
              </div>
              {approvals.length > 0 && (
                <button
                  onClick={() => onNavigateTab('approvals')}
                  className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
                >
                  See all {visibleApprovalsCount} <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {approvals.length === 0 ? (
              <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-card flex items-center gap-4">
                <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Clock className="w-5 h-5 text-gray-400" />
                </div>
                <div>
                  <div className="font-semibold text-gray-800 text-sm">Nothing waiting for approval</div>
                  <div className="text-xs text-gray-500 mt-0.5">All invoices within your authority have been signed off.</div>
                </div>
              </div>
            ) : (
              <div className="space-y-2.5">
                {approvals.map(appr => (
                  <div
                    key={appr.id}
                    className="bg-white rounded-2xl border border-blue-100 shadow-card p-4 flex items-start justify-between gap-4"
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 border border-blue-200/60">
                        <CheckCircle className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold text-gray-900 text-sm">{appr.vendor_name || 'Unknown Vendor'}</div>
                        <div className="text-xs text-gray-500">{appr.invoice_number} · {appr.policy_name}</div>
                        <div className="text-base font-bold text-gray-900 mt-0.5">{formatCurrency(appr.invoice_amount)}</div>
                      </div>
                    </div>
                    <button
                      onClick={() => onNavigateTab('approvals')}
                      className="flex-shrink-0 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition-colors whitespace-nowrap shadow-xs"
                    >
                      Review &amp; approve
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

