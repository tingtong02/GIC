import * as React from 'react';
import ReactECharts from 'echarts-for-react';

export function KGNetworkChart() {
  const option = {
    tooltip: {
      formatter: '{c}'
    },
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [
      {
        type: 'graph',
        layout: 'force',
        symbolSize: 20,
        roam: true,
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
          fontSize: 11,
          fontFamily: 'JetBrains Mono, monospace'
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [4, 8],
        edgeLabel: {
          fontSize: 10
        },
        force: {
          repulsion: 300,
          edgeLength: 80,
          gravity: 0.1
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 2,
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.15)'
        },
        lineStyle: {
          color: '#cbd5e1',
          curveness: 0.2,
          width: 1.5
        },
        emphasis: {
          focus: 'adjacency',
          scale: true,
          lineStyle: {
            width: 3,
            color: '#6366f1'
          }
        },
        data: [
          { name: 'MAG_BOU', value: 'Geomagnetic Observatory', itemStyle: { color: '#0ea5e9' }, symbolSize: 30 },
          { name: 'MAG_FRD', value: 'Geomagnetic Observatory', itemStyle: { color: '#0ea5e9' }, symbolSize: 30 },
          { name: 'Grid_Region_A', value: 'High-Voltage Cluster', itemStyle: { color: '#8b5cf6' }, symbolSize: 45 },
          { name: 'Grid_Region_B', value: 'High-Voltage Cluster', itemStyle: { color: '#8b5cf6' }, symbolSize: 45 },
          { name: 'Node_101', value: '765kV Transformer', itemStyle: { color: '#f43f5e' } },
          { name: 'Node_102', value: '765kV Transformer', itemStyle: { color: '#f43f5e' } },
          { name: 'Node_103', value: '500kV Substation', itemStyle: { color: '#f59e0b' } },
          { name: 'Node_104', value: '500kV Substation', itemStyle: { color: '#f59e0b' } },
          { name: 'Node_105', value: '500kV Substation', itemStyle: { color: '#f59e0b' } },
          { name: 'Fault_Rule_1', value: 'Constraint Rule: Line Trip', itemStyle: { color: '#10b981' }, symbolSize: 15, symbol: 'rect' }
        ],
        links: [
          { source: 'MAG_BOU', target: 'Grid_Region_A', value: 'drives_field' },
          { source: 'MAG_FRD', target: 'Grid_Region_B', value: 'drives_field' },
          { source: 'Node_101', target: 'Grid_Region_A', value: 'belongs_to' },
          { source: 'Node_102', target: 'Grid_Region_A', value: 'belongs_to' },
          { source: 'Node_103', target: 'Grid_Region_B', value: 'belongs_to' },
          { source: 'Node_104', target: 'Grid_Region_B', value: 'belongs_to' },
          { source: 'Node_105', target: 'Grid_Region_B', value: 'belongs_to' },
          { source: 'Node_101', target: 'Node_102', value: 'physically_connected' },
          { source: 'Node_103', target: 'Node_104', value: 'physically_connected' },
          { source: 'Node_104', target: 'Node_105', value: 'physically_connected' },
          { source: 'Node_102', target: 'Fault_Rule_1', value: 'constrained_by' }
        ]
      }
    ]
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-8 overflow-hidden relative group my-8">
      <div className="absolute top-6 left-8 z-10 pointer-events-none max-w-sm bg-white/70 backdrop-blur-sm p-4 rounded-md">
        <h4 className="text-xs uppercase tracking-widest font-bold text-slate-800 border-b border-slate-200 pb-2 mb-2">KG Schema Topology (Phase 6)</h4>
        <p className="text-xs text-slate-600 leading-relaxed font-medium">交互提示：尝试 Hover 悬浮在任意节点上，观察 <strong>聚焦隔离 (Adjacency Focus)</strong> 效应。</p>
        <p className="text-xs text-slate-500 leading-relaxed font-light mt-2 -mb-1">KG 通过隶属、驱动和故障规则强行注入异构特征，是压榨数值极限的核心武器。</p>
      </div>
      <div className="-m-8">
        <ReactECharts option={option} style={{ height: '400px' }} opts={{ renderer: 'svg' }} />
      </div>
    </div>
  );
}
