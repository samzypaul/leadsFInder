"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ScanResult } from "@/lib/api";
import { useRequireAuth } from "@/lib/useRequireAuth";

const STAGE_LABEL: Record<string, string> = {
  instagram: "1 · Instagram analysis",
  facebook: "2 · Facebook verification",
  google_business: "3 · Google Business Profile",
  deep_search: "4 · Deep web search",
  lead_created: "5 · Qualified lead created",
  verdict: "Verdict",
};

export default function ScanPage() {
  const router = useRouter();
  const { ready } = useRequireAuth();
  const [instagram, setInstagram] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function runScan(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setResult(null);
    setLoading(true);
    try {
      const r = await api.scan(
        { instagram_url: instagram || undefined, business_name: name || undefined },
        true,
      );
      setResult(r);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  if (!ready) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">New scan</h1>
      <p className="text-sm text-slate-500">
        Enter an Instagram profile URL (recommended) or a business name. The workflow runs five
        verification steps before deciding the business has no website.
      </p>

      <form onSubmit={runScan} className="card space-y-4 p-6">
        <div>
          <label className="mb-1 block text-sm font-medium">Instagram profile URL</label>
          <input
            className="input"
            placeholder="https://www.instagram.com/serengetidreamsafaris/"
            value={instagram}
            onChange={(e) => setInstagram(e.target.value)}
          />
        </div>
        <div className="text-center text-xs text-slate-400">— or —</div>
        <div>
          <label className="mb-1 block text-sm font-medium">Business name</label>
          <input
            className="input"
            placeholder="Serengeti Dreams Safaris"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <button className="btn-primary w-full" disabled={loading || (!instagram && !name)}>
          {loading ? "Scanning…" : "Run scan"}
        </button>
        <p className="text-center text-xs text-slate-400">
          Demo fixtures available: <code>serengetidreamsafaris</code>,{" "}
          <code>mamandogokitchen</code>, <code>zanzibarpearlproperties</code>,{" "}
          <code>kilizotech</code>
        </p>
      </form>

      {err && <div className="card p-4 text-sm text-red-600">{err}</div>}

      {result && (
        <div className="card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Verdict:{" "}
              <span
                className={
                  result.verdict === "Qualified Lead" ? "text-emerald-600" : "text-slate-500"
                }
              >
                {result.verdict}
              </span>
            </h2>
            {result.lead_id && (
              <button className="btn-primary" onClick={() => router.push(`/leads/${result.lead_id}`)}>
                View lead →
              </button>
            )}
          </div>

          <ol className="space-y-3">
            {result.steps.map((s, i) => (
              <li key={i} className="flex items-start gap-3">
                <span
                  className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-bold text-white ${
                    s.found_website ? "bg-slate-400" : "bg-brand"
                  }`}
                >
                  {s.found_website ? "✓" : "•"}
                </span>
                <div>
                  <div className="text-sm font-medium">
                    {STAGE_LABEL[s.stage] ?? s.stage}
                  </div>
                  <div className="text-sm text-slate-500">{s.detail}</div>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
