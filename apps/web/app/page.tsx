"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Brain, CheckCircle2, Info, Play, X } from "lucide-react";
import { useState } from "react";

const MONTHLY_DATA = [
  { month: "Oct", revenue: 48200, expenses: 28400 },
  { month: "Nov", revenue: 52100, expenses: 31200 },
  { month: "Dec", revenue: 38900, expenses: 24100 },
  { month: "Jan", revenue: 55400, expenses: 33800 },
  { month: "Feb", revenue: 47300, expenses: 29600 },
  { month: "Mar", revenue: 61200, expenses: 36400 },
  { month: "Apr", revenue: 51300, expenses: 31200 },
];

function InfoTip({ content }: { content: string }) {
  return (
    <div className="group relative inline-flex ml-1">
      <Info size={14} className="text-gray-400 hover:text-blue-500 cursor-help" />
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
        {content}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
      </div>
    </div>
  );
}

function KpiCard({ label, value, trend, icon: Icon, tooltip }: any) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-gray-500 flex items-center">
            {label}
            {tooltip && <InfoTip content={tooltip} />}
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{value}</div>
        </div>
        <div className="p-2 rounded-lg bg-blue-50">
          <Icon size={20} className="text-blue-600" />
        </div>
      </div>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trend >= 0 ? "text-green-600" : "text-red-500"}`}>
          {trend >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {Math.abs(trend)}% vs last month
        </div>
      )}
    </div>
  );
}

const TOUR_STEPS = [
  { title: "AI Auto-Categorised", desc: "The AI automatically categorises 68-89% of transactions. Target is 80%." },
  { title: "Revenue", desc: "Your total income from sales and other sources for this period." },
  { title: "Expenses", desc: "All business costs including rent, wages, supplies." },
  { title: "Net Profit", desc: "Revenue minus Expenses. Your actual earnings." },
  { title: "Export BAS", desc: "One-click GST-ready CSV for your BAS return." },
];

function TourModal({ isOpen, onClose, step, setStep }: any) {
  if (!isOpen) return null;
  const total = TOUR_STEPS.length;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="text-sm text-gray-500">Step {step + 1} of {total}</div>
            <h3 className="text-lg font-bold">{TOUR_STEPS[step].title}</h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X size={20} />
          </button>
        </div>
        <p className="text-gray-600 mb-6">{TOUR_STEPS[step].desc}</p>
        <div className="flex justify-between">
          <button onClick={onClose} className="text-sm text-gray-500 hover:text-gray-700">Skip Tour</button>
          <button onClick={() => setStep(step < total - 1 ? step + 1 : onClose())} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
            {step < total - 1 ? "Next" : "Got It!"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [tourOpen, setTourOpen] = useState(false);
  const [tourStep, setTourStep] = useState(0);
  const revenue = "51,300";
  const expenses = "31,200";
  const profit = "18,450";
  const autoRate = 89;

  return (
    <div className="space-y-6">
      <TourModal isOpen={tourOpen} onClose={() => setTourOpen(false)} step={tourStep} setStep={setTourStep} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">FY 2024–25 · April 2025</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setTourOpen(true)} className="flex items-center gap-2 bg-blue-50 text-blue-700 text-sm px-3 py-1.5 rounded-lg font-medium hover:bg-blue-100">
            <Play size={14} />
            Start Tour
          </button>
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 text-xs px-3 py-1.5 rounded-full font-medium">
            <CheckCircle2 size={14} />
            Ledger balanced
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <KpiCard label="Revenue (YTD)" value={`$${revenue}`} icon={TrendingUp} trend={4.2} tooltip="Your total income from sales and services" />
        <KpiCard label="Expenses (YTD)" value={`$${expenses}`} icon={TrendingDown} trend={-2.1} tooltip="All business costs this period" />
        <KpiCard label="Net Profit (YTD)" value={`$${profit}`} icon={DollarSign} trend={8.7} tooltip="Revenue minus Expenses" />
        <KpiCard label="AI Auto-Categorised" value={`${autoRate}%`} icon={Brain} tooltip="68% auto-categorised. Target: 80%. Hover over transactions to see how it works." />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-800 mb-4">Revenue vs Expenses</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={MONTHLY_DATA} barGap={4}>
              <XAxis dataKey="month" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={(v: number) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <RechartsTooltip formatter={(v: number) => `$${v.toLocaleString()}`} />
              <Bar dataKey="revenue" fill="#3b82f6" radius={[4,4,0,0]} name="Revenue" />
              <Bar dataKey="expenses" fill="#e2e8f0" radius={[4,4,0,0]} name="Expenses" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-800 mb-4">AI Categorisation</h2>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={[
                { name: "Embedding", value: 78, color: "#22c55e" },
                { name: "LLM", value: 14, color: "#3b82f6" },
                { name: "Review", value: 5, color: "#f59e0b" },
                { name: "Manual", value: 3, color: "#6b7280" },
              ]} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" paddingAngle={3}>
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