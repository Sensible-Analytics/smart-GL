"use client";
import { useState } from "react";
import { ChevronDown, ChevronRight, CheckCircle2 } from "lucide-react";
import { DemoBadge } from "@/components/DemoBadge";

const JOURNAL_ENTRIES = [
  {
    id: "JE-0042", date: "17/04/2025", description: "Bunnings Warehouse - Plumbing Materials",
    reference: "BUNNINGS 00435", status: "posted", totalDebit: 23450, totalCredit: 23450,
    lines: [
      { account: "5000 Plumbing Materials & Parts", debit: 21318,  credit: 0,      gst: 2132  },
      { account: "1200 GST Receivable",              debit: 2132,   credit: 0,      gst: 0     },
      { account: "1000 ANZ Business Cheque",         debit: 0,      credit: 23450,  gst: 0     },
    ]
  },
  {
    id: "JE-0041", date: "16/04/2025", description: "Customer Invoice 2024-0342 - Emergency Plumbing",
    reference: "INV-2024-0342", status: "posted", totalDebit: 660000, totalCredit: 660000,
    lines: [
      { account: "1000 ANZ Business Cheque",         debit: 660000, credit: 0,      gst: 0     },
      { account: "4000 Plumbing Services Revenue",   debit: 0,      credit: 600000, gst: 0     },
      { account: "2100 GST Collected",               debit: 0,      credit: 60000,  gst: 60000 },
    ]
  },
  {
    id: "JE-0040", date: "16/04/2025", description: "Ampol Fuel - Vehicle Operating Expense",
    reference: "AMPOL BROOKVALE", status: "posted", totalDebit: 8920, totalCredit: 8920,
    lines: [
      { account: "6000 Fuel & Vehicle",              debit: 8109,   credit: 0,      gst: 811   },
      { account: "1200 GST Receivable",              debit: 811,    credit: 0,      gst: 0     },
      { account: "1000 ANZ Business Cheque",           debit: 0,      credit: 8920,   gst: 0     },
    ]
  },
  {
    id: "JE-0039", date: "15/04/2025", description: "ATO BAS Payment Q3",
    reference: "ATO PORTAL", status: "posted", totalDebit: 310000, totalCredit: 310000,
    lines: [
      { account: "2110 GST Payable",                 debit: 310000, credit: 0,      gst: 0     },
      { account: "1000 ANZ Business Cheque",          debit: 0,      credit: 310000, gst: 0     },
    ]
  },
];

function fmt(cents: number) {
  return cents > 0 ? `$${(cents / 100).toLocaleString("en-AU", { minimumFractionDigits: 2 })}` : "—";
}

export default function JournalPage() {
  const [expanded, setExpanded] = useState<string | null>("JE-0042");

  const totalDebits  = JOURNAL_ENTRIES.reduce((s, e) => s + e.totalDebit, 0);
  const totalCredits = JOURNAL_ENTRIES.reduce((s, e) => s + e.totalCredit, 0);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Journal</h1>
          <p className="text-sm text-gray-500 mt-0.5">Double-entry ledger — powered by Formance</p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 border border-green-200
          text-green-700 text-xs px-3 py-1.5 rounded-full font-medium">
          <CheckCircle2 size={14} />
          Balanced: Dr ${(totalDebits/100).toLocaleString()} = Cr ${(totalCredits/100).toLocaleString()}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-4 py-3 text-left w-8" />
              <th className="px-4 py-3 text-left">Reference</th>
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3 text-left">Description</th>
              <th className="px-4 py-3 text-right">Debit</th>
              <th className="px-4 py-3 text-right">Credit</th>
              <th className="px-4 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {JOURNAL_ENTRIES.map(entry => (
              <>
                <tr
                  key={entry.id}
                  className="hover:bg-gray-50 cursor-pointer border-t border-gray-100"
                  onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
                >
                  <td className="px-4 py-3 text-gray-400">
                    {expanded === entry.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{entry.id}</td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{entry.date}</td>
                  <td className="px-4 py-3 text-gray-800 font-medium">{entry.description}</td>
                  <td className="px-4 py-3 text-right font-medium text-gray-700">{fmt(entry.totalDebit)}</td>
                  <td className="px-4 py-3 text-right font-medium text-gray-700">{fmt(entry.totalCredit)}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                      {entry.status}
                    </span>
                  </td>
                </tr>
                {expanded === entry.id && entry.lines.map((line, i) => (
                  <tr key={i} className="bg-blue-50/40 text-xs border-t border-blue-100">
                    <td className="px-4 py-2" />
                    <td colSpan={3} className="px-8 py-2 text-gray-600 font-medium">{line.account}</td>
                    <td className="px-4 py-2 text-right text-gray-700">{fmt(line.debit)}</td>
                    <td className="px-4 py-2 text-right text-gray-700">{fmt(line.credit)}</td>
                    <td className="px-4 py-2 text-gray-400 text-xs">
                      {line.gst > 0 ? `GST $${(line.gst/100).toFixed(2)}` : ""}
                    </td>
                  </tr>
                ))}
              </>
            ))}
            <tr className="bg-gray-50 border-t-2 border-gray-200 font-semibold text-sm">
              <td colSpan={4} className="px-4 py-3 text-gray-700">Totals</td>
              <td className="px-4 py-3 text-right text-gray-900">{fmt(totalDebits)}</td>
              <td className="px-4 py-3 text-right text-gray-900">{fmt(totalCredits)}</td>
              <td />
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
