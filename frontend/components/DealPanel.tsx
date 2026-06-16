"use client";

import { useState } from "react";
import { api, Deal, DEAL_STAGES } from "@/lib/api";

const STAGE_LABEL: Record<string, string> = {
  prospect: "Prospect",
  contacted: "Contacted",
  proposal_sent: "Proposal sent",
  negotiating: "Negotiating",
  won: "Won",
  lost: "Lost",
};

function money(n: number, currency: string) {
  return `${currency} ${(n || 0).toLocaleString()}`;
}

export function DealPanel({ leadId, deal: initial }: { leadId: number; deal: Deal | null }) {
  const [deal, setDeal] = useState<Deal | null>(initial);
  const [form, setForm] = useState({
    currency: initial?.currency ?? "TZS",
    revenue: initial?.revenue ?? 0,
    cost: initial?.cost ?? 0,
    deposit: initial?.deposit ?? 0,
    notes: initial?.notes ?? "",
  });
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  const stage = deal?.stage ?? "prospect";
  const profit = (Number(form.revenue) || 0) - (Number(form.cost) || 0);
  const outstanding = (Number(form.revenue) || 0) - (Number(form.deposit) || 0);

  async function setStage(s: string) {
    setBusy(true);
    try {
      setDeal(await api.updateDeal(leadId, { stage: s }));
    } finally {
      setBusy(false);
    }
  }

  async function saveFinancials() {
    setBusy(true);
    setSaved(false);
    try {
      const d = await api.updateDeal(leadId, {
        currency: form.currency,
        revenue: Number(form.revenue) || 0,
        cost: Number(form.cost) || 0,
        deposit: Number(form.deposit) || 0,
        notes: form.notes,
      });
      setDeal(d);
      setSaved(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Funnel stages */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs text-slate-500">Funnel stage</span>
          {deal?.outreach_made && (
            <span className="badge border-emerald-200 bg-emerald-100 text-emerald-700">outreach made</span>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {DEAL_STAGES.map((s) => (
            <button
              key={s}
              onClick={() => setStage(s)}
              disabled={busy}
              className={`badge capitalize ${
                stage === s
                  ? s === "won"
                    ? "border-emerald-300 bg-emerald-600 text-white"
                    : s === "lost"
                    ? "border-red-300 bg-red-600 text-white"
                    : "border-brand bg-brand text-white"
                  : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"
              }`}
            >
              {STAGE_LABEL[s]}
            </button>
          ))}
        </div>
      </div>

      {/* Financials */}
      <div className="grid grid-cols-2 gap-3">
        <label className="text-sm">
          <span className="mb-1 block text-slate-500">Currency</span>
          <input className="input" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-500">Revenue (earned)</span>
          <input className="input" type="number" value={form.revenue} onChange={(e) => setForm({ ...form, revenue: Number(e.target.value) })} />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-500">Cost (spent)</span>
          <input className="input" type="number" value={form.cost} onChange={(e) => setForm({ ...form, cost: Number(e.target.value) })} />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-500">Deposit / advance</span>
          <input className="input" type="number" value={form.deposit} onChange={(e) => setForm({ ...form, deposit: Number(e.target.value) })} />
        </label>
        <label className="col-span-2 text-sm">
          <span className="mb-1 block text-slate-500">Notes</span>
          <textarea className="input min-h-[60px]" value={form.notes ?? ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </label>
      </div>

      {/* Profit / loss summary */}
      <div className="grid grid-cols-2 gap-3 rounded-lg bg-slate-50 p-3 text-sm">
        <div>
          <div className="text-slate-500">Profit / loss</div>
          <div className={`text-lg font-bold ${profit >= 0 ? "text-emerald-600" : "text-red-600"}`}>
            {profit >= 0 ? "" : "−"}{money(Math.abs(profit), form.currency)}
            <span className="ml-1 text-xs font-normal text-slate-400">{profit >= 0 ? "profit" : "loss"}</span>
          </div>
        </div>
        <div>
          <div className="text-slate-500">Outstanding</div>
          <div className="text-lg font-bold text-slate-800">{money(outstanding, form.currency)}</div>
          <div className="text-xs text-slate-400">after {money(Number(form.deposit) || 0, form.currency)} deposit</div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="btn-primary" onClick={saveFinancials} disabled={busy}>Save financials</button>
        {saved && <span className="text-sm text-emerald-600">Saved ✓</span>}
      </div>
    </div>
  );
}
