import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Play,
  RotateCcw,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  FileText,
  DollarSign,
  Package,
  Layers,
  ArrowLeftRight,
  Sparkles,
  ChevronRight,
  Check,
  XCircle,
  HelpCircle,
  Zap,
  ListOrdered
} from 'lucide-react';
import { api } from '../api/client';
import type {
  ScenarioSummary,
  ScenarioSimulationResponse,
  WhatIfRequest,
  WhatIfSimulationResponse,
  DemoStep
} from '../types';
import { formatCurrency } from '../utils/format';

interface ScenarioSimulatorViewProps {
  onSelectInvoice?: (invoiceId: string) => void;
}

const E2E_DEMO_STEPS: DemoStep[] = [
  {
    step_number: 1,
    step_code: 'INTAKE',
    title: '1. Secure Document Intake & Hash Verification',
    description: 'Vendor submits PDF invoice. System validates MIME type, magic bytes, checks for exact SHA-256 duplicate, and writes immutable document intake record.',
    action_taken: 'Stored document with cryptographic hash. Generated secure access URI.',
    result_status: 'RECEIVED',
    key_metric: '100% SHA-256 Verified',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 2,
    step_code: 'AI_EXTRACT',
    title: '2. Gemini AI Structured Extraction',
    description: 'Gemini extraction engine parses invoice headers, tax registrations, line items, and bank remittances with field-level confidence scores.',
    action_taken: 'Extracted structured draft schema. Architectural invariant: AI Extraction != Financial Validation.',
    result_status: 'EXTRACTED',
    key_metric: '98.5% Field Confidence',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 3,
    step_code: 'HUMAN_REVIEW',
    title: '3. Human-in-the-Loop Confirmation',
    description: 'AP Clerk reviews the extracted values against the original document side-by-side, edits discrepancies if any, and confirms draft.',
    action_taken: 'Clerk confirms draft. Invoice status transitions to PROCESSING. Controls trigger ONLY after DB commit.',
    result_status: 'CONFIRMED',
    key_metric: 'Human Sign-off Recorded',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 4,
    step_code: 'CONTROL_RUN',
    title: '4. Deterministic AP Control Engine (18 Rules)',
    description: '18 automated financial checks evaluate vendor master, PO approval, 3-way match (quantity & price), tax rates, and duplicate proximity.',
    action_taken: 'Evaluated 18 control rules deterministically. Zero AI hallucination in financial decisions.',
    result_status: 'EVALUATED',
    key_metric: '18 Rules Executed in 12ms',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 5,
    step_code: 'EXCEPTION_DETECTED',
    title: '5. Discrepancy & Exception Flagged',
    description: 'Scenario B triggers QUANTITY_MISMATCH: Invoice billed 120 units, but warehouse Goods Receipt confirmed only 100 units received.',
    action_taken: 'Generated APException. Prevented automatic payable creation. Invoice status set to EXCEPTION.',
    result_status: 'EXCEPTION',
    key_metric: 'Variance: +20 Units (₹24,000)',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 6,
    step_code: 'RISK_INTELLIGENCE',
    title: '6. Risk Intelligence & "Why Isn\'t This Payable?"',
    description: 'System computes deterministic risk score (78/100 HIGH) and provides human-friendly explanation: What happened, Why it matters, and What to do.',
    action_taken: 'Synthesized plain-English root cause: Billed quantity exceeds accepted warehouse delivery.',
    result_status: 'HIGH RISK (Score: 78)',
    key_metric: '3 Blocking Issues Found',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 7,
    step_code: 'WHAT_IF_SANDBOX',
    title: '7. What-If Simulation Sandbox',
    description: 'Finance manager simulates credit note adjustment: "What if invoice quantity is adjusted from 120 to 100?" in zero-mutation memory state.',
    action_taken: 'Evaluated simulated state against control rules without altering database tables.',
    result_status: 'SIMULATED',
    key_metric: 'Before/After Diff Generated',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 8,
    step_code: 'SIMULATION_CLEARED',
    title: '8. Simulation Result: All Controls Pass',
    description: 'Simulation confirms: When quantity matches 100, 3-way match passes completely and risk score plummets from 78 to 12 (LOW RISK).',
    action_taken: 'Simulated decision: APPROVED_FOR_PAYMENT. Proves corrective action will succeed.',
    result_status: 'CLEARED IN SANDBOX',
    key_metric: 'Risk Reduced by 66 pts',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 9,
    step_code: 'REVISION_UPDATE',
    title: '9. Vendor Re-Issue / Corrected Revision',
    description: 'Vendor submits corrected Revision 2 reflecting 100 units. Controls execute automatically and all 18 rules pass.',
    action_taken: 'Revision 2 created. Exception marked RESOLVED. Invoice promoted to AWAITING_APPROVAL.',
    result_status: 'AWAITING_APPROVAL',
    key_metric: '18/18 Controls Passed',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 10,
    step_code: 'APPROVAL_WORKFLOW',
    title: '10. Authorized Managerial Approval',
    description: 'Finance Manager (Tier 2 authority up to ₹5,00,000) reviews cleared controls and grants cryptographic sign-off with audit notes.',
    action_taken: 'Approval recorded with timestamp, user ID, policy tier, and justification.',
    result_status: 'APPROVED',
    key_metric: 'Authorized Sign-off',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 11,
    step_code: 'PAYABLE_LEDGER',
    title: '11. Golden Transaction: Payable Ledger Created',
    description: 'System commits approved obligation into ap.payable_ledger. Liability is now legally recognized and scheduled for payment.',
    action_taken: 'Payable number PAY-2026-0002 generated. Remaining balance ₹1,41,600 initialized.',
    result_status: 'PAYABLE_CREATED',
    key_metric: 'Liability ₹1,41,600 Recognized',
    invoice_number: 'INV-2026-0002',
  },
  {
    step_number: 12,
    step_code: 'DISBURSEMENT_AUDIT',
    title: '12. Disbursement & Cryptographic Audit Replay',
    description: 'Payment executed via NEFT banking channel. Every transition from intake to disbursement is permanently replayable in Audit Replay.',
    action_taken: 'Payment record created. Payable status marked PAID. Complete immutable hash-chain verified.',
    result_status: 'SETTLED & AUDITED',
    key_metric: 'Zero Variance / Fully Audited',
    invoice_number: 'INV-2026-0002',
  },
];

