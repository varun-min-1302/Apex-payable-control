import React, { useState, useEffect } from 'react';
import {
  X,
  CheckCircle,
  FileText,
  Building,
  RotateCcw,
  Layers,
  History,
  ShieldCheck,
  CreditCard,
  Package,
  Calendar,
  DollarSign,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  ShieldAlert,
  ChevronRight,
  ArrowDown
} from 'lucide-react';
import { api } from '../api/client';
import type {
  InvoiceDetail,
  InvoiceExplanation,
  ControlGraph as ControlGraphType,
  AuditReplay,
  RevisionDiffResponse,
  InvoiceRiskProfile
} from '../types';
import { formatCurrency, formatDate, humanStatus, getStatusColor } from '../utils/format';
import { ControlGraph } from '../components/ControlGraph';
import { AuditReplayTimeline } from '../components/AuditReplayTimeline';
import { RevisionDiffViewer } from '../components/RevisionDiffViewer';
import { RiskProfileCard } from '../components/RiskProfileCard';

interface InvoiceDetailModalProps {
  invoiceId: string;
  onClose: () => void;
  onRefreshParent?: () => void;
  activeEmail?: string;
  onSelectPersona?: (email: string) => void;
}

type TabKey = 'overview' | 'controls' | 'risk' | 'audit' | 'changes';

