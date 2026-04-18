"use client";

import { useState } from "react";
import { Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

const ACCOUNTS = [
  { code: "1000", name: "ANZ Business Cheque", type: "asset", gst: "N-T", system: true },
  { code: "1100", name: "Trade Debtors", type: "asset", gst: "N-T", system: true },
  { code: "1200", name: "GST Receivable", type: "asset", gst: "N-T", system: true },
  { code: "2000", name: "Trade Creditors", type: "liability", gst: "N-T", system: true },
  { code: "2100", name: "GST Collected", type: "liability", gst: "N-T", system: true },
  { code: "3000", name: "Retained Earnings", type: "equity", gst: "N-T", system: true },
  { code: "4000", name: "Plumbing Services Revenue", type: "revenue", gst: "G1", system: true },
  { code: "4010", name: "Emergency Call-Out Revenue", type: "revenue", gst: "G1", system: false },
  { code: "5000", name: "Plumbing Materials & Parts", type: "expense", gst: "G11", system: false },
  { code: "5010", name: "Subcontractor Labour", type: "expense", gst: "G11", system: false },
  { code: "6000", name: "Fuel & Vehicle", type: "expense", gst: "G11", system: false },
  { code: "6100", name: "Electricity", type: "expense", gst: "G11", system: false },
  { code: "6200", name: "Software Subscriptions", type: "expense", gst: "G11", system: false },
  { code: "6700", name: "Wages & Salaries", type: "expense", gst: "N-T", system: false },
  { code: "6800", name: "ATO Payments", type: "expense", gst: "N-T", system: false },
];

const TYPE_COLORS: Record<string, string> = {
  asset: "bg-blue-100 text-blue-700",
  liability: "bg-red-100 text-red-700",
  equity: "bg-purple-100 text-purple-700",
  revenue: "bg-green-100 text-green-700",
  expense: "bg-orange-100 text-orange-700",
};

type AccountType = "all" | "asset" | "liability" | "equity" | "revenue" | "expense";

export default function ChartOfAccountsPage() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<AccountType>("all");

  const filteredAccounts = ACCOUNTS.filter((account) => {
    const matchesSearch =
      search === "" ||
      account.name.toLowerCase().includes(search.toLowerCase()) ||
      account.code.includes(search);
    const matchesType = typeFilter === "all" || account.type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Chart of Accounts</h1>
          <p className="text-muted-foreground mt-1">
            Manage your account codes and categories
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Account
        </Button>
      </div>

      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search accounts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div className="flex gap-2">
          {(["all", "asset", "liability", "equity", "revenue", "expense"] as AccountType[]).map(
            (type) => (
              <Button
                key={type}
                variant={typeFilter === type ? "default" : "outline"}
                size="sm"
                onClick={() => setTypeFilter(type)}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </Button>
            )
          )}
        </div>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-4 font-medium">Code</th>
              <th className="text-left p-4 font-medium">Name</th>
              <th className="text-left p-4 font-medium">Type</th>
              <th className="text-left p-4 font-medium">GST</th>
              <th className="text-left p-4 font-medium">System</th>
            </tr>
          </thead>
          <tbody>
            {filteredAccounts.map((account) => (
              <tr key={account.code} className="border-t">
                <td className="p-4 font-mono">{account.code}</td>
                <td className="p-4">{account.name}</td>
                <td className="p-4">
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-medium ${TYPE_COLORS[account.type] || "bg-gray-100 text-gray-600"}`}
                  >
                    {account.type.charAt(0).toUpperCase() +
                      account.type.slice(1)}
                  </span>
                </td>
                <td className="p-4">{account.gst}</td>
                <td className="p-4">
                  {account.system ? (
                    <span className="text-muted-foreground">—</span>
                  ) : (
                    <span className="text-muted-foreground">User</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}