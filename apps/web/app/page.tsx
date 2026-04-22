"use client";
import { useState, useRef, useEffect, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Brain, CheckCircle2, Info, Play, X, Target } from "lucide-react";

interface TourStep {
  id: string;
  title: string;
  desc: string;
  value: string;
  color: string;
  action?: () => void;
}

interface TourState {
  currentStep: number;
  isOpen: boolean;
  steps: TourStep[];
}

const TOUR_STEPS: TourStep[] = [
  { id: "overview", title: "AI Auto-Categorised", desc: "The AI automatically categorises 68-89% of transactions. Target is 80%.", value: "89% auto-categorization", color: "#22c55e", action: undefined },
  { id: "revenue", title: "Revenue", desc: "Your total income from sales and other sources for this period.", value: "68% auto = 15hrs saved", color: "#3b82f6", action: undefined },
  { id: "expenses", title: "Expenses", desc: "All business costs including rent, wages, supplies.", value: "5hrs/week saved", color: "#e2e8f0", action: undefined },
  { id: "profit", title: "Net Profit", desc: "Revenue minus Expenses. Your actual earnings.", value: "8.7% growth", color: "#f59e0b", action: undefined },
  { id: "export", title: "Export BAS", desc: "One-click GST-ready CSV for your BAS return.", value: "15min → seconds", color: "#8b5cf6", action: undefined },
  { id: "gst", title: "GST Compliance", desc: "Automated tax calculations and reporting.", value: "8hrs/month saved", color: "#14b8a6", action: undefined },
  { id: "datefilter", title: "Date Filtering", desc: "Analyze any time period instantly.", value: "3hrs/report saved", color: "#f97316", action: undefined },
  { id: "csvexport", title: "Export Functionality", desc: "Generate reports instantly with one click.", value: "15min → seconds", color: "#ec4899", action: undefined },
];

type InteractiveElementProps = {
  children: ReactNode;
  tourId: string;
  className?: string;
};

function TourOverlay({ isOpen, onClose, step, setStep }: { isOpen: boolean; onClose: () => void; step: number; setStep: (n: number) => void }) {
  const currentStep = TOUR_STEPS[step];
  return (
    <div className="fixed inset-0 z-50 pointer-events-none">
      <div className="absolute inset-0 bg-black/70 pointer-events-auto" />
      <div className="absolute inset-0 pointer-events-auto">
        <motion.div
          className="absolute w-64 h-64 bg-white/10 backdrop-blur-xl border-2 border-white/20 rounded-full pointer-events-none"
          style={{ top: "50%", left: "50%", transform: "translate(-50%, -50%)" }}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
        />
        <motion.div
          className="absolute w-96 h-96 border-2 border-white/20 rounded-full"
          style={{ top: "50%", left: "50%", transform: "translate(-50%, -50%)" }}
          initial={{ scale: 1, opacity: 1 }}
          animate={{ scale: 1.1, opacity: 0 }}
          transition={{ repeat: Infinity, duration: 4, delay: 1, ease: "easeOut" }}
        />
      </div>

      <div className="absolute bottom-6 right-6 flex gap-3 pointer-events-auto">
        {step > 0 && (
          <button onClick={() => setStep(step - 1)} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-white/20 rounded-lg transition-colors">
            Previous
          </button>
        )}
        {step < TOUR_STEPS.length - 1 ? (
          <button onClick={() => setStep(step + 1)} className="px-4 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
            Next
          </button>
        ) : (
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-white/20 rounded-lg transition-colors">
            Got it!
          </button>
        )}
      </div>

      <div className="absolute top-4 right-4 w-80 pointer-events-auto">
        <motion.div
          className="bg-white rounded-2xl shadow-2xl p-6 border-l-4"
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-1">{currentStep.title}</h3>
              <p className="text-sm text-gray-600">{currentStep.desc}</p>
            </div>
            <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
              <X size={18} className="text-gray-500" />
            </button>
          </div>
          <div className="flex items-center gap-3 pt-3 border-t border-gray-100">
            <div className="p-2 rounded-lg bg-blue-50">
              <Target size={20} className="text-blue-600" />
            </div>
            <div>
              <span className="text-xs text-gray-500">Value</span>
              <span className="text-sm font-semibold text-gray-900">{currentStep.value}</span>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2 pointer-events-auto">
        {TOUR_STEPS.map((_, idx) => (
          <button key={idx} onClick={() => setStep(idx)} className={`w-2 h-2 rounded-full transition-all ${idx === step ? 'w-12 bg-white/80' : 'bg-white/30 hover:bg-white/50'}`} />
        ))}
      </div>
    </div>
  );
}

function InteractiveElement({ children, tourId, className = "" }: InteractiveElementProps) {
  return <div data-tour={tourId} className={`relative z-10 ${className}`}>{children}</div>;
}