export const ScenarioSimulatorView: React.FC<ScenarioSimulatorViewProps> = ({ onSelectInvoice }) => {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('SCENARIO_B');
  const [loading, setLoading] = useState<boolean>(true);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [mode, setMode] = useState<'simulator' | 'demo'>('simulator');
  const [demoTrack, setDemoTrack] = useState<'e2e' | 'scenario'>('e2e');

  // Baseline simulation data
  const [baselineSimulation, setBaselineSimulation] = useState<ScenarioSimulationResponse | null>(null);

  // What-If Form State
  const [whatIfParams, setWhatIfParams] = useState<WhatIfRequest>({
    quantity: undefined,
    unit_price: undefined,
    tax_rate: undefined,
    receipt_quantity: undefined,
    match_vendor: undefined,
    has_po: undefined,
    po_approved: undefined,
    is_duplicate: undefined,
    bank_details_match: undefined,
  });

  const [whatIfResponse, setWhatIfResponse] = useState<WhatIfSimulationResponse | null>(null);
  const [whatIfError, setWhatIfError] = useState<string | null>(null);

  // Demo Mode State
  const [scenarioDemoSteps, setScenarioDemoSteps] = useState<DemoStep[]>([]);
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [loadingDemo, setLoadingDemo] = useState<boolean>(false);

  // Filter for control checks
  const [controlFilter, setControlFilter] = useState<'ALL' | 'FAIL' | 'PASS' | 'WARNING'>('ALL');

  // Load scenarios on mount
  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const data = await api.listScenarios();
        setScenarios(data);
        if (data.length > 0) {
          const initialId = data.some(s => s.scenario_id === 'SCENARIO_B') ? 'SCENARIO_B' : data[0].scenario_id;
          setSelectedScenarioId(initialId);
        }
      } catch (err) {
        console.error('Failed to load scenarios:', err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  // Run baseline simulation whenever selected scenario changes
  useEffect(() => {
    if (!selectedScenarioId) return;

    const runBaseline = async () => {
      try {
        setSimulating(true);
        setWhatIfResponse(null);
        setWhatIfError(null);
        const sim = await api.simulateScenario(selectedScenarioId);
        setBaselineSimulation(sim);

        // Pre-fill what-if form inputs from baseline items
        const firstItem = sim.inputs.invoice.items?.[0];
        setWhatIfParams({
          quantity: firstItem ? Number(firstItem.quantity) : undefined,
          unit_price: firstItem ? Number(firstItem.unit_price) : undefined,
          tax_rate: firstItem ? Number(firstItem.tax_rate) : undefined,
          receipt_quantity: sim.inputs.goods_receipts?.[0]?.items?.[0]?.received_quantity
            ? Number(sim.inputs.goods_receipts[0].items[0].received_quantity)
            : undefined,
          match_vendor: true,
          has_po: !!sim.inputs.purchase_order,
          po_approved: sim.inputs.purchase_order?.status === 'APPROVED',
          is_duplicate: false,
          bank_details_match: true,
        });
      } catch (err: any) {
        console.error('Failed to simulate baseline scenario:', err);
      } finally {
        setSimulating(false);
      }
    };

    runBaseline();

    // If demo mode active, fetch scenario demo steps
    if (mode === 'demo') {
      fetchDemoSteps(selectedScenarioId);
    }
  }, [selectedScenarioId, mode]);

  const fetchDemoSteps = async (scId: string) => {
    try {
      setLoadingDemo(true);
      const steps = await api.getScenarioDemoSteps(scId);
      setScenarioDemoSteps(steps);
      setActiveStepIndex(0);
    } catch (err) {
      console.error('Failed to load demo steps:', err);
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleWhatIfSubmit = async (e?: React.FormEvent, overrideParams?: WhatIfRequest) => {
    if (e) e.preventDefault();
    if (!selectedScenarioId) return;

    const activeParams = overrideParams || whatIfParams;

    try {
      setSimulating(true);
      setWhatIfError(null);
      const cleanedRequest: WhatIfRequest = {};
      if (activeParams.quantity !== undefined && activeParams.quantity !== null && activeParams.quantity !== '') {
        cleanedRequest.quantity = Number(activeParams.quantity);
      }
      if (activeParams.unit_price !== undefined && activeParams.unit_price !== null && activeParams.unit_price !== '') {
        cleanedRequest.unit_price = Number(activeParams.unit_price);
      }
      if (activeParams.tax_rate !== undefined && activeParams.tax_rate !== null && activeParams.tax_rate !== '') {
        cleanedRequest.tax_rate = Number(activeParams.tax_rate);
      }
      if (activeParams.receipt_quantity !== undefined && activeParams.receipt_quantity !== null && activeParams.receipt_quantity !== '') {
        cleanedRequest.receipt_quantity = Number(activeParams.receipt_quantity);
      }
      if (activeParams.match_vendor !== undefined) cleanedRequest.match_vendor = activeParams.match_vendor;
      if (activeParams.has_po !== undefined) cleanedRequest.has_po = activeParams.has_po;
      if (activeParams.po_approved !== undefined) cleanedRequest.po_approved = activeParams.po_approved;
      if (activeParams.is_duplicate !== undefined) cleanedRequest.is_duplicate = activeParams.is_duplicate;
      if (activeParams.bank_details_match !== undefined) cleanedRequest.bank_details_match = activeParams.bank_details_match;

      const res = await api.simulateWhatIf(selectedScenarioId, cleanedRequest);
      setWhatIfResponse(res);
    } catch (err: any) {
      setWhatIfError(err.message || 'What-If simulation failed');
    } finally {
      setSimulating(false);
    }
  };

  const handleResetWhatIf = () => {
    if (!baselineSimulation) return;
    const firstItem = baselineSimulation.inputs.invoice.items?.[0];
    setWhatIfParams({
      quantity: firstItem ? Number(firstItem.quantity) : undefined,
      unit_price: firstItem ? Number(firstItem.unit_price) : undefined,
      tax_rate: firstItem ? Number(firstItem.tax_rate) : undefined,
      receipt_quantity: baselineSimulation.inputs.goods_receipts?.[0]?.items?.[0]?.received_quantity
        ? Number(baselineSimulation.inputs.goods_receipts[0].items[0].received_quantity)
        : undefined,
      match_vendor: true,
      has_po: !!baselineSimulation.inputs.purchase_order,
      po_approved: baselineSimulation.inputs.purchase_order?.status === 'APPROVED',
      is_duplicate: false,
      bank_details_match: true,
    });
    setWhatIfResponse(null);
    setWhatIfError(null);
  };

  // Quick preset helper
  const getPresetAction = () => {
    if (!selectedScenarioId) return null;
    const sc = scenarios.find(s => s.scenario_id === selectedScenarioId);
    const code = (sc?.scenario_code || selectedScenarioId).toUpperCase();

    if (code.includes('SCENARIO B') || selectedScenarioId === 'SCENARIO_B' || selectedScenarioId === 'scenario-b') {
      return {
        label: 'Align Qty to Received Goods (120 → 100)',
        patch: { quantity: 100, receipt_quantity: 100 },
      };
    }
    if (code.includes('SCENARIO C') || selectedScenarioId === 'SCENARIO_C' || selectedScenarioId === 'scenario-c') {
      return {
        label: 'Align Unit Price to PO (₹1,500 → ₹1,200)',
        patch: { unit_price: 1200 },
      };
    }
    if (code.includes('SCENARIO D') || selectedScenarioId === 'SCENARIO_D' || selectedScenarioId === 'scenario-d') {
      return {
        label: 'Set PO Status to Approved',
        patch: { po_approved: true },
      };
    }
    if (code.includes('SCENARIO G') || selectedScenarioId === 'SCENARIO_G' || selectedScenarioId === 'scenario-g') {
      return {
        label: 'Mark as Unique Non-Duplicate',
        patch: { is_duplicate: false },
      };
    }
    if (code.includes('SCENARIO K') || selectedScenarioId === 'SCENARIO_K' || selectedScenarioId === 'scenario-k') {
      return {
        label: 'Restore Verified Bank Account',
        patch: { bank_details_match: true },
      };
    }
    return null;
  };

  const handleApplyPreset = (preset: { label: string; patch: Partial<WhatIfRequest> }) => {
    const updated = { ...whatIfParams, ...preset.patch };
    setWhatIfParams(updated);
    handleWhatIfSubmit(undefined, updated);
  };

  const activeScenario = scenarios.find(s => s.scenario_id === selectedScenarioId);
  const presetAction = getPresetAction();

  // Active display simulation (either what-if or baseline)
  const currentSim = whatIfResponse ? whatIfResponse.simulated_output : baselineSimulation;

  const filteredChecks = currentSim?.control_checks.filter(c => {
    if (controlFilter === 'ALL') return true;
    if (controlFilter === 'FAIL') return c.status === 'FAIL';
    if (controlFilter === 'PASS') return c.status === 'PASS';
    if (controlFilter === 'WARNING') return c.status === 'WARNING';
    return true;
  }) || [];

  // Active demo steps list
  const currentDemoSteps = demoTrack === 'e2e' ? E2E_DEMO_STEPS : scenarioDemoSteps;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-indigo-100 text-indigo-800 border border-indigo-200">
              Control Simulator &amp; Stress Testing
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              Zero DB Mutation
            </span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AP Control Simulator</h1>
          <p className="text-sm text-gray-500 mt-1 max-w-2xl">
            Execute in-memory financial validations, test edge-case stress scenarios (A–O), inspect deterministic risk signals, and explore parameter changes in the interactive What-If sandbox.
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-1 bg-white border border-gray-200 p-1 rounded-xl shadow-xs self-start md:self-auto">
          <button
            type="button"
            onClick={() => setMode('simulator')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              mode === 'simulator'
                ? 'bg-gray-900 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Sandbox Simulator
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('demo');
              if (selectedScenarioId) fetchDemoSteps(selectedScenarioId);
            }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              mode === 'demo'
                ? 'bg-gray-900 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Demo Walkthrough
          </button>
        </div>
      </div>

      {/* Scenario Selector Row */}
      <div className="bg-white rounded-2xl border border-gray-200 p-4 shadow-card">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
            <FlaskConical className="w-4 h-4 text-indigo-600" />
            Select Test Scenario (Scenarios A through O)
          </span>
          <span className="text-xs text-gray-400 font-mono">
            {scenarios.length} Scenarios Available
          </span>
        </div>

        {loading ? (
          <div className="h-14 bg-gray-100 rounded-xl animate-pulse" />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
            {scenarios.map(sc => {
              const isSelected = sc.scenario_id === selectedScenarioId;
              const isPassing = sc.expected_outcome === 'PAYABLE_CREATED' || sc.expected_outcome === 'APPROVED';

              return (
                <button
                  key={sc.scenario_id}
                  type="button"
                  onClick={() => setSelectedScenarioId(sc.scenario_id)}
                  className={`p-2.5 rounded-xl border text-left transition-all relative ${
                    isSelected
                      ? 'bg-indigo-50/80 border-indigo-500 ring-2 ring-indigo-500/20 shadow-xs'
                      : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-indigo-700">
                      {sc.scenario_code}
                    </span>
                    <span
                      className={`w-2 h-2 rounded-full ${
                        isPassing ? 'bg-emerald-500' : 'bg-red-500'
                      }`}
                      title={isPassing ? 'Expected Pass' : 'Expected Exception'}
                    />
                  </div>
                  <div className="text-[11px] font-semibold text-gray-900 truncate mt-1">
                    {sc.scenario_name.replace(/^Scenario [A-O]:\s*/, '')}
                  </div>
                  <div className="text-[10px] text-gray-400 truncate mt-0.5">
                    {sc.invoice_number}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Active Scenario Summary Card */}
      {activeScenario && (
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono font-bold text-sm text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-100">
                {activeScenario.scenario_code}
              </span>
              <h2 className="text-base font-bold text-gray-900">{activeScenario.scenario_name}</h2>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                  activeScenario.expected_outcome === 'PAYABLE_CREATED' || activeScenario.expected_outcome === 'APPROVED'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-red-50 text-red-700 border-red-200'
                }`}
              >
                Expected: {activeScenario.expected_outcome}
              </span>
            </div>
            <p className="text-xs text-gray-600 mt-1">{activeScenario.summary}</p>
            <div className="flex items-center gap-3 text-[11px] text-gray-500 pt-1">
              <span>Primary Control: <strong className="text-gray-800 font-mono">{activeScenario.primary_control}</strong></span>
              <span>·</span>
              <span>Category: <strong className="text-gray-800">{activeScenario.risk_category}</strong></span>
              <span>·</span>
              <span>Invoice: <strong className="text-gray-800 font-mono">{activeScenario.invoice_number}</strong></span>
            </div>
          </div>

          {activeScenario.invoice_id && onSelectInvoice && (
            <button
              type="button"
              onClick={() => onSelectInvoice(activeScenario.invoice_id!)}
              className="px-3.5 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-semibold rounded-xl transition-colors whitespace-nowrap self-start md:self-auto"
            >
              Inspect Production Invoice &rarr;
            </button>
          )}
        </div>
      )}

      {/* DEMO MODE VIEW */}
      {mode === 'demo' && (
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-card space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gray-100 pb-4 gap-3">
            <div>
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                Hackathon Presentation Walkthrough Mode
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Structured narrative demonstrating how the control engine detects risks, enforces policy, and records auditable transactions.
              </p>
            </div>

            {/* Track Switcher */}
            <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-xl text-xs font-semibold self-start sm:self-auto">
              <button
                type="button"
                onClick={() => {
                  setDemoTrack('e2e');
                  setActiveStepIndex(0);
                }}
                className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                  demoTrack === 'e2e' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <ListOrdered className="w-3.5 h-3.5" />
                12-Step Full Story
              </button>
              <button
                type="button"
                onClick={() => {
                  setDemoTrack('scenario');
                  setActiveStepIndex(0);
                  if (selectedScenarioId) fetchDemoSteps(selectedScenarioId);
                }}
                className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                  demoTrack === 'scenario' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <FlaskConical className="w-3.5 h-3.5" />
                Scenario Deep-Dive
              </button>
            </div>
          </div>

          {loadingDemo ? (
            <div className="h-40 bg-gray-50 rounded-xl animate-pulse" />
          ) : currentDemoSteps.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">
              Loading demo narrative steps...
            </div>
          ) : (
            <div className="space-y-6">
              {/* Stepper Pills */}
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2">
                {currentDemoSteps.map((step, idx) => {
                  const isActive = idx === activeStepIndex;
                  const isDone = idx < activeStepIndex;

                  return (
                    <button
                      key={step.step_number}
                      type="button"
                      onClick={() => setActiveStepIndex(idx)}
                      className={`p-2.5 rounded-xl border text-left transition-all ${
                        isActive
                          ? 'bg-amber-50/80 border-amber-400 ring-2 ring-amber-400/20'
                          : isDone
                          ? 'bg-emerald-50/50 border-emerald-200 text-emerald-800'
                          : 'bg-gray-50 border-gray-200 text-gray-500'
                      }`}
                    >
                      <div className="text-[10px] font-mono font-bold uppercase">
                        Step {step.step_number}
                      </div>
                      <div className="text-xs font-bold truncate mt-0.5">
                        {step.title.replace(/^\d+\.\s*/, '')}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Current Active Step Card */}
              {currentDemoSteps[activeStepIndex] && (
                <div className="bg-gradient-to-br from-gray-900 to-gray-800 text-white p-6 rounded-2xl shadow-lg space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-400/20 text-amber-300 border border-amber-400/30 uppercase">
                        {currentDemoSteps[activeStepIndex].step_code}
                      </span>
                      <h4 className="text-xl font-bold text-white mt-2">
                        {currentDemoSteps[activeStepIndex].title}
                      </h4>
                      <p className="text-sm text-gray-300 mt-1 leading-relaxed max-w-2xl">
                        {currentDemoSteps[activeStepIndex].description}
                      </p>
                    </div>

                    <div className="bg-white/10 p-3 rounded-xl border border-white/15 text-right flex-shrink-0">
                      <div className="text-[10px] uppercase font-bold text-gray-400">Key Metric</div>
                      <div className="text-sm font-bold text-amber-300 mt-0.5 font-mono">
                        {currentDemoSteps[activeStepIndex].key_metric}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-white/10 text-xs">
                    <div className="bg-white/5 p-3 rounded-xl border border-white/10">
                      <span className="text-gray-400 block font-bold uppercase text-[10px]">
                        Control Action Taken
                      </span>
                      <span className="text-gray-200 mt-1 block">
                        {currentDemoSteps[activeStepIndex].action_taken}
                      </span>
                    </div>

                    <div className="bg-white/5 p-3 rounded-xl border border-white/10">
                      <span className="text-gray-400 block font-bold uppercase text-[10px]">
                        Result Status &amp; Ledger Integrity
                      </span>
                      <span className="text-emerald-300 font-semibold mt-1 block flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        {currentDemoSteps[activeStepIndex].result_status}
                      </span>
                    </div>
                  </div>

                  {/* Stepper Navigation Buttons */}
                  <div className="flex items-center justify-between pt-2">
                    <button
                      type="button"
                      disabled={activeStepIndex === 0}
                      onClick={() => setActiveStepIndex(prev => Math.max(0, prev - 1))}
                      className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      &larr; Previous Step
                    </button>

                    <button
                      type="button"
                      disabled={activeStepIndex >= currentDemoSteps.length - 1}
                      onClick={() => setActiveStepIndex(prev => Math.min(currentDemoSteps.length - 1, prev + 1))}
                      className="px-5 py-2 rounded-xl bg-amber-400 hover:bg-amber-300 text-gray-900 text-xs font-bold transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1.5"
                    >
                      Next Step &rarr;
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SIMULATOR & WHAT-IF SANDBOX VIEW */}
      {mode === 'simulator' && (
        <div className="space-y-6">
          {/* Main 2-Column Layout: Left = What-If Sandbox Form; Right = Results & Before/After */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column (5 cols): What-If Sandbox Controls */}
            <div className="lg:col-span-5 space-y-4">
              <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-card space-y-4">
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                      <Sliders className="w-4 h-4 text-indigo-600" />
                      "What-If?" Sandbox Controls
                    </h3>
                    <p className="text-[11px] text-gray-500 mt-0.5">
                      Adjust transaction variables to observe deterministic control changes.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={handleResetWhatIf}
                    className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Reset to baseline"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </div>

                {/* Instant Quick-Fix Preset Banner */}
                {presetAction && (
                  <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="min-w-0">
                      <span className="text-[10px] font-bold text-indigo-800 uppercase tracking-wider block">
                        ⚡ Quick Fix Preset
                      </span>
                      <span className="text-xs font-semibold text-gray-800 block truncate">
                        {presetAction.label}
                      </span>
                    </div>
                    <button
                      type="button"
                      disabled={simulating}
                      onClick={() => handleApplyPreset(presetAction)}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-colors whitespace-nowrap shadow-xs disabled:opacity-50 self-start sm:self-auto"
                    >
                      Apply &amp; Simulate
                    </button>
                  </div>
                )}

                <form onSubmit={handleWhatIfSubmit} className="space-y-3.5 text-xs">
                  {/* Financial Fields */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-gray-600 font-semibold mb-1">
                        Invoice Quantity
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={whatIfParams.quantity ?? ''}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            quantity: e.target.value === '' ? undefined : Number(e.target.value),
                          }))
                        }
                        placeholder="e.g. 100"
                        className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none font-mono"
                      />
                    </div>

                    <div>
                      <label className="block text-gray-600 font-semibold mb-1">
                        Unit Price (₹)
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={whatIfParams.unit_price ?? ''}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            unit_price: e.target.value === '' ? undefined : Number(e.target.value),
                          }))
                        }
                        placeholder="e.g. 1500"
                        className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none font-mono"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-gray-600 font-semibold mb-1">
                        Tax Rate (e.g. 0.18 for 18%)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={whatIfParams.tax_rate ?? ''}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            tax_rate: e.target.value === '' ? undefined : Number(e.target.value),
                          }))
                        }
                        placeholder="0.18"
                        className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none font-mono"
                      />
                    </div>

                    <div>
                      <label className="block text-gray-600 font-semibold mb-1">
                        Receipt Quantity (GR)
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={whatIfParams.receipt_quantity ?? ''}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            receipt_quantity: e.target.value === '' ? undefined : Number(e.target.value),
                          }))
                        }
                        placeholder="e.g. 100"
                        className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none font-mono"
                      />
                    </div>
                  </div>

                  {/* Boolean Overrides */}
                  <div className="space-y-2 pt-2 border-t border-gray-100">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">Vendor matches PO</span>
                      <select
                        value={whatIfParams.match_vendor === undefined ? '' : String(whatIfParams.match_vendor)}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            match_vendor: e.target.value === '' ? undefined : e.target.value === 'true',
                          }))
                        }
                        className="px-2 py-1 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none"
                      >
                        <option value="true">Yes (Match)</option>
                        <option value="false">No (Mismatch)</option>
                      </select>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">Purchase Order Exists</span>
                      <select
                        value={whatIfParams.has_po === undefined ? '' : String(whatIfParams.has_po)}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            has_po: e.target.value === '' ? undefined : e.target.value === 'true',
                          }))
                        }
                        className="px-2 py-1 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none"
                      >
                        <option value="true">Yes</option>
                        <option value="false">No (Unmatched)</option>
                      </select>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">PO Status</span>
                      <select
                        value={whatIfParams.po_approved === undefined ? '' : String(whatIfParams.po_approved)}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            po_approved: e.target.value === '' ? undefined : e.target.value === 'true',
                          }))
                        }
                        className="px-2 py-1 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none"
                      >
                        <option value="true">Approved</option>
                        <option value="false">Draft / Pending</option>
                      </select>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">Duplicate Invoice Flag</span>
                      <select
                        value={whatIfParams.is_duplicate === undefined ? '' : String(whatIfParams.is_duplicate)}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            is_duplicate: e.target.value === '' ? undefined : e.target.value === 'true',
                          }))
                        }
                        className="px-2 py-1 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none"
                      >
                        <option value="false">Unique Invoice</option>
                        <option value="true">Exact Duplicate</option>
                      </select>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">Bank Details Verified</span>
                      <select
                        value={whatIfParams.bank_details_match === undefined ? '' : String(whatIfParams.bank_details_match)}
                        onChange={e =>
                          setWhatIfParams(p => ({
                            ...p,
                            bank_details_match: e.target.value === '' ? undefined : e.target.value === 'true',
                          }))
                        }
                        className="px-2 py-1 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none"
                      >
                        <option value="true">Matches Master</option>
                        <option value="false">Mismatch / Changed</option>
                      </select>
                    </div>
                  </div>

                  {whatIfError && (
                    <div className="p-2.5 bg-red-50 text-red-700 border border-red-200 rounded-xl text-xs">
                      {whatIfError}
                    </div>
                  )}

                  <div className="pt-2 flex gap-2">
                    <button
                      type="submit"
                      disabled={simulating}
                      className="flex-1 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition-colors flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      {simulating ? 'Simulating...' : 'Run What-If Simulation'}
                    </button>
                    {whatIfResponse && (
                      <button
                        type="button"
                        onClick={handleResetWhatIf}
                        className="py-2.5 px-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-semibold transition-colors"
                      >
                        Reset
                      </button>
                    )}
                  </div>
                </form>
              </div>

              {/* Baseline Input Values Summary */}
              {baselineSimulation && (
                <div className="bg-gray-50/80 rounded-2xl border border-gray-200 p-4 space-y-2 text-xs">
                  <span className="font-bold text-gray-700 uppercase tracking-wider text-[10px] block">
                    Scenario Baseline Inputs (Read-Only Context)
                  </span>
                  <div className="space-y-1 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Vendor:</span>
                      <span className="font-semibold text-gray-800">
                        {baselineSimulation.inputs.vendor?.legal_name || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">PO Number:</span>
                      <span className="font-semibold text-gray-800">
                        {baselineSimulation.inputs.purchase_order?.po_number || 'None'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Invoice Total:</span>
                      <span className="font-semibold text-gray-800">
                        {formatCurrency(baselineSimulation.inputs.invoice.grand_total)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Items:</span>
                      <span className="font-semibold text-gray-800">
                        {baselineSimulation.inputs.invoice.items?.length || 0} line(s)
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column (7 cols): What-If Diff & Simulation Decision Outcome */}
            <div className="lg:col-span-7 space-y-4">
              {/* Before vs. After Diff (if What-If was executed) */}
              {whatIfResponse && (
                <div className="bg-white rounded-2xl border-2 border-indigo-200 p-5 shadow-card space-y-4">
                  <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                    <div className="flex items-center gap-2">
                      <ArrowLeftRight className="w-5 h-5 text-indigo-600" />
                      <div>
                        <h4 className="text-sm font-bold text-gray-900">
                          Before vs. After Simulation Diff
                        </h4>
                        <p className="text-[11px] text-gray-500">
                          Direct comparison between baseline scenario and simulated overrides.
                        </p>
                      </div>
                    </div>

                    {whatIfResponse.diff.outcome_changed && (
                      <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                        <Check className="w-3.5 h-3.5" /> Outcome Changed
                      </span>
                    )}
                  </div>

                  {/* Score & Decision Delta Cards */}
                  <div className="grid grid-cols-2 gap-3">
                    {/* Risk Score Delta */}
                    <div className="bg-gray-50 p-3.5 rounded-xl border border-gray-200 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
                          Risk Score Shift
                        </span>
                        <div className="flex items-baseline gap-2 mt-1">
                          <span className="text-lg font-bold text-gray-400 line-through font-mono">
                            {whatIfResponse.diff.before_risk_score}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 text-gray-400" />
                          <span className="text-2xl font-black text-gray-900 font-mono">
                            {whatIfResponse.diff.after_risk_score}
                          </span>
                        </div>
                      </div>
                      <span
                        className={`text-xs font-bold px-2 py-1 rounded-lg flex items-center gap-1 ${
                          whatIfResponse.diff.risk_reduced
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {whatIfResponse.diff.risk_reduced ? (
                          <TrendingDown className="w-3.5 h-3.5" />
                        ) : (
                          <TrendingUp className="w-3.5 h-3.5" />
                        )}
                        {whatIfResponse.diff.after_risk_score - whatIfResponse.diff.before_risk_score > 0 ? '+' : ''}
                        {whatIfResponse.diff.after_risk_score - whatIfResponse.diff.before_risk_score} pts
                      </span>
                    </div>

                    {/* Decision Delta */}
                    <div className="bg-gray-50 p-3.5 rounded-xl border border-gray-200 flex flex-col justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
                        Control Decision
                      </span>
                      <div className="mt-1 flex items-center gap-1.5 flex-wrap">
                        <span className="text-[11px] font-semibold text-gray-400 line-through truncate">
                          {whatIfResponse.diff.before_decision}
                        </span>
                        <ArrowRight className="w-3 h-3 text-gray-400" />
                        <span className="text-xs font-bold text-indigo-700 truncate">
                          {whatIfResponse.diff.after_decision}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Affected Controls Summary */}
                  {whatIfResponse.diff.affected_controls.length > 0 && (
                    <div className="space-y-2 pt-2 border-t border-gray-100">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
                        Impacted Control Rules ({whatIfResponse.diff.affected_controls.length})
                      </span>
                      <div className="space-y-1.5">
                        {whatIfResponse.diff.affected_controls.map(item => (
                          <div
                            key={item.control_code}
                            className="bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 flex items-center justify-between text-xs"
                          >
                            <span className="font-semibold text-gray-800">{item.title}</span>
                            <div className="flex items-center gap-2">
                              <span
                                className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                  item.before_status === 'PASS'
                                    ? 'bg-green-100 text-green-700'
                                    : 'bg-red-100 text-red-700'
                                }`}
                              >
                                {item.before_status}
                              </span>
                              <ArrowRight className="w-3 h-3 text-gray-400" />
                              <span
                                className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                  item.after_status === 'PASS'
                                    ? 'bg-green-100 text-green-700'
                                    : 'bg-red-100 text-red-700'
                                }`}
                              >
                                {item.after_status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Control Impact Map */}
                  {whatIfResponse.impact_map.length > 0 && (
                    <div className="pt-2 border-t border-gray-100 space-y-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
                        Control Impact Map
                      </span>
                      <div className="space-y-2">
                        {whatIfResponse.impact_map.map((node, i) => (
                          <div
                            key={i}
                            className="bg-indigo-50/60 border border-indigo-100 rounded-xl p-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-gray-900 bg-white px-2 py-0.5 rounded border border-gray-200 text-[11px]">
                                {node.changed_input}
                              </span>
                              <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
                              <span className="text-gray-700 font-medium">
                                Controls: {node.affected_controls.join(', ')}
                              </span>
                            </div>
                            <span className="font-bold text-indigo-700 bg-white px-2 py-0.5 rounded border border-indigo-200 text-[10px] self-start sm:self-auto">
                              &rarr; {node.final_outcome}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Simulation Decision & Next Action Card */}
              {currentSim && (
                <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-card space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                        {whatIfResponse ? 'Simulated Decision' : 'Baseline Decision'}
                      </span>
                      <div className="flex items-center gap-2.5 mt-1">
                        <span
                          className={`text-lg font-bold px-3 py-1 rounded-xl flex items-center gap-1.5 ${
                            currentSim.decision === 'APPROVED_FOR_PAYMENT' || currentSim.decision === 'AWAITING_APPROVAL'
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                              : 'bg-red-100 text-red-800 border border-red-200'
                          }`}
                        >
                          {currentSim.decision === 'APPROVED_FOR_PAYMENT' || currentSim.decision === 'AWAITING_APPROVAL' ? (
                            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-600" />
                          )}
                          {currentSim.decision}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 mt-2 font-medium">
                        {currentSim.next_action}
                      </p>
                    </div>

                    <div className="bg-gray-50 p-3 rounded-xl border border-gray-200 text-right flex-shrink-0">
                      <span className="text-[10px] uppercase font-bold text-gray-400 block">
                        Risk Score
                      </span>
                      <span className="text-2xl font-black text-gray-900 font-mono">
                        {currentSim.risk_profile.risk_score}
                        <span className="text-xs text-gray-400 font-semibold">/100</span>
                      </span>
                      <div
                        className={`text-[9px] font-bold uppercase mt-0.5 ${
                          currentSim.risk_profile.risk_level === 'CRITICAL'
                            ? 'text-red-700'
                            : currentSim.risk_profile.risk_level === 'HIGH'
                            ? 'text-orange-700'
                            : currentSim.risk_profile.risk_level === 'MEDIUM'
                            ? 'text-amber-700'
                            : 'text-emerald-700'
                        }`}
                      >
                        {currentSim.risk_profile.risk_level} Risk
                      </div>
                    </div>
                  </div>

                  {/* 18-Rule Control Pipeline Results Table */}
                  <div className="pt-3 border-t border-gray-100 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider">
                        Control Pipeline Execution ({currentSim.control_checks.length} Checks)
                      </h4>

                      <div className="flex items-center gap-1 bg-gray-100 p-0.5 rounded-lg text-[10px] font-semibold">
                        {(['ALL', 'FAIL', 'PASS', 'WARNING'] as const).map(f => (
                          <button
                            key={f}
                            type="button"
                            onClick={() => setControlFilter(f)}
                            className={`px-2 py-0.5 rounded ${
                              controlFilter === f
                                ? 'bg-white text-gray-900 shadow-xs'
                                : 'text-gray-500 hover:text-gray-900'
                            }`}
                          >
                            {f}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="max-h-72 overflow-y-auto space-y-1.5 pr-1 divide-y divide-gray-100">
                      {filteredChecks.map(check => {
                        const isPass = check.status === 'PASS';
                        const isFail = check.status === 'FAIL';

                        return (
                          <div
                            key={check.control_code}
                            className="pt-1.5 pb-1 flex items-start justify-between gap-3 text-xs"
                          >
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                                    isPass ? 'bg-emerald-500' : isFail ? 'bg-red-500' : 'bg-amber-500'
                                  }`}
                                />
                                <span className="font-semibold text-gray-800 truncate">
                                  {check.title}
                                </span>
                                <span className="text-[10px] font-mono text-gray-400">
                                  {check.control_code}
                                </span>
                              </div>
                              {check.variance && (
                                <div className="text-[11px] font-mono text-gray-600 mt-0.5 ml-3.5">
                                  Variance: {check.variance}
                                </div>
                              )}
                              {check.message && (
                                <div className="text-[11px] text-gray-500 mt-0.5 ml-3.5">
                                  {check.message}
                                </div>
                              )}
                            </div>

                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-md flex-shrink-0 ${
                                isPass
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : isFail
                                  ? 'bg-red-50 text-red-700 border border-red-200'
                                  : 'bg-amber-50 text-amber-700 border border-amber-200'
                              }`}
                            >
                              {check.status}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
