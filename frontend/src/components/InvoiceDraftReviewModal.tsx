import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
  Plus,
  Trash2,
  Save,
  Check,
  Building,
  DollarSign,
  Hash,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import type {
  InvoiceDraft,
  ConfirmDraftResponse,
  Vendor,
  ExtractedLineItem,
} from '../types';
import { formatCurrency } from '../utils/format';

interface InvoiceDraftReviewModalProps {
  draft: InvoiceDraft | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirmed?: (result: ConfirmDraftResponse) => void;
  onSelectInvoice?: (invoiceId: string) => void;
}

export const InvoiceDraftReviewModal: React.FC<InvoiceDraftReviewModalProps> = ({
  draft,
  isOpen,
  onClose,
  onConfirmed,
  onSelectInvoice,
}) => {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selectedVendorId, setSelectedVendorId] = useState<string>('');
  const [activeEvidenceSnippet, setActiveEvidenceSnippet] = useState<string | null>(null);

  // Editable Form fields
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [invoiceDate, setInvoiceDate] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [poNumber, setPoNumber] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [subtotal, setSubtotal] = useState<number>(0);
  const [taxTotal, setTaxTotal] = useState<number>(0);
  const [grandTotal, setGrandTotal] = useState<number>(0);
  const [lineItems, setLineItems] = useState<ExtractedLineItem[]>([]);

  // Action states
  const [saving, setSaving] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [confirmResult, setConfirmResult] = useState<ConfirmDraftResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initialize data from draft when opened
  useEffect(() => {
    if (!draft) return;
    const data = draft.extracted_data || {};

    setInvoiceNumber(data.invoice_number?.value || '');
    setInvoiceDate(data.invoice_date?.value || '');
    setDueDate(data.due_date?.value || '');
    setPoNumber(data.purchase_order_number?.value || '');
    setCurrency(data.currency?.value || 'INR');
    setSubtotal(Number(data.subtotal?.value || 0));
    setTaxTotal(Number(data.tax_total?.value || 0));
    setGrandTotal(Number(data.grand_total?.value || 0));

    if (data.line_items?.value && Array.isArray(data.line_items.value)) {
      setLineItems(data.line_items.value);
    } else {
      setLineItems([]);
    }

    if (draft.vendor_match?.vendor_id) {
      setSelectedVendorId(draft.vendor_match.vendor_id);
    }

    setConfirmResult(null);
    setErrorMessage(null);
    setSaveSuccess(false);

    // Fetch vendor master for selection dropdown
    api.listVendors().then(setVendors).catch(console.error);
  }, [draft]);

  if (!isOpen || !draft) return null;

  const documentUrl = api.getDocumentUrl(draft.document_id);

  // Confidence pill helper
  const renderConfidenceBadge = (confidence?: number, source?: string) => {
    if (source === 'HUMAN_REVIEW') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
          Edited by you
        </span>
      );
    }
    if (confidence === undefined || confidence === null) return null;

    const pct = Math.round(confidence * 100);
    if (pct >= 85) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
          <Sparkles className="w-2.5 h-2.5" /> {pct}%
        </span>
      );
    }
    if (pct >= 50) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
          {pct}%
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
        Low {pct}%
      </span>
    );
  };

  // Arithmetic validation
  const calculatedGrandTotal = Number((subtotal + taxTotal).toFixed(2));
  const arithmeticMismatch = Math.abs(calculatedGrandTotal - grandTotal) > 0.05;

  const lineItemsSum = lineItems.reduce(
    (sum, item) => sum + Number(item.line_total || 0),
    0
  );
  const itemsMismatch = lineItems.length > 0 && Math.abs(lineItemsSum - subtotal) > 0.05;

  // Handle line item changes
  const handleItemChange = (index: number, field: keyof ExtractedLineItem, val: any) => {
    const updated = [...lineItems];
    const item = { ...updated[index], [field]: val };
    if (field === 'quantity' || field === 'unit_price') {
      const q = field === 'quantity' ? Number(val) : Number(item.quantity);
      const p = field === 'unit_price' ? Number(val) : Number(item.unit_price);
      item.line_total = Number((q * p).toFixed(2));
    }
    updated[index] = item;
    setLineItems(updated);
  };

  const handleAddItem = () => {
    setLineItems([
      ...lineItems,
      {
        line_number: lineItems.length + 1,
        description: 'New Item',
        quantity: 1,
        unit_price: 0,
        tax_rate: 18,
        line_total: 0,
        confidence: 1.0,
      },
    ]);
  };

  const handleRemoveItem = (index: number) => {
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  // Save draft changes (PUT)
  const handleSaveDraft = async () => {
    try {
      setSaving(true);
      setErrorMessage(null);
      await api.updateDraft(draft.draft_id, {
        invoice_number: invoiceNumber,
        invoice_date: invoiceDate,
        due_date: dueDate,
        purchase_order_number: poNumber,
        currency,
        subtotal,
        tax_total: taxTotal,
        grand_total: grandTotal,
        vendor_id: selectedVendorId || undefined,
        line_items: lineItems,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save draft changes');
    } finally {
      setSaving(false);
    }
  };

  // Confirm draft (POST /confirm) -> creates invoice & runs 18 controls
  const handleConfirmDraft = async () => {
    if (!invoiceNumber.trim()) {
      setErrorMessage('Invoice number is required.');
      return;
    }
    if (!selectedVendorId) {
      setErrorMessage('Please link this invoice to a master vendor.');
      return;
    }
    if (grandTotal <= 0) {
      setErrorMessage('Grand total must be greater than zero.');
      return;
    }

    try {
      setConfirming(true);
      setErrorMessage(null);

      // Save any pending edits first
      await api.updateDraft(draft.draft_id, {
        invoice_number: invoiceNumber,
        invoice_date: invoiceDate,
        due_date: dueDate,
        purchase_order_number: poNumber,
        currency,
        subtotal,
        tax_total: taxTotal,
        grand_total: grandTotal,
        vendor_id: selectedVendorId,
        line_items: lineItems,
      });

      // Confirm
      const res = await api.confirmDraft(draft.draft_id);
      setConfirmResult(res);
      if (onConfirmed) {
        onConfirmed(res);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Confirmation failed. Please check the fields and try again.');
    } finally {
      setConfirming(false);
    }
  };

  const overallScorePct = draft.overall_confidence
    ? Math.round(draft.overall_confidence * 100)
    : null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/50 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
      <div className="bg-popover text-popover-foreground rounded-[24px] max-w-6xl w-full max-h-[92vh] flex flex-col shadow-modal border border-border overflow-hidden animate-in fade-in zoom-in-95">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-popover flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-ai/10 text-ai flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-lg font-bold text-foreground">Review Extracted Invoice</h2>
                {overallScorePct !== null && (
                  <span
                    className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                      overallScorePct >= 85
                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                        : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                    }`}
                  >
                    <Sparkles className="w-3 h-3" /> {overallScorePct}% AI Confidence
                  </span>
                )}
                <span className="text-xs font-semibold text-muted-foreground bg-muted px-2.5 py-0.5 rounded-full">
                  Draft
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Inspect AI extraction, verify evidence against the document, and confirm to run controls.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Success Confirmation Modal Overlay */}
        {confirmResult ? (
          <div className="p-8 text-center space-y-6 max-w-lg mx-auto my-auto">
            <div
              className={`w-16 h-16 rounded-3xl mx-auto flex items-center justify-center ${
                confirmResult.failed_controls === 0
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                  : 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
              }`}
            >
              {confirmResult.failed_controls === 0 ? (
                <ShieldCheck className="w-9 h-9" />
              ) : (
                <ShieldAlert className="w-9 h-9" />
              )}
            </div>

            <div>
              <h3 className="text-xl font-bold text-foreground">Invoice Confirmed &amp; Evaluated</h3>
              <p className="text-sm text-muted-foreground mt-1">{confirmResult.message}</p>
            </div>

            <div className="bg-muted/40 rounded-2xl p-4 text-left border border-border space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Invoice Number</span>
                <span className="font-semibold text-foreground">{confirmResult.invoice_number}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Initial Financial Status</span>
                <span className="font-semibold text-foreground">{confirmResult.status}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-border pt-2">
                <span className="text-muted-foreground">18 Controls Evaluated</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  {confirmResult.passed_controls} Passed
                </span>
              </div>
              {confirmResult.failed_controls > 0 && (
                <div className="flex justify-between text-sm text-amber-600 dark:text-amber-400">
                  <span>Exceptions Generated</span>
                  <span className="font-bold">{confirmResult.exception_count} exception(s)</span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-3 bg-muted hover:bg-muted/80 text-foreground font-semibold rounded-xl text-sm transition-colors"
              >
                Close
              </button>
              {onSelectInvoice && confirmResult.invoice_id && (
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onSelectInvoice(confirmResult.invoice_id);
                  }}
                  className="flex-1 py-3 bg-primary hover:opacity-90 text-primary-foreground font-semibold rounded-xl text-sm transition-all shadow-xs flex items-center justify-center gap-1.5"
                >
                  View invoice <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Dual-Pane Review Workspace */
          <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 bg-surface-muted/20">
            
            {/* LEFT PANE: Document Preview & Extracted Evidence */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              
              {/* Document Frame / Preview */}
              <div className="bg-card text-card-foreground rounded-2xl border border-border shadow-card p-4 flex flex-col h-[340px]">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-primary" />
                    <span className="text-xs font-semibold text-foreground truncate max-w-[200px]">
                      Source Document
                    </span>
                  </div>
                  <a
                    href={documentUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline font-medium"
                  >
                    Open original <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <div className="flex-1 mt-3 bg-muted/40 rounded-xl overflow-hidden border border-border flex items-center justify-center">
                  <iframe
                    src={documentUrl}
                    title="Invoice Document Preview"
                    className="w-full h-full border-0"
                  />
                </div>
              </div>

              {/* Evidence Inspector */}
              <div className="bg-card text-card-foreground rounded-2xl border border-border shadow-card p-4">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                  <HelpCircle className="w-3.5 h-3.5 text-primary" />
                  Document Evidence Snippets
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  Click or hover any field to inspect the exact text segment extracted by AI.
                </p>

                {activeEvidenceSnippet ? (
                  <div className="bg-primary/10 border border-primary/20 rounded-xl p-3">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-primary block mb-1">
                      Matched text in document:
                    </span>
                    <p className="text-xs font-mono text-foreground whitespace-pre-wrap">
                      "{activeEvidenceSnippet}"
                    </p>
                  </div>
                ) : (
                  <div className="bg-muted/30 border border-border rounded-xl p-3 text-xs text-muted-foreground italic text-center">
                    Select a field on the right to view its document evidence.
                  </div>
                )}

                {/* Evidence snippet pills */}
                <div className="mt-3 flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                  {Object.entries(draft.extracted_data || {}).map(([key, f]) => {
                    if (!f?.evidence_snippet) return null;
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setActiveEvidenceSnippet(f.evidence_snippet)}
                        className={`text-[11px] px-2.5 py-1 rounded-lg border transition-colors ${
                          activeEvidenceSnippet === f.evidence_snippet
                            ? 'bg-primary text-primary-foreground border-primary font-semibold'
                            : 'bg-card text-muted-foreground border-border hover:bg-muted hover:text-foreground'
                        }`}
                      >
                        {key.replace(/_/g, ' ')}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* RIGHT PANE: Extracted Structured Data & Edit Form */}
            <div className="lg:col-span-7 flex flex-col gap-4">
              
              {/* Error Message */}
              {errorMessage && (
                <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-4 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-bold text-rose-700 dark:text-rose-400">Validation Notice</div>
                    <div className="text-xs text-rose-600 dark:text-rose-300 mt-0.5">{errorMessage}</div>
                  </div>
                </div>
              )}

              {/* Warnings Banner */}
              {draft.warnings && draft.warnings.length > 0 && (
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4 space-y-1">
                  <div className="flex items-center gap-2 text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wide">
                    <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                    Extraction Discrepancies
                  </div>
                  {draft.warnings.map((w, idx) => (
                    <div key={idx} className="text-xs text-amber-800 dark:text-amber-300 pl-6">
                      • {w}
                    </div>
                  ))}
                </div>
              )}

              {/* Vendor Matching Card */}
              <div className="bg-card text-card-foreground rounded-2xl border border-border shadow-card p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    <Building className="w-3.5 h-3.5 text-primary" />
                    Vendor Identification &amp; Master Match
                  </div>
                  {draft.vendor_match?.matched ? (
                    <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Check className="w-3 h-3" /> Matched ({draft.vendor_match.match_method})
                    </span>
                  ) : (
                    <span className="text-[11px] font-semibold text-amber-700 dark:text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                      Unmatched Vendor
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-muted/30 border border-border rounded-xl">
                    <span className="text-muted-foreground block mb-0.5">As Extracted from Invoice:</span>
                    <span className="font-semibold text-foreground text-sm block">
                      {draft.extracted_data?.vendor_name?.value || 'Unknown Vendor'}
                    </span>
                    <span className="text-muted-foreground font-mono text-[11px]">
                      Tax ID: {draft.extracted_data?.vendor_tax_id?.value || 'None'}
                    </span>
                  </div>

                  <div className="p-3 bg-card border border-border rounded-xl space-y-1">
                    <label className="text-foreground font-semibold block">
                      Match to Master Vendor:
                    </label>
                    <select
                      value={selectedVendorId}
                      onChange={(e) => setSelectedVendorId(e.target.value)}
                      className="w-full bg-background border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                      <option value="">-- Select Master Vendor --</option>
                      {vendors.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.legal_name || v.display_name} ({v.vendor_code})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Invoice Header Form */}
              <div className="bg-card text-card-foreground rounded-2xl border border-border shadow-card p-4 space-y-4">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  <Hash className="w-3.5 h-3.5 text-primary" />
                  Invoice Header Details
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-semibold text-foreground">Invoice Number</label>
                      {renderConfidenceBadge(
                        draft.extracted_data?.invoice_number?.confidence,
                        draft.extracted_data?.invoice_number?.source
                      )}
                    </div>
                    <input
                      type="text"
                      value={invoiceNumber}
                      onFocus={() =>
                        setActiveEvidenceSnippet(
                          draft.extracted_data?.invoice_number?.evidence_snippet || null
                        )
                      }
                      onChange={(e) => setInvoiceNumber(e.target.value)}
                      className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-mono font-bold text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-semibold text-foreground">Invoice Date</label>
                      {renderConfidenceBadge(
                        draft.extracted_data?.invoice_date?.confidence,
                        draft.extracted_data?.invoice_date?.source
                      )}
                    </div>
                    <input
                      type="date"
                      value={invoiceDate}
                      onFocus={() =>
                        setActiveEvidenceSnippet(
                          draft.extracted_data?.invoice_date?.evidence_snippet || null
                        )
                      }
                      onChange={(e) => setInvoiceDate(e.target.value)}
                      className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-semibold text-foreground">Due Date</label>
                      {renderConfidenceBadge(
                        draft.extracted_data?.due_date?.confidence,
                        draft.extracted_data?.due_date?.source
                      )}
                    </div>
                    <input
                      type="date"
                      value={dueDate}
                      onFocus={() =>
                        setActiveEvidenceSnippet(
                          draft.extracted_data?.due_date?.evidence_snippet || null
                        )
                      }
                      onChange={(e) => setDueDate(e.target.value)}
                      className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-semibold text-foreground">
                        Purchase Order #
                      </label>
                      {renderConfidenceBadge(
                        draft.extracted_data?.purchase_order_number?.confidence,
                        draft.extracted_data?.purchase_order_number?.source
                      )}
                    </div>
                    <input
                      type="text"
                      placeholder="PO reference if applicable"
                      value={poNumber}
                      onFocus={() =>
                        setActiveEvidenceSnippet(
                          draft.extracted_data?.purchase_order_number?.evidence_snippet || null
                        )
                      }
                      onChange={(e) => setPoNumber(e.target.value)}
                      className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-foreground block mb-1">Currency</label>
                    <input
                      type="text"
                      value={currency}
                      onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                      className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary uppercase"
                    />
                  </div>
                </div>
              </div>

              {/* Financial Totals & Arithmetic Verification */}
              <div className="bg-card text-card-foreground rounded-2xl border border-border shadow-card p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    <DollarSign className="w-3.5 h-3.5 text-primary" />
                    Financial Totals &amp; Reconciliation
                  </div>
                  {arithmeticMismatch ? (
                    <span className="text-[11px] font-semibold text-rose-700 dark:text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Subtotal + Tax ≠ Grand Total
                    </span>
                  ) : (
                    <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                      <Check className="w-3 h-3" /> Arithmetic Verified
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-foreground block mb-1">
                      Subtotal (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={subtotal}
                      onChange={(e) => setSubtotal(Number(e.target.value))}
                      className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-mono font-semibold text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-foreground block mb-1">
                      Tax Total (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={taxTotal}
                      onChange={(e) => setTaxTotal(Number(e.target.value))}
                      className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-mono font-semibold text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-foreground block mb-1">
                      Grand Total (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={grandTotal}
                      onChange={(e) => setGrandTotal(Number(e.target.value))}
                      className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-mono font-bold text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                </div>

                {itemsMismatch && (
                  <div className="text-xs text-amber-700 dark:text-amber-400 bg-amber-500/10 p-2.5 rounded-xl border border-amber-500/20 flex items-center justify-between">
                    <span>
                      Sum of line items ({formatCurrency(lineItemsSum)}) differs from subtotal ({formatCurrency(subtotal)}).
                    </span>
                    <button
                      type="button"
                      onClick={() => setSubtotal(Number(lineItemsSum.toFixed(2)))}
                      className="underline font-semibold ml-2 hover:opacity-80"
                    >
                      Update subtotal
                    </button>
                  </div>
                )}
              </div>

              {/* Line Items Table */}
              <div className="bg-card text-card-foreground rounded-2xl border border-border shadow-card p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    <FileText className="w-3.5 h-3.5 text-primary" />
                    Line Items ({lineItems.length})
                  </div>
                  <button
                    type="button"
                    onClick={handleAddItem}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:opacity-90 px-2 py-1 rounded-lg hover:bg-primary/10 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Item
                  </button>
                </div>

                <div className="overflow-x-auto max-h-56 overflow-y-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-muted/30 border-b border-border text-muted-foreground font-semibold">
                        <th className="py-2 px-2 w-8">#</th>
                        <th className="py-2 px-2">Description</th>
                        <th className="py-2 px-2 w-16 text-right">Qty</th>
                        <th className="py-2 px-2 w-24 text-right">Unit Price</th>
                        <th className="py-2 px-2 w-16 text-right">Tax %</th>
                        <th className="py-2 px-2 w-24 text-right">Total</th>
                        <th className="py-2 px-2 w-8"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {lineItems.map((item, idx) => (
                        <tr key={idx} className="hover:bg-muted/30 transition-colors">
                          <td className="py-1.5 px-2 font-mono text-muted-foreground">{idx + 1}</td>
                          <td className="py-1.5 px-2">
                            <input
                              type="text"
                              value={item.description}
                              onChange={(e) =>
                                handleItemChange(idx, 'description', e.target.value)
                              }
                              className="w-full bg-transparent border-0 border-b border-transparent hover:border-border focus:border-primary p-0 text-xs text-foreground focus:ring-0"
                            />
                          </td>
                          <td className="py-1.5 px-2 text-right">
                            <input
                              type="number"
                              step="1"
                              value={item.quantity}
                              onChange={(e) =>
                                handleItemChange(idx, 'quantity', Number(e.target.value))
                              }
                              className="w-14 bg-transparent border-0 border-b border-transparent hover:border-border focus:border-primary p-0 text-xs text-right text-foreground focus:ring-0 font-mono"
                            />
                          </td>
                          <td className="py-1.5 px-2 text-right">
                            <input
                              type="number"
                              step="0.01"
                              value={item.unit_price}
                              onChange={(e) =>
                                handleItemChange(idx, 'unit_price', Number(e.target.value))
                              }
                              className="w-20 bg-transparent border-0 border-b border-transparent hover:border-border focus:border-primary p-0 text-xs text-right text-foreground focus:ring-0 font-mono"
                            />
                          </td>
                          <td className="py-1.5 px-2 text-right">
                            <input
                              type="number"
                              step="0.1"
                              value={item.tax_rate}
                              onChange={(e) =>
                                handleItemChange(idx, 'tax_rate', Number(e.target.value))
                              }
                              className="w-12 bg-transparent border-0 border-b border-transparent hover:border-border focus:border-primary p-0 text-xs text-right text-foreground focus:ring-0 font-mono"
                            />
                          </td>
                          <td className="py-1.5 px-2 text-right font-mono font-semibold text-foreground">
                            {formatCurrency(item.line_total)}
                          </td>
                          <td className="py-1.5 px-2 text-center">
                            <button
                              type="button"
                              onClick={() => handleRemoveItem(idx)}
                              className="text-muted-foreground hover:text-rose-600 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer Actions */}
        {!confirmResult && (
          <div className="px-6 py-4 border-t border-border flex items-center justify-between bg-popover flex-shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 bg-muted hover:bg-muted/80 text-foreground font-semibold rounded-xl text-xs transition-colors"
            >
              Cancel &amp; Review Later
            </button>

            <div className="flex items-center gap-3">
              {saveSuccess && (
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> Saved
                </span>
              )}
              <button
                type="button"
                onClick={handleSaveDraft}
                disabled={saving}
                className="px-4 py-2.5 bg-card border border-border hover:bg-muted text-foreground font-semibold rounded-xl text-xs transition-colors shadow-xs flex items-center gap-1.5 disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5 text-muted-foreground" />
                {saving ? 'Saving...' : 'Save Draft'}
              </button>

              <button
                type="button"
                onClick={handleConfirmDraft}
                disabled={confirming}
                className="px-5 py-2.5 bg-primary hover:opacity-90 text-primary-foreground font-semibold rounded-xl text-xs transition-all shadow-xs flex items-center gap-2 disabled:opacity-50"
              >
                <ShieldCheck className="w-4 h-4" />
                {confirming ? 'Running 18 Controls...' : 'Confirm & Verify'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
