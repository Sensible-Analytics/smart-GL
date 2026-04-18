"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Brain, CheckCircle2 } from "lucide-react";

const MONTHLY_DATA = [
  { month: "Oct", revenue: 48200, expenses: 28400 },
  { month: "Nov", revenue: 52100, expenses: 31200 },
  { month: "Dec", revenue: 38900, expenses: 24100 },
  { month: "Jan", revenue: 55400, expenses: 33800 },
  { month: "Feb", revenue: 47300, expenses: 29600 },
  { month: "Mar", revenue: 61200, expenses: 36400 },
  { month: "Apr", revenue: 51300, expenses: 31200 },
];

function KpiCard({ label, value, trend, icon: Icon }: any) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-gray-500">{label}</div>
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

export default function Dashboard() {
  const revenue = "51,300";
  const expenses = "31,200";
  const profit = "18,450";
  const autoRate = 89;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">FY 2024–25 · April 2025</p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 text-xs px-3 py-1.5 rounded-full font-medium">
          <CheckCircle2 size={14} />
          Ledger balanced
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <KpiCard label="Revenue (YTD)" value={`$${revenue}`} icon={TrendingUp} trend={4.2} />
        <KpiCard label="Expenses (YTD)" value={`$${expenses}`} icon={TrendingDown} trend={-2.1} />
        <KpiCard label="Net Profit (YTD)" value={`$${profit}`} icon={DollarSign} trend={8.7} />
        <KpiCard label="AI Auto-Categorised" value={`${autoRate}%`} icon={Brain} />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-800 mb-4">Revenue vs Expenses</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={MONTHLY_DATA} barGap={4}>
              <XAxis dataKey="month" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={(v: number) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v: number) => `$${v.toLocaleString()}`} />
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