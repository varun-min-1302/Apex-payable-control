import React, {
 useState 
} from 'react';

import {

  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  Play,
  RotateCcw

} from 'lucide-react';

import type {
 InvoiceExplanation, BlockingReason 
} from '../types';


interface WhyNotPayableCardProps {

  explanation: InvoiceExplanation | null;

  loading?: boolean;

  onRunControls?: () => void;

  runningControls?: boolean;


}

function getSeverityBadge(severity: string) {

  switch (severity?.toUpperCase()) {

    case 'CRITICAL':
      return {
 label: 'Critical', bg: 'bg-red-100 text-red-800 border-red-200' 
};

    case 'HIGH':
      return {
 label: 'High', bg: 'bg-orange-100 text-orange-800 border-orange-200' 
};

    case 'MEDIUM':
      return {
 label: 'Medium', bg: 'bg-amber-100 text-amber-800 border-amber-200' 
};

    default:
      return {
 label: 'Info', bg: 'bg-blue-100 text-blue-800 border-blue-200' 
};

  
}

}

export const WhyNotPayableCard: React.FC<WhyNotPayableCardProps> = ({

  explanation,
  loading = false,
  onRunControls,
  runningControls = false,

}) => {

  const [expandedDetails, setExpandedDetails] = useState<Record<string, boolean>>({

});


  if (loading) {

    return (
      <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5 animate-pulse space-y-3">
        <div className="h-6 bg-gray-200 rounded w-1/3" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
      </div>
    );

  
}

  if (!explanation) return null;


  const toggleTechnical = (code: string) => {

    setExpandedDetails(prev => ({
 ...prev, [code]: !prev[code] 
}));

  
};


  // 1. Payable / Ready to Disburse
  if (explanation.can_be_paid) {

    return (
      <div className="bg-green-50 border border-green-200 rounded-2xl p-5 shadow-card">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <CheckCircle className="w-5 h-5 text-green-700" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-green-950">{
explanation.headline
}</h3>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-green-200 text-green-800">
                Ready for payment
              </span>
            </div>
            <p className="text-sm text-green-800 mt-1">{
explanation.summary
}</p>
            <div className="mt-3 flex items-center gap-2 text-xs font-medium text-green-900 bg-white/70 border border-green-200 rounded-xl px-3.5 py-2">
              <ArrowRight className="w-3.5 h-3.5 text-green-700 flex-shrink-0" />
              <span>Next step: {
explanation.next_action
}</span>
            </div>
          </div>
        </div>
      </div>
    );

  
}

  // 2. Paid
  if (explanation.status === 'PAID') {

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 shadow-card">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <CheckCircle className="w-5 h-5 text-blue-700" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-bold text-blue-950">{
explanation.headline
}</h3>
            <p className="text-sm text-blue-800 mt-1">{
explanation.summary
}</p>
            <div className="mt-3 text-xs text-blue-900 font-medium">
              Next step: {
explanation.next_action
}
            </div>
          </div>
        </div>
      </div>
    );

  
}

  // 3. Awaiting Approval
  if (explanation.status === 'AWAITING_APPROVAL') {

    return (
      <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-5 shadow-card">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <Clock className="w-5 h-5 text-indigo-700" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-indigo-950">{
explanation.headline
}</h3>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-200 text-indigo-800">
                Checks Passed
              </span>
            </div>
            <p className="text-sm text-indigo-800 mt-1">{
explanation.summary
}</p>
            <div className="mt-3 flex items-center gap-2 text-xs font-medium text-indigo-900 bg-white/70 border border-indigo-200 rounded-xl px-3.5 py-2">
              <ArrowRight className="w-3.5 h-3.5 text-indigo-700 flex-shrink-0" />
              <span>Next step: {
explanation.next_action
}</span>
            </div>
          </div>
        </div>
      </div>
    );

  
}

  // 4. Pending Control Run
  const isPendingRun = explanation.blocking_reasons.some(r => r.control_code === 'CONTROL_RUN_PENDING');

  if (isPendingRun) {

    return (
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 shadow-card">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <AlertTriangle className="w-5 h-5 text-amber-700" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-bold text-amber-950">{
explanation.headline
}</h3>
            <p className="text-sm text-amber-800 mt-1">{
explanation.summary
}</p>
            {
onRunControls && (
              <div className="mt-4">
                <button
                  onClick={
onRunControls
}
                  disabled={
runningControls
}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-amber-700 hover:bg-amber-800 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors disabled:opacity-50"
                >
                  <Play className={
`w-3.5 h-3.5 fill-white ${
runningControls ? 'animate-spin' : ''
}`
} />
                  {
runningControls ? 'Running checks...' : 'Run automated checks now'
}
                </button>
              </div>
            )
}
          </div>
        </div>
      </div>
    );

  
}

  // 5. Blocked / Not Payable (Exceptions, Rejections, Control Failures)
  return (
    <div className="bg-red-50/70 border border-red-200 rounded-2xl p-5 shadow-card space-y-4">
      {
/* Top Banner */
}
      <div className="flex items-start gap-3.5">
        <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
          <XCircle className="w-5 h-5 text-red-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base font-bold text-gray-900">{
explanation.headline
}</h3>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-200">
              Cannot Be Paid
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{
explanation.summary
}</p>
        </div>
        {
onRunControls && (
          <button
            onClick={
onRunControls
}
            disabled={
runningControls
}
            title="Re-run verification checks"
            className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 text-xs font-medium rounded-xl transition-colors disabled:opacity-50 shadow-sm"
          >
            <RotateCcw className={
`w-3.5 h-3.5 ${
runningControls ? 'animate-spin' : ''
}`
} />
            {
runningControls ? 'Checking...' : 'Re-check'
}
          </button>
        )
}
      </div>

      {
/* Structured 4-Step Cards for Each Blocking Issue */
}
      <div className="space-y-3 pt-1">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Issues blocking payment ({
explanation.blocking_reasons.length
})
        </div>

        {
explanation.blocking_reasons.map((reason, idx) => {

          const sev = getSeverityBadge(reason.severity);

          const isExpanded = !!expandedDetails[reason.control_code];


          return (
            <div
              key={
`${
reason.control_code
}-${
idx
}`
}
              className="bg-white border border-red-100 rounded-xl p-4 shadow-sm space-y-3"
            >
              {
/* Issue Title + Severity */
}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-gray-900 text-sm">{
reason.title
}</span>
                  <span className={
`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
sev.bg
}`
}>
                    {
sev.label
}
                  </span>
                </div>
                <span className="font-mono text-[11px] text-gray-400 bg-gray-50 px-2 py-0.5 rounded border border-gray-100">
                  {
reason.control_code
}
                </span>
              </div>

              {
/* 1. What Happened */
}
              <div className="text-xs space-y-1">
                <div className="text-gray-400 font-semibold uppercase tracking-wider text-[10px]">1. What happened</div>
                <div className="text-gray-800 font-medium leading-relaxed bg-gray-50/80 p-2 rounded-lg border border-gray-100">
                  {
reason.what_happened
}
                </div>
              </div>

              {
/* 2. Why It Matters */
}
              <div className="text-xs space-y-1">
                <div className="text-amber-700 font-semibold uppercase tracking-wider text-[10px] flex items-center gap-1">
                  <ShieldAlert className="w-3 h-3 text-amber-600" />
                  2. Why does it matter?
                </div>
                <div className="text-gray-700 leading-relaxed bg-amber-50/50 p-2 rounded-lg border border-amber-100/60">
                  {
reason.why_it_matters
}
                </div>
              </div>

              {
/* 3. What To Do */
}
              <div className="text-xs space-y-1">
                <div className="text-blue-700 font-semibold uppercase tracking-wider text-[10px] flex items-center gap-1">
                  <ArrowRight className="w-3 h-3 text-blue-600" />
                  3. Recommended action
                </div>
                <div className="text-gray-800 font-medium leading-relaxed bg-blue-50/50 p-2 rounded-lg border border-blue-100/60">
                  {
reason.recommended_action
}
                </div>
              </div>

              {
/* 4. Collapsible Technical Details */
}
              <div className="pt-1 border-t border-gray-100">
                <button
                  type="button"
                  onClick={
() => toggleTechnical(reason.control_code)
}
                  className="flex items-center gap-1.5 text-[11px] font-semibold text-gray-400 hover:text-gray-600 uppercase tracking-wide transition-colors"
                >
                  {
isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />
}
                  Technical details &amp;
 rule logic
                </button>

                {
isExpanded && (
                  <div className="mt-2.5 p-3 bg-gray-50 rounded-xl text-xs space-y-2 border border-gray-200">
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-white p-2 rounded-lg border border-gray-200">
                        <span className="text-[10px] text-gray-400 font-mono uppercase block">Expected</span>
                        <span className="font-semibold text-gray-800 font-mono text-xs">{
reason.expected || '—'
}</span>
                      </div>
                      <div className="bg-white p-2 rounded-lg border border-gray-200">
                        <span className="text-[10px] text-gray-400 font-mono uppercase block">Actual</span>
                        <span className="font-semibold text-red-600 font-mono text-xs">{
reason.actual || '—'
}</span>
                      </div>
                      <div className="bg-white p-2 rounded-lg border border-gray-200">
                        <span className="text-[10px] text-gray-400 font-mono uppercase block">Variance</span>
                        <span className="font-bold text-gray-900 font-mono text-xs">{
reason.variance || '—'
}</span>
                      </div>
                    </div>
                    {
reason.technical_rule && (
                      <div className="bg-white p-2.5 rounded-lg border border-gray-200 font-mono text-[11px] text-gray-600">
                        <span className="font-semibold text-gray-400 block mb-0.5">Control engine check:</span>
                        {
reason.technical_rule
}
                      </div>
                    )
}
                  </div>
                )
}
              </div>
            </div>
          );

        
})
}
      </div>

      {
/* Next Action Box */
}
      <div className="bg-white border border-gray-200 rounded-xl p-3 flex items-center gap-2.5 text-xs text-gray-800">
        <ArrowRight className="w-4 h-4 text-blue-600 flex-shrink-0" />
        <div>
          <span className="font-semibold text-gray-900">Next step: </span>
          <span className="text-gray-600">{
explanation.next_action
}</span>
        </div>
      </div>
    </div>
  );


};

