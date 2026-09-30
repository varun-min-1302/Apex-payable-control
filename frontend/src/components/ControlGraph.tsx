import React, {
 useState 
} from 'react';

import {

  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Building,
  FileCheck,
  Package,
  Calculator,
  Copy,
  ShieldAlert,
  UserCheck,
  CreditCard,
  ChevronDown,
  ChevronRight

} from 'lucide-react';

import type {
 ControlGraph as ControlGraphType, ControlGraphNode, ControlGraphCheck 
} from '../types';


interface ControlGraphProps {

  graph: ControlGraphType | null;

  loading?: boolean;


}

function getNodeIcon(nodeId: string, className: string = 'w-4 h-4') {

  switch (nodeId) {

    case 'vendor':
      return <Building className={
className
} />;

    case 'po':
      return <FileCheck className={
className
} />;

    case 'receipt':
      return <Package className={
className
} />;

    case 'financial':
      return <Calculator className={
className
} />;

    case 'duplicate':
      return <Copy className={
className
} />;

    case 'risk':
      return <ShieldAlert className={
className
} />;

    case 'approval':
      return <UserCheck className={
className
} />;

    case 'payable':
      return <CreditCard className={
className
} />;

    default:
      return <CheckCircle className={
className
} />;

  
}

}

function getStatusBadge(status: string) {

  switch (status) {

    case 'PASS':
      return {

        bg: 'bg-green-50 text-green-700 border-green-200',
        badge: 'Passed',
        icon: <CheckCircle className="w-3.5 h-3.5 text-green-600" />,
        ring: 'border-green-300 ring-2 ring-green-100',
      
};

    case 'FAIL':
      return {

        bg: 'bg-red-50 text-red-700 border-red-200',
        badge: 'Failed',
        icon: <XCircle className="w-3.5 h-3.5 text-red-600" />,
        ring: 'border-red-300 ring-2 ring-red-100',
      
};

    case 'WARNING':
      return {

        bg: 'bg-amber-50 text-amber-700 border-amber-200',
        badge: 'Warning',
        icon: <AlertCircle className="w-3.5 h-3.5 text-amber-600" />,
        ring: 'border-amber-300 ring-2 ring-amber-100',
      
};

    case 'PENDING':
      return {

        bg: 'bg-blue-50 text-blue-700 border-blue-200',
        badge: 'Pending',
        icon: <Clock className="w-3.5 h-3.5 text-blue-600" />,
        ring: 'border-blue-200',
      
};

    default:
      return {

        bg: 'bg-gray-100 text-gray-500 border-gray-200',
        badge: 'N/A',
        icon: <Clock className="w-3.5 h-3.5 text-gray-400" />,
        ring: 'border-gray-200',
      
};

  
}

}

