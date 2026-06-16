"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ClientAnalytics, LeadSummary } from "@/lib/api";
import { StatCard } from "@/components/ui";
import { useRequireAuth } from "@/lib/useRequireAuth";

export default function ClientsPage() {
  const { ready } = useRequireAuth();
  const [a, setA] = useState<ClientAnalytics | null>(null);
  const [clients, setClients] = useState<LeadSummary[]>([]);

  useEffect(() => {
    if (!ready) return;
    api.clientAnalytics().then(setA);
    api.leads({ relationship: "client", sort: "created_at" }).then(setClients);
  }, [ready]);

  if (!ready) return null;
  if (!a) return <div className="text-slate-400">Loading clients…</div>;

  const cur = a.currency;
  const money = (n: number) => `${cur} ${(n || 0).toLocaleString()}`;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Clients</h1>
        <p className="mt-1 text-sm text-slate-500">
          Leads you&apos;ve won. Open any client to edit details, financials, and documents.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Clients (won)" value={a.clients} accent="text-emerald-600" />
        <StatCard label="Win rate" value={`${Math.round(a.win_rate * 100)}%`} accent="text-slate-900" />
        <StatCard label={`Revenue (${cur})`} value={a.total_revenue.toLocaleString()} accent="text-emerald-600" />
        <StatCard
          label={`${a.total_profit >= 0 ? "Profit" : "Loss"} (${cur})`}
          value={Math.abs(a.total_profit).toLocaleString()}
          accent={a.total_profit >= 0 ? "text-emerald-600" : "text-red-600"}
        />
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={`Avg deal (${cur})`} value={a.avg_deal_size.toLocaleString()} />
        <StatCard label={`Deposits (${cur})`} value={a.total_deposits.toLocaleString()} />
        <StatCard label={`Outstanding (${cur})`} value={a.outstanding.toLocaleString()} accent="text-orange-600" />
        <StatCard label="Lost deals" value={a.lost} accent="text-slate-500" />
      </div>

      <div className="card">
        <div className="border-b border-slate-100 px-5 py-3 font-semibold">Client list</div>
        {clients.length === 0 ? (
          <p className="p-6 text-sm text-slate-400">
            No clients yet. Mark a lead&apos;s deal as <span className="font-medium">Won</span> and it
            shows up here.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            <div className="grid grid-cols-12 px-5 py-2 text-xs font-medium uppercase tracking-wide text-slate-400">
              <div className="col-span-6">Business</div>
              <div className="col-span-3 text-right">Revenue</div>
              <div className="col-span-3 text-right">Profit</div>
            </div>
            {clients.map((c) => (
              <Link
                key={c.id}
                href={`/leads/${c.id}`}
                className="grid grid-cols-12 items-center px-5 py-3 text-sm hover:bg-slate-50"
              >
                <div className="col-span-6 min-w-0">
                  <div className="truncate font-medium text-slate-900">{c.business_name}</div>
                  <div className="truncate text-xs text-slate-500">
                    {[c.category, c.city].filter(Boolean).join(" • ")}
                  </div>
                </div>
                <div className="col-span-3 text-right text-slate-700">{money(c.deal_revenue ?? 0)}</div>
                <div className={`col-span-3 text-right font-medium ${(c.deal_profit ?? 0) >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                  {money(c.deal_profit ?? 0)}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {a.top_clients.length > 0 && (
        <div className="card p-5">
          <h2 className="mb-3 font-semibold">Top clients by revenue</h2>
          <div className="space-y-2">
            {a.top_clients.map((t) => {
              const max = a.top_clients[0].revenue || 1;
              return (
                <div key={t.id}>
                  <div className="mb-1 flex justify-between text-sm">
                    <Link href={`/leads/${t.id}`} className="text-slate-700 hover:text-brand">{t.business_name}</Link>
                    <span className="font-medium">{money(t.revenue)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${(t.revenue / max) * 100}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
