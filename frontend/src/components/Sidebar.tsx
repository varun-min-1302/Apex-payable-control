import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  FileText,
  AlertCircle,
  CheckSquare,
  CreditCard,
  Building2,
  Activity,
  FlaskConical,
  Sliders,
  Sun,
  Moon,
  ChevronDown,
  CheckCircle,
  Wifi,
  WifiOff,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import type { DemoUser } from '../types';

export type NavTab =
  | 'home'
  | 'invoices'
  | 'attention'
  | 'approvals'
  | 'payments'
  | 'procurement'
  | 'activity'
  | 'simulator'
  | 'finathon';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  openExceptionsCount: number;
  pendingApprovalsCount: number;
  activeEmail: string;
  onSelectPersona: (email: string) => void;
  onRefreshData?: () => void;
}

const THEME_VERSION = '5';

function readTheme(): boolean {
  try {
    if (localStorage.getItem('themeV') !== THEME_VERSION) {
      localStorage.removeItem('theme');
      localStorage.setItem('themeV', THEME_VERSION);
      document.documentElement.classList.remove('dark');
      return false;
    }
    return localStorage.getItem('theme') === 'dark';
  } catch {
    return false;
  }
}

function applyTheme(dark: boolean) {
  try {
    if (dark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.removeItem('theme');
    }
    localStorage.setItem('themeV', THEME_VERSION);
  } catch { /* ignore */ }
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  openExceptionsCount,
  pendingApprovalsCount,
  activeEmail,
  onSelectPersona,
}) => {
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [isDark, setIsDark] = useState<boolean>(() => readTheme());

  useEffect(() => {
    applyTheme(isDark);
  }, [isDark]);

  const toggleTheme = () => setIsDark(prev => !prev);

  useEffect(() => {
    api.getDemoUsers()
      .then(users => setDemoUsers(users))
      .catch(() => {
        setDemoUsers([
          { id: '1', email: 'priya.nair@apexfin.in', full_name: 'Priya Nair', roles: ['AP_CLERK'] },
          { id: '2', email: 'vikram.malhotra@apexfin.in', full_name: 'Vikram Malhotra', roles: ['PROCUREMENT_MANAGER'] },
          { id: '3', email: 'sneha.kulkarni@apexfin.in', full_name: 'Sneha Kulkarni', roles: ['RECEIVING_USER'] },
          { id: '4', email: 'ananya.rao@apexfin.in', full_name: 'Ananya Rao', roles: ['FINANCE_MANAGER'] },
          { id: '5', email: 'rohan.verma@apexfin.in', full_name: 'Rohan Verma', roles: ['FINANCE_HEAD'] },
          { id: '6', email: 'sunita.mehta@apexfin.in', full_name: 'Sunita Mehta', roles: ['AUDITOR'] },
          { id: '7', email: 'rajesh.sharma@apexfin.in', full_name: 'Rajesh Sharma', roles: ['ADMIN'] },
        ]);
      });
    fetch('/health')
      .then(res => res.json())
      .then(data => setBackendHealthy(data.status === 'HEALTHY'))
      .catch(() => setBackendHealthy(false));
  }, []);

  const activeUser = demoUsers.find(u => u.email === activeEmail) || {
    full_name: 'Ananya Rao',
    email: activeEmail,
    roles: ['FINANCE_MANAGER'] as any
  };

  const getRoleLabel = (role: string) => {
    const map: Record<string, string> = {
      ADMIN: 'Admin',
      FINANCE_HEAD: 'Finance Head',
      FINANCE_MANAGER: 'Finance Manager',
      PROCUREMENT_MANAGER: 'Procurement',
      AP_CLERK: 'AP Clerk',
      RECEIVING_USER: 'Receiving',
      AUDITOR: 'Auditor',
    };
    return map[role] || role;
  };

  const mainNavItems = [
    { tab: 'home' as NavTab, label: 'Overview', icon: LayoutDashboard },
    { tab: 'invoices' as NavTab, label: 'Invoices', icon: FileText },
    { tab: 'attention' as NavTab, label: 'Needs Attention', icon: AlertCircle, badge: openExceptionsCount, badgeType: 'warning' },
    { tab: 'approvals' as NavTab, label: 'Approvals', icon: CheckSquare, badge: pendingApprovalsCount, badgeType: 'info' },
    { tab: 'payments' as NavTab, label: 'Payments', icon: CreditCard },
    { tab: 'procurement' as NavTab, label: 'Vendors & Orders', icon: Building2 },
  ];

  const toolsNavItems = [
    { tab: 'simulator' as NavTab, label: 'Control Simulator', icon: Sparkles },
    { tab: 'finathon' as NavTab, label: 'Finathon Scenarios', icon: Sliders },
    { tab: 'activity' as NavTab, label: 'Audit Activity', icon: Activity },
  ];

  const renderNavItem = (item: typeof mainNavItems[0]) => {
    const Icon = item.icon;
    const isActive = currentTab === item.tab;
    return (
      <button
        key={item.tab}
        onClick={() => onSelectTab(item.tab)}
        className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 cursor-pointer ${
          isActive
            ? 'bg-foreground text-background font-semibold shadow-xs'
            : 'text-muted-foreground hover:text-foreground hover:bg-muted/80'
        }`}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-inherit' : 'text-muted-foreground'}`} />
          <span className="truncate">{item.label}</span>
        </div>
        {item.badge !== undefined && item.badge > 0 && (
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full leading-none flex-shrink-0 ${
              isActive
                ? 'bg-background/20 text-inherit'
                : item.badgeType === 'warning'
                ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-400 border border-amber-300 dark:border-amber-800'
                : 'bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-400 border border-blue-300 dark:border-blue-800'
            }`}
          >
            {item.badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <aside className="w-64 bg-card border-r border-border h-screen flex flex-col flex-shrink-0 sticky top-0 z-40 select-none">
      
      {/* 1. Sidebar Brand Header */}
      <div className="p-5 border-b border-border flex items-center gap-3 cursor-pointer" onClick={() => onSelectTab('home')}>
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-700 via-primary to-indigo-500 flex items-center justify-center shadow-xs flex-shrink-0">
          <svg viewBox="0 0 24 24" className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="leading-tight min-w-0">
          <div className="text-sm font-extrabold text-foreground tracking-tight truncate">
            Apex Payables
          </div>
          <div className="text-[10px] text-muted-foreground font-medium truncate">
            Apex FinTech Technologies
          </div>
        </div>
      </div>

      {/* 2. Navigation Items List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        
        {/* Main Section */}
        <div>
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider px-3 mb-2">
            Main Menu
          </div>
          <div className="space-y-1">
            {mainNavItems.map(renderNavItem)}
          </div>
        </div>

        {/* Tools Section */}
        <div>
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider px-3 mb-2">
            Controls &amp; Audit
          </div>
          <div className="space-y-1">
            {toolsNavItems.map(renderNavItem)}
          </div>
        </div>

      </div>

      {/* 3. Bottom Utility Area: Health + Theme + User Persona */}
      <div className="p-3 border-t border-border bg-muted/20 space-y-2.5">
        
        {/* System Health & Theme Toggle Bar */}
        <div className="flex items-center justify-between px-2">
          {/* Health */}
          <div className="flex items-center gap-1.5 text-[11px] font-medium">
            {backendHealthy === null ? (
              <span className="text-muted-foreground text-[10px]">Connecting...</span>
            ) : backendHealthy ? (
              <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Operational
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-red-500 font-semibold text-[11px]">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                Offline
              </span>
            )}
          </div>

          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleTheme}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle theme"
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground bg-card hover:bg-muted border border-border shadow-xs hover:shadow-sm transition-all cursor-pointer"
          >
            {isDark ? (
              <Sun className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <Moon className="w-3.5 h-3.5 text-slate-700" />
            )}
          </button>
        </div>

        {/* User Persona Switcher */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-muted/80 border border-border transition-all bg-card shadow-xs hover:shadow-sm cursor-pointer"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-primary/10 text-primary font-bold text-xs flex items-center justify-center flex-shrink-0">
                {activeUser.full_name.charAt(0)}
              </div>
              <div className="text-left leading-tight min-w-0">
                <div className="text-xs font-semibold text-foreground truncate">{activeUser.full_name}</div>
                <div className="text-[10px] text-muted-foreground truncate">{getRoleLabel(activeUser.roles[0] || '')}</div>
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0 ml-1" />
          </button>

          {dropdownOpen && (
            <div className="absolute bottom-full left-0 right-0 mb-2 bg-popover text-popover-foreground rounded-2xl border border-border shadow-modal py-2 z-50 animate-in fade-in zoom-in-95">
              <div className="px-4 py-2 border-b border-border">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Switch Persona (Role RBAC)</p>
              </div>
              <div className="py-1 max-h-64 overflow-y-auto">
                {demoUsers.map((user) => {
                  const isSelected = user.email === activeEmail;
                  return (
                    <button
                      key={user.id}
                      onClick={() => {
                        onSelectPersona(user.email);
                        setDropdownOpen(false);
                      }}
                      className={`w-full text-left px-4 py-2.5 flex items-center gap-3 hover:bg-muted/70 transition-colors cursor-pointer ${
                        isSelected ? 'bg-primary/10' : ''
                      }`}
                    >
                      <div className="w-7 h-7 rounded-lg bg-primary/15 text-primary text-xs font-bold flex items-center justify-center flex-shrink-0">
                        {user.full_name.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                          <span className="truncate">{user.full_name}</span>
                          {isSelected && <CheckCircle className="w-3 h-3 text-primary flex-shrink-0" />}
                        </div>
                        <div className="text-[10px] text-muted-foreground truncate">{getRoleLabel(user.roles[0] || '')}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

      </div>

    </aside>
  );
};
