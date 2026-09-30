import React, {
 useState 
} from 'react';

import {

  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  FileCheck

} from 'lucide-react';

import type {
 InvoiceRiskProfile, RiskFactor 
} from '../types';


interface RiskProfileCardProps {

  riskProfile: InvoiceRiskProfile | null;

  loading?: boolean;


}

export const RiskProfileCard: React.FC<RiskProfileCardProps> = ({
 riskProfile, loading 
}) => {

  const [expandedFactor, setExpandedFactor] = useState<string | null>(null);


  if (loading) {

    return (
      <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-card animate-pulse space-y-4">
        <div className="h-6 bg-gray-200 rounded w-1/3" />
        <div className="h-4 bg-gray-100 rounded w-2/3" />
        <div className="h-24 bg-gray-50 rounded-xl" />
      </div>
    );

  
}

  if (!riskProfile) {

    return null;

  
}

  const {

    risk_score,
    risk_level,
    headline,
    summary,
    recommended_attention,
    risk_factors,
    control_summary
  
} = riskProfile;


  const getScoreTheme = (level: string) => {

    switch (level) {

      case 'CRITICAL':
        return {

          bg: 'bg-red-50',
          border: 'border-red-200',
          badgeBg: 'bg-red-100 text-red-800 border-red-300',
          barColor: 'bg-red-500',
          textColor: 'text-red-700',
          accentColor: '#ef4444',
          icon: ShieldAlert,
        
};

      case 'HIGH':
        return {

          bg: 'bg-orange-50',
          border: 'border-orange-200',
          badgeBg: 'bg-orange-100 text-orange-800 border-orange-300',
          barColor: 'bg-orange-500',
          textColor: 'text-orange-700',
          accentColor: '#f97316',
          icon: AlertTriangle,
        
};

      case 'MEDIUM':
        return {

          bg: 'bg-amber-50',
          border: 'border-amber-200',
          badgeBg: 'bg-amber-100 text-amber-800 border-amber-300',
          barColor: 'bg-amber-500',
          textColor: 'text-amber-700',
          accentColor: '#f59e0b',
          icon: Info,
        
};

      default:
        return {

          bg: 'bg-emerald-50',
          border: 'border-emerald-200',
          badgeBg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          barColor: 'bg-emerald-500',
          textColor: 'text-emerald-700',
          accentColor: '#10b981',
          icon: ShieldCheck,
        
};

    
}
  
};


  const theme = getScoreTheme(risk_level);

  const StatusIcon = theme.icon;


  const toggleFactor = (code: string) => {

    setExpandedFactor(prev => (prev === code ? null : code));

  
};


  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
      {
/* Top Banner with Score Gauge and Executive Headline */
}
      <div className={
`p-6 border-b ${
theme.border
} ${
theme.bg
}`
}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className={
`w-12 h-12 rounded-2xl flex items-center justify-center shadow-xs flex-shrink-0 bg-white border ${
theme.border
}`
}>
              <StatusIcon className={
`w-6 h-6 ${
theme.textColor
}`
} />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className={
`px-2.5 py-0.5 rounded-full text-xs font-bold border uppercase tracking-wider ${
theme.badgeBg
}`
}>
                  {
risk_level
} Risk
                </span>
                {
recommended_attention ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-700 border border-red-200">
                    <AlertCircle className="w-3 h-3" /> Attention Recommended
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3" /> Safe to Process
                  </span>
                )
}
              </div>
              <h3 className="text-base font-bold text-gray-900 mt-1.5">{
headline
}</h3>
              <p className="text-xs text-gray-600 mt-1 max-w-xl leading-relaxed">{
summary
}</p>
            </div>
          </div>

          {
/* Risk Score Pill & Bar */
}
          <div className="flex flex-col items-end sm:min-w-[170px] bg-white p-4 rounded-2xl border border-gray-200/80 shadow-xs">
            <div className="text-[10px] uppercase font-bold tracking-wider text-gray-400">Deterministic Risk Score</div>
            <div className="flex items-baseline gap-1 mt-1">
              <span className={
`text-3xl font-extrabold ${
theme.textColor
}`
}>{
risk_score
}</span>
              <span className="text-xs text-gray-400 font-semibold">/ 100</span>
            </div>
            <div className="w-full bg-gray-100 h-2 rounded-full mt-2.5 overflow-hidden">
              <div
                className={
`h-full ${
theme.barColor
} transition-all duration-500`
}
                style={
{
 width: `${
Math.min(risk_score, 100)
}%` 
}
}
              />
            </div>
            <div className="flex justify-between w-full text-[9px] text-gray-400 mt-1 font-mono">
              <span>0 (Clean)</span>
              <span>100 (Max)</span>
            </div>
          </div>
        </div>

        {
/* Verification Summary Badges */
}
        <div className="mt-5 pt-4 border-t border-gray-200/60 flex flex-wrap items-center gap-3 text-xs">
          <span className="text-gray-500 font-medium">Control Engine Results:</span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-green-200 text-green-700 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
            {
control_summary.passed
} Passed
          </span>
          {
control_summary.failed > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-red-200 text-red-700 font-semibold">
              <AlertCircle className="w-3.5 h-3.5 text-red-600" />
              {
control_summary.failed
} Failed
            </span>
          )
}
          {
control_summary.warnings > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-amber-200 text-amber-700 font-semibold">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              {
control_summary.warnings
} Warnings
            </span>
          )
}
          <span className="text-gray-400 ml-auto text-[11px]">
            {
risk_factors.length
} Active Risk Signal{
risk_factors.length === 1 ? '' : 's'
}
          </span>
        </div>
      </div>

      {
/* Risk Factors Section */
}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              Identified Risk Factors &amp;
 Signals
            </h4>
            <p className="text-xs text-gray-500 mt-0.5">
              Deterministic risk drivers calculated from active exceptions and failed business controls.
            </p>
          </div>
        </div>

        {
risk_factors.length === 0 ? (
          <div className="bg-emerald-50/60 border border-emerald-100 rounded-xl p-6 text-center">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <div className="text-sm font-bold text-emerald-900">Zero Risk Signals Detected</div>
            <div className="text-xs text-emerald-700 mt-1 max-w-md mx-auto">
              All 18 deterministic AP controls executed successfully. No price, quantity, vendor, or duplicate anomalies were found.
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {
risk_factors.map(factor => {

              const isExpanded = expandedFactor === factor.code;

              const severityBadge =
                factor.severity === 'CRITICAL'
                  ? 'bg-red-100 text-red-800 border-red-200'
                  : factor.severity === 'HIGH'
                  ? 'bg-orange-100 text-orange-800 border-orange-200'
                  : factor.severity === 'MEDIUM'
                  ? 'bg-amber-100 text-amber-800 border-amber-200'
                  : 'bg-blue-100 text-blue-800 border-blue-200';


              return (
                <div
                  key={
factor.code
}
                  className="border border-gray-200 rounded-xl overflow-hidden hover:border-gray-300 transition-colors bg-white shadow-2xs"
                >
                  <button
                    type="button"
                    onClick={
() => toggleFactor(factor.code)
}
                    className="w-full px-4 py-3 flex items-center justify-between gap-3 text-left hover:bg-gray-50/70 transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className={
`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
severityBadge
}`
}>
                        {
factor.severity
}
                      </span>
                      <div className="min-w-0">
                        <span className="text-xs font-bold text-gray-900 truncate block">
                          {
factor.title
}
                        </span>
                        <span className="text-[11px] text-gray-500 font-mono">
                          {
factor.code
} · Category: {
factor.category
}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="text-xs font-bold text-red-600 bg-red-50 border border-red-100 px-2 py-0.5 rounded-md">
                        +{
factor.score_contribution
} pts
                      </span>
                      {
isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      )
}
                    </div>
                  </button>

                  {
isExpanded && (
                    <div className="px-5 py-4 border-t border-gray-100 bg-gray-50/50 space-y-3 text-xs">
                      <div>
                        <span className="font-bold text-gray-700 block uppercase tracking-wider text-[10px]">
                          What Happened
                        </span>
                        <p className="text-gray-800 mt-0.5 leading-relaxed">{
factor.description
}</p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="bg-white p-3 rounded-lg border border-gray-200">
                          <span className="font-bold text-amber-800 block uppercase tracking-wider text-[10px] flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3 text-amber-600" />
                            Why It Matters
                          </span>
                          <p className="text-gray-700 mt-1 leading-relaxed">{
factor.why_it_matters
}</p>
                        </div>

                        <div className="bg-white p-3 rounded-lg border border-gray-200">
                          <span className="font-bold text-blue-800 block uppercase tracking-wider text-[10px] flex items-center gap-1">
                            <FileCheck className="w-3 h-3 text-blue-600" />
                            Recommended Action
                          </span>
                          <p className="text-gray-700 mt-1 leading-relaxed">{
factor.recommended_action
}</p>
                        </div>
                      </div>

                      <div className="bg-gray-100/80 p-2.5 rounded-lg border border-gray-200 font-mono text-[11px] text-gray-700 flex items-start gap-2">
                        <span className="font-bold text-gray-500 uppercase text-[10px]">Evidence:</span>
                        <span className="break-all">{
factor.evidence
}</span>
                      </div>
                    </div>
                  )
}
                </div>
              );

            
})
}
          </div>
        )
}
      </div>
    </div>
  );


};