export default function Dashboard() {
  const [tourOpen, setTourOpen] = useState<boolean>(false);
  const [tourStep, setTourStep] = useState<number>(0);
  const revenue = "51,300";
  const expenses = "31,200";
  const profit = "18,450";
  const autoRate = 89;

  return (
    <div className="space-y-6 p-6">
      <TourOverlay isOpen={tourOpen} onClose={() => setTourOpen(false)} step={tourStep} setStep={setTourStep} />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">FY 2024–25 · April 2025</p>
        </div>
        <div className="flex items-center gap-3">
          {!tourOpen && (
            <button onClick={() => setTourOpen(true)} className="flex items-center gap-2 bg-blue-50 text-blue-700 text-sm px-4 py-1.5 rounded-lg font-medium hover:bg-blue-100 transition-colors">
              <Play size={14} />
              Start Tour
            </button>
          )}
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 text-xs px-3 py-1.5 rounded-full font-medium">
            <CheckCircle2 size={14} />
            Ledger balanced
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <InteractiveElement tourId="revenue" className="KpiCard">
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm text-gray-500 flex items-center">Revenue (YTD)<Info size={14} className="text-gray-400 hover:text-blue-500 cursor-help ml-1" /></div>
                <div className="text-2xl font-bold text-gray-900 mt-1">${revenue}</div>
              </div>
              <div className="p-2 rounded-lg bg-blue-50"><TrendingUp size={20} className="text-blue-600" /></div>
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs font-medium text-green-600"><TrendingUp size={12} />4.2% vs last month</div>
          </div>
        </InteractiveElement>

        <InteractiveElement tourId="auto-cat" className="KpiCard">
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm text-gray-500 flex items-center">AI Auto-Categorised<Info size={14} className="text-gray-400 hover:text-blue-500 cursor-help ml-1" /></div>
                <div className="text-2xl font-bold text-gray-900 mt-1">{autoRate}%</div>
              </div>
              <div className="p-2 rounded-lg bg-green-50"><Brain size={20} className="text-green-600" /></div>
            </div>
            <div className="mt-2 text-xs font-medium text-green-600">Target: 80%</div>
          </div>
        </InteractiveElement>

        <InteractiveElement tourId="expenses" className="KpiCard">
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm text-gray-500 flex items-center">Expenses (YTD)<Info size={14} className="text-gray-400 hover:text-blue-500 cursor-help ml-1" /></div>
                <div className="text-2xl font-bold text-gray-900 mt-1">${expenses}</div>
              </div>
              <div className="p-2 rounded-lg bg-red-50"><TrendingDown size={20} className="text-red-600" /></div>
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs font-medium text-red-600"><TrendingDown size={12} />-2.1% vs last month</div>
          </div>
        </InteractiveElement>

        <InteractiveElement tourId="profit" className="KpiCard">
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm text-gray-500 flex items-center">Net Profit (YTD)<Info size={14} className="text-gray-400 hover:text-blue-500 cursor-help ml-1" /></div>
                <div className="text-2xl font-bold text-gray-900 mt-1">${profit}</div>
              </div>
              <div className="p-2 rounded-lg bg-orange-50"><DollarSign size={20} className="text-orange-600" /></div>
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs font-medium text-orange-600"><TrendingUp size={12} />8.7% growth</div>
          </div>
        </InteractiveElement>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-800 mb-4">Revenue vs Expenses</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={[{ month: "Oct", revenue: 48200, expenses: 28400 }, { month: "Nov", revenue: 52100, expenses: 31200 }, { month: "Dec", revenue: 38900, expenses: 24100 }, { month: "Jan", revenue: 55400, expenses: 33800 }, { month: "Feb", revenue: 47300, expenses: 29600 }, { month: "Mar", revenue: 61200, expenses: 36400 }, { month: "Apr", revenue: 51300, expenses: 31200 }]}>
              <XAxis dataKey="month" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <RechartsTooltip formatter={(v) => `$${v.toLocaleString()}`} />
              <Bar dataKey="revenue" fill="#3b82f6" radius={[4,4,0,0]} name="Revenue" />
              <Bar dataKey="expenses" fill="#e2e8f0" radius={[4,4,0,0]} name="Expenses" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-800 mb-4">AI Categorisation</h2>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={[{ name: "Embedding", value: 78, color: "#22c55e" }, { name: "LLM", value: 14, color: "#3b82f6" }, { name: "Review", value: 5, color: "#f59e0b" }, { name: "Manual", value: 3, color: "#6b7280" }]} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" paddingAngle={3}>
                {[{ color: "#22c55e" }, { color: "#3b82f6" }, { color: "#f59e0b" }, { color: "#6b7280" }].map((c, i) => <Cell key={i} fill={c.color} />)}
              </Pie>
              <Legend iconSize={10} iconType="circle" wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
