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
  { id: "overview", title: "AI Auto-Categorised", desc: "The AI automatically categorises 68-89% of transactions. Target is 80%. Each transaction is analyzed and sorted into the right account code - saves hours of data entry.", value: "89% auto-categorization", color: "#22c55e" },
  { id: "revenue", title: "Revenue", desc: "Total income from all sales and other sources. Track how much money is coming in from clients and jobs.", value: "$51,300 YTD", color: "#3b82f6" },
  { id: "expenses", title: "Expenses", desc: "All business costs - materials, wages, rent, vehicle. Know exactly where money is going.", value: "$31,200 YTD", color: "#e2e8f0" },
  { id: "auto-cat", title: "Auto-Categorisation", desc: "AI looks at each transaction and picks the right account code. Most are done automatically - you only review the tricky ones.", value: "68-89% auto-categorization", color: "#22c55e" },
  { id: "profit", title: "Net Profit", desc: "What's left after expenses. Your real earnings - revenue minus all costs.", value: "$18,450 YTD", color: "#f59e0b" },
  { id: "ledger", title: "Ledger Balanced", desc: "Double-entry ensures every transaction has matching credits and debits. The books always balance.", value: "Ledger balanced", color: "#14b8a6" },
  { id: "export", title: "Export Reports", desc: "One-click reports ready for BAS, tax, or your accountant. CSV or screen view.", value: "15min → seconds", color: "#8b5cf6" },
  { id: "chart", title: "Visual Trends", desc: "See revenue vs expenses over time. Spot patterns and plan ahead.", value: "7 months data", color: "#ec4899" },
];

type InteractiveElementProps = {
  children: ReactNode;
  tourId: string;
  className?: string;
};

function TourOverlay({ isOpen, onClose, step, setStep }: { isOpen: boolean; onClose: () => void; step: number; setStep: (n: number) => void }) {
  const currentStep = TOUR_STEPS[step];
  const STEP_IDS = TOUR_STEPS.map(s => s.id);

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/70" />

      <div className="absolute top-4 right-4 w-80">
        <motion.div
          className="bg-white rounded-2xl shadow-2xl p-6 border-l-4"
          style={{ borderLeftColor: currentStep.color }}
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
            <div className="p-2 rounded-lg" style={{ backgroundColor: currentStep.color + "20" }}>
              <Target size={20} style={{ color: currentStep.color }} />
            </div>
            <div>
              <span className="text-xs text-gray-500 block">Result</span>
              <span className="text-sm font-semibold text-gray-900">{currentStep.value}</span>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="absolute bottom-6 right-6 flex gap-3">
        {step > 0 && (
          <button onClick={() => setStep(step - 1)} className="px-4 py-2 text-sm font-medium text-white hover:bg-white/20 rounded-lg transition-colors">
            Previous
          </button>
        )}
        {step < TOUR_STEPS.length - 1 ? (
          <button onClick={() => setStep(step + 1)} className="px-4 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
            Next
          </button>
        ) : (
          <button onClick={onClose} className="px-4 py-2 text-sm font-bold text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
            Got it!
          </button>
        )}
      </div>

      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2">
        {TOUR_STEPS.map((s, idx) => (
          <button
            key={idx}
            onClick={() => setStep(idx)}
            className={`h-2 rounded-full transition-all ${idx === step ? 'w-8 bg-white' : 'w-2 bg-white/40 hover:bg-white/60'}`}
            style={{ backgroundColor: idx === step ? currentStep.color : undefined }}
          />
        ))}
      </div>
    </div>
  );
}

function InteractiveElement({ children, tourId, className = "", isActive = false }: InteractiveElementProps & { isActive?: boolean }) {
  return (
    <div data-tour={tourId} className={`relative z-10 transition-all duration-300 ${className}`}>
      {children}
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-xl border-2 border-blue-500 bg-blue-500/10 pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        />
      )}
    </div>
  );
}

export default function Dashboard() {
  const [tourOpen, setTourOpen] = useState<boolean>(false);
  const [tourStep, setTourStep] = useState<number>(0);
  const revenue = "51,300";
  const expenses = "31,200";
  const profit = "18,450";
  const autoRate = 89;
  const currentTourId = STEP_IDS[tourStep];

  return (
    <div className="space-y-6 p-6">
      {tourOpen && (
        <TourOverlay isOpen={tourOpen} onClose={() => setTourOpen(false)} step={tourStep} setStep={setTourStep} />
      )}

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
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 text-xs px-3 py-1.5 rounded-full font-medium" data-tour="ledger">
            <CheckCircle2 size={14} />
            Ledger balanced
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <InteractiveElement tourId="revenue" className="KpiCard" isActive={tourOpen && currentTourId === "revenue"}>
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

        <InteractiveElement tourId="auto-cat" className="KpiCard" isActive={tourOpen && currentTourId === "auto-cat"}>
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

        <InteractiveElement tourId="expenses" className="KpiCard" isActive={tourOpen && currentTourId === "expenses"}>
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

        <InteractiveElement tourId="profit" className="KpiCard" isActive={tourOpen && currentTourId === "profit"}>
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
        <InteractiveElement tourId="chart" className="col-span-2" isActive={tourOpen && currentTourId === "chart"}>
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
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
        </InteractiveElement>

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
