import React, {
 useState 
} from 'react';

import {

  GitCommit,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  FileText,
  User,
  Clock,
  Layers

} from 'lucide-react';

import type {
 RevisionDiffResponse, RevisionComparison 
} from '../types';

import {
 formatDateTime 
} from '../utils/format';


interface RevisionDiffViewerProps {

  diffData: RevisionDiffResponse | null;

  loading?: boolean;


}

export const RevisionDiffViewer: React.FC<RevisionDiffViewerProps> = ({

  diffData,
  loading = false,

}) => {

  const [selectedIndex, setSelectedIndex] = useState<number>(0);


  if (loading) {

    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 animate-pulse">
        <div className="h-5 bg-gray-200 rounded w-1/3" />
        <div className="h-20 bg-gray-100 rounded-xl" />
      </div>
    );

  
}

  if (!diffData || !diffData.has_multiple_revisions || diffData.diffs.length === 0) {

    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center text-gray-500 text-sm">
        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-3">
          <Layers className="w-5 h-5 text-gray-400" />
        </div>
        <p className="font-semibold text-gray-700">Original Revision (Rev 1)</p>
        <p className="text-xs text-gray-400 mt-1">This invoice has not been revised since its initial submission.</p>
      </div>
    );

  
}

  const comparison: RevisionComparison = diffData.diffs[selectedIndex] || diffData.diffs[0];


  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-card space-y-5">
      {
/* Header */
}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4">
        <div>
          <h3 className="font-bold text-gray-900 text-base flex items-center gap-2">
            <GitCommit className="w-4 h-4 text-indigo-600" />
            Revision History &amp;
 What Changed
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Compare header fields and item revisions across invoice versions ({
diffData.revisions_count
} total revisions).
          </p>
        </div>

        {
/* Revision Selector if multiple diffs */
}
        {
diffData.diffs.length > 1 && (
          <div className="flex items-center gap-1.5 p-1 bg-gray-50 rounded-xl border border-gray-200">
            {
diffData.diffs.map((diff, idx) => (
              <button
                key={
idx
}
                onClick={
() => setSelectedIndex(idx)
}
                className={
`px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${

                  selectedIndex === idx
                    ? 'bg-white text-gray-900 shadow-sm border border-gray-200'
                    : 'text-gray-500 hover:text-gray-800'
                
}`
}
              >
                Rev {
diff.from_revision_number
} → Rev {
diff.to_revision_number
}
              </button>
            ))
}
          </div>
        )
}
      </div>

      {
/* Revision Meta Card */
}
      <div className="bg-indigo-50/50 border border-indigo-100 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-indigo-950 text-sm">
              Revision {
comparison.from_revision_number
} → Revision {
comparison.to_revision_number
}
            </span>
            <span className="bg-indigo-100 text-indigo-800 font-semibold px-2 py-0.5 rounded-full text-[10px]">
              Latest
            </span>
          </div>
          <div className="text-gray-500 flex items-center gap-2">
            <span className="flex items-center gap-1">
              <User className="w-3 h-3 text-gray-400" /> {
comparison.changed_by
}
            </span>
            <span>·</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-gray-400" /> {
formatDateTime(comparison.changed_at)
}
            </span>
          </div>
        </div>

        {
/* Controls Re-run status pill */
}
        <div className="flex items-center gap-2">
          {
comparison.controls_rerun && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-indigo-200 rounded-xl text-indigo-800 font-medium shadow-xs">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              <span>Controls re-evaluated: <strong>{
comparison.resulting_control_status
}</strong></span>
            </div>
          )
}
        </div>
      </div>

      {
/* Header Diffs Section */
}
      {
comparison.header_diffs.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Header Field Changes ({
comparison.header_diffs.length
})
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {
comparison.header_diffs.map((h, i) => (
              <div key={
i
} className="bg-gray-50 rounded-xl p-3 border border-gray-200 space-y-1.5">
                <span className="font-semibold text-gray-700 text-xs">{
h.label
}</span>
                <div className="flex items-center gap-2 text-xs">
                  <span className="line-through text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-200/60 font-mono">
                    {
h.previous_value
}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                  <span className="font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200/60 font-mono">
                    {
h.new_value
}
                  </span>
                </div>
              </div>
            ))
}
          </div>
        </div>
      ) : (
        <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-xl border border-gray-200">
          No invoice header fields were modified in this revision.
        </div>
      )
}

      {
/* Line Item Diffs Section */
}
      {
comparison.item_diffs.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Line Item Modifications ({
comparison.item_diffs.length
})
          </div>
          <div className="space-y-2">
            {
comparison.item_diffs.map((item, i) => (
              <div key={
i
} className="bg-gray-50 rounded-xl p-3 border border-gray-200 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-gray-500">#{
item.line_number
}</span>
                    <span className="font-semibold text-gray-800 text-xs">{
item.description
}</span>
                  </div>
                  <span className={
`text-[10px] font-bold px-2 py-0.5 rounded-full border ${

                    item.change_type === 'MODIFIED'
                      ? 'bg-amber-100 text-amber-800 border-amber-200'
                      : item.change_type === 'ADDED'
                      ? 'bg-green-100 text-green-800 border-green-200'
                      : 'bg-red-100 text-red-800 border-red-200'
                  
}`
}>
                    {
item.change_type
}
                  </span>
                </div>

                {
item.changes && item.changes.length > 0 && (
                  <div className="text-xs text-gray-600 flex flex-wrap gap-2">
                    {
item.changes.map((c, ci) => (
                      <span key={
ci
} className="bg-white px-2 py-0.5 rounded border border-gray-200 font-mono text-[11px]">
                        {
c
}
                      </span>
                    ))
}
                  </div>
                )
}

                <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-gray-200/60">
                  <div>
                    <span className="text-gray-400 block text-[10px]">Previous:</span>
                    <span className="font-mono text-gray-600">{
item.previous
}</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block text-[10px]">Updated:</span>
                    <span className="font-mono font-semibold text-gray-900">{
item.current
}</span>
                  </div>
                </div>
              </div>
            ))
}
          </div>
        </div>
      ) : (
        <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-xl border border-gray-200">
          No line item modifications recorded in this revision.
        </div>
      )
}
    </div>
  );


};

