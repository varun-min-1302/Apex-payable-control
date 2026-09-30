import React, { useState, useEffect } from 'react';
import { ChevronDown, CheckCircle, Wifi, WifiOff, RefreshCw, Sun, Moon } from 'lucide-react';
import { api } from '../api/client';
import type { DemoUser } from '../types';

interface HeaderProps {
  activeEmail: string;
  onSelectPersona: (email: string) => void;
  onRefreshData?: () => void;
}

// Theme version — must match the boot script in index.html.
// Bump both when you need to reset all users to light mode defaults.
const THEME_VERSION = '4';

/**
 * Read the current resolved theme from localStorage (versioned).
 * Returns true = dark mode, false = light mode (default).
 */
function readTheme(): boolean {
  try {
    if (localStorage.getItem('themeV') !== THEME_VERSION) {
      // Stale version → wipe, reset to light, write new version
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

/**
 * Apply theme to the <html> element and persist to localStorage.
 */
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

export const Header: React.FC<HeaderProps> = ({ activeEmail, onSelectPersona, onRefreshData }) => {
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  // Initialise from versioned localStorage — false (light) for any stale/missing value
  const [isDark, setIsDark] = useState<boolean>(() => readTheme());

  // On first mount: ensure the HTML class is in sync with our state.
  // This fixes in-session HMR state drift where the old isDark=true might persist.
  useEffect(() => {
    applyTheme(isDark);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Whenever isDark changes (toggle), sync to DOM and localStorage
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
    full_name: 'Ananya Rao', email: activeEmail, roles: ['FINANCE_MANAGER'] as any
  };

  const getRoleLabel = (role: string) => {
    const map: Record<string, string> = {
      ADMIN: 'Admin', FINANCE_HEAD: 'Finance Head', FINANCE_MANAGER: 'Finance Manager',
      PROCUREMENT_MANAGER: 'Procurement', AP_CLERK: 'AP Clerk', RECEIVING_USER: 'Receiving', AUDITOR: 'Auditor',
    };
    return map[role] || role;
  };

  const getAvatarColor = (role: string) => {
    const map: Record<string, string> = {
      ADMIN: 'bg-purple-100 text-purple-700', FINANCE_HEAD: 'bg-amber-100 text-amber-700',
      FINANCE_MANAGER: 'bg-green-100 text-green-700', PROCUREMENT_MANAGER: 'bg-blue-100 text-blue-700',
      AP_CLERK: 'bg-cyan-100 text-cyan-700', RECEIVING_USER: 'bg-orange-100 text-orange-700',
      AUDITOR: 'bg-gray-100 text-gray-700',
    };
    return map[role] || 'bg-gray-100 text-gray-700';
  };

  return (
    <header className="bg-surface border-b border-border sticky top-0 z-40">
      <div className="px-6 py-3 flex items-center justify-between max-w-screen-2xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-bold text-foreground leading-none">Apex Payables</div>
            <div className="text-xs text-muted-foreground leading-none mt-0.5">Apex FinTech Technologies</div>
          </div>
        </div>
        <div className="hidden md:flex items-center gap-2 text-xs">
          {backendHealthy === null ? (
            <span className="text-muted-foreground">Connecting...</span>
          ) : backendHealthy ? (
            <span className="flex items-center gap-1.5 text-green-600"><Wifi className="w-3.5 h-3.5" />System operational</span>
          ) : (
            <span className="flex items-center gap-1.5 text-red-500"><WifiOff className="w-3.5 h-3.5" />Connection issue</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Theme toggle — light default, dark on explicit user action */}
          <button
            type="button"
            onClick={toggleTheme}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle theme"
            className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition-colors flex items-center justify-center cursor-pointer border border-transparent hover:border-border"
          >
            {isDark ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-slate-600" />
            )}
          </button>

          {onRefreshData && (
            <button onClick={onRefreshData} title="Refresh" className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          <div className="relative">
            <button onClick={() => setDropdownOpen(!dropdownOpen)} className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-muted border border-border transition-colors">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${getAvatarColor(activeUser.roles[0] || '')}`}>
                {activeUser.full_name.charAt(0)}
              </div>
              <div className="hidden sm:block text-left">
                <div className="text-sm font-semibold text-foreground leading-none">{activeUser.full_name}</div>
                <div className="text-xs text-muted-foreground leading-none mt-0.5">{getRoleLabel(activeUser.roles[0] || '')}</div>
              </div>
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            </button>
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-popover rounded-2xl border border-border shadow-modal py-2 z-50">
                <div className="px-4 py-2 border-b border-border">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Switch role (Demo)</p>
                </div>
                <div className="py-1 max-h-80 overflow-y-auto">
                  {demoUsers.map((user) => {
                    const isSelected = user.email === activeEmail;
                    return (
                      <button key={user.id} onClick={() => { onSelectPersona(user.email); setDropdownOpen(false); }}
                        className={`w-full text-left px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50 transition-colors ${isSelected ? 'bg-blue-50' : ''}`}>
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${getAvatarColor(user.roles[0] || '')}`}>
                          {user.full_name.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-800 flex items-center gap-2">
                            {user.full_name}
                            {isSelected && <CheckCircle className="w-3.5 h-3.5 text-blue-600" />}
                          </div>
                          <div className="text-xs text-gray-400">{getRoleLabel(user.roles[0] || '')}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

