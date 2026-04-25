"use client";

import { Brain, TrendingUp, AlertTriangle, Lightbulb } from "lucide-react";
import { DemoBadge } from "@/components/DemoBadge";

const INSIGHTS = [
  {
    type: "anomaly",
    title: "Unusual expense: Officeworks $78.90",
    body: "This transaction is 2.3 std deviations above your monthly average. Consider verifying the business purpose.",
    action: "Review transaction",
    severity: "warning",
  },
  {
    type: "pattern",
    title: "Woolworths transactions likely split-purpose",
    body: "3 transactions on the same day may contain personal items. Review to ensure proper GST treatment.",
    action: "Review 3 transactions",
    severity: "info",
  },
  {
    type: "suggestion",
    title: "Superannuation liability may be underpaid",
    body: "Based on wages posted this period, the superannuation accrual appears low by $234.50.",
    action: "Create journal entry",
    severity: "error",
  },
  {
    type: "pattern",
    title: "High confidence: Reece Plumbing = Account 5000",
    body: "This merchant has been mapped to Account 5000 (Materials) with 94% confidence across 12 transactions.",
    action: null,
    severity: "success",
  },
  {
    type: "auto-journal",
    title: "Auto journal: Monthly depreciation",
    body: "Depreciation of $1,250 calculated for fixed assets based on useful life schedules. Ready to post.",
    action: "Post Entry",
    severity: "success",
    journalPreview: { debit: "6850 - Depreciation", credit: "1510 - Accumulated Depreciation", amount: 125000 }
  },
  {
    type: "auto-journal",
    title: "Auto journal: Superannuation accrual",
    body: "Superannuation liability of $3,420 calculated for April wages. Ready to post.",
    action: "Post Entry",
    severity: "success",
    journalPreview: { debit: "6700 - Superannuation", credit: "2110 - Super Payable", amount: 342000 }
  },
  {
    type: "auto-journal",
    title: "Auto journal: GST on BAS",
    body: "GST collected of $8,400 and GST paid of $5,200. Net GST payable $3,200. Ready to post.",
    action: "Post Entry",
    severity: "success",
    journalPreview: { debit: "2000 - GST Collected", credit: "2001 - GST Paid", amount: 320000 }
  },
];

const severityStyles = {
  error: {
    icon: AlertTriangle,
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-800",
    badge: "bg-red-100 text-red-700",
  },
  warning: {
    icon: TrendingUp,
    bg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-800",
    badge: "bg-amber-100 text-amber-700",
  },
  info: {
    icon: Brain,
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-800",
    badge: "bg-blue-100 text-blue-700",
  },
  success: {
    icon: Lightbulb,
    bg: "bg-green-50",
    border: "border-green-200",
    text: "text-green-800",
    badge: "bg-green-100 text-green-700",
  },
};

export default function AIInsightsPage() {
  return (
    <div className="max-w-4xl space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">AI Insights</h1>
          <p className="text-gray-500 mt-1">
            AI-detected anomalies and suggestions for your ledger
          </p>
        </div>
        <DemoBadge />
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Embedding Match</div>
          <div className="text-2xl font-semibold text-gray-900">78%</div>
          <div className="text-xs text-gray-400">of classifications</div>
        </div>
        <div className="bg-white rounded-lg border p-4 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">LLM Review</div>
          <div className="text-2xl font-semibold text-gray-900">14%</div>
          <div className="text-xs text-gray-400">of transactions</div>
        </div>
        <div className="bg-white rounded-lg border p-4 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Human Review</div>
          <div className="text-2xl font-semibold text-gray-900">5%</div>
          <div className="text-xs text-gray-400">confidence flag</div>
        </div>
        <div className="bg-white rounded-lg border p-4 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Training Samples</div>
          <div className="text-2xl font-semibold text-gray-900">643</div>
          <div className="text-xs text-gray-400">labelled entries</div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-medium text-gray-900">Insights</h2>
        <div className="space-y-3">
          {INSIGHTS.map((insight, idx) => {
            const style = severityStyles[insight.severity as keyof typeof severityStyles];
            const Icon = style.icon;
            return (
              <div
                key={idx}
                className={`rounded-lg border ${style.bg} ${style.border} p-4`}
              >
                <div className="flex items-start gap-3">
                  <Icon className={`w-5 h-5 mt-0.5 ${style.text}`} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`font-medium ${style.text}`}>{insight.title}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${style.badge}`}>
                        {insight.severity}
                      </span>
                    </div>
                    <p className={`text-sm ${style.text} opacity-80`}>{insight.body}</p>
                    {insight.action && (
                      <button className="mt-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline">
                        {insight.action} →
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Stage 2: Auto-Journal</h3>
        <p className="text-gray-500 text-sm mb-4">
          AI will suggest and apply recurring journal entries automatically
        </p>
        <span className="inline-flex items-center px-3 py-1.5 rounded text-sm font-medium bg-gray-100 text-gray-600">
          Coming Soon
        </span>
      </div>
    </div>
  );
}