"use client";

import { useState } from "react";
import Link from "next/link";
import { api, Candidate, DiscoverResponse, DiscoverScanResult, DiscoveryFilters } from "@/lib/api";
import { useRequireAuth } from "@/lib/useRequireAuth";

const EXAMPLES = [
  "tour operators in Arusha without a website",
  "hotels in Zanzibar with over 10k followers",
  "restaurants in Dar es Salaam with no website",
  "salons and beauty businesses in Dar es Salaam",
];

const CATEGORIES = ["", "Tour Agency", "Restaurant", "Cafe", "Hotel", "Real Estate",
  "Beauty Salon", "Automotive", "Information Technology", "Healthcare", "Construction"];
const CITIES = ["", "Arusha", "Dar es Salaam", "Dodoma", "Mwanza", "Moshi", "Zanzibar City",
  "Mbeya", "Tanga", "Bagamoyo", "Iringa"];

function chip(label: string, value: unknown) {
  if (value === null || value === undefined || value === "" || (Array.isArray(value) && !value.length))
    return null;
  return (
    <span key={label} className="badge border-slate-200 bg-slate-100 text-slate-600">
      {label}: <span className="ml-1 font-semibold text-slate-800">{String(value)}</span>
    </span>
  );
}

export default function DiscoverPage() {
  const { ready } = useRequireAuth();
  const [query, setQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<DiscoveryFilters>({ only_without_website: true, limit: 10 });
  const [res, setRes] = useState<DiscoverResponse | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [scanRes, setScanRes] = useState<DiscoverScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (!ready) return null;

  function buildFilters(): DiscoveryFilters | undefined {
    const f: DiscoveryFilters = {};
    if (filters.category) f.category = filters.category;
    if (filters.city) f.city = filters.city;
    if (filters.min_followers) f.min_followers = Number(filters.min_followers);
    f.only_without_website = filters.only_without_website ?? true;
    f.limit = filters.limit ?? 10;
    return Object.keys(f).length ? f : undefined;
  }

  async function search() {
    setErr(null);
    setScanRes(null);
    setLoading(true);
    try {
      const body: { query?: string; filters?: DiscoveryFilters } = {};
      if (query.trim()) body.query = query.trim();
      const f = showFilters ? buildFilters() : undefined;
      if (f) body.filters = f;
      if (!body.query && !body.filters) {
        setErr("Type a search or set at least one filter.");
        return;
      }
      const r = await api.discover(body);
      setRes(r);
      setSelected(new Set(r.candidates.map((c) => c.business_name)));
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  function toggle(name: string) {
    const next = new Set(selected);
    next.has(name) ? next.delete(name) : next.add(name);
    setSelected(next);
  }

  async function scanSelected() {
    if (!res) return;
    const chosen = res.candidates.filter((c) => selected.has(c.business_name));
    if (!chosen.length) return;
    setScanning(true);
    setErr(null);
    try {
      const r = await api.discoverScan({ candidates: chosen, max_scans: chosen.length });
      setScanRes(r);
    } catch (e) {
      setErr(String(e));
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Discover businesses</h1>
        <p className="mt-1 text-sm text-slate-500">
          Describe what you&apos;re looking for in plain English — AI turns it into a targeted
          search. Then scan the matches to create qualified leads.
        </p>
      </div>

      {/* Search box */}
      <div className="card space-y-4 p-6">
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            className="input"
            placeholder="e.g. tour operators in Arusha without a website"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
          />
          <button className="btn-primary shrink-0" onClick={search} disabled={loading}>
            {loading ? "Searching…" : "🔍 Search"}
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setQuery(ex)}
              className="badge border-brand/20 bg-brand/5 text-brand-dark hover:bg-brand/10"
            >
              {ex}
            </button>
          ))}
        </div>

        <button
          className="text-sm text-slate-500 hover:text-slate-800"
          onClick={() => setShowFilters((s) => !s)}
        >
          {showFilters ? "▾ Hide" : "▸ Show"} advanced filters
        </button>

        {showFilters && (
          <div className="grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Category</span>
              <select
                className="input"
                value={filters.category ?? ""}
                onChange={(e) => setFilters({ ...filters, category: e.target.value })}
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c || "Any"}</option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">City</span>
              <select
                className="input"
                value={filters.city ?? ""}
                onChange={(e) => setFilters({ ...filters, city: e.target.value })}
              >
                {CITIES.map((c) => (
                  <option key={c} value={c}>{c || "Any"}</option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Min followers</span>
              <input
                type="number"
                className="input"
                value={filters.min_followers ?? ""}
                onChange={(e) =>
                  setFilters({ ...filters, min_followers: e.target.value ? Number(e.target.value) : null })
                }
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Limit</span>
              <input
                type="number"
                className="input"
                value={filters.limit ?? 10}
                onChange={(e) => setFilters({ ...filters, limit: Number(e.target.value) })}
              />
            </label>
            <label className="flex items-center gap-2 text-sm sm:col-span-2">
              <input
                type="checkbox"
                checked={filters.only_without_website ?? true}
                onChange={(e) => setFilters({ ...filters, only_without_website: e.target.checked })}
              />
              Only businesses likely without a website
            </label>
          </div>
        )}
      </div>

      {err && <div className="card p-4 text-sm text-red-600">{err}</div>}

      {/* Results */}
      {res && (
        <div className="card">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold">
                {res.count} match{res.count === 1 ? "" : "es"}
              </span>
              {res.query && (
                <span className={`badge ${res.ai_parsed ? "border-violet-200 bg-violet-100 text-violet-700" : "border-slate-200 bg-slate-100 text-slate-600"}`}>
                  {res.ai_parsed ? "AI-parsed" : "parsed"}
                </span>
              )}
              {chip("category", res.interpreted_filters.category)}
              {chip("city", res.interpreted_filters.city)}
              {chip("min followers", res.interpreted_filters.min_followers)}
              {res.interpreted_filters.only_without_website && chip("filter", "no website")}
            </div>
            <button
              className="btn-primary"
              onClick={scanSelected}
              disabled={scanning || selected.size === 0}
            >
              {scanning ? "Scanning…" : `Scan ${selected.size} selected →`}
            </button>
          </div>

          {res.candidates.length === 0 ? (
            <p className="p-6 text-sm text-slate-400">
              No matching businesses. Try a broader search or different filters.
            </p>
          ) : (
            res.candidates.map((c: Candidate) => (
              <label
                key={c.business_name}
                className="flex cursor-pointer items-center gap-4 border-b border-slate-100 px-5 py-3 last:border-0 hover:bg-slate-50"
              >
                <input
                  type="checkbox"
                  checked={selected.has(c.business_name)}
                  onChange={() => toggle(c.business_name)}
                />
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-slate-900">{c.business_name}</div>
                  <div className="text-xs text-slate-500">
                    {[c.category, c.city].filter(Boolean).join(" • ")}
                    {c.followers ? ` • ${c.followers.toLocaleString()} followers` : ""}
                  </div>
                </div>
                {c.likely_no_website && (
                  <span className="badge border-emerald-200 bg-emerald-100 text-emerald-700">
                    likely no website
                  </span>
                )}
                <span className="badge border-slate-200 bg-slate-100 text-slate-500">{c.source}</span>
              </label>
            ))
          )}
        </div>
      )}

      {/* Scan results */}
      {scanRes && (
        <div className="card p-6">
          <h2 className="mb-1 text-lg font-semibold">Scan complete</h2>
          <p className="mb-4 text-sm text-slate-500">
            Scanned {scanRes.scanned} · <span className="font-medium text-emerald-600">
              {scanRes.qualified_leads} qualified leads</span> · {scanRes.websites_found} already
            had websites
          </p>
          <div className="divide-y divide-slate-100">
            {scanRes.results.map((r) => (
              <div key={r.business_name} className="flex items-center justify-between py-2">
                <div>
                  <div className="font-medium">{r.business_name}</div>
                  <div className="text-xs text-slate-500">
                    <span className={r.verdict === "Qualified Lead" ? "text-emerald-600" : "text-slate-500"}>
                      {r.verdict}
                    </span>
                  </div>
                </div>
                {r.lead_id && (
                  <Link href={`/leads/${r.lead_id}`} className="text-sm text-brand hover:underline">
                    View lead →
                  </Link>
                )}
              </div>
            ))}
          </div>
          <Link href="/leads" className="btn-ghost mt-4 inline-flex">
            Go to all leads →
          </Link>
        </div>
      )}
    </div>
  );
}
