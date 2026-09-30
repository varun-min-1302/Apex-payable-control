import React, { useState, useEffect } from 'react';
import {
  Search,
  FileText,
  ChevronRight,
  Plus,
  Sparkles,
  Filter,
  ArrowUpDown,
  AlertCircle,
  CheckCircle,
  Clock,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import type { InvoiceSummary, InvoiceDraft } from '../types';
import { formatCurrency, formatDate, humanStatus, getStatusColor } from '../utils/format';
import { AddInvoiceModal } from '../components/AddInvoiceModal';
import { InvoiceDraftReviewModal } from '../components/InvoiceDraftReviewModal';

interface InvoicesViewProps {
  onSelectInvoice: (invoiceId: string) => void;
}

type StatusFilter = 'ALL' | 'AWAITING_APPROVAL' | 'EXCEPTION' | 'PAYABLE_CREATED' | 'PAID' | 'REJECTED';

const STATUS_TABS: { key: StatusFilter; label: string }[] = [
  { key: 'ALL', label: 'All' },
  { key: 'EXCEPTION', label: 'Needs attention' },
  { key: 'AWAITING_APPROVAL', label: 'Pending approval' },
  { key: 'PAYABLE_CREATED', label: 'Approved for payment' },
  { key: 'PAID', label: 'Paid' },
  { key: 'REJECTED', label: 'Rejected' },
];

export const InvoicesView: React.FC<InvoicesViewProps> = ({ onSelectInvoice }) => {
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [drafts, setDrafts] = useState<InvoiceDraft[]>([]);
  const [activeDraft, setActiveDraft] = useState<InvoiceDraft | null>(null);
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [vendorFilter, setVendorFilter] = useState<string>('ALL');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      const [invData, draftData] = await Promise.all([
        api.listInvoices({ status: statusFilter === 'ALL' ? undefined : statusFilter }),
        api.listDrafts().catch(() => [] as InvoiceDraft[]),
      ]);
      setInvoices(Array.isArray(invData) ? invData : []);
      setDrafts(Array.isArray(draftData) ? draftData.filter(d => d.status !== 'CONFIRMED') : []);
    } catch (err) {
      console.error(err);
      setInvoices([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [statusFilter]);

  // Unique vendors for filter dropdown
  const uniqueVendors = Array.from(new Set(invoices.map(i => i.vendor_name).filter(Boolean))) as string[];

  // Filter and sort invoices
  const filtered = invoices.filter(inv => {
    const matchesSearch =
      (inv.invoice_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (inv.vendor_name || '').toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRisk =
      riskFilter === 'ALL' ||
      (inv.risk_level && inv.risk_level.toUpperCase() === riskFilter.toUpperCase());

    const matchesVendor =
      vendorFilter === 'ALL' || inv.vendor_name === vendorFilter;

    return matchesSearch && matchesRisk && matchesVendor;
  }).sort((a, b) => {
    const dateA = new Date(a.invoice_date || a.created_at).getTime();
    const dateB = new Date(b.invoice_date || b.created_at).getTime();
    return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
  });

  const getNextAction = (status: string) => {
    switch (status) {
      case 'EXCEPTION':
        return { label: 'Review issue', color: 'bg-amber-100 hover:bg-amber-200 text-amber-800 border-amber-200' };
      case 'AWAITING_APPROVAL':
        return { label: 'Review & approve', color: 'bg-blue-600 hover:bg-blue-700 text-white border-transparent' };
      case 'PAYABLE_CREATED':
      case 'PARTIALLY_PAID':
        return { label: 'Ready to pay', color: 'bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border-indigo-200' };
      case 'PAID':
        return { label: 'Paid in full', color: 'bg-green-50 text-green-700 border-green-200 cursor-default' };
      case 'REJECTED':
        return { label: 'Rejected', color: 'bg-gray-100 text-gray-500 border-gray-200 cursor-default' };
      default:
        return { label: 'Inspect', color: 'bg-gray-50 hover:bg-gray-100 text-gray-700 border-gray-200' };
    }
  };

  const getRiskBadge = (level?: string | null, score?: number | null) => {
    if (!level) return <span className="text-gray-400 text-xs">—</span>;
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-100 text-red-800 border border-red-200">
            CRITICAL {score !== undefined && score !== null ? `(${score})` : ''}
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-orange-100 text-orange-800 border border-orange-200">
            HIGH {score !== undefined && score !== null ? `(${score})` : ''}
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
            MEDIUM {score !== undefined && score !== null ? `(${score})` : ''}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            LOW {score !== undefined && score !== null ? `(${score})` : ''}
          </span>
        );
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Invoices</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            All invoices received and verified by the automated control engine.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl transition-all shadow-xs"
          >
            <Plus className="w-4 h-4" /> Add invoice
          </button>
        </div>
      </div>

      {/* 2. Drafts Ready for Review Banner */}
      {drafts.length > 0 && (
        <div className="bg-indigo-50/80 border border-indigo-100 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white border border-indigo-200 text-indigo-600 flex items-center justify-center flex-shrink-0 shadow-xs">
              <Sparkles className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <div className="text-sm font-bold text-indigo-950">
                {drafts.length} Invoice Draft{drafts.length > 1 ? 's' : ''} Ready for Review
              </div>
              <div className="text-xs text-indigo-700">
                AI extraction completed. Review extracted fields and vendor matching before confirming.
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              setActiveDraft(drafts[0]);
              setShowDraftModal(true);
            }}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-1.5 whitespace-nowrap self-start sm:self-auto"
          >
            Review next draft <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 3. Main Invoices Container */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
        {/* Filter Controls Row */}
        <div className="p-4 border-b border-gray-100 space-y-3">
          {/* Status Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {STATUS_TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setStatusFilter(tab.key)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors whitespace-nowrap ${
                  statusFilter === tab.key
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-800'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Secondary Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-gray-100 text-xs">
            {/* Search */}
            <div className="relative flex-1 min-w-[220px] max-w-sm">
              <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search vendor or invoice number..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-gray-50 border border-gray-200 rounded-xl text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Risk Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-gray-400 font-medium text-[11px]">Risk:</span>
                <select
                  value={riskFilter}
                  onChange={e => setRiskFilter(e.target.value)}
                  className="px-2.5 py-1.5 bg-gray-50 border border-gray-200 rounded-xl text-xs font-semibold text-gray-700 focus:outline-none"
                >
                  <option value="ALL">All Risk</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              {/* Vendor Filter */}
              {uniqueVendors.length > 0 && (
                <div className="flex items-center gap-1.5">
                  <span className="text-gray-400 font-medium text-[11px]">Vendor:</span>
                  <select
                    value={vendorFilter}
                    onChange={e => setVendorFilter(e.target.value)}
                    className="px-2.5 py-1.5 bg-gray-50 border border-gray-200 rounded-xl text-xs font-semibold text-gray-700 focus:outline-none max-w-[150px] truncate"
                  >
                    <option value="ALL">All Vendors</option>
                    {uniqueVendors.map(v => (
                      <option key={v} value={v}>
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Date Sort Toggle */}
              <button
                type="button"
                onClick={() => setSortOrder(prev => (prev === 'desc' ? 'asc' : 'desc'))}
                className="px-2.5 py-1.5 bg-gray-50 border border-gray-200 rounded-xl text-xs font-semibold text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-1"
                title="Toggle Sort Order"
              >
                <ArrowUpDown className="w-3 h-3 text-gray-500" />
                {sortOrder === 'desc' ? 'Newest' : 'Oldest'}
              </button>
            </div>
          </div>
        </div>

        {/* 4. Invoice Table */}
        {loading ? (
          <div className="p-8 space-y-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto text-gray-400">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-gray-800">No invoices yet</h3>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              Upload an invoice document or submit draft extraction to start the control workflow.
            </p>
            <div className="pt-2">
              <button
                onClick={() => setShowAddModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl transition-all shadow-xs"
              >
                <Plus className="w-4 h-4" /> Add invoice
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-gray-50/80 border-b border-gray-100 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Invoice</th>
                  <th className="py-3 px-4">Vendor</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4">Received</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Risk</th>
                  <th className="py-3 px-4 text-right">Next Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map(inv => {
                  const sc = getStatusColor(inv.status);
                  const action = getNextAction(inv.status);

                  return (
                    <tr
                      key={inv.id}
                      onClick={() => onSelectInvoice(inv.id)}
                      className="hover:bg-gray-50/80 transition-colors cursor-pointer group"
                    >
                      {/* Invoice Number */}
                      <td className="py-3.5 px-4 font-mono font-bold text-gray-900">
                        {inv.invoice_number}
                      </td>

                      {/* Vendor Name */}
                      <td className="py-3.5 px-4 font-semibold text-gray-800 max-w-xs truncate">
                        {inv.vendor_name || 'Unknown Vendor'}
                      </td>

                      {/* Amount */}
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-gray-900">
                        {formatCurrency(inv.grand_total)}
                      </td>

                      {/* Received Date */}
                      <td className="py-3.5 px-4 text-gray-500 whitespace-nowrap">
                        {formatDate(inv.invoice_date || inv.created_at)}
                      </td>

                      {/* Human Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${sc.bg} ${sc.text}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                          {humanStatus(inv.status)}
                        </span>
                      </td>

                      {/* Deterministic Risk Badge */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {getRiskBadge(inv.risk_level, inv.risk_score)}
                      </td>

                      {/* Next Action Button */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectInvoice(inv.id);
                          }}
                          className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all inline-flex items-center gap-1 shadow-2xs ${action.color}`}
                        >
                          {action.label}
                          {action.label !== 'Paid in full' && action.label !== 'Rejected' && (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
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

      {/* Upload and Extract Modals */}
      <AddInvoiceModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          load();
        }}
        onExtractDraft={(draft) => {
          setActiveDraft(draft);
          setShowDraftModal(true);
        }}
      />

      <InvoiceDraftReviewModal
        draft={activeDraft}
        isOpen={showDraftModal}
        onClose={() => {
          setShowDraftModal(false);
          setActiveDraft(null);
        }}
        onConfirmed={() => {
          load();
        }}
        onSelectInvoice={onSelectInvoice}
      />
    </div>
  );
};
