"use client";

import { useState, useEffect } from "react";
import { CfoChat } from "@/components/CfoChat";
import {
  Card, CardContent, CardHeader, CardTitle
} from "@/components/ui/card";
import {
  TrendingUp, TrendingDown, AlertTriangle,
  DollarSign, FileText, PieChart, Activity
} from "lucide-react";

interface Anomaly {
  id: string;
  type: string;
  description: string;
  amount: number;
  date: string;
}

interface Briefing {
  id: string;
  period: string;
  summary: string;
  created_at: string;
}

interface CashFlow {
  period: string;
  inflow: number;
  outflow: number;
  net: number;
}

export default function CfoDashboardPage() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [briefings, setBriefings] = useState<Briefing[]>([]);
  const [cashFlow, setCashFlow] = useState<CashFlow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/cfo/anomalies").then(r => r.json()).then(d => d.anomalies || []).catch(() => []),
      fetch("/api/cfo/briefing").then(r => r.json()).then(d => Array.isArray(d) ? d : [d]).catch(() => []),
      fetch("/api/cfo/cash-flow").then(r => r.json()).catch(() => ({})),
    ]).then(([a, b, c]) => {
      setAnomalies(a || []);
      setBriefings(b || []);
      const cf = c?.current ? [
        { period: c.current.month_year, inflow: c.current.inflows_cents/100, outflow: c.current.outflows_cents/100, net: (c.current.closing_cents - c.current.opening_cents)/100 }
      ] : [];
      setCashFlow(cf);
    }).catch(console.error)
    .finally(() => setLoading(false));
  }, []);

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">CFO Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            AI-powered financial insights and analysis
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              Cash Flow Forecast
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-32 flex items-center justify-center text-muted-foreground">
                Loading...
              </div>
            ) : cashFlow.length > 0 ? (
              <div className="space-y-3">
                {cashFlow.slice(0, 6).map((item) => (
                  <div key={item.period} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{item.period}</span>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-green-600">
                        +${item.inflow.toLocaleString()}
                      </span>
                      <span className="text-red-600">
                        -${item.outflow.toLocaleString()}
                      </span>
                      <span className={`font-medium ${
                        item.net >= 0 ? "text-green-600" : "text-red-600"
                      }`}>
                        {item.net >= 0 ? "+" : ""}
                        ${item.net.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-muted-foreground">
                No cash flow data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              Anomalies
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-muted-foreground">Loading...</div>
            ) : anomalies.length > 0 ? (
              <div className="space-y-3">
                {anomalies.slice(0, 5).map((a: any) => (
                  <div key={a.id} className="p-3 bg-amber-50 rounded-lg">
                    <div className="text-sm font-medium">{a.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {a.description}
                    </div>
                    <div className="text-xs font-medium mt-2 flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded ${
                        a.severity === "high" ? "bg-red-100 text-red-700" :
                        a.severity === "medium" ? "bg-orange-100 text-orange-700" :
                        "bg-gray-100 text-gray-600"
                      }`}>
                        {a.severity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-muted-foreground text-sm">
                No anomalies detected
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 h-[500px]">
          <CardContent className="p-4 h-full">
            <CfoChat />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              Monthly Briefings
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-muted-foreground">Loading...</div>
            ) : briefings.length > 0 ? (
              <div className="space-y-3">
                {briefings.slice(0, 5).map((b) => (
                  <div key={b.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm font-medium">{b.period}</div>
                    <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {b.summary}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-muted-foreground text-sm">
                No briefings available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}