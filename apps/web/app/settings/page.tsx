"use client";
import { useState } from "react";
import { Building2, CreditCard, Settings as SettingsIcon, Bell, Shield, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DemoBadge } from "@/components/DemoBadge";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-0.5">Manage your business and account preferences</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-blue-50">
              <Building2 size={20} className="text-blue-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-800">Business Details</h2>
              <p className="text-xs text-gray-500">Coastal Trades Pty Ltd</p>
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Business Name</span>
              <span className="text-gray-800 font-medium">Coastal Trades Pty Ltd</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">ABN</span>
              <span className="text-gray-800 font-medium">51 824 753 556</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">GST Registered</span>
              <span className="text-green-600 font-medium">Yes</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">GST Basis</span>
              <span className="text-gray-800">Cash</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Financial Year</span>
              <span className="text-gray-800">Jul – Jun</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-500">Timezone</span>
              <span className="text-gray-800">Australia/Sydney</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-green-50">
              <CreditCard size={20} className="text-green-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-800">Bank Feeds</h2>
              <p className="text-xs text-gray-500">Basiq connection</p>
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Provider</span>
              <span className="text-gray-800 font-medium">Basiq Open Banking</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Connected Banks</span>
              <span className="text-gray-800">ANZ</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Accounts Linked</span>
              <span className="text-gray-800">2 accounts</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Last Sync</span>
              <span className="text-gray-800">Today 09:14</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-500">Sync Frequency</span>
              <span className="text-gray-800">Every 4 hours</span>
            </div>
          </div>
          <Button variant="outline" size="sm" className="mt-4">
            Reconnect Bank
          </Button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-purple-50">
              <SettingsIcon size={20} className="text-purple-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-800">Ledger</h2>
              <p className="text-xs text-gray-500">formance Ledger</p>
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Provider</span>
              <span className="text-gray-800 font-medium">Formance Ledger</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Ledger Name</span>
              <span className="text-gray-800">smartgl</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Status</span>
              <span className="text-green-600 font-medium">Active</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-500">Journal Entries</span>
              <span className="text-gray-800">42 posted</span>
            </div>
          </div>
          <DemoBadge />
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-amber-50">
              <User size={20} className="text-amber-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-800">User Preferences</h2>
              <p className="text-xs text-gray-500">AI categorisation</p>
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Embedding Auto-Accept</span>
              <span className="text-gray-800">≥ 88% confidence</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">LLM Auto-Accept</span>
              <span className="text-gray-800">≥ 70% confidence</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">AI Model</span>
              <span className="text-gray-800">Claude Sonnet 4</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-500">Auto-Categorise on Import</span>
              <span className="text-green-600 font-medium">Enabled</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="font-semibold text-gray-700">Stage 2 Features</h2>
          <DemoBadge label="STAGE 2" />
        </div>
        <p className="text-sm text-gray-500">
          Additional settings coming in Stage 2: multi-user access, role-based permissions, custom GST rates, 
          bank feed scheduling, BAS agent reminders, and cross-tenant AI learning.
        </p>
      </div>
    </div>
  );
}