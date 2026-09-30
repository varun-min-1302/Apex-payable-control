import React from 'react';
import { Home, FileText, AlertCircle, CheckSquare, CreditCard, Building2, Activity, FlaskConical } from 'lucide-react';

export type NavTab = 'home' | 'invoices' | 'attention' | 'approvals' | 'payments' | 'procurement' | 'activity' | 'finathon' | 'simulator';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  openExceptionsCount: number;
  pendingApprovalsCount: number;
}

interface NavItem {
  tab: NavTab;
  label: string;
  icon: React.ElementType;
  badge?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, openExceptionsCount, pendingApprovalsCount }) => {
  const navItems: NavItem[] = [
    { tab: 'home', label: 'Home', icon: Home },
    { tab: 'invoices', label: 'Invoices', icon: FileText },
    { tab: 'attention', label: 'Needs Attention', icon: AlertCircle, badge: openExceptionsCount },
    { tab: 'approvals', label: 'Approvals', icon: CheckSquare, badge: pendingApprovalsCount },
    { tab: 'payments', label: 'Payments', icon: CreditCard },
    { tab: 'procurement', label: 'Vendors & Orders', icon: Building2 },
    { tab: 'activity', label: 'Activity', icon: Activity },
  ];

  const secondaryItems: NavItem[] = [
    { tab: 'finathon', label: 'Finathon Scenarios', icon: FlaskConical },
  ];

  const renderItem = (item: NavItem, secondary = false) => {
    const Icon = item.icon;
    const isActive = currentTab === item.tab;
    return (
      <button key={item.tab} onClick={() => onSelectTab(item.tab)}
        className={`w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors group ${
          isActive ? 'bg-primary/10 text-primary font-semibold' : `text-muted-foreground hover:bg-muted hover:text-foreground`
        }`}>
        <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`} />
        <span className={`text-sm font-medium flex-1 ${isActive ? 'font-semibold' : ''}`}>{item.label}</span>
        {item.badge !== undefined && item.badge > 0 && (
          <span className={`text-xs font-bold min-w-[20px] h-5 flex items-center justify-center rounded-full px-1.5 ${
            item.tab === 'attention' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
          }`}>{item.badge}</span>
        )}
      </button>
    );
  };

  return (
    <nav className="w-56 bg-sidebar border-r border-border flex flex-col py-4 flex-shrink-0">
      <div className="px-3 flex-1">
        <div className="space-y-0.5">
          {navItems.map(item => renderItem(item))}
        </div>
        <div className="mt-4 pt-4 border-t border-border">
          <p className="text-[10px] uppercase font-semibold text-muted-foreground px-3 mb-2 tracking-wider">Testing & Demo</p>
          {secondaryItems.map(item => renderItem(item, true))}
        </div>
      </div>
    </nav>
  );
};


