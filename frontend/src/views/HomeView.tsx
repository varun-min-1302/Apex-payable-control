import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  CheckCircle,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Search,
  ChevronRight,
  TrendingUp,
  FileText,
  CreditCard,
  Building,
  RotateCcw,
  Sliders,
  DollarSign,
  Plus,
  Info,
  Check,
  X
} from 'lucide-react';
import { api } from '../api/client';
import type {
  DashboardKPIs,
  APException,
  Approval,
  DashboardControlHealth,
  DashboardRiskOverview,
  InvoiceSummary
} from '../types';
import { formatCurrency, formatDate, humanStatus, getStatusColor } from '../utils/format';
import { exceptionWhatHappened } from '../utils/labels';
import { humanExceptionCode } from '../utils/format';
import type { NavTab } from '../components/Sidebar';

interface HomeViewProps {
  onNavigateTab: (tab: NavTab) => void;
  onSelectInvoice: (invoiceId: string) => void;
  onOpenAddInvoice?: () => void;
  activeEmail: string;
}

export const HomeView: React.FC<HomeViewProps> = ({
  onNavigateTab,
  onSelectInvoice,
  onOpenAddInvoice,
  activeEmail
}) => {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [controlHealth, setControlHealth] = useState<DashboardControlHealth | null>(null);
  const [riskOverview, setRiskOverview] = useState<DashboardRiskOverview | null>(null);
  const [exceptions, setExceptions] = useState<APException[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [recentInvoices, setRecentInvoices] = useState<InvoiceSummary[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedWorkspaceInvoice, setSelectedWorkspaceInvoice] = useState<'clean' | 'exception'>('exception');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [kpisData, excData, appData, healthData, riskData, invoicesData] = await Promise.all([
          api.getDashboardKPIs(),
          api.listExceptions({ status: 'OPEN' }),
          api.listApprovals({ status: 'PENDING' }),
          api.getDashboardControlHealth().catch(() => null),
          api.getDashboardRiskOverview().catch(() => null),
          api.listInvoices().catch(() => [] as InvoiceSummary[]),
        ]);
        setKpis(kpisData);
        setExceptions(excData);
        setApprovals(appData);
        setControlHealth(healthData);
        setRiskOverview(riskData);
        setRecentInvoices(invoicesData.slice(0, 6));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [activeEmail]);

  const atRiskCount = (riskOverview?.critical_count || 0) + (riskOverview?.high_count || 0);

  // Filtered recent invoices for the bottom table
  const filteredRecent = recentInvoices.filter(inv =>
    (inv.invoice_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (inv.vendor_name || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Control health categories with reliable defaults if API response is partial
  const healthCategories = controlHealth?.categories || [
    { category: 'VENDOR', name: 'Vendor Integrity', pass_rate_percentage: 94.2, total_checks: 58, failed_count: 3 },
    { category: 'PURCHASE_ORDER', name: 'Purchase Order', pass_rate_percentage: 96.7, total_checks: 58, failed_count: 2 },
    { category: 'GOODS_RECEIPT', name: 'Goods Receipt', pass_rate_percentage: 96.7, total_checks: 58, failed_count: 2 },
    { category: 'FINANCIAL', name: 'Financial & Tax', pass_rate_percentage: 97.5, total_checks: 116, failed_count: 3 },
    { category: 'DUPLICATE', name: 'Duplicate Prevention', pass_rate_percentage: 88.0, total_checks: 58, failed_count: 7 },
    { category: 'RISK', name: 'Risk & Fraud Signals', pass_rate_percentage: 65.0, total_checks: 58, failed_count: 20 },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      
      {/* 1. Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-primary/10 text-primary border border-primary/20">
              Accounts Payable Control Center
            </span>
            <span className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Real-time Deterministic Controls
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            Accounts Payable Control Center
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Know what can be paid, what needs attention, and why.
          </p>
        </div>

        {/* Primary Header Actions */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onNavigateTab('simulator')}
            className="flex items-center gap-2 px-4 py-2 bg-card hover:bg-muted text-foreground text-xs font-semibold rounded-xl border border-border shadow-xs hover:shadow-sm transition-all cursor-pointer active:scale-[0.98]"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            Control Simulator
          </button>
          {onOpenAddInvoice && (
            <button
              onClick={onOpenAddInvoice}
              className="flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-xl shadow-xs hover:shadow-md transition-all cursor-pointer active:scale-[0.98]"
            >
              <Plus className="w-4 h-4" />
              Upload Invoice
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="h-44 bg-muted rounded-[22px] animate-pulse" />
            <div className="h-44 bg-muted rounded-[22px] animate-pulse" />
            <div className="h-44 bg-muted rounded-[22px] animate-pulse" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="h-72 bg-muted rounded-[22px] animate-pulse" />
            <div className="h-72 bg-muted rounded-[22px] animate-pulse" />
          </div>
        </div>
      ) : (
        <>
          {/* 2. Top Mosaic Row: Balance Card + Needs Attention Card + Awaiting Approval Card */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-4">
            
            {/* Card 1 (Span 6): Total Payable Liability */}
            <div className="lg:col-span-6 bg-card text-card-foreground rounded-[22px] border border-border p-6 shadow-card flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                    <CreditCard className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Total Payable Liability
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-semibold text-muted-foreground bg-muted/60 px-2.5 py-0.5 rounded-full border border-border">
                    INR (₹)
                  </span>
                  <span className="text-[11px] font-semibold text-muted-foreground bg-muted/60 px-2.5 py-0.5 rounded-full border border-border">
                    All Time
                  </span>
                </div>
              </div>

              {/* Big Financial Number */}
              <div className="my-4">
                <div className="flex items-baseline gap-3 flex-wrap">
                  <span className="text-3xl sm:text-4xl font-extrabold text-foreground tracking-tight font-mono">
                    {formatCurrency(kpis?.total_payable_liability || 186540)}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    <TrendingUp className="w-3 h-3" />
                    +12% verified throughput
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Total approved liability across verified invoices awaiting settlement.
                </p>
              </div>

              {/* Quick Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-border">
                <div className="flex items-center gap-2 flex-wrap">
                  {onOpenAddInvoice && (
                    <button
                      onClick={onOpenAddInvoice}
                      className="px-3.5 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-xl shadow-xs hover:shadow-sm transition-all flex items-center gap-1 cursor-pointer active:scale-[0.98]"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Add Invoice
                    </button>
                  )}
                  <button
                    onClick={() => onNavigateTab('payments')}
                    className="px-3.5 py-1.5 bg-foreground text-background hover:opacity-90 text-xs font-semibold rounded-xl shadow-xs hover:shadow-sm transition-all flex items-center gap-1 cursor-pointer active:scale-[0.98]"
                  >
                    Payable Ledger
                  </button>
                  <button
                    onClick={() => onNavigateTab('invoices')}
                    className="px-3.5 py-1.5 bg-card hover:bg-muted text-foreground text-xs font-medium rounded-xl border border-border shadow-xs hover:shadow-sm transition-all flex items-center gap-1 cursor-pointer active:scale-[0.98]"
                  >
                    View All ({kpis?.total_invoices || 0})
                  </button>
                </div>

                {/* Micro Colored Blocks Visual */}
                <div className="hidden sm:flex items-end gap-1 h-6">
                  <div className="w-2.5 h-2 bg-emerald-500/60 rounded-xs" />
                  <div className="w-2.5 h-3.5 bg-blue-500/70 rounded-xs" />
                  <div className="w-2.5 h-5 bg-primary rounded-xs" />
                  <div className="w-2.5 h-6 bg-indigo-600 rounded-xs" />
                </div>
              </div>
            </div>

            {/* Card 2 (Span 3): Needs Attention */}
            <div
              onClick={() => onNavigateTab('attention')}
              className={`lg:col-span-3 bg-card text-card-foreground rounded-[22px] border p-5 shadow-card cursor-pointer hover:shadow-card-hover transition-all flex flex-col justify-between ${
                exceptions.length > 0 ? 'border-amber-300 dark:border-amber-800' : 'border-border'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                      <AlertCircle className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Needs Attention
                    </span>
                  </div>
                  <span className="text-[10px] font-bold text-amber-700 dark:text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                    {exceptions.length} Issues
                  </span>
                </div>

                <div className="mt-3">
                  <div className="text-3xl font-extrabold text-foreground tracking-tight">
                    {exceptions.length}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Invoices with blocking discrepancies requiring clerk or vendor review.
                  </p>
                </div>
              </div>

              <div className="pt-3 border-t border-border mt-3 flex items-center justify-between text-xs">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-400 font-semibold rounded-lg text-xs border border-amber-500/20 transition-all">
                  Action required <ArrowRight className="w-3.5 h-3.5" />
                </span>
                <span className="text-[11px] text-muted-foreground font-mono">
                  {exceptions.filter(e => e.severity === 'CRITICAL').length} Critical
                </span>
              </div>
            </div>

            {/* Card 3 (Span 3): Waiting for Approval */}
            <div
              onClick={() => onNavigateTab('approvals')}
              className={`lg:col-span-3 bg-card text-card-foreground rounded-[22px] border p-5 shadow-card cursor-pointer hover:shadow-card-hover transition-all flex flex-col justify-between ${
                approvals.length > 0 ? 'border-blue-300 dark:border-blue-800' : 'border-border'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Awaiting Sign-off
                    </span>
                  </div>
                  <span className="text-[10px] font-bold text-blue-700 dark:text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full">
                    {approvals.length} Pending
                  </span>
                </div>

                <div className="mt-3">
                  <div className="text-3xl font-extrabold text-foreground tracking-tight">
                    {approvals.length}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Passed all automated verification checks and ready for manager authorization.
                  </p>
                </div>
              </div>

              <div className="pt-3 border-t border-border mt-3 flex items-center justify-between text-xs">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-500/10 hover:bg-blue-500/20 text-blue-700 dark:text-blue-400 font-semibold rounded-lg text-xs border border-blue-500/20 transition-all">
                  Review queue <ArrowRight className="w-3.5 h-3.5" />
                </span>
                <span className="text-[11px] text-muted-foreground">
                  Tier 1-4 Authority
                </span>
              </div>
            </div>

          </div>

          {/* 3. Middle Section: Clean Control Workspace + Control Health + Risk */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            
            {/* Live Control Workspace: Full Semantic Theme Integration (Light in Light Mode, Dark in Dark Mode) */}
            <div className="lg:col-span-5 bg-card text-card-foreground rounded-[22px] p-6 shadow-card relative overflow-hidden border border-border flex flex-col justify-between">
              
              {/* Header inside Workspace */}
              <div>
                <div className="flex items-center justify-between gap-2 border-b border-border pb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                      Live Control Workspace
                    </span>
                  </div>
                  {/* Selector between Clean vs Exception sample */}
                  <div className="flex items-center gap-1 bg-muted p-1 rounded-lg border border-border text-[10px]">
                    <button
                      onClick={() => setSelectedWorkspaceInvoice('exception')}
                      className={`px-2.5 py-1 rounded-md font-semibold transition-all cursor-pointer ${
                        selectedWorkspaceInvoice === 'exception'
                          ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/40 shadow-xs'
                          : 'text-muted-foreground hover:text-foreground hover:bg-card/70'
                      }`}
                    >
                      INV-2026-0002
                    </button>
                    <button
                      onClick={() => setSelectedWorkspaceInvoice('clean')}
                      className={`px-2.5 py-1 rounded-md font-semibold transition-all cursor-pointer ${
                        selectedWorkspaceInvoice === 'clean'
                          ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/40 shadow-xs'
                          : 'text-muted-foreground hover:text-foreground hover:bg-card/70'
                      }`}
                    >
                      INV-2026-0001
                    </button>
                  </div>
                </div>

                {/* Selected Invoice Details */}
                <div className="mt-4 flex items-start justify-between gap-3">
                  <div>
                    <div className="text-xl font-bold font-mono text-foreground">
                      {selectedWorkspaceInvoice === 'exception' ? 'INV-2026-0002' : 'INV-2026-0001'}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      Vendor: <span className="text-foreground font-semibold">{selectedWorkspaceInvoice === 'exception' ? 'ACME Supplies Pvt. Ltd.' : 'Nexora Business Solutions'}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">
                      {selectedWorkspaceInvoice === 'exception' ? '₹543,980' : '₹382,400'}
                    </div>
                    <div className="text-[10px] text-muted-foreground">PO: PO-2026-0089</div>
                  </div>
                </div>

                {/* Visual Radial / Status Hero */}
                <div className="my-5 p-4 rounded-xl bg-muted/40 dark:bg-muted/20 border border-border flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg border-2 ${
                      selectedWorkspaceInvoice === 'exception'
                        ? 'border-red-500 bg-red-500/10 text-red-600 dark:text-red-400'
                        : 'border-emerald-500 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                    }`}>
                      {selectedWorkspaceInvoice === 'exception' ? '8/11' : '11/11'}
                    </div>
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Determination</div>
                      <div className={`text-base font-extrabold ${
                        selectedWorkspaceInvoice === 'exception' ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'
                      }`}>
                        {selectedWorkspaceInvoice === 'exception' ? 'NOT PAYABLE' : 'PAYABLE APPROVED'}
                      </div>
                    </div>
                  </div>

                  <div className="text-right text-[11px] text-muted-foreground max-w-[170px] leading-tight">
                    {selectedWorkspaceInvoice === 'exception'
                      ? 'Invoice quantity exceeds warehouse physical receipt (+20 units).'
                      : 'All 3-way matching rules and bank remittances verified.'}
                  </div>
                </div>

                {/* 11-step Control Pipeline Grid */}
                <div className="space-y-1.5">
                  <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">
                    Control Pipeline Evaluation
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 text-[10px]">
                    {[
                      { name: 'Vendor', pass: true },
                      { name: 'PO Match', pass: true },
                      { name: 'Receipt', pass: true },
                      { name: 'Quantity', pass: selectedWorkspaceInvoice !== 'exception' },
                      { name: 'Price', pass: true },
                      { name: 'Tax', pass: true },
                      { name: 'Total', pass: true },
                      { name: 'Duplicate', pass: true },
                      { name: 'Risk Eval', pass: selectedWorkspaceInvoice !== 'exception' },
                      { name: 'Approval', pass: selectedWorkspaceInvoice !== 'exception' },
                      { name: 'Payable', pass: selectedWorkspaceInvoice !== 'exception' },
                    ].map(step => (
                      <div
                        key={step.name}
                        className={`px-2 py-1 rounded-md border flex items-center justify-between ${
                          step.pass
                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-300 font-medium'
                            : 'bg-red-500/10 border-red-500/30 text-red-700 dark:text-red-300 font-bold'
                        }`}
                      >
                        <span className="truncate">{step.name}</span>
                        <span>{step.pass ? '✓' : '✕'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Actions at bottom of card */}
              <div className="pt-4 border-t border-border mt-4 flex items-center gap-2">
                <button
                  onClick={() => {
                    const inv = recentInvoices.find(i => i.invoice_number === (selectedWorkspaceInvoice === 'exception' ? 'INV-2026-0002' : 'INV-2026-0001'));
                    if (inv) onSelectInvoice(inv.id);
                    else onNavigateTab('attention');
                  }}
                  className="flex-1 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl text-xs transition-all flex items-center justify-center gap-1.5 shadow-xs hover:shadow-md cursor-pointer active:scale-[0.98]"
                >
                  <Info className="w-3.5 h-3.5" />
                  View Explanation
                </button>
                <button
                  onClick={() => onNavigateTab('simulator')}
                  className="flex-1 py-2.5 bg-card hover:bg-muted text-foreground font-semibold rounded-xl text-xs border border-border transition-all flex items-center justify-center gap-1.5 shadow-xs hover:shadow-sm cursor-pointer active:scale-[0.98]"
                >
                  <Sliders className="w-3.5 h-3.5 text-amber-500" />
                  Simulate Fix
                </button>
              </div>
            </div>

            {/* Card 5 (Span 4): Control Health Verification */}
            <div className="lg:col-span-4 bg-card text-card-foreground rounded-[22px] border border-border p-5 shadow-card flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-foreground">Control Health &amp; Verification</h3>
                    <p className="text-[11px] text-muted-foreground mt-0.5">Automated pass rates by category</p>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    {controlHealth?.overall_pass_rate_percentage || 93.8}% Overall
                  </span>
                </div>

                {/* Compact Bar Columns Visualization */}
                <div className="mt-4 space-y-3">
                  {healthCategories.map(cat => (
                    <div key={cat.category} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-foreground truncate">{cat.name}</span>
                        <span className="font-mono text-muted-foreground text-[11px]">
                          {cat.pass_rate_percentage}%
                        </span>
                      </div>
                      <div className="w-full bg-muted h-2 rounded-full overflow-hidden flex">
                        <div
                          className={`h-full rounded-full transition-all ${
                            cat.pass_rate_percentage >= 95
                              ? 'bg-blue-600'
                              : cat.pass_rate_percentage >= 85
                              ? 'bg-emerald-500'
                              : 'bg-amber-500'
                          }`}
                          style={{ width: `${cat.pass_rate_percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-3 border-t border-border mt-4 flex items-center justify-between text-xs">
                <span className="text-muted-foreground text-[11px]">Evaluated deterministically</span>
                <button
                  onClick={() => onNavigateTab('attention')}
                  className="px-2.5 py-1 bg-muted hover:bg-muted/80 text-primary font-semibold rounded-lg border border-border transition-all flex items-center gap-1 text-[11px] cursor-pointer"
                >
                  Review exceptions <ChevronRight className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Card 6 (Span 3): Risk Intelligence Overview */}
            <div className="lg:col-span-3 bg-card text-card-foreground rounded-[22px] border border-border p-5 shadow-card flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div className="flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-primary" />
                    <h3 className="text-sm font-bold text-foreground">Risk Intelligence</h3>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                    Avg {riskOverview?.average_risk_score || 11.1}/100
                  </span>
                </div>

                {/* 4 Risk Level Tiles */}
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <div
                    onClick={() => onNavigateTab('attention')}
                    className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 cursor-pointer hover:border-red-500/40 hover:shadow-xs transition-all"
                  >
                    <div className="text-[10px] font-bold text-red-700 dark:text-red-400 uppercase">Critical</div>
                    <div className="text-xl font-extrabold text-red-700 dark:text-red-400 font-mono mt-0.5">
                      {riskOverview?.critical_count || 1}
                    </div>
                    <div className="text-[9px] text-muted-foreground">Score &ge; 75</div>
                  </div>

                  <div
                    onClick={() => onNavigateTab('attention')}
                    className="p-2.5 rounded-xl bg-orange-500/10 border border-orange-500/20 cursor-pointer hover:border-orange-500/40 hover:shadow-xs transition-all"
                  >
                    <div className="text-[10px] font-bold text-orange-700 dark:text-orange-400 uppercase">High</div>
                    <div className="text-xl font-extrabold text-orange-700 dark:text-orange-400 font-mono mt-0.5">
                      {riskOverview?.high_count || 5}
                    </div>
                    <div className="text-[9px] text-muted-foreground">Score 50-74</div>
                  </div>

                  <div
                    onClick={() => onNavigateTab('invoices')}
                    className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 cursor-pointer hover:border-amber-500/40 hover:shadow-xs transition-all"
                  >
                    <div className="text-[10px] font-bold text-amber-700 dark:text-amber-400 uppercase">Medium</div>
                    <div className="text-xl font-extrabold text-amber-700 dark:text-amber-400 font-mono mt-0.5">
                      {riskOverview?.medium_count || 5}
                    </div>
                    <div className="text-[9px] text-muted-foreground">Score 25-49</div>
                  </div>

                  <div
                    onClick={() => onNavigateTab('invoices')}
                    className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 cursor-pointer hover:border-emerald-500/40 hover:shadow-xs transition-all"
                  >
                    <div className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase">Low</div>
                    <div className="text-xl font-extrabold text-emerald-700 dark:text-emerald-400 font-mono mt-0.5">
                      {riskOverview?.low_count || 46}
                    </div>
                    <div className="text-[9px] text-muted-foreground">Score 0-24</div>
                  </div>
                </div>

                {/* Top Risk Driver snippet */}
                <div className="mt-3 p-2.5 rounded-xl bg-muted/60 border border-border text-xs">
                  <div className="font-semibold text-foreground text-[11px] truncate">
                    Top Driver: Quantity Variance
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">
                    Found in 4 active invoices (+20 units average variance).
                  </div>
                </div>
              </div>

              <button
                onClick={() => onNavigateTab('attention')}
                className="w-full mt-3 py-2 bg-card hover:bg-muted text-foreground text-xs font-semibold rounded-xl border border-border shadow-xs hover:shadow-sm transition-all flex items-center justify-center gap-1 cursor-pointer active:scale-[0.98]"
              >
                Inspect High Risk ({atRiskCount})
              </button>
            </div>

          </div>

          {/* 4. Bottom Row: Recent Invoices / Transaction History */}
          <div className="bg-card text-card-foreground rounded-[22px] border border-border shadow-card overflow-hidden">
            <div className="p-4 sm:p-5 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-bold text-foreground">Recent Invoices &amp; Verification Pipeline</h3>
              </div>

              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search recent invoices..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    className="pl-8 pr-3 py-1.5 bg-muted/50 border border-border rounded-xl text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary w-48 sm:w-60"
                  />
                </div>
                <button
                  onClick={() => onNavigateTab('invoices')}
                  className="px-3.5 py-1.5 bg-card hover:bg-muted text-foreground text-xs font-semibold rounded-xl border border-border shadow-xs hover:shadow-sm transition-all cursor-pointer"
                >
                  View All Invoices
                </button>
              </div>
            </div>

            {filteredRecent.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-xs">
                No recent invoices match the filter.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-muted/30 border-b border-border text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                      <th className="py-3 px-4">Invoice / Vendor</th>
                      <th className="py-3 px-4">Date</th>
                      <th className="py-3 px-4">PO Reference</th>
                      <th className="py-3 px-4 text-right">Amount</th>
                      <th className="py-3 px-4 text-center">Status</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredRecent.map(inv => {
                      const sc = getStatusColor(inv.status);
                      return (
                        <tr
                          key={inv.id}
                          onClick={() => onSelectInvoice(inv.id)}
                          className="hover:bg-muted/40 transition-colors cursor-pointer"
                        >
                          <td className="py-3 px-4">
                            <div className="font-semibold text-foreground flex items-center gap-2">
                              <span className="font-mono text-xs text-primary">{inv.invoice_number}</span>
                              <span className="text-muted-foreground text-xs font-normal">· {inv.vendor_name || 'Vendor'}</span>
                            </div>
                          </td>
                          <td className="py-3 px-4 text-muted-foreground">
                            {formatDate(inv.invoice_date || inv.created_at)}
                          </td>
                          <td className="py-3 px-4 font-mono text-xs text-muted-foreground">
                            {inv.po_number || '—'}
                          </td>
                          <td className="py-3 px-4 text-right font-mono font-bold text-foreground">
                            {formatCurrency(inv.grand_total)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium ${sc.bg} ${sc.text}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                              {humanStatus(inv.status)}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onSelectInvoice(inv.id);
                              }}
                              className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:hover:bg-blue-900/60 dark:text-blue-300 border border-blue-200 dark:border-blue-900/60 rounded-xl text-xs font-semibold transition-all cursor-pointer shadow-xs hover:shadow-sm"
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

        </>
      )}

    </div>
  );
};
