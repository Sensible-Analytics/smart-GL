"use client";
import { useState, Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { X, Building2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AddBankModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AUSTRALIAN_BANKS = [
  { code: "ANZ", name: "ANZ" },
  { code: "CBA", name: "Commonwealth Bank" },
  { code: "NAB", name: "NAB" },
  { code: "Westpac", name: "Westpac" },
  { code: "BoQ", name: "Bank of Queensland" },
  { code: "Suncorp", name: "Suncorp Bank" },
  { code: "ING", name: "ING" },
  { code: "Macquarie", name: "Macquarie" },
  { code: "Bendigo", name: "Bendigo Bank" },
  { code: "AMP", name: "AMP Bank" },
];

export function AddBankModal({ isOpen, onClose }: AddBankModalProps) {
  const [step, setStep] = useState<"select" | "details" | "success">("select");
  const [selectedBank, setSelectedBank] = useState("");
  const [form, setForm] = useState({
    accountName: "",
    bsb: "",
    accountNumber: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.accountName.trim()) e.accountName = "Account name is required";
    if (!form.bsb.trim()) e.bsb = "BSB is required";
    else if (!/^\d{6}$/.test(form.bsb.replace(/[-\s]/g, ""))) e.bsb = "Enter 6 digits (e.g., 012-345)";
    if (!form.accountNumber.trim()) e.accountNumber = "Account number is required";
    else if (!/^\d{6,10}$/.test(form.accountNumber.replace(/[-\s]/g, ""))) e.accountNumber = "Enter 6-10 digits";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    setStep("success");
  };

  const handleClose = () => {
    setStep("select");
    setSelectedBank("");
    setForm({ accountName: "", bsb: "", accountNumber: "" });
    setErrors({});
    onClose();
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/30" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-xl bg-white p-6 shadow-xl transition-all">
                <div className="flex items-center justify-between mb-5">
                  <Dialog.Title className="text-lg font-semibold text-gray-900">
                    Add Bank Account
                  </Dialog.Title>
                  <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
                    <X size={20} />
                  </button>
                </div>

                {step === "select" && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select your bank
                      </label>
                      <select
                        value={selectedBank}
                        onChange={(e) => setSelectedBank(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Choose a bank...</option>
                        {AUSTRALIAN_BANKS.map((b) => (
                          <option key={b.code} value={b.code}>
                            {b.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <Button
                      onClick={() => selectedBank && setStep("details")}
                      disabled={!selectedBank}
                      className="w-full"
                    >
                      Continue
                    </Button>
                  </div>
                )}

                {step === "details" && (
                  <div className="space-y-4">
                    <div className="bg-blue-50 rounded-lg p-3 flex items-center gap-2 text-sm text-blue-700">
                      <Building2 size={16} />
                      Connected to: {AUSTRALIAN_BANKS.find((b) => b.code === selectedBank)?.name}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Account Nickname
                      </label>
                      <input
                        type="text"
                        value={form.accountName}
                        onChange={(e) => setForm({ ...form, accountName: e.target.value })}
                        placeholder="e.g., Business Savings"
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {errors.accountName && (
                        <p className="text-red-500 text-xs mt-1">{errors.accountName}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        BSB Number
                      </label>
                      <input
                        type="text"
                        value={form.bsb}
                        onChange={(e) => setForm({ ...form, bsb: e.target.value })}
                        placeholder="e.g., 012-345"
                        maxLength={7}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {errors.bsb && (
                        <p className="text-red-500 text-xs mt-1">{errors.bsb}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Account Number
                      </label>
                      <input
                        type="text"
                        value={form.accountNumber}
                        onChange={(e) => setForm({ ...form, accountNumber: e.target.value })}
                        placeholder="e.g., 12345678"
                        maxLength={10}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {errors.accountNumber && (
                        <p className="text-red-500 text-xs mt-1">{errors.accountNumber}</p>
                      )}
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button variant="outline" onClick={() => setStep("select")} className="flex-1">
                        Back
                      </Button>
                      <Button onClick={handleSubmit} className="flex-1">
                        Connect Account
                      </Button>
                    </div>
                  </div>
                )}

                {step === "success" && (
                  <div className="text-center py-4">
                    <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                      <CheckCircle2 size={32} className="text-green-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Account Connected!
                    </h3>
                    <p className="text-sm text-gray-500 mb-6">
                      Your {form.accountName} account has been linked successfully.
                    </p>
                    <Button onClick={handleClose} className="w-full">
                      Done
                    </Button>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}