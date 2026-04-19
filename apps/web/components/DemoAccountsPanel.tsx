"use client";
import { useState } from "react";
import { Info, Building2, Database, User } from "lucide-react";

interface DemoAccount {
  id: string;
  name: string;
  account_no: string;
  balance: number;
  type: string;
  institution: string;
}

interface DemoAccountsPanelProps {
  demoAccounts: DemoAccount[];
}

const TYPE_COLORS: Record<string, string> = {
  mortgage: "bg-red-100 text-red-700 border-red-200",
  credit: "bg-orange-100 text-orange-700 border-orange-200",
  savings: "bg-green-100 text-green-700 border-green-200",
  transaction: "bg-blue-100 text-blue-700 border-blue-200",
};

export function DemoAccountsPanel({ demoAccounts }: DemoAccountsPanelProps) {
  const [showInfo, setShowInfo] = useState(false);

  if (!demoAccounts || demoAccounts.length === 0) return null;

  const formatCurrency = (amount: number) => {
    const formatted = new Intl.NumberFormat("en-AU", {
      style: "currency",
      currency: "AUD",
    }).format(Math.abs(amount));
    return amount < 0 ? `-${formatted}` : formatted;
  };

  const totalBalance = demoAccounts.reduce((sum, acc) => sum + acc.balance, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-amber-100 border border-amber-200 px-2 py-1 rounded text-xs font-medium text-amber-700">
            Demo
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Demo Accounts</h2>
        </div>
        <button
          onClick={() => setShowInfo(!showInfo)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
        >
          <Info size={14} />
          {showInfo ? "Hide" : "Show"} source info
        </button>
      </div>

      {showInfo && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm">
          <div className="font-semibold text-amber-800 mb-2">
            How this data was obtained
          </div>
          <div className="space-y-2 text-amber-700">
            <div className="flex items-center gap-2">
              <Building2 size={14} />
              <span>
                <span className="font-medium">Source:</span> Basiq Sandbox (Hooli Bank
                AU00000)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Database size={14} />
              <span>
                <span className="font-medium">Data queried via:</span> Neon database (project:
                smart-gl)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <User size={14} />
              <span>
                <span className="font-medium">Account:</span> Wentworth-Smith demo
                persona
              </span>
            </div>
            <div className="text-xs text-amber-600 mt-2 pt-2 border-t border-amber-200">
              This is sample data for demonstration purposes. Real bank connections
              provide live transaction data.
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {demoAccounts.map((account) => (
          <div
            key={account.id}
            className="bg-white rounded-xl p-5 border-2 border-dashed border-amber-200"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="font-semibold text-gray-900">{account.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {account.account_no}
                </div>
              </div>
              <span
                className={`inline-flex px-2 py-0.5 rounded text-xs font-medium border ${
                  TYPE_COLORS[account.type] || "bg-gray-100 text-gray-600 border-gray-200"
                }`}
              >
                {account.type}
              </span>
            </div>
            <div
              className={`text-2xl font-bold mb-3 ${
                account.balance < 0 ? "text-red-600" : "text-green-600"
              }`}
            >
              {formatCurrency(account.balance)}
            </div>
            <div className="text-xs text-gray-400">
              {account.institution}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-amber-700">Demo accounts total</span>
          <span
            className={`font-bold ${
              totalBalance < 0 ? "text-red-600" : "text-green-600"
            }`}
          >
            {formatCurrency(totalBalance)}
          </span>
        </div>
        <div className="text-xs text-amber-600 mt-1">
          These are additional demo accounts, not replacing your real connected accounts
        </div>
      </div>
    </div>
  );
}