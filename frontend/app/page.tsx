"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, DashboardStats } from "@/lib/api";
import { StatCard, LeadRow } from "@/components/ui";
import { useRequireAuth } from "@/lib/useRequireAuth";

export default function DashboardPage() {
  const { ready } = useRequireAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (ready) api.stats().then(setStats).catch((e) => setErr(String(e)));
  }, [ready]);

  if (!ready) return null;

  if (err)
    return (
      <div className="card p-6 text-sm text-red-600">
        Could not reach the API at <code>{process.env.NEXT_PUBLIC_API_BASE}</code>. Is the
        backend running? <br />
        <span className="text-slate-500">{err}</span>
      </div>
    );

  if (!stats) return <div className="text-slate-400">Loading dashboard…</div>;

  const pipeline = Object.entries(stats.pipeline);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Link href="/scan" className="btn-primary">
          + New Scan
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <StatCard label="Businesses scanned" value={stats.total_scanned} />
        <StatCard label="With website" value={stats.with_website} accent="text-slate-500" />
        <StatCard label="Without website" value={stats.without_website} accent="text-emerald-600" />
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Lead quality
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="🔥 Hot" value={stats.hot_leads} accent="text-red-600" />
          <StatCard label="🌤 Warm" value={stats.warm_leads} accent="text-orange-600" />
          <StatCard label="◐ Medium" value={stats.medium_leads} accent="text-yellow-600" />
          <StatCard label="○ Low" value={stats.low_leads} accent="text-slate-500" />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h2 className="font-semibold">Recent leads</h2>
            <Link href="/leads" className="text-sm text-brand hover:underline">
              View all →
            </Link>
          </div>
          {stats.recent_leads.length === 0 ? (
            <p className="p-6 text-sm text-slate-400">No leads yet. Run a scan to get started.</p>
          ) : (
            stats.recent_leads.map((l) => <LeadRow key={l.id} lead={l} />)
          )}
        </div>

        <div className="card p-5">
          <h2 className="mb-4 font-semibold">Outreach pipeline</h2>
          <div className="space-y-3">
            {pipeline.length === 0 && <p className="text-sm text-slate-400">No data</p>}
            {pipeline.map(([stage, count]) => {
              const total = pipeline.reduce((a, [, c]) => a + c, 0) || 1;
              return (
                <div key={stage}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="capitalize text-slate-600">{stage}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div
                      className="h-2 rounded-full bg-brand"
                      style={{ width: `${(count / total) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
