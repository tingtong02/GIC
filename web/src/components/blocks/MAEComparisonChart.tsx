import React from 'react';
import ReactECharts from 'echarts-for-react';

export function MAEComparisonChart() {
  const option = {
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const data = params[0];
        return `<strong>${data.name}</strong><br/>MAE: ${data.value}`;
      }
    },
    grid: { left: '3%', right: '10%', bottom: '0%', top: '5%', containLabel: true },
    xAxis: {
      type: 'value',
      show: false,
    },
    yAxis: {
      type: 'category',
      data: ['Phase 4 (Graph Baseline)', 'Phase 5 (Physics+Temporal GNN)', 'Phase 6 (KG Feature Only)'],
      inverse: true,
      axisLabel: { 
        fontWeight: 'bold', 
        color: '#1e293b',
        width: 150,
        overflow: 'break'
      },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [
      {
        name: 'MAE',
        type: 'bar',
        data: [
          { value: 22.18, itemStyle: { color: '#cbd5e1' } },
          { value: 7.74, itemStyle: { color: '#3b82f6' } },
          { value: 5.95, itemStyle: { color: '#10b981' } }
        ],
        label: {
          show: true,
          position: 'right',
          formatter: '{c}',
          fontWeight: 'bold',
          color: '#0f172a',
          fontSize: 16
        },
        barWidth: '40%',
        showBackground: true,
        backgroundStyle: { color: '#f8fafc' },
        itemStyle: { borderRadius: [0, 4, 4, 0] }
      }
    ]
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-8 my-8">
      <h3 className="text-sm uppercase tracking-wider font-bold text-slate-800 mb-2 border-b border-slate-100 pb-3">
        Synthetic Benchmark: Hidden-Node MAE 对比
      </h3>
      <p className="text-sm text-slate-500 mb-6 mt-3 leading-relaxed">
        数值越低代表预测误差越小。可以清晰看到从早期图基线（Phase 4），到引入物理时空特征（Phase 5），再到知识图谱特征增强（Phase 6）所带来的性能断崖式提升。
      </p>
      <div className="-ml-4">
        <ReactECharts option={option} style={{ height: '240px' }} opts={{ renderer: 'svg' }} />
      </div>
    </div>
  );
}
