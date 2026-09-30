import React, {
 useState 
} from 'react';

import {

  History,
  User,
  Cpu,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
  CreditCard,
  AlertTriangle,
  FileText,
  Filter

} from 'lucide-react';

import type {
 AuditReplay, AuditReplayEvent 
} from '../types';

import {
 formatDateTime 
} from '../utils/format';


interface AuditReplayTimelineProps {

  replay: AuditReplay | null;

  loading?: boolean;


}

type EventFilter = 'ALL' | 'INTAKE' | 'CONTROLS' | 'APPROVALS' | 'PAYMENTS' | 'EXCEPTIONS' | 'LIFECYCLE';


function getCategoryIcon(cat: string) {

  switch (cat) {

    case 'INTAKE':
      return <FileText className="w-3.5 h-3.5 text-blue-600" />;

    case 'CONTROLS':
      return <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />;

    case 'APPROVALS':
      return <User className="w-3.5 h-3.5 text-emerald-600" />;

    case 'PAYMENTS':
      return <CreditCard className="w-3.5 h-3.5 text-purple-600" />;

    case 'EXCEPTIONS':
      return <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;

    default:
      return <History className="w-3.5 h-3.5 text-gray-500" />;

  
}

}

function getCategoryBadge(cat: string) {

  switch (cat) {

    case 'INTAKE':
      return 'bg-blue-50 text-blue-700 border-blue-200';

    case 'CONTROLS':
      return 'bg-indigo-50 text-indigo-700 border-indigo-200';

    case 'APPROVALS':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';

    case 'PAYMENTS':
      return 'bg-purple-50 text-purple-700 border-purple-200';

    case 'EXCEPTIONS':
      return 'bg-amber-50 text-amber-700 border-amber-200';

    default:
      return 'bg-gray-100 text-gray-700 border-gray-200';

  
}

}

export const AuditReplayTimeline: React.FC<AuditReplayTimelineProps> = ({

  replay,
  loading = false,

}) => {

  const [filter, setFilter] = useState<EventFilter>('ALL');

  const [expandedEvents, setExpandedEvents] = useState<Record<string, boolean>>({

});


  if (loading) {

    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 animate-pulse">
        <div className="h-5 bg-gray-200 rounded w-1/4" />
        <div className="space-y-3">
          {
[...Array(4)].map((_, i) => (
            <div key={
i
} className="h-16 bg-gray-100 rounded-xl" />
          ))
}
        </div>
      </div>
    );

  
}

  if (!replay || replay.timeline.length === 0) {

    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center text-gray-500 text-sm">
        No audit events recorded for this invoice yet.
      </div>
    );

  
}

  const toggleExpand = (id: string) => {

    setExpandedEvents(prev => ({
 ...prev, [id]: !prev[id] 
}));

  
};


  const filteredTimeline = replay.timeline.filter(e => {

    if (filter === 'ALL') return true;

    return e.category === filter;

  
});


  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-card space-y-5">
      {
/* Header and Filter */
}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4">
        <div>
          <h3 className="font-bold text-gray-900 text-base flex items-center gap-2">
            <History className="w-4 h-4 text-blue-600" />
            Audit Replay Timeline
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Immutable chronological record of all actions, decisions, and system checks ({
replay.events_count
} total events).
          </p>
        </div>

        {
/* Filter Pills */
}
        <div className="flex items-center gap-1 overflow-x-auto p-1 bg-gray-50 rounded-xl border border-gray-200">
          {
(['ALL', 'INTAKE', 'CONTROLS', 'APPROVALS', 'PAYMENTS', 'EXCEPTIONS'] as EventFilter[]).map(cat => (
            <button
              key={
cat
}
              onClick={
() => setFilter(cat)
}
              className={
`px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap ${

                filter === cat
                  ? 'bg-white text-gray-900 shadow-sm border border-gray-200'
                  : 'text-gray-500 hover:text-gray-800'
              
}`
}
            >
              {
cat === 'ALL' ? 'All' : cat
}
            </button>
          ))
}
        </div>
      </div>

      {
/* Timeline Events */
}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200">
        {
filteredTimeline.map(ev => {

          const isExpanded = !!expandedEvents[ev.id];

          const isSystem = ev.actor_name.toLowerCase().includes('engine') || ev.actor_name.toLowerCase().includes('system');


          return (
            <div key={
ev.id
} className="relative">
              {
/* Timeline Dot */
}
              <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-white border-2 border-blue-500 flex items-center justify-center shadow-xs">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />
              </div>

              {
/* Event Content Card */
}
              <div className="bg-gray-50 rounded-xl p-3.5 border border-gray-200 hover:border-gray-300 transition-colors space-y-2">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-gray-900 text-xs">{
ev.title
}</span>
                      <span className={
`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
getCategoryBadge(ev.category)
}`
}>
                        {
ev.category
}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{
ev.description
}</p>
                  </div>
                  <span className="text-[11px] font-mono text-gray-400 whitespace-nowrap">
                    {
formatDateTime(ev.timestamp)
}
                  </span>
                </div>

                {
/* Actor Info */
}
                <div className="flex items-center justify-between pt-1 border-t border-gray-200/60 text-xs">
                  <div className="flex items-center gap-1.5 text-gray-600">
                    {
isSystem ? (
                      <Cpu className="w-3.5 h-3.5 text-indigo-500" />
                    ) : (
                      <User className="w-3.5 h-3.5 text-gray-400" />
                    )
}
                    <span className="font-medium text-gray-800">{
ev.actor_name
}</span>
                    <span className="text-gray-400 text-[11px]">({
ev.actor_role
})</span>
                  </div>

                  {
/* Technical toggle */
}
                  <button
                    onClick={
() => toggleExpand(ev.id)
}
                    className="flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    {
isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />
}
                    {
isExpanded ? 'Hide audit details' : 'Audit details'
}
                  </button>
                </div>

                {
/* Expanded Technical Details */
}
                {
isExpanded && (
                  <div className="mt-2 pt-2 border-t border-gray-200 text-xs font-mono space-y-2 bg-white p-3 rounded-lg border">
                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      <div>
                        <span className="text-gray-400 font-semibold uppercase block text-[10px]">Action</span>
                        <span className="text-gray-800">{
ev.action
}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 font-semibold uppercase block text-[10px]">Entity ID</span>
                        <span className="text-gray-800 truncate block">{
ev.entity_id
}</span>
                      </div>
                    </div>

                    {
/* State Changes if present */
}
                    {
(ev.previous_state || ev.new_state) && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-gray-100">
                        {
ev.previous_state && (
                          <div className="bg-gray-50 p-2 rounded border border-gray-200 overflow-x-auto">
                            <span className="text-[10px] text-gray-400 font-bold uppercase block mb-1">Previous state</span>
                            <pre className="text-[10px] text-gray-700 whitespace-pre-wrap">{
JSON.stringify(ev.previous_state, null, 2)
}</pre>
                          </div>
                        )
}
                        {
ev.new_state && (
                          <div className="bg-blue-50/50 p-2 rounded border border-blue-200 overflow-x-auto">
                            <span className="text-[10px] text-blue-600 font-bold uppercase block mb-1">New state</span>
                            <pre className="text-[10px] text-blue-950 whitespace-pre-wrap">{
JSON.stringify(ev.new_state, null, 2)
}</pre>
                          </div>
                        )
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
    </div>
  );


};

