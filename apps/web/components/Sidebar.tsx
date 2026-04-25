"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, ArrowLeftRight, BookOpen,
  BarChart2, Landmark, List, Settings, Brain, Wallet
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/journal", label: "Journal", icon: BookOpen },
  { href: "/reports", label: "Reports", icon: BarChart2 },
  { href: "/bank-feeds", label: "Bank Feeds", icon: Landmark },
  { href: "/accounts", label: "Chart of Accounts", icon: List },
  { href: "/cfo", label: "CFO Dashboard", icon: Wallet },
  { href: "/ai-insights", label: "AI Insights", icon: Brain },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col shrink-0">
      <div className="px-6 py-5 border-b border-gray-700">
        <div className="text-xl font-bold text-white">Smart GL</div>
        <div className="text-xs text-gray-400 mt-0.5">Coastal Trades Pty Ltd</div>
        <div className="text-xs text-gray-500">ABN 51 824 753 556</div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              path === href
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            )}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="px-6 py-4 border-t border-gray-700 text-xs text-gray-500">
        FY 2024–25 · AUD
      </div>
    </aside>
  );
}