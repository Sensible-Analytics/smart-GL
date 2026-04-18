"use client";
import { useState } from "react";
import { RefreshCw, Plus, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

const CONNECTIONS = [
  { id: "c1", bank: "ANZ",     name: "Business Everyday",  number: "****4521", balance: "$82,345.20", lastSync: "Today 09:14", status: "active",  txnCount: 143 },
  { id: "c2", bank: "ANZ",     name: "Business Savings",   number: "****7834", balance: "$24,100.00", lastSync: "Today 09:14", status: "active",  txnCount: 12  },
];

export default function BankFeedsPage() {
  const [syncing, setSyncing] = useState(false);
  const { toast }  = useToast();

  async function runSync() {
    setSyncing(true);
    try {
      const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/basiq/sync`, { method: "POST" });
      const d = await r.json();
      toast({ title: `Sync complete`, description: `${d.inserted ?? 0} new transactions imported` });
    } catch {
      toast({ title: "Sync failed", variant: "destructive" });
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bank Feeds</h1>
          <p className="text-sm text-gray-500 mt-0.5">Connected via Basiq Open Banking (CDR)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={runSync} disabled={syncing}>
            <RefreshCw size={14} className={`mr-1.5 ${syncing ? "animate-spin" : ""}`} />
            Sync All
          </Button>
          <Button size="sm">
            <Plus size={14} className="mr-1.5" />
            Add Bank Account
          </Button>
        </div>
      </div>


      <div className="grid grid-cols-2 gap-4">
        {CONNECTIONS.map(c => (
          <div key={c.id} className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="font-semibold text-gray-900">{c.bank} — {c.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">{c.number}</div>
              </div>
              <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full">
                <CheckCircle2 size={12} />
                Active
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-3">{c.balance}</div>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
              <div><span className="text-gray-400">Last sync</span><br /><span className="text-gray-700 font-medium">{c.lastSync}</span></div>
              <div><span className="text-gray-400">Transactions</span><br /><span className="text-gray-700 font-medium">{c.txnCount} this period</span></div>
            </div>
          </div>
        ))}

        <div className="bg-gray-50 rounded-xl p-5 border border-dashed border-gray-200 flex flex-col items-center justify-center gap-2 cursor-pointer hover:bg-gray-100 transition-colors">
          <div className="w-10 h-10 rounded-full bg-white border border-gray-200 flex items-center justify-center">
            <Plus size={18} className="text-gray-400" />
          </div>
          <div className="text-sm font-medium text-gray-600">Connect another bank</div>
          <div className="text-xs text-gray-400 text-center">135+ Australian banks supported via CDR</div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="px-5 py-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Sync History</h2>
        </div>
        <div className="divide-y divide-gray-50">
          {[
            { time: "Today 09:14",     bank: "ANZ (both accounts)", result: "143 transactions",  status: "success" },
            { time: "Yesterday 09:00", bank: "ANZ (both accounts)", result: "8 new transactions", status: "success" },
            { time: "16/04 09:00",     bank: "ANZ (both accounts)", result: "11 new transactions",status: "success" },
            { time: "15/04 15:32",     bank: "ANZ Business",        result: "Connection timeout", status: "error"   },
          ].map((r, i) => (
            <div key={i} className="flex items-center justify-between px-5 py-3 text-sm">
              <div className="flex items-center gap-3">
                {r.status === "success"
                  ? <CheckCircle2 size={16} className="text-green-500" />
                  : <AlertCircle size={16} className="text-red-400" />
                }
                <div>
                  <div className="text-gray-800 font-medium">{r.bank}</div>
                  <div className="text-xs text-gray-400">{r.result}</div>
                </div>
              </div>
              <div className="text-xs text-gray-400 flex items-center gap-1">
                <Clock size={12} />
                {r.time}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 text-sm">
        <div className="font-semibold text-blue-800 mb-2">About Basiq Open Banking</div>
        <div className="text-blue-700 space-y-1 text-xs">
          <p>Bank feeds are powered by Basiq, an ACCC-accredited Consumer Data Right (CDR) data recipient.</p>
          <p>Data is fetched via CDR Open Banking for supported institutions. Older banks use a web connector fallback.</p>
          <p>Transactions are fetched 30 days back on each sync to capture delayed postings. Deduplication is guaranteed by Basiq transaction ID.</p>
        </div>
      </div>
    </div>
  );
}
