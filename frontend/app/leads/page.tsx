"use client";

import { useEffect, useState } from "react";
import { api, LeadSummary } from "@/lib/api";
import { LeadRow } from "@/components/ui";
import { useRequireAuth } from "@/lib/useRequireAuth";

const PRIORITIES = ["", "Hot Lead", "Warm Lead", "Medium Lead", "Low Priority"];

export default function LeadsPage() {
  const { ready } = useRequireAuth();
  const [leads, setLeads] = useState<LeadSummary[]>([]);
  const [q, setQ] = useState("");
  const [priority, setPriority] = useState("");
  const [status, setStatus] = useState("Qualified Lead");
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    const params: Record<string, string> = { sort: "score" };
    if (q) params.q = q;
    if (priority) params.priority = priority;
    if (status) params.status = status;
    api.leads(params).then(setLeads).finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!ready) return;
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, priority, status, ready]);

  if (!ready) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Leads</h1>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => api.download("csv", status || undefined)}>
            Export CSV
          </button>
          <button className="btn-ghost" onClick={() => api.download("excel", status || undefined)}>
            Export Excel
          </button>
        </div>
      </div>

      <div className="card flex flex-wrap items-center gap-3 p-4">
        <input
          className="input max-w-xs"
          placeholder="Search business name…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select className="input max-w-[12rem]" value={priority} onChange={(e) => setPriority(e.target.value)}>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p || "All priorities"}
            </option>
          ))}
        </select>
        <select className="input max-w-[12rem]" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="Qualified Lead">Qualified Lead</option>
          <option value="Website Found">Website Found</option>
        </select>
      </div>

      <div className="card">
        {loading ? (
          <p className="p-6 text-sm text-slate-400">Loading…</p>
        ) : leads.length === 0 ? (
          <p className="p-6 text-sm text-slate-400">No leads match your filters.</p>
        ) : (
          leads.map((l) => <LeadRow key={l.id} lead={l} />)
        )}
      </div>
    </div>
  );
}
