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
        <div className="bg-white rounded-3xl p-8 max-w-sm w-full text-center shadow-2xl border border-gray-200">
          <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-800 font-semibold text-sm">Loading invoice control intelligence...</p>
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
      <div className="bg-white rounded-3xl max-w-5xl w-full shadow-2xl border border-gray-200 my-4 flex flex-col max-h-[92vh] overflow-hidden">
        {/* 1. Header (Invoice number, Vendor, Amount, Status, Risk) */}
        <div className="px-6 py-5 border-b border-gray-100 flex items-start justify-between bg-white flex-shrink-0">
          <div className="flex-1 min-w-0 pr-4">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-2xl font-black text-gray-900 font-mono tracking-tight">
                {detail.invoice_number}
              </h2>
              <span className={`text-xs font-bold px-3 py-1 rounded-full border ${sc.bg} ${sc.text}`}>
                {humanStatus(detail.status)}
              </span>
              {riskProfile && (
                <span
                  className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                    riskProfile.risk_level === 'CRITICAL'
                      ? 'bg-red-100 text-red-800 border-red-200'
                      : riskProfile.risk_level === 'HIGH'
                      ? 'bg-orange-100 text-orange-800 border-orange-200'
                      : riskProfile.risk_level === 'MEDIUM'
                      ? 'bg-amber-100 text-amber-800 border-amber-200'
                      : 'bg-emerald-100 text-emerald-800 border-emerald-200'
                  }`}
                >
                  Risk: {riskProfile.risk_level} ({riskProfile.risk_score} / 100)
                </span>
              )}
            </div>

            <div className="text-sm text-gray-600 mt-1.5 flex items-center gap-2 flex-wrap">
              <span className="font-bold text-gray-800">{detail.vendor_name}</span>
              <span className="text-gray-300">·</span>
              <span className="font-mono font-bold text-gray-900">
                {formatCurrency(detail.grand_total)}
              </span>
              {detail.po_number && (
                <>
                  <span className="text-gray-300">·</span>
                  <span className="text-gray-600">
                    PO: <strong className="font-mono text-gray-800">{detail.po_number}</strong>
                  </span>
                </>
              )}
              {hasMultipleRevisions && (
                <>
                  <span className="text-gray-300">·</span>
                  <span className="bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded text-xs font-bold">
                    Rev {detail.revisions?.length}
                  </span>
                </>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors flex-shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="overflow-y-auto flex-1 p-6 space-y-6 bg-gray-50/50">
          {/* 2. IMMEDIATE ANSWER: "Can this invoice be paid?" */}
          <div
            className={`rounded-2xl border p-5 shadow-card transition-all ${
              explanation?.can_be_paid
                ? 'bg-emerald-50 border-emerald-200'
                : detail.status === 'PAID'
                ? 'bg-blue-50 border-blue-200'
                : detail.status === 'AWAITING_APPROVAL'
                ? 'bg-indigo-50 border-indigo-200'
                : 'bg-red-50/80 border-red-200'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div
                  className={`w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-xs mt-0.5 ${
                    explanation?.can_be_paid
                      ? 'bg-emerald-100 text-emerald-700'
                      : detail.status === 'PAID'
                      ? 'bg-blue-100 text-blue-700'
                      : detail.status === 'AWAITING_APPROVAL'
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-red-100 text-red-600'
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
                  <div className="text-[10px] uppercase font-bold tracking-wider text-gray-500">
                    Payment Eligibility Decision
                  </div>
                  <h3 className="text-lg font-black text-gray-900 mt-0.5">
                    {explanation?.can_be_paid
                      ? 'YES — Ready for Payment'
                      : detail.status === 'PAID'
                      ? 'PAID IN FULL — Disbursement Confirmed'
                      : detail.status === 'AWAITING_APPROVAL'
                      ? 'NOT YET — Awaiting Management Sign-off'
                      : `NOT YET — ${blockingReasons.length || 1} Check${blockingReasons.length === 1 ? '' : 's'} Need Attention`}
                  </h3>
                  <p className="text-xs text-gray-700 mt-1 max-w-2xl leading-relaxed">
                    {explanation?.summary || 'Invoice is undergoing deterministic financial validation.'}
                  </p>
                </div>
              </div>

              {/* Action Button */}
              {isBlocked && (
                <button
                  type="button"
                  onClick={() => setActiveTab('controls')}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl transition-colors shadow-xs whitespace-nowrap self-start flex items-center gap-1.5"
                >
                  Review Issues ({blockingReasons.length}) <ChevronRight className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* WHY? (Plain English Blocking Reasons) */}
            {isBlocked && blockingReasons.length > 0 && (
              <div className="mt-4 pt-4 border-t border-red-200/60 space-y-2">
                <span className="text-[11px] font-bold text-red-900 uppercase tracking-wider block">
                  Why?
                </span>
                <div className="space-y-1.5">
                  {blockingReasons.map((reason, idx) => (
                    <div
                      key={idx}
                      className="bg-white/90 border border-red-200/80 rounded-xl px-3 py-2 text-xs flex items-start gap-2.5 shadow-2xs"
                    >
                      <span className="text-red-600 font-bold text-sm leading-none mt-0.5">❌</span>
                      <div className="min-w-0 flex-1">
                        <span className="font-bold text-gray-900">{reason.title}: </span>
                        <span className="text-gray-700">{reason.what_happened}</span>
                        {reason.recommended_action && (
                          <div className="text-[11px] text-blue-700 font-medium mt-0.5">
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

          {/* 3. Control Graph Breadcrumb Pipeline (8-Stage Flow) */}
          <div className="bg-white rounded-2xl border border-gray-200 p-4 shadow-card space-y-2">
            <div className="flex items-center justify-between text-xs pb-1">
              <span className="font-bold text-gray-800 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                Control Graph Verification Pipeline
              </span>
              <button
                type="button"
                onClick={() => setActiveTab('controls')}
                className="text-[11px] text-blue-600 hover:text-blue-700 font-semibold"
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
                        ? 'bg-emerald-50/60 border-emerald-200 text-emerald-800'
                        : isFail
                        ? 'bg-red-50 border-red-200 text-red-800 ring-2 ring-red-100'
                        : isWarn
                        ? 'bg-amber-50 border-amber-200 text-amber-800'
                        : 'bg-gray-50 border-gray-200 text-gray-400'
                    }`}
                  >
                    <div className="text-[9px] font-mono font-bold uppercase tracking-wider text-gray-400">
                      0{idx + 1}
                    </div>
                    <div className="text-[11px] font-bold truncate mt-0.5">
                      {stage.label}
                    </div>
                    <div className="mt-1">
                      {isPass ? (
                        <span className="text-[9px] font-bold text-emerald-600 bg-white/80 px-1.5 py-0.2 rounded">OK</span>
                      ) : isFail ? (
                        <span className="text-[9px] font-bold text-red-600 bg-white/80 px-1.5 py-0.2 rounded">FAIL</span>
                      ) : isWarn ? (
                        <span className="text-[9px] font-bold text-amber-600 bg-white/80 px-1.5 py-0.2 rounded">WARN</span>
                      ) : (
                        <span className="text-[9px] font-medium text-gray-400">—</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 4. Navigation Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-2">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-3 px-4 text-xs font-semibold rounded-t-xl transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === 'overview'
                    ? 'border-brand-600 text-brand-700 bg-white'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/60'
                }`}
              >
                <FileText className="w-4 h-4" />
                Overview
              </button>

              <button
                onClick={() => setActiveTab('controls')}
                className={`py-3 px-4 text-xs font-semibold rounded-t-xl transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === 'controls'
                    ? 'border-brand-600 text-brand-700 bg-white'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/60'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                Controls ({explanation ? `${explanation.passed_checks} OK` : '18'})
              </button>

              <button
                onClick={() => setActiveTab('risk')}
                className={`py-3 px-4 text-xs font-semibold rounded-t-xl transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === 'risk'
                    ? 'border-brand-600 text-brand-700 bg-white'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/60'
                }`}
              >
                <AlertTriangle className="w-4 h-4" />
                Risk
                {riskProfile && (
                  <span
                    className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                      riskProfile.risk_level === 'CRITICAL'
                        ? 'bg-red-100 text-red-800'
                        : riskProfile.risk_level === 'HIGH'
                        ? 'bg-orange-100 text-orange-800'
                        : riskProfile.risk_level === 'MEDIUM'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {riskProfile.risk_score}
                  </span>
                )}
              </button>

              <button
                onClick={() => setActiveTab('audit')}
                className={`py-3 px-4 text-xs font-semibold rounded-t-xl transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === 'audit'
                    ? 'border-brand-600 text-brand-700 bg-white'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/60'
                }`}
              >
                <History className="w-4 h-4" />
                Audit
                {replay && (
                  <span className="bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full text-[10px]">
                    {replay.events_count}
                  </span>
                )}
              </button>

              {hasMultipleRevisions && (
                <button
                  onClick={() => setActiveTab('changes')}
                  className={`py-3 px-4 text-xs font-semibold rounded-t-xl transition-colors border-b-2 flex items-center gap-2 ${
                    activeTab === 'changes'
                      ? 'border-brand-600 text-brand-700 bg-white'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/60'
                  }`}
                >
                  <Layers className="w-4 h-4" />
                  Changes
                  <span className="bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full text-[10px] font-bold">
                    Diff
                  </span>
                </button>
              )}
            </nav>
          </div>

          {/* 5. Tab Content Panes */}

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Metadata 4-Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-xs">
                  <div className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Grand Total</div>
                  <div className="text-xl font-bold text-gray-900 mt-1">{formatCurrency(detail.grand_total)}</div>
                </div>
                <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-xs">
                  <div className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Invoice Date</div>
                  <div className="text-sm font-bold text-gray-800 mt-1.5">{formatDate(detail.invoice_date)}</div>
                </div>
                <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-xs">
                  <div className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Payment Due</div>
                  <div className="text-sm font-bold text-gray-800 mt-1.5">{formatDate(detail.due_date)}</div>
                </div>
                <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-xs">
                  <div className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Pass Rate</div>
                  <div className="text-sm font-bold text-emerald-700 mt-1.5">
                    {explanation ? `${explanation.passed_checks} Checks OK` : '—'}
                  </div>
                </div>
              </div>

              {/* Line Items Table */}
              <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-card">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <h4 className="font-bold text-gray-900 text-sm">
                    Line Items ({currentRevision?.items?.length || 0})
                  </h4>
                  <span className="text-xs text-gray-400 font-mono">
                    Currency: {detail.currency || 'INR'}
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-gray-50 text-gray-400 font-bold uppercase tracking-wider text-left border-b border-gray-100 text-[10px]">
                        <th className="py-2.5 px-4">#</th>
                        <th className="py-2.5 px-4">Description</th>
                        <th className="py-2.5 px-4 text-right">Quantity</th>
                        <th className="py-2.5 px-4 text-right">Unit Price</th>
                        <th className="py-2.5 px-4 text-right">Tax</th>
                        <th className="py-2.5 px-4 text-right">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {currentRevision?.items?.map(item => (
                        <tr key={item.id} className="hover:bg-gray-50/50">
                          <td className="py-2.5 px-4 font-mono text-gray-400">{item.line_number}</td>
                          <td className="py-2.5 px-4 font-medium text-gray-800">{item.description}</td>
                          <td className="py-2.5 px-4 text-right font-mono text-gray-700">
                            {item.quantity} {item.unit_of_measure}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono text-gray-700">
                            {formatCurrency(item.unit_price)}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono text-gray-500">
                            {formatCurrency(item.tax_amount)}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono font-bold text-gray-900">
                            {formatCurrency(item.line_total)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-gray-50 border-t border-gray-200">
                        <td colSpan={5} className="py-3 px-4 text-right font-bold text-gray-600 text-xs">
                          Grand Total:
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-black text-gray-900 text-sm">
                          {formatCurrency(detail.grand_total)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Vendor Master & Banking */}
              <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-card space-y-3">
                <h4 className="font-bold text-gray-900 text-sm flex items-center gap-2">
                  <Building className="w-4 h-4 text-gray-500" />
                  Vendor Master &amp; Banking Details
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs pt-1">
                  <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                    <span className="text-gray-400 font-semibold block text-[10px] uppercase">Vendor Legal Name</span>
                    <span className="font-bold text-gray-800 text-xs mt-0.5 block">{detail.vendor_name}</span>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                    <span className="text-gray-400 font-semibold block text-[10px] uppercase">Tax Identifier</span>
                    <span className="font-mono font-semibold text-gray-800 text-xs mt-0.5 block">
                      {detail.vendor_tax_id || '—'}
                    </span>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                    <span className="text-gray-400 font-semibold block text-[10px] uppercase">Bank Account (Last 4)</span>
                    <span className="font-mono font-semibold text-gray-800 text-xs mt-0.5 block">
                      {detail.bank_account_last4 ? `•••• ${detail.bank_account_last4}` : '—'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: CONTROLS */}
          {activeTab === 'controls' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-white p-4 rounded-2xl border border-gray-200">
                <div>
                  <h4 className="font-bold text-sm text-gray-900">18-Rule Control Pipeline Results</h4>
                  <p className="text-xs text-gray-500">
                    Deterministic evaluations mapped through 3-way matching and risk controls.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleRunControls}
                  disabled={runningControls}
                  className="px-3.5 py-1.5 bg-gray-900 hover:bg-gray-800 text-white rounded-xl text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${runningControls ? 'animate-spin' : ''}`} />
                  {runningControls ? 'Re-running...' : 'Re-run Checks'}
                </button>
              </div>

              {controlRunError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-xs">
                  {controlRunError}
                </div>
              )}

              <ControlGraph graph={graph} loading={loading} />
            </div>
          )}

          {/* TAB 3: RISK */}
          {activeTab === 'risk' && (
            <div className="space-y-4">
              <RiskProfileCard riskProfile={riskProfile} loading={loading} />
            </div>
          )}

          {/* TAB 4: AUDIT */}
          {activeTab === 'audit' && (
            <div className="space-y-4">
              <AuditReplayTimeline replay={replay} loading={loading} />
            </div>
          )}

          {/* TAB 5: CHANGES */}
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