export const ControlGraph: React.FC<ControlGraphProps> = ({
 graph, loading = false 
}) => {

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);


  if (loading) {

    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 animate-pulse">
        <div className="h-5 bg-gray-200 rounded w-1/4" />
        <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
          {
[...Array(8)].map((_, i) => (
            <div key={
i
} className="h-24 bg-gray-100 rounded-xl" />
          ))
}
        </div>
      </div>
    );

  
}

  if (!graph || !graph.nodes || graph.nodes.length === 0) {

    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-6 text-center text-sm text-gray-500">
        No control graph data available for this invoice.
      </div>
    );

  
}

  const activeNode = selectedNodeId
    ? graph.nodes.find(n => n.id === selectedNodeId) || graph.nodes[0]
    : graph.nodes.find(n => n.status === 'FAIL') || graph.nodes[0];


  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-card space-y-5">
      {
/* Header */
}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold text-gray-900 text-base">Control Verification Pipeline</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Deterministic 8-stage verification pipeline required for financial authorization.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500">
            {
graph.nodes.filter(n => n.status === 'PASS').length
} of {
graph.nodes.length
} stages clear
          </span>
        </div>
      </div>

      {
/* 8-Stage Stepper / Pipeline */
}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        {
graph.nodes.map((node, index) => {

          const statusStyle = getStatusBadge(node.status);

          const isSelected = activeNode?.id === node.id;


          return (
            <button
              key={
node.id
}
              onClick={
() => setSelectedNodeId(node.id)
}
              className={
`text-left p-3 rounded-xl border transition-all flex flex-col justify-between ${

                isSelected
                  ? 'bg-blue-50/70 border-blue-500 ring-2 ring-blue-100 shadow-sm'
                  : 'bg-gray-50/60 border-gray-200 hover:bg-gray-100/70'
              
}`
}
            >
              <div>
                {
/* Node order and icon */
}
                <div className="flex items-center justify-between mb-2">
                  <div className={
`p-1.5 rounded-lg ${
isSelected ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200'
}`
}>
                    {
getNodeIcon(node.id, 'w-3.5 h-3.5')
}
                  </div>
                  <span className="text-[10px] font-mono text-gray-400 font-bold">#{
node.order
}</span>
                </div>

                {
/* Node label */
}
                <div className="font-semibold text-gray-900 text-xs truncate" title={
node.label
}>
                  {
node.label
}
                </div>
              </div>

              {
/* Status pill & check count */
}
              <div className="mt-3 pt-2 border-t border-gray-200/60">
                <div className="flex items-center justify-between">
                  <span className={
`text-[10px] font-semibold px-1.5 py-0.5 rounded-full border ${
statusStyle.bg
}`
}>
                    {
statusStyle.badge
}
                  </span>
                  {
node.total_checks > 0 && (
                    <span className="text-[10px] font-mono text-gray-500">
                      {
node.passed_count
}/{
node.total_checks
}
                    </span>
                  )
}
                </div>
              </div>
            </button>
          );

        
})
}
      </div>

      {
/* Inspected Stage Details */
}
      {
activeNode && (
        <div className="bg-gray-50 rounded-xl p-4 border border-gray-200 space-y-3">
          <div className="flex items-center justify-between border-b border-gray-200 pb-2.5">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-white rounded-lg border border-gray-200 text-gray-700">
                {
getNodeIcon(activeNode.id, 'w-4 h-4')
}
              </div>
              <div>
                <span className="font-bold text-gray-900 text-sm">{
activeNode.label
}</span>
                <span className="text-xs text-gray-500 ml-2">Stage #{
activeNode.order
}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={
`text-xs font-semibold px-2.5 py-1 rounded-full border ${
getStatusBadge(activeNode.status).bg
}`
}>
                {
activeNode.status
}
              </span>
            </div>
          </div>

          <p className="text-xs text-gray-600">{
activeNode.summary
}</p>

          {
/* Checks list within this stage */
}
          {
activeNode.checks.length === 0 ? (
            <div className="text-xs text-gray-400 italic py-2">
              No individual control checks assigned to this stage.
            </div>
          ) : (
            <div className="space-y-2 pt-1">
              <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                Stage Controls ({
activeNode.checks.length
})
              </div>

              {
activeNode.checks.map((chk, i) => {

                const chkStatus = getStatusBadge(chk.status);


                return (
                  <div
                    key={
`${
chk.control_code
}-${
i
}`
}
                    className={
`bg-white rounded-xl p-3 border ${

                      chk.status === 'FAIL'
                        ? 'border-red-200 bg-red-50/20'
                        : chk.status === 'WARNING'
                        ? 'border-amber-200'
                        : 'border-gray-200'
                    
}`
}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-2.5">
                        <div className="mt-0.5 flex-shrink-0">{
chkStatus.icon
}</div>
                        <div>
                          <div className="font-semibold text-gray-900 text-xs flex items-center gap-2">
                            <span>{
chk.title
}</span>
                            <span className="font-mono text-[10px] text-gray-400">({
chk.control_code
})</span>
                          </div>
                          {
chk.message && (
                            <div className="text-xs text-gray-600 mt-0.5">{
chk.message
}</div>
                          )
}
                        </div>
                      </div>
                      <span className={
`text-[10px] font-semibold px-2 py-0.5 rounded-full border flex-shrink-0 ${
chkStatus.bg
}`
}>
                        {
chk.status
}
                      </span>
                    </div>

                    {
/* Discrepancy details if failed or warning */
}
                    {
(chk.expected || chk.actual || chk.variance) && (
                      <div className="mt-2.5 pt-2 border-t border-gray-100 grid grid-cols-3 gap-2 text-[11px]">
                        <div>
                          <span className="text-gray-400 block font-mono text-[10px]">Expected</span>
                          <span className="font-semibold text-gray-800">{
chk.expected || '—'
}</span>
                        </div>
                        <div>
                          <span className="text-gray-400 block font-mono text-[10px]">Actual</span>
                          <span className="font-semibold text-red-600">{
chk.actual || '—'
}</span>
                        </div>
                        <div>
                          <span className="text-gray-400 block font-mono text-[10px]">Variance</span>
                          <span className="font-bold text-gray-900">{
chk.variance || '—'
}</span>
                        </div>
                      </div>
                    )
}

                    {
/* Why it matters & action if available */
}
                    {
(chk.why_it_matters || chk.recommended_action) && (
                      <div className="mt-2 text-xs space-y-1 bg-gray-50 p-2 rounded-lg border border-gray-100">
                        {
chk.why_it_matters && (
                          <div className="text-gray-600">
                            <span className="font-semibold text-gray-800">Impact: </span>
                            {
chk.why_it_matters
}
                          </div>
                        )
}
                        {
chk.recommended_action && (
                          <div className="text-blue-700">
                            <span className="font-semibold text-blue-900">Action: </span>
                            {
chk.recommended_action
}
                          </div>
                        )
}
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
      )
}
    </div>
  );


};

