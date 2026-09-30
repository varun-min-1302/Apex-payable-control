export function exceptionWhatHappened(code: string): string {
  const map: Record<string, string> = {
    PRICE_MISMATCH: 'The invoice price is higher than the agreed purchase order price.',
    QUANTITY_MISMATCH: 'The invoice quantity is more than what was actually received.',
    PO_NOT_FOUND: 'This invoice does not reference a valid purchase order.',
    VENDOR_MISMATCH: 'The invoice vendor does not match the vendor on the purchase order.',
    BANK_DETAILS_MISMATCH: 'The bank account on this invoice differs from our verified vendor records.',
    DUPLICATE_INVOICE: 'This invoice appears to be a duplicate of one we have already processed.',
    TAX_MISMATCH: 'The tax rate on this invoice differs from what was agreed in the purchase order.',
    TOTAL_MISMATCH: 'The invoice total does not match the sum of the line items.',
    VENDOR_INACTIVE: 'This vendor is not currently active in our system.',
    RISK_SIGNAL: 'This invoice has been flagged for additional review.',
  };
  return map[code] || 'This invoice has been flagged and needs review before it can proceed.';
}

export function exceptionWhatToDo(code: string): string {
  const map: Record<string, string> = {
    PRICE_MISMATCH: 'Contact the vendor to request a corrected invoice or credit note matching the agreed price.',
    QUANTITY_MISMATCH: 'Check with the warehouse team to confirm actual goods received, then request a corrected invoice.',
    PO_NOT_FOUND: 'Ask the procurement team to raise a purchase order, or reject this invoice if unauthorized.',
    VENDOR_MISMATCH: 'Verify whether this vendor is authorized to supply under the referenced purchase order.',
    BANK_DETAILS_MISMATCH: 'Verify the vendor\'s bank account directly through official channels before proceeding.',
    DUPLICATE_INVOICE: 'Check if this invoice has already been paid. If so, reject it. If different goods, ask for a new invoice number.',
    TAX_MISMATCH: 'Confirm the applicable tax rate with the vendor and request a corrected invoice.',
    TOTAL_MISMATCH: 'Ask the vendor to reissue the invoice with correct totals.',
    VENDOR_INACTIVE: 'Reactivate the vendor in the system if appropriate, or reject this invoice.',
    RISK_SIGNAL: 'Review the flagged details carefully before approving.',
  };
  return map[code] || 'Review the issue and take appropriate corrective action before approving this invoice.';
}
