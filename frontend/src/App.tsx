import React, { useState, useEffect } from 'react';
import { Sidebar, NavTab } from './components/Sidebar';
import { Header } from './components/Header';
import { HomeView } from './views/HomeView';
import { InvoicesView } from './views/InvoicesView';
import { NeedsAttentionView } from './views/NeedsAttentionView';
import { ApprovalsView } from './views/ApprovalsView';
import { PaymentsView } from './views/PaymentsView';
import { ProcurementView } from './views/ProcurementView';
import { ActivityView } from './views/ActivityView';
import { FinathonScenariosView } from './views/FinathonScenariosView';
import { ScenarioSimulatorView } from './views/ScenarioSimulatorView';
import { InvoiceDetailModal } from './views/InvoiceDetailModal';
import { AddInvoiceModal } from './components/AddInvoiceModal';
import { InvoiceDraftReviewModal } from './components/InvoiceDraftReviewModal';
import { api } from './api/client';
import type { InvoiceDraft } from './types';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('home');
  const [activeEmail, setActiveEmail] = useState<string>(() => api.getActiveUserEmail());
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);
  const [openExceptionsCount, setOpenExceptionsCount] = useState<number>(0);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);

  // Global modals for invoice intake & draft review
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [activeDraft, setActiveDraft] = useState<InvoiceDraft | null>(null);
  const [showDraftModal, setShowDraftModal] = useState<boolean>(false);

  const refreshBadgeCounts = async () => {
    try {
      const [visibleExceptions, approvals] = await Promise.all([
        api.listExceptions({ status: 'OPEN' }),
        api.listApprovals({ status: 'PENDING' }),
      ]);
      setOpenExceptionsCount(visibleExceptions.length);
      setPendingApprovalsCount(approvals.length);
    } catch (err) {
      console.error('Failed to update badge counts:', err);
    }
  };

  useEffect(() => {
    refreshBadgeCounts();
  }, [activeEmail]);

  const handleSelectPersona = (email: string) => {
    api.setActiveUserEmail(email);
    setActiveEmail(email);
    refreshBadgeCounts();
  };

  return (
    <div className="min-h-screen w-full bg-surface text-foreground flex transition-colors overflow-hidden">
      
      {/* Sleek Left Navigation Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        openExceptionsCount={openExceptionsCount}
        pendingApprovalsCount={pendingApprovalsCount}
        activeEmail={activeEmail}
        onSelectPersona={handleSelectPersona}
        onRefreshData={refreshBadgeCounts}
      />

      {/* Main Workspace (Top Header + Dynamic View Container) */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden bg-surface">
        
        {/* Clean Top Action Header */}
        <Header
          currentTab={currentTab}
          openExceptionsCount={openExceptionsCount}
          pendingApprovalsCount={pendingApprovalsCount}
          onOpenAddInvoice={() => setShowAddModal(true)}
          onNavigateTab={setCurrentTab}
          onRefreshData={refreshBadgeCounts}
        />

        {/* Scrollable Dynamic View Content - Edge-to-edge breathing room */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-surface">
          {currentTab === 'home' && (
            <HomeView
              onNavigateTab={setCurrentTab}
              onSelectInvoice={(id) => setSelectedInvoiceId(id)}
              onOpenAddInvoice={() => setShowAddModal(true)}
              activeEmail={activeEmail}
            />
          )}

          {currentTab === 'invoices' && (
            <InvoicesView
              onSelectInvoice={(id) => setSelectedInvoiceId(id)}
            />
          )}

          {currentTab === 'attention' && (
            <NeedsAttentionView
              onSelectInvoice={(id) => setSelectedInvoiceId(id)}
              onRefreshParent={refreshBadgeCounts}
              activeEmail={activeEmail}
              onSelectPersona={handleSelectPersona}
            />
          )}

          {currentTab === 'approvals' && (
            <ApprovalsView
              onSelectInvoice={(id) => setSelectedInvoiceId(id)}
              onRefreshParent={refreshBadgeCounts}
              activeEmail={activeEmail}
              onSelectPersona={handleSelectPersona}
            />
          )}

          {currentTab === 'payments' && (
            <PaymentsView
              onRefreshParent={refreshBadgeCounts}
              onSelectInvoice={(id) => setSelectedInvoiceId(id)}
            />
          )}

          {currentTab === 'procurement' && (
            <ProcurementView />
          )}

          {currentTab === 'activity' && (
            <ActivityView />
          )}

          {currentTab === 'simulator' && (
            <ScenarioSimulatorView
              onSelectInvoice={(id) => setSelectedInvoiceId(id)}
            />
          )}

          {currentTab === 'finathon' && (
            <FinathonScenariosView
              onSelectInvoice={(id) => setSelectedInvoiceId(id)}
            />
          )}
        </main>

      </div>

      {/* Invoice Detail Modal */}
      {selectedInvoiceId && (
        <InvoiceDetailModal
          invoiceId={selectedInvoiceId}
          onClose={() => setSelectedInvoiceId(null)}
          onRefreshParent={refreshBadgeCounts}
          activeEmail={activeEmail}
          onSelectPersona={handleSelectPersona}
        />
      )}

      {/* Global Add Invoice Modal */}
      <AddInvoiceModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          refreshBadgeCounts();
        }}
        onExtractDraft={(draft) => {
          setShowAddModal(false);
          setActiveDraft(draft);
          setShowDraftModal(true);
        }}
      />

      {/* Global Review Gemini Extracted Draft Modal */}
      {showDraftModal && activeDraft && (
        <InvoiceDraftReviewModal
          draft={activeDraft}
          isOpen={showDraftModal}
          onClose={() => {
            setShowDraftModal(false);
            setActiveDraft(null);
            refreshBadgeCounts();
          }}
          onConfirmed={(result) => {
            setShowDraftModal(false);
            setActiveDraft(null);
            refreshBadgeCounts();
            if (result.invoice_id) setSelectedInvoiceId(result.invoice_id);
          }}
          onSelectInvoice={(id) => setSelectedInvoiceId(id)}
        />
      )}

    </div>
  );
}

export default App;
