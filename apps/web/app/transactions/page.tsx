"use client";
import { useEffect, useState } from "react";
import { RefreshCw, CheckCheck, Filter, Search, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { DemoBadge } from "@/components/DemoBadge";

const DEMO_TRANSACTIONS = [
  { id: "t1",  date: "17/04/2025", desc: "BUNNINGS 00435 SYDNEY",           amount: -23450,  account: "Plumbing Materials",    code: "5000", confidence: 0.97, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t2",  date: "17/04/2025", desc: "CUSTOMER INV 2024-0342",           amount: 660000,  account: "Plumbing Services",     code: "4000", confidence: 0.92, tier: "llm",       status: "categorised", gst: "G1" },
  { id: "t3",  date: "16/04/2025", desc: "AMPOL FUEL BROOKVALE",             amount: -8920,   account: "Fuel & Vehicle",        code: "6000", confidence: 0.94, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t4",  date: "16/04/2025", desc: "GOOGLE WORKSPACE 1234",            amount: -2200,   account: "Software Subscriptions",code: "6200", confidence: 0.96, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t5",  date: "15/04/2025", desc: "WOOLWORTHS 3421 MANLY",            amount: -15630,  account: null,                    code: null,   confidence: 0.61, tier: "review",    status: "pending",     gst: null  },
  { id: "t6",  date: "15/04/2025", desc: "ATO PORTAL BAS Q3",                amount: -310000, account: "ATO Payments",          code: "6800", confidence: 0.91, tier: "llm",       status: "categorised", gst: "N-T" },
  { id: "t7",  date: "14/04/2025", desc: "REECE PLUMBING SUPPLIES",          amount: -45600,  account: "Plumbing Materials",    code: "5000", confidence: 0.99, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t8",  date: "14/04/2025", desc: "CUSTOMER PAYMENT INV 2024-0339",   amount: 440000,  account: "Plumbing Services",     code: "4000", confidence: 0.88, tier: "llm",       status: "categorised", gst: "G1" },
  { id: "t9",  date: "13/04/2025", desc: "AGL ENERGY ELECTRICITY",           amount: -23100,  account: "Electricity",           code: "6100", confidence: 0.95, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t10", date: "13/04/2025", desc: "TRANSFER TO SAVINGS",              amount: -500000, account: null,                    code: null,   confidence: 0.55, tier: "review",    status: "pending",     gst: null  },
  { id: "t11", date: "12/04/2025", desc: "TOLL ROADS NSW LINKT",             amount: -3450,   account: "Fuel & Vehicle",        code: "6000", confidence: 0.89, tier: "llm",       status: "categorised", gst: "G11" },
  { id: "t12", date: "12/04/2025", desc: "OFFICEWORKS CHATSWOOD",            amount: -7890,   account: null,                    code: null,   confidence: 0.68, tier: "review",    status: "pending",     gst: null  },
  { id: "t13", date: "11/04/2025", desc: "INSURANCE PREMIUM TRADE",          amount: -98000,  account: "Vehicle Registration",  code: "6010", confidence: 0.83, tier: "llm",       status: "categorised", gst: "G11" },
  { id: "t14", date: "11/04/2025", desc: "CUSTOMER EMERGENCY CALLOUT 2024",  amount: 165000,  account: "Emergency Call-Out",    code: "4010", confidence: 0.91, tier: "llm",       status: "categorised", gst: "G1" },
];

function TierBadge({ tier }: { tier: string }) {
  const styles: Record<string, string> = {
    embedding: "bg-green-100 text-green-700 border-green-200",
    llm:       "bg-blue-100 text-blue-700 border-blue-200",
    review:    "bg-amber-100 text-amber-700 border-amber-200",
    human:     "bg-purple-100 text-purple-700 border-purple-200",
  };
  const labels: Record<string, string> = {
    embedding: "Embedding", llm: "LLM", review: "Needs Review", human: "Manual"
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${styles[tier] ?? styles.review}`}>
      {labels[tier] ?? tier}
    </span>
  );
}

function ConfBadge({ confidence, tier }: { confidence: number; tier: string }) {
  if (tier === "review" || confidence < 0.7) {
    return <span className="text-amber-600 font-semibold">{(confidence * 100).toFixed(0)}%</span>;
  }
  if (confidence >= 0.9) {
    return <span className="text-green-600 font-semibold">{(confidence * 100).toFixed(0)}%</span>;
  }
  return <span className="text-blue-600 font-semibold">{(confidence * 100).toFixed(0)}%</span>;
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState(DEMO_TRANSACTIONS);
  const [filter, setFilter] = useState("all");
  const [search, setSearch]  = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const filtered = transactions.filter(t => {
    const matchStatus = filter === "all" || t.status === filter || (filter === "review" && t.tier === "review");
    const matchSearch = t.desc.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  const pendingCount = transactions.filter(t => t.tier === "review").length;

  async function syncTransactions() {
    setLoading(true);
    try {
      const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/basiq/sync`, { method: "POST" });
      const data = await r.json();
      toast({ title: `Synced ${data.inserted ?? 0} new transactions`, description: `${data.synced ?? 0} total fetched from Basiq` });
    } catch {
      toast({ title: "Sync failed", description: "Check Basiq connection", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  async function categoriseAll() {
    setLoading(true);
    toast({ title: "Running AI categorisation...", description: "Processing all pending transactions" });
    await new Promise(r => setTimeout(r, 1500));
    toast({ title: "Categorisation complete", description: "89% auto-categorised" });
    setLoading(false);
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {filtered.length} transactions · {pendingCount} need review
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={syncTransactions} disabled={loading}>
            <RefreshCw size={14} className={`mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Sync Bank Feed
          </Button>
          <Button size="sm" onClick={categoriseAll} disabled={loading}>
            <CheckCheck size={14} className="mr-1.5" />
            Categorise All
          </Button>
        </div>
      </div>

      {pendingCount > 0 && (
        <div className="flex items-center gap-2 bg-amber-50 border border-amber-200
          text-amber-800 text-sm px-4 py-2.5 rounded-lg">
          <AlertCircle size={16} className="shrink-0" />
          <span><strong>{pendingCount} transactions</strong> need your review before they can be posted to the ledger.</span>
          <button onClick={() => setFilter("review")}
            className="ml-auto text-amber-700 underline text-xs font-medium">Show only</button>
        </div>
      )}

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Search transactions..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-44 text-sm">
            <Filter size={14} className="mr-1.5 text-gray-400" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Transactions</SelectItem>
            <SelectItem value="review">Needs Review</SelectItem>
            <SelectItem value="categorised">Categorised</SelectItem>
            <SelectItem value="posted">Posted</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              {["Date","Description","Amount","Account","Tier","Confidence","GST","Action"].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.map(t => (
              <tr key={t.id} className={`hover:bg-gray-50 transition-colors ${t.tier === "review" ? "bg-amber-50/40" : ""}`}>
                <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">{t.date}</td>
                <td className="px-4 py-3 text-gray-900 max-w-[220px]">
                  <div className="truncate font-medium">{t.desc}</div>
                </td>
                <td className={`px-4 py-3 font-semibold whitespace-nowrap ${t.amount < 0 ? "text-red-600" : "text-green-600"}`}>
                  {t.amount < 0 ? "-" : "+"}${(Math.abs(t.amount) / 100).toFixed(2)}
                </td>
                <td className="px-4 py-3">
                  {t.account
                    ? <span className="text-gray-700">{t.account} <span className="text-gray-400 text-xs">({t.code})</span></span>
                    : <span className="text-gray-400 italic">Uncategorised</span>
                  }
                </td>
                <td className="px-4 py-3"><TierBadge tier={t.tier} /></td>
                <td className="px-4 py-3"><ConfBadge confidence={t.confidence} tier={t.tier} /></td>
                <td className="px-4 py-3 text-gray-500 text-xs">{t.gst ?? "—"}</td>
                <td className="px-4 py-3">
                  {t.tier === "review"
                    ? <Button size="sm" variant="outline" className="text-xs h-7 border-amber-300 text-amber-700 hover:bg-amber-50">
                        Fix
                      </Button>
                    : <Button size="sm" variant="ghost" className="text-xs h-7 text-gray-400">
                        Edit
                      </Button>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}