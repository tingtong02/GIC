import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';
import { Check, X } from 'lucide-react';

export interface ArchitectureState {
  id: string;
  name: string;
  pros: string[];
  cons: string[];
  maeScore: number;
}

interface TradeoffToggleProps {
  defaultPath: ArchitectureState;
  optionalPath: ArchitectureState;
}

export function TradeoffToggle({ defaultPath, optionalPath }: TradeoffToggleProps) {
  const [activeTab, setActiveTab] = useState<string>(defaultPath.id);

  const activeData = activeTab === defaultPath.id ? defaultPath : optionalPath;

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden mt-8 mb-8">
      {/* Tabs Header */}
      <div className="flex border-b border-slate-200 bg-slate-50/50">
        {[defaultPath, optionalPath].map((path) => (
          <button
            key={path.id}
            onClick={() => setActiveTab(path.id)}
            className={cn(
              "flex-1 py-4 px-6 text-sm font-semibold transition-colors focus:outline-none relative",
              activeTab === path.id ? "text-slate-900 bg-white" : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
            )}
          >
            {path.name}
            {activeTab === path.id && (
              <motion.div
                layoutId="tradeoff-tab-indicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
                initial={false}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-8 pb-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.2 }}
            className="space-y-8"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-4">
               <div>
                 <h4 className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Synthetic Benchmark Hidden-Node MAE</h4>
                 <div className="text-4xl font-light text-slate-800 tracking-tight mt-1">{activeData.maeScore.toFixed(2)}</div>
               </div>
               {activeData.id === defaultPath.id ? (
                 <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                    Default 默认系统架构
                 </span>
               ) : (
                 <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Optional 可选增强架构
                 </span>
               )}
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h4 className="flex items-center text-xs font-bold text-slate-900 mb-4 uppercase tracking-wider border-b border-slate-100 pb-2">
                  <span className="bg-emerald-100 p-0.5 rounded mr-2"><Check size={14} className="text-emerald-700"/></span> 保留与优势 (Pros)
                </h4>
                <ul className="space-y-3">
                  {activeData.pros.map((p, i) => (
                    <li key={i} className="text-sm text-slate-600 leading-relaxed flex items-start">
                      <span className="text-slate-300 mr-2">—</span> {p}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="flex items-center text-xs font-bold text-slate-900 mb-4 uppercase tracking-wider border-b border-slate-100 pb-2">
                  <span className="bg-rose-100 p-0.5 rounded mr-2"><X size={14} className="text-rose-700"/></span> 妥协与代价 (Cons)
                </h4>
                <ul className="space-y-3">
                  {activeData.cons.map((c, i) => (
                    <li key={i} className="text-sm text-slate-600 leading-relaxed flex items-start">
                      <span className="text-slate-300 mr-2">—</span> {c}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
