export function formatCurrency(val: string | number | undefined | null): string {

  if (val === undefined || val === null) return '₹0';

  const num = typeof val === 'string' ? parseFloat(val) : val;

  if (isNaN(num)) return '₹0';

  // Format in Indian style with lakhs/crores notation
  return new Intl.NumberFormat('en-IN', {

    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  
}).format(num);


}

export function formatCurrencyFull(val: string | number | undefined | null): string {

  if (val === undefined || val === null) return '₹0.00';

  const num = typeof val === 'string' ? parseFloat(val) : val;

  if (isNaN(num)) return '₹0.00';

  return new Intl.NumberFormat('en-IN', {

    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  
}).format(num);


}

export function formatDate(dateStr: string | undefined | null): string {

  if (!dateStr) return '—';

  const d = new Date(dateStr);

  return d.toLocaleDateString('en-IN', {
 day: 'numeric', month: 'short', year: 'numeric' 
});


}

export function formatDateTime(dateStr: string | undefined | null): string {

  if (!dateStr) return '—';

  const d = new Date(dateStr);

  return d.toLocaleString('en-IN', {
 day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' 
});


}

export function humanStatus(status: string): string {

  const map: Record<string, string> = {

    RECEIVED: 'Received',
    PROCESSING: 'Being checked',
    AWAITING_APPROVAL: 'Waiting for approval',
    EXCEPTION: 'Needs attention',
    APPROVED: 'Approved',
    PAYABLE_CREATED: 'Approved for payment',
    PARTIALLY_PAID: 'Partially paid',
    PAID: 'Paid',
    REJECTED: 'Rejected',
    OPEN: 'Open',
    IN_REVIEW: 'Under review',
    RESOLVED: 'Resolved',
    CANCELLED: 'Cancelled',
  
};

  return map[status] || status;


}

export function humanControlCode(code: string): string {

  const map: Record<string, string> = {

    VENDOR_EXISTS: 'Vendor verified',
    VENDOR_STATUS: 'Vendor is active',
    VENDOR_TAX_ID_MATCH: 'Tax information matches',
    BANK_DETAILS_MATCH: 'Bank details verified',
    PO_EXISTS: 'Purchase order found',
    PO_APPROVED: 'Purchase order approved',
    PO_VENDOR_MATCH: 'Vendor matches purchase order',
    PO_ITEM_MATCH: 'Items match purchase order',
    RECEIPT_MATCH: 'Goods received',
    QUANTITY_MATCH: 'Quantity verified',
    PRICE_MATCH: 'Price verified',
    TAX_VALIDATION: 'Tax calculation verified',
    TOTAL_VALIDATION: 'Invoice total verified',
    DUPLICATE_EXACT: 'Possible duplicate invoice',
    DUPLICATE_SEMANTIC: 'Similar invoice detected',
    THRESHOLD_PROXIMITY: 'Close to approval limit',
    UNUSUAL_AMOUNT: 'Unusual invoice amount',
  
};

  return map[code] || code.replace(/_/g, ' ').toLowerCase().replace(/^./, c => c.toUpperCase());


}

export function humanExceptionCode(code: string): string {

  const map: Record<string, string> = {

    PRICE_MISMATCH: 'Price doesn\'t match',
    QUANTITY_MISMATCH: 'Quantity doesn\'t match',
    PO_NOT_FOUND: 'Purchase order not found',
    VENDOR_MISMATCH: 'Vendor doesn\'t match',
    BANK_DETAILS_MISMATCH: 'Bank details need verification',
    DUPLICATE_INVOICE: 'Possible duplicate invoice',
    TAX_MISMATCH: 'Tax rate doesn\'t match',
    TOTAL_MISMATCH: 'Invoice total is incorrect',
    VENDOR_INACTIVE: 'Vendor is not active',
    RISK_SIGNAL: 'Flagged for review',
  
};

  return map[code] || code.replace(/_/g, ' ').toLowerCase().replace(/^./, c => c.toUpperCase());


}

export function getStatusColor(status: string): {
 bg: string;
 text: string;
 dot: string 
} {

  switch (status) {

    case 'APPROVED': case 'PAID': case 'RESOLVED':
      return {
 bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' 
};

    case 'AWAITING_APPROVAL': case 'RECEIVED': case 'PROCESSING':
      return {
 bg: 'bg-blue-50', text: 'text-blue-700', dot: 'bg-blue-500' 
};

    case 'EXCEPTION': case 'OPEN': case 'IN_REVIEW':
      return {
 bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' 
};

    case 'PAYABLE_CREATED': case 'PARTIALLY_PAID':
      return {
 bg: 'bg-indigo-50', text: 'text-indigo-700', dot: 'bg-indigo-500' 
};

    case 'REJECTED': case 'CANCELLED':
      return {
 bg: 'bg-gray-100', text: 'text-gray-500', dot: 'bg-gray-400' 
};

    default:
      return {
 bg: 'bg-gray-100', text: 'text-gray-600', dot: 'bg-gray-400' 
};

  
}

}
