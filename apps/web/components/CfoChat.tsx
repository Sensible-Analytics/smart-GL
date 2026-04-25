"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { MessageSquare, Send, Loader2, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED_QUESTIONS = [
  "How did we do this month?",
  "What's our cash runway?",
  "Show me any anomalies",
  "What are our top expenses?",
  "Compare to industry peers",
];

const MOCK_RESPONSES: Record<string, string> = {
  "How did we do this month?": "March was a strong month. Revenue was $127,500, up 12.5% from February. After expenses of $89,200, you kept $38,300 in profit. That's 30% margin - nice work!",
  "What's our cash runway?": "You have $28,500 in the bank. At your current burn rate (~$2,970/day), you're looking at about 4 months before you need to raise more cash. Watch out - a BAS payment of ~$15,000 is due in 2 weeks.",
  "Show me any anomalies": "Found 3 issues to review:\n\n1. HIGH: Duplicate payment - $4,250 paid to same vendor twice\n2. MEDIUM: First payment to new vendor for $12,000 - verify this is legit\n3. LOW: 12 transactions over $500 missing receipts",
  "What are our top expenses?": "Top expenses in March:\n\n1. Wages: $9,200\n2. Materials: $8,950\n3. ATO: $3,100\n4. Subcontractors: $2,400\n5. Vehicle: $2,100\n\nMarketing was up 45% - was that a special campaign?",
  "Compare to industry peers": "You're at the 48th percentile vs similar businesses. Your gross margin (48.5%) is below the industry median (52%), but your net profit (12.1%) is above average (8.5%). Your operating costs are in line - 62% vs industry 58%.",
};

export function CfoChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your Smart CFO Assistant. Ask me about your finances - revenue, expenses, cash flow, or anything else.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (question?: string) => {
    const q = question || input;
    if (!q.trim()) return;

    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const qLower = q.toLowerCase();
      for (const [key, answer] of Object.entries(MOCK_RESPONSES)) {
        if (qLower.includes(key.toLowerCase().replace("?", ""))) {
          setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
          setLoading(false);
          return;
        }
      }
      const res = await fetch("/api/cfo/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      if (!res.ok) throw new Error("Failed to get response");

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-600" />
          Smart CFO
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0">
        <div className="flex-1 overflow-y-auto space-y-3 mb-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg ${
                m.role === "user"
                  ? "bg-blue-50 ml-8"
                  : "bg-gray-50 mr-8"
              }`}
            >
              <div className="text-sm whitespace-pre-wrap">{m.content}</div>
            </div>
          ))}
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-600 text-sm">
              {error}
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-2 mb-3">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => handleSubmit(q)}
              className="text-xs px-2 py-1 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="Ask about your finances..."
            className="flex-1 px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <Button
            onClick={() => handleSubmit()}
            disabled={loading || !input.trim()}
            size="sm"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}