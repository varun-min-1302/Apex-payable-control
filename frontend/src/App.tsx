import React, {
 useState, useEffect 
} from 'react';

import {
 Header 
} from './components/Header';

import {
 Sidebar, NavTab 
} from './components/Sidebar';

import {
 HomeView 
} from './views/HomeView';

import {
 InvoicesView 
} from './views/InvoicesView';

import {
 NeedsAttentionView 
} from './views/NeedsAttentionView';

import {
 ApprovalsView 
} from './views/ApprovalsView';

import {
 PaymentsView 
} from './views/PaymentsView';

import {
 ProcurementView 
} from './views/ProcurementView';

import {
 ActivityView 
} from './views/ActivityView';

import {
 FinathonScenariosView 
} from './views/FinathonScenariosView';

import {
 ScenarioSimulatorView 
} from './views/ScenarioSimulatorView';

import {
 InvoiceDetailModal 
} from './views/InvoiceDetailModal';

import {
 api 
} from './api/client';


export function App() {

  const [currentTab, setCurrentTab] = useState<NavTab>('home');

  const [activeEmail, setActiveEmail] = useState<string>(() => api.getActiveUserEmail());

  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);

  const [openExceptionsCount, setOpenExceptionsCount] = useState<number>(0);

  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);


  const refreshBadgeCounts = async () => {

    try {

      // Use the same permission-aware endpoints that each view uses,
      // so the sidebar badge always matches what the user sees on the page.
      const [visibleExceptions, approvals] = await Promise.all([
        api.listExceptions({
 status: 'OPEN' 
}),   // RBAC-filtered, same as NeedsAttentionView
        api.listApprovals({
 status: 'PENDING' 
}),  // RBAC-filtered, same as ApprovalsView
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
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">

      {
/* Top Header */
}
      <Header
        activeEmail={
activeEmail
}
        onSelectPersona={
handleSelectPersona
}
        onRefreshData={
refreshBadgeCounts
}
      />

      {
/* Main Workspace (Sidebar + Content Area) */
}
      <div className="flex-1 flex overflow-hidden bg-background">

        {
/* Navigation Sidebar */
}
        <Sidebar
          currentTab={
currentTab
}
          onSelectTab={
setCurrentTab
}
          openExceptionsCount={
openExceptionsCount
}
          pendingApprovalsCount={
pendingApprovalsCount
}
        />

        {
/* Dynamic View Container */
}
        <main className="flex-1 overflow-y-auto px-8 py-8 bg-background">

          {
currentTab === 'home' && (
            <HomeView
              onNavigateTab={
setCurrentTab
}
              onSelectInvoice={
(id) => setSelectedInvoiceId(id)
}
              activeEmail={
activeEmail
}
            />
          )
}

          {
currentTab === 'invoices' && (
            <InvoicesView
              onSelectInvoice={
(id) => setSelectedInvoiceId(id)
}
            />
          )
}

          {
currentTab === 'attention' && (
            <NeedsAttentionView
              onSelectInvoice={
(id) => setSelectedInvoiceId(id)
}
              onRefreshParent={
refreshBadgeCounts
}
              activeEmail={
activeEmail
}
              onSelectPersona={
handleSelectPersona
}
            />
          )
}

          {
currentTab === 'approvals' && (
            <ApprovalsView
              onSelectInvoice={
(id) => setSelectedInvoiceId(id)
}
              onRefreshParent={
refreshBadgeCounts
}
              activeEmail={
activeEmail
}
              onSelectPersona={
handleSelectPersona
}
            />
          )
}

          {
currentTab === 'payments' && (
            <PaymentsView
              onRefreshParent={
refreshBadgeCounts
}
              onSelectInvoice={
(id) => setSelectedInvoiceId(id)
}
            />
          )
}

          {
currentTab === 'procurement' && (
            <ProcurementView />
          )
}

          {
currentTab === 'activity' && (
            <ActivityView />
          )
}

          {
currentTab === 'simulator' && (
            <ScenarioSimulatorView
              onSelectInvoice={
(id) => setSelectedInvoiceId(id)
}
            />
          )
}

          {
currentTab === 'finathon' && (
            <FinathonScenariosView
              onSelectInvoice={
(id) => setSelectedInvoiceId(id)
}
            />
          )
}

        </main>

      </div>

      {
/* Invoice Detail Modal */
}
      {
selectedInvoiceId && (
        <InvoiceDetailModal
          invoiceId={
selectedInvoiceId
}
          onClose={
() => setSelectedInvoiceId(null)
}
          onRefreshParent={
refreshBadgeCounts
}
          activeEmail={
activeEmail
}
          onSelectPersona={
handleSelectPersona
}
        />
      )
}

    </div>
  );


}

export default App;

