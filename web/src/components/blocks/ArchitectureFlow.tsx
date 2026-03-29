import * as React from 'react';
import { motion } from 'framer-motion';

export function ArchitectureFlow() {
  return (
    <div className="relative w-full max-w-4xl mx-auto my-12 p-8 rounded-2xl bg-white border border-slate-200 shadow-sm overflow-hidden font-sans">
      <div className="flex justify-between items-center mb-10 relative z-10">
        <div className="text-left">
          <h3 className="text-slate-800 text-lg font-bold tracking-tight mb-1">Phase 5 (Default) Architecture</h3>
          <p className="text-slate-500 text-xs">Physics-informed Temporal GNN (GraphSAGE + GRU)</p>
        </div>
        <div className="px-3 py-1 bg-emerald-50 border border-emerald-200 rounded text-emerald-600 text-xs font-mono font-bold uppercase tracking-wider">
          Frozen Mainline
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr_auto_1.2fr] gap-4 items-center relative z-10">
        
        {/* Column 1: Signal Inputs */}
        <div className="flex flex-col gap-6">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="p-5 rounded-xl bg-slate-50 border border-slate-200 shadow-sm relative group"
          >
            <p className="text-[10px] text-slate-400 font-mono mb-2 uppercase tracking-wider">Time-Series Stream</p>
            <h4 className="text-slate-700 font-bold mb-1 text-sm">GIC Station Proxies</h4>
            <p className="text-slate-500 text-xs leading-relaxed">Sparse real-event observations from INTERMAGNET.</p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="p-5 rounded-xl bg-blue-50 border border-blue-200 shadow-sm relative group"
          >
             <div className="absolute -top-2 -right-2 w-4 h-4 bg-blue-500 rounded-full animate-pulse blur-sm"></div>
            <p className="text-[10px] text-blue-500 font-mono mb-2 uppercase tracking-wider">Pre-processor</p>
            <h4 className="text-blue-900 font-bold mb-1 text-sm">FastICA Filter</h4>
            <p className="text-blue-700/80 text-xs leading-relaxed">Extracts residual short-term turbulence from slow drifts.</p>
          </motion.div>
        </div>

        {/* Arrow 1 */}
        <div className="hidden md:flex flex-col items-center justify-center opacity-40">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-400"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
        </div>

        {/* Column 2: Physics Prior */}
        <div className="flex flex-col justify-center">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="p-6 rounded-xl bg-slate-800 text-white border border-slate-700 shadow-lg relative group overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/20 rounded-full blur-3xl"></div>
            <p className="text-[10px] text-indigo-300 font-mono mb-2 uppercase tracking-wider">Physics Base (Phase 1-3)</p>
            <h4 className="font-bold mb-2 text-md">Uniform Field Solver</h4>
            <p className="text-slate-300 text-xs leading-relaxed mb-4">Solves static grid equations using known resistances to establish a deterministic prior.</p>
            
            <div className="flex gap-2">
              <span className="px-2 py-0.5 bg-slate-700 text-[10px] text-slate-300 rounded shadow-inner font-mono">mpc.bus</span>
              <span className="px-2 py-0.5 bg-slate-700 text-[10px] text-slate-300 rounded shadow-inner font-mono">mpc.branch</span>
            </div>
          </motion.div>
        </div>

        {/* Arrow 2 */}
        <div className="hidden md:flex flex-col items-center justify-center opacity-40">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-400"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
        </div>

        {/* Column 3: GNN */}
        <div className="flex flex-col gap-4">
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4 }}
            className="p-6 rounded-xl bg-gradient-to-br from-indigo-50 to-white border border-indigo-200 shadow-md relative"
          >
             <div className="absolute top-3 right-3 flex space-x-1">
               <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
               <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
               <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
             </div>
            <p className="text-[10px] text-indigo-500 font-mono mb-2 uppercase tracking-wider">Learning Core (Phase 5)</p>
            <h4 className="text-indigo-950 font-bold mb-2 text-md">Temporal GNN</h4>
            <p className="text-indigo-800/80 text-xs leading-relaxed">Aggregates spatial structure (GraphSAGE) and temporal memory (GRU) to learn residual deviations from the physical base.</p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between"
          >
             <div>
               <h4 className="text-emerald-800 font-bold text-sm">GIC Inference Output</h4>
               <p className="text-emerald-600/80 text-[11px]">System Reconstruction</p>
             </div>
             <div className="w-6 h-6 rounded-full bg-emerald-200 flex items-center justify-center">
               <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-700"><polyline points="20 6 9 17 4 12"></polyline></svg>
             </div>
          </motion.div>
        </div>

      </div>
    </div>
  );
}