export const InvoiceDetailModal: React.FC<InvoiceDetailModalProps> = ({
  invoiceId,
  onClose,
  onRefreshParent,
}) => {
  const [detail, setDetail] = useState<InvoiceDetail | null>(null);
  const [explanation, setExplanation] = useState<InvoiceExplanation | null>(null);
  const [graph, setGraph] = useState<ControlGraphType | null>(null);
  const [replay, setReplay] = useState<AuditReplay | null>(null);
  const [diffData, setDiffData] = useState<RevisionDiffResponse | null>(null);
  const [riskProfile, setRiskProfile] = useState<InvoiceRiskProfile | null>(null);

  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [loading, setLoading] = useState(true);
  const [runningControls, setRunningControls] = useState(false);
  const [controlRunError, setControlRunError] = useState<string | null>(null);

  const loadAll = async () => {
    try {
      setLoading(true);
      const [invData, expData, cgData, arData, rdData, rpData] = await Promise.all([
        api.getInvoiceDetail(invoiceId),
        api.getInvoiceExplanation(invoiceId).catch(() => null),
        api.getInvoiceControlGraph(invoiceId).catch(() => null),
        api.getInvoiceAuditReplay(invoiceId).catch(() => null),
        api.getInvoiceRevisionsDiff(invoiceId).catch(() => null),
        api.getInvoiceRiskProfile(invoiceId).catch(() => null),
      ]);
      setDetail(invData);
      setExplanation(expData);
      setGraph(cgData);
      setReplay(arData);
      setDiffData(rdData);
      setRiskProfile(rpData);
    } catch (err) {
      console.error('Failed to load invoice modal data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [invoiceId]);

  const handleRunControls = async () => {
    if (runningControls) return;
    try {
      setRunningControls(true);
      setControlRunError(null);
      await api.triggerControlRun(invoiceId);
      await loadAll();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      setControlRunError(err.message || 'Error executing controls');
    } finally {
      setRunningControls(false);
    }
  };

  if (loading || !detail) {
    return (
      <div className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4">
        <div className="bg-popover text-popover-foreground rounded-[24px] p-8 max-w-sm w-full text-center shadow-modal border border-border">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-foreground font-semibold text-xs">Loading invoice control intelligence...</p>
        </div>
      </div>
    );
  }

  const currentRevision = detail.revisions?.[0];
  const sc = getStatusColor(detail.status);
  const hasMultipleRevisions = diffData?.has_multiple_revisions || (detail.revisions?.length > 1);

  // 8-stage pipeline nodes for the breadcrumb
  const pipelineStages = [
    { id: 'vendor', label: 'Vendor' },
    { id: 'po', label: 'Purchase Order' },
    { id: 'receipt', label: 'Goods Receipt' },
    { id: 'financial', label: 'Financial' },
    { id: 'duplicate', label: 'Duplicate' },
    { id: 'risk', label: 'Risk' },
    { id: 'approval', label: 'Approval' },
    { id: 'payable', label: 'Payable' },
  ];

  const getNodeStatus = (nodeId: string) => {
    if (!graph) return 'PENDING';
    const found = graph.nodes.find(n => n.id === nodeId);
    return found ? found.status : 'PENDING';
  };

  const isBlocked = detail.status === 'EXCEPTION' || (explanation && !explanation.can_be_paid && explanation.status !== 'PAID');
  const blockingReasons = explanation?.blocking_reasons || [];

  return (
    <div
      className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4 overflow-y-auto"
      onClick={e => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-popover text-popover-foreground rounded-[24px] max-w-5xl w-full shadow-modal border border-border my-4 flex flex-col max-h-[92vh] overflow-hidden animate-in fade-in zoom-in-95">
        
        {/* 1. Header (Invoice number, Vendor, Amount, Status, Risk) */}
        <div className="px-6 py-5 border-b border-border flex items-start justify-between bg-popover flex-shrink-0">
          <div className="flex-1 min-w-0 pr-4">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-2xl font-extrabold text-foreground font-mono tracking-tight">
                {detail.invoice_number}
              </h2>
              <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${sc.bg} ${sc.text}`}>
                {humanStatus(detail.status)}
              </span>
              {riskProfile && (
                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                    riskProfile.risk_level === 'CRITICAL'
                      ? 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20'
                      : riskProfile.risk_level === 'HIGH'
                      ? 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20'
                      : riskProfile.risk_level === 'MEDIUM'
                      ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                      : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                  }`}
                >
                  Risk: {riskProfile.risk_level} ({riskProfile.risk_score}/100)
                </span>
              )}
            </div>

            <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-foreground">{detail.vendor_name}</span>
              <span>·</span>
              <span className="font-mono font-bold text-foreground">
                {formatCurrency(detail.grand_total)}
              </span>
              {detail.po_number && (
                <>
                  <span>·</span>
                  <span>PO: <strong className="font-mono text-foreground">{detail.po_number}</strong></span>
                </>
              )}
              {hasMultipleRevisions && (
                <>
                  <span>·</span>
                  <span className="bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded text-[10px] font-bold">
                    Revision {detail.revisions?.length}
                  </span>
                </>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-muted-foreground hover:bg-muted hover:text-foreground transition-colors flex-shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="overflow-y-auto flex-1 p-6 space-y-5 bg-surface-muted/30">
          
          {/* 2. IMMEDIATE ANSWER: "Can this invoice be paid?" */}
          <div
            className={`rounded-[20px] border p-5 shadow-card transition-all ${
              explanation?.can_be_paid
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-800 dark:text-emerald-300'
                : detail.status === 'PAID'
                ? 'bg-blue-500/10 border-blue-500/20 text-blue-800 dark:text-blue-300'
                : detail.status === 'AWAITING_APPROVAL'
                ? 'bg-primary/10 border-primary/20 text-primary'
                : 'bg-red-500/10 border-red-500/20 text-red-800 dark:text-red-300'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div
                  className={`w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-xs mt-0.5 ${
                    explanation?.can_be_paid
                      ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                      : detail.status === 'PAID'
                      ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400'
                      : detail.status === 'AWAITING_APPROVAL'
                      ? 'bg-primary/20 text-primary'
                      : 'bg-red-500/20 text-red-600 dark:text-red-400'
                  }`}
                >
                  {explanation?.can_be_paid || detail.status === 'PAID' ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : detail.status === 'AWAITING_APPROVAL' ? (
                    <Clock className="w-6 h-6" />
                  ) : (
                    <XCircle className="w-6 h-6" />
                  )}
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold tracking-wider opacity-70">
                    Payment Eligibility Decision
                  </div>
                  <h3 className="text-lg font-extrabold mt-0.5">
                    {explanation?.can_be_paid
                      ? 'YES — Approved for Payment'
                      : detail.status === 'PAID'
                      ? 'PAID IN FULL — Disbursement Settled'
                      : detail.status === 'AWAITING_APPROVAL'
                      ? 'WAITING FOR APPROVAL — Managerial Sign-off Pending'
                      : `NOT YET PAYABLE — ${blockingReasons.length || 1} Issue${blockingReasons.length === 1 ? '' : 's'} Blocking Payment`}
                  </h3>
                  <p className="text-xs opacity-90 mt-1 max-w-2xl leading-relaxed">
                    {explanation?.summary || 'Invoice is undergoing deterministic financial validation.'}
                  </p>
                </div>
              </div>

              {isBlocked && (
                <button
                  type="button"
                  onClick={() => setActiveTab('controls')}
                  className="px-3.5 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-xl transition-colors shadow-xs whitespace-nowrap self-start flex items-center gap-1.5"
                >
                  Inspect Issues ({blockingReasons.length}) <ChevronRight className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Why? Blocking Reasons */}
            {isBlocked && blockingReasons.length > 0 && (
              <div className="mt-4 pt-3.5 border-t border-red-500/20 space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider block">
                  Root Cause Explanation
                </span>
                <div className="space-y-1.5">
                  {blockingReasons.map((reason, idx) => (
                    <div
                      key={idx}
                      className="bg-card/90 border border-red-500/30 rounded-xl px-3 py-2 text-xs flex items-start gap-2.5 shadow-2xs"
                    >
                      <span className="text-red-500 font-bold text-sm leading-none mt-0.5">❌</span>
                      <div className="min-w-0 flex-1">
                        <span className="font-bold text-foreground">{reason.title}: </span>
                        <span className="text-muted-foreground">{reason.what_happened}</span>
                        {reason.recommended_action && (
                          <div className="text-[11px] text-primary font-medium mt-0.5">
                            Action: {reason.recommended_action}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 3. Control Graph Pipeline (8-Stage Flow) */}
          <div className="bg-card text-card-foreground rounded-[20px] border border-border/80 p-4 shadow-card space-y-2">
            <div className="flex items-center justify-between text-xs pb-1">
              <span className="font-bold text-foreground uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-primary" />
                8-Stage Control Graph Pipeline
              </span>
              <button
                type="button"
                onClick={() => setActiveTab('controls')}
                className="text-[11px] text-primary hover:underline font-semibold"
              >
                Inspect checks &rarr;
              </button>
            </div>

            <div className="grid grid-cols-4 sm:grid-cols-8 gap-1.5">
              {pipelineStages.map((stage, idx) => {
                const nodeStatus = getNodeStatus(stage.id);
                const isPass = nodeStatus === 'PASS';
                const isFail = nodeStatus === 'FAIL';
                const isWarn = nodeStatus === 'WARNING';

                return (
                  <div
                    key={stage.id}
                    onClick={() => setActiveTab('controls')}
                    className={`p-2 rounded-xl border text-center transition-all cursor-pointer flex flex-col justify-between ${
                      isPass
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-300'
                        : isFail
                        ? 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-300 ring-1 ring-red-500/30'
                        : isWarn
                        ? 'bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-300'
                        : 'bg-muted/40 border-border text-muted-foreground'
                    }`}
                  >
                    <div className="text-[9px] font-mono font-bold uppercase tracking-wider opacity-60">
                      0{idx + 1}
                    </div>
                    <div className="text-[11px] font-bold truncate mt-0.5">
                      {stage.label}
                    </div>
                    <div className="mt-1">
                      {isPass ? (
                        <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 bg-card/80 px-1.5 py-0.2 rounded">OK</span>
                      ) : isFail ? (
                        <span className="text-[9px] font-bold text-red-600 dark:text-red-400 bg-card/80 px-1.5 py-0.2 rounded">FAIL</span>
                      ) : isWarn ? (
                        <span className="text-[9px] font-bold text-amber-600 dark:text-amber-400 bg-card/80 px-1.5 py-0.2 rounded">WARN</span>
                      ) : (
                        <span className="text-[9px] font-medium text-muted-foreground">—</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 4. Navigation Tabs */}
          <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-full border border-border/60 self-start overflow-x-auto">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'overview'
                  ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              Overview
            </button>

            <button
              onClick={() => setActiveTab('controls')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'controls'
                  ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Controls ({explanation ? `${explanation.passed_checks} OK` : '18'})
            </button>

            <button
              onClick={() => setActiveTab('risk')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'risk'
                  ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              Risk
              {riskProfile && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-primary/20 text-inherit">
                  {riskProfile.risk_score}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'audit'
                  ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Audit
              {replay && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-muted text-inherit">
                  {replay.events_count}
                </span>
              )}
            </button>

            {hasMultipleRevisions && (
              <button
                onClick={() => setActiveTab('changes')}
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
                  activeTab === 'changes'
                    ? 'bg-foreground text-background dark:bg-card dark:text-foreground font-semibold shadow-xs'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                Changes
              </button>
            )}
          </div>

          {/* 5. Tab Panes */}
          {activeTab === 'overview' && (
            <div className="space-y-5">
              {/* Metadata Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-card text-card-foreground rounded-2xl p-4 border border-border/80 shadow-xs">
                  <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Grand Total</div>
                  <div className="text-xl font-bold font-mono text-foreground mt-1">{formatCurrency(detail.grand_total)}</div>
                </div>
                <div className="bg-card text-card-foreground rounded-2xl p-4 border border-border/80 shadow-xs">
                  <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Invoice Date</div>
                  <div className="text-xs font-bold text-foreground mt-1.5">{formatDate(detail.invoice_date)}</div>
                </div>
                <div className="bg-card text-card-foreground rounded-2xl p-4 border border-border/80 shadow-xs">
                  <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Payment Due</div>
                  <div className="text-xs font-bold text-foreground mt-1.5">{formatDate(detail.due_date)}</div>
                </div>
                <div className="bg-card text-card-foreground rounded-2xl p-4 border border-border/80 shadow-xs">
                  <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Passed Checks</div>
                  <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 mt-1.5">
                    {explanation ? `${explanation.passed_checks} / ${explanation.total_checks || (explanation.passed_checks + (explanation.blocking_reasons?.length || 0)) || 18} OK` : '18 Rules'}
                  </div>
                </div>
              </div>

              {/* Line Items Table */}
              <div className="bg-card text-card-foreground rounded-2xl border border-border/80 overflow-hidden shadow-card">
                <div className="px-5 py-3.5 border-b border-border/60 flex items-center justify-between">
                  <h4 className="font-bold text-foreground text-xs uppercase tracking-wider">
                    Line Items ({currentRevision?.items?.length || 0})
                  </h4>
                  <span className="text-[11px] text-muted-foreground font-mono">
                    Currency: {detail.currency || 'INR'}
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-muted/30 text-muted-foreground font-bold uppercase tracking-wider text-left border-b border-border/60 text-[10px]">
                        <th className="py-2.5 px-4">#</th>
                        <th className="py-2.5 px-4">Description</th>
                        <th className="py-2.5 px-4 text-right">Quantity</th>
                        <th className="py-2.5 px-4 text-right">Unit Price</th>
                        <th className="py-2.5 px-4 text-right">Tax</th>
                        <th className="py-2.5 px-4 text-right">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {currentRevision?.items?.map(item => (
                        <tr key={item.id} className="hover:bg-muted/30">
                          <td className="py-2.5 px-4 font-mono text-muted-foreground">{item.line_number}</td>
                          <td className="py-2.5 px-4 font-medium text-foreground">{item.description}</td>
                          <td className="py-2.5 px-4 text-right font-mono text-foreground">
                            {item.quantity} {item.unit_of_measure}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono text-foreground">
                            {formatCurrency(item.unit_price)}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono text-muted-foreground">
                            {formatCurrency(item.tax_amount)}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono font-bold text-foreground">
                            {formatCurrency(item.line_total)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-muted/30 border-t border-border">
                        <td colSpan={5} className="py-3 px-4 text-right font-bold text-foreground text-xs">
                          Grand Total:
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-black text-foreground text-sm">
                          {formatCurrency(detail.grand_total)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Vendor Master & Remittance Proof */}
              <div className="bg-card text-card-foreground rounded-2xl border border-border/80 p-5 shadow-card space-y-3">
                <h4 className="font-bold text-foreground text-xs uppercase tracking-wider flex items-center gap-2">
                  <Building className="w-4 h-4 text-primary" />
                  Vendor Master &amp; Banking Remittance Verification
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs pt-1">
                  <div className="bg-muted/40 p-3 rounded-xl border border-border/60">
                    <span className="text-muted-foreground font-semibold block text-[10px] uppercase">Legal Vendor Name</span>
                    <span className="font-bold text-foreground text-xs mt-0.5 block">{detail.vendor_name}</span>
                  </div>
                  <div className="bg-muted/40 p-3 rounded-xl border border-border/60">
                    <span className="text-muted-foreground font-semibold block text-[10px] uppercase">Tax Identifier (GSTIN)</span>
                    <span className="font-mono font-semibold text-foreground text-xs mt-0.5 block">
                      {detail.vendor_tax_id || '—'}
                    </span>
                  </div>
                  <div className="bg-muted/40 p-3 rounded-xl border border-border/60">
                    <span className="text-muted-foreground font-semibold block text-[10px] uppercase">Bank Account (Last 4)</span>
                    <span className="font-mono font-semibold text-foreground text-xs mt-0.5 block">
                      {detail.bank_account_last4 ? `•••• ${detail.bank_account_last4}` : '—'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'controls' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-card text-card-foreground p-4 rounded-2xl border border-border/80">
                <div>
                  <h4 className="font-bold text-xs uppercase tracking-wider text-foreground">18-Rule Control Pipeline Results</h4>
                  <p className="text-[11px] text-muted-foreground">
                    Deterministic evaluations mapped through 3-way matching, arithmetic integrity, and risk screening.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleRunControls}
                  disabled={runningControls}
                  className="px-3.5 py-1.5 bg-foreground text-background dark:bg-card dark:text-foreground rounded-xl text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1.5 shadow-xs"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${runningControls ? 'animate-spin' : ''}`} />
                  {runningControls ? 'Re-running...' : 'Re-run Checks'}
                </button>
              </div>

              {controlRunError && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 px-4 py-3 rounded-xl text-xs">
                  {controlRunError}
                </div>
              )}

              <ControlGraph graph={graph} loading={loading} />
            </div>
          )}

          {activeTab === 'risk' && (
            <div className="space-y-4">
              <RiskProfileCard riskProfile={riskProfile} loading={loading} />
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="space-y-4">
              <AuditReplayTimeline replay={replay} loading={loading} />
            </div>
          )}

          {activeTab === 'changes' && hasMultipleRevisions && (
            <div className="space-y-4">
              <RevisionDiffViewer diffData={diffData} loading={loading} />
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
