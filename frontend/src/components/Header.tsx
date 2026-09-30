import React from 'react';
import {
  Bell,
  RefreshCw,
  Plus,
  Sparkles,
  LayoutDashboard,
  FileText,
  AlertCircle,
  CheckSquare,
  CreditCard,
  Building2,
  Activity,
  FlaskConical,
  Sliders
} from 'lucide-react';
import type { NavTab } from './Sidebar';

interface HeaderProps {
  currentTab: NavTab;
  openExceptionsCount: number;
  pendingApprovalsCount: number;
  onOpenAddInvoice?: () => void;
  onNavigateTab: (tab: NavTab) => void;
  onRefreshData?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  openExceptionsCount,
  pendingApprovalsCount,
  onOpenAddInvoice,
  onNavigateTab,
  onRefreshData
}) => {
  const getPageInfo = (tab: NavTab) => {
    switch (tab) {
      case 'home':
        return { title: 'Control Center Overview', icon: LayoutDashboard };
      case 'invoices':
        return { title: 'Invoice Ledger & Extraction', icon: FileText };
      case 'attention':
        return { title: 'Needs Attention (Exceptions)', icon: AlertCircle };
      case 'approvals':
        return { title: 'Authority Sign-offs & Approvals', icon: CheckSquare };
      case 'payments':
        return { title: 'Payment Ledger & Disbursements', icon: CreditCard };
      case 'procurement':
        return { title: 'Vendors, POs & Goods Receipts', icon: Building2 };
      case 'simulator':
        return { title: 'Scenario & Rule Simulator', icon: Sparkles };
      case 'finathon':
        return { title: 'Finathon Benchmark Scenarios (A–O)', icon: Sliders };
      case 'activity':
        return { title: 'Audit Trail & Verification Activity', icon: Activity };
      default:
        return { title: 'Accounts Payable Control', icon: LayoutDashboard };
    }
  };

  const totalNotifications = openExceptionsCount + pendingApprovalsCount;
  const page = getPageInfo(currentTab);
  const PageIcon = page.icon;

  return (
    <header className="bg-surface/90 backdrop-blur-md border-b border-border sticky top-0 z-30 px-6 sm:px-8 py-3.5 flex items-center justify-between gap-4 transition-colors">
      
      {/* 1. Left Breadcrumb / Page Title */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-8 h-8 rounded-xl bg-card border border-border flex items-center justify-center text-primary shadow-xs flex-shrink-0">
          <PageIcon className="w-4 h-4" />
        </div>
        <div className="min-w-0 leading-tight">
          <div className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
            <span>Apex Payables</span>
            <span>/</span>
            <span className="text-foreground font-semibold">{page.title}</span>
          </div>
        </div>
      </div>

      {/* 2. Right Quick Actions & Alerts */}
      <div className="flex items-center gap-2.5 flex-shrink-0">
        
        {/* Refresh button */}
        {onRefreshData && (
          <button
            onClick={onRefreshData}
            title="Refresh Ledger Data"
            className="p-2 rounded-xl text-muted-foreground hover:text-foreground bg-card hover:bg-muted border border-border shadow-xs hover:shadow-sm transition-all cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}

        {/* Notifications button */}
        <button
          onClick={() => onNavigateTab('attention')}
          title={`${totalNotifications} items requiring attention`}
          className="relative p-2 rounded-xl text-muted-foreground hover:text-foreground bg-card hover:bg-muted border border-border shadow-xs hover:shadow-sm transition-all cursor-pointer"
        >
          <Bell className="w-4 h-4" />
          {totalNotifications > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-amber-500 ring-2 ring-card animate-pulse" />
          )}
        </button>

        {/* Shortcut to Simulator */}
        <button
          onClick={() => onNavigateTab('simulator')}
          className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 bg-card hover:bg-muted text-foreground text-xs font-semibold rounded-xl border border-border shadow-xs hover:shadow-sm transition-all cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          Simulator
        </button>

        {/* Primary Intake Action */}
        {onOpenAddInvoice && (
          <button
            onClick={onOpenAddInvoice}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-xl shadow-xs hover:shadow-md transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Upload Invoice
          </button>
        )}

      </div>

    </header>
  );
};
