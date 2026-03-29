import * as React from 'react';
import ReactECharts from 'echarts-for-react';
import { useEffect, useState } from 'react';

export function KGNetworkChart() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });

  useEffect(() => {
    fetch('/kg_instances_real.json')
      .then(res => res.json())
      .then(data => setGraphData(data))
      .catch(err => console.error("Failed to fetch KG data:", err));
  }, []);

  const option = {
    tooltip: {
      formatter: '{b}'
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
          show: false,
          position: 'right',
          formatter: '{b}',
          fontSize: 10,
          fontFamily: 'JetBrains Mono, monospace'
        },
        edgeSymbol: ['none', 'none'],
        edgeSymbolSize: [4, 8],
        edgeLabel: {
          fontSize: 10
        },
        force: {
          repulsion: 150,
          edgeLength: 60,
          gravity: 0.1
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1.5,
          shadowBlur: 5,
          shadowColor: 'rgba(0, 0, 0, 0.15)'
        },
        lineStyle: {
          color: '#cbd5e1',
          curveness: 0.3,
          width: 0.8,
          opacity: 0.5
        },
        emphasis: {
          focus: 'adjacency',
          scale: true,
          label: {
            show: true
          },
          lineStyle: {
            width: 2,
            opacity: 1,
            color: '#6366f1'
          }
        },
        data: graphData.nodes,
        links: graphData.links
      }
    ]
  };

  if (!graphData.nodes.length) return <div className="h-[400px] flex items-center justify-center text-slate-400">Loading KG Instances...</div>;

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
