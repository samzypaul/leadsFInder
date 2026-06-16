// Typed API client for the LeadHunter TZ backend.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

const TOKEN_KEY = "lh_token";

export const auth = {
  get: (): string | null =>
    typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY),
  set: (t: string) => window.localStorage.setItem(TOKEN_KEY, t),
  clear: () => window.localStorage.removeItem(TOKEN_KEY),
  isAuthed: (): boolean => typeof window !== "undefined" && !!window.localStorage.getItem(TOKEN_KEY),
};

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_admin: boolean;
}

export interface DiscoveryFilters {
  industry?: string | null;
  city?: string | null;
  region?: string | null;
  category?: string | null;
  keywords?: string[];
  min_followers?: number | null;
  only_without_website?: boolean;
  limit?: number;
}

export interface Candidate {
  business_name: string;
  instagram_url: string | null;
  category: string | null;
  city: string | null;
  region: string | null;
  followers: number | null;
  source: string;
  likely_no_website: boolean | null;
}

export interface DiscoverResponse {
  interpreted_filters: DiscoveryFilters;
  query: string | null;
  ai_parsed: boolean;
  count: number;
  candidates: Candidate[];
}

export interface DiscoverScanResult {
  scanned: number;
  qualified_leads: number;
  websites_found: number;
  results: { business_name: string; verdict: string; lead_id: number | null; final_stage: string | null }[];
}

export interface LeadSummary {
  id: number;
  business_name: string;
  category: string | null;
  city: string | null;
  status: string;
  outreach_status: string;
  score: number | null;
  priority: string | null;
  phone: string | null;
  email: string | null;
  created_at: string;
}

export interface Competitor {
  id: number;
  name: string;
  website_url: string | null;
  key_services: string | null;
}

export interface OutreachMessage {
  id: number;
  channel: string;
  subject: string | null;
  body: string;
  created_at: string;
}

export interface Lead extends LeadSummary {
  username: string | null;
  target_service: string | null;
  industry: string | null;
  description: string | null;
  instagram_url: string | null;
  facebook_url: string | null;
  google_business_url: string | null;
  website_url: string | null;
  whatsapp: string | null;
  address: string | null;
  region: string | null;
  country: string | null;
  followers: number | null;
  posts_count: number | null;
  reviews_count: number | null;
  rating: number | null;
  score_breakdown: Record<string, number> | null;
  ai_summary: string | null;
  opportunity_analysis: { reasons: string[] } | null;
  marketing_strategy: { website: string[]; ai: string[]; marketing: string[] } | null;
  proposal: ProposalDoc | null;
  competitor_comparison: string | null;
  ai_generated: boolean;
  updated_at: string;
  competitors: Competitor[];
  outreach_messages: OutreachMessage[];
}

export interface ProposalDoc {
  executive_summary: string;
  current_situation: string;
  recommended_solution: string[];
  expected_benefits: string[];
  estimated_timeline: Record<string, string>;
  call_to_action: string;
}

export interface DashboardStats {
  total_scanned: number;
  with_website: number;
  without_website: number;
  hot_leads: number;
  warm_leads: number;
  medium_leads: number;
  low_leads: number;
  pipeline: Record<string, number>;
  by_priority: Record<string, number>;
  recent_leads: LeadSummary[];
}

export interface ScanStep {
  stage: string;
  found_website: boolean;
  detail: string;
  data: Record<string, unknown> | null;
}

export interface ScanResult {
  job_id: number;
  verdict: string;
  final_stage: string | null;
  website_url: string | null;
  steps: ScanStep[];
  lead_id: number | null;
}

function authHeaders(): Record<string, string> {
  const t = auth.get();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (res.status === 401 && path !== "/auth/login") {
    // Token missing/expired — bounce to login.
    auth.clear();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** Fetch a binary export with the auth header and trigger a browser download. */
async function downloadExport(fmt: "csv" | "excel", status?: string): Promise<void> {
  const url = `${API_BASE}/export/${fmt}${status ? `?status=${encodeURIComponent(status)}` : ""}`;
  const res = await fetch(url, { headers: authHeaders(), cache: "no-store" });
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = fmt === "csv" ? "leads.csv" : "leads.xlsx";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}

export const api = {
  health: () => req<{ status: string; ai_enabled: boolean; scraper_mode: string }>("/health"),

  // ── auth ──
  login: async (email: string, password: string) => {
    const r = await req<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    auth.set(r.access_token);
    return r.user;
  },
  signup: async (email: string, password: string, fullName?: string) => {
    const r = await req<{ access_token: string; user: User }>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName || null }),
    });
    auth.set(r.access_token);
    return r.user;
  },
  me: () => req<User>("/auth/me"),
  logout: () => {
    auth.clear();
    if (typeof window !== "undefined") window.location.href = "/login";
  },

  // ── discovery ──
  discover: (body: { query?: string; filters?: DiscoveryFilters; service?: string }) =>
    req<DiscoverResponse>("/discover", { method: "POST", body: JSON.stringify(body) }),
  discoverScan: (body: { query?: string; filters?: DiscoveryFilters; candidates?: Candidate[]; max_scans?: number; service?: string }) =>
    req<DiscoverScanResult>("/discover/scan", { method: "POST", body: JSON.stringify(body) }),

  stats: () => req<DashboardStats>("/dashboard/stats"),
  leads: (params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return req<LeadSummary[]>(`/leads${qs ? `?${qs}` : ""}`);
  },
  lead: (id: number) => req<Lead>(`/leads/${id}`),
  updateLead: (id: number, body: Record<string, unknown>) =>
    req<Lead>(`/leads/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  reenrich: (id: number) => req<Lead>(`/leads/${id}/enrich`, { method: "POST" }),
  deleteLead: (id: number) => req<void>(`/leads/${id}`, { method: "DELETE" }),
  scan: (body: { instagram_url?: string; business_name?: string; service?: string }, wait = true) =>
    req<ScanResult>(`/scan?wait=${wait}`, { method: "POST", body: JSON.stringify(body) }),
  scanStatus: (jobId: number) => req<ScanResult>(`/scan/${jobId}`),
  generateOutreach: (id: number, channels?: string[]) =>
    req<OutreachMessage[]>(`/leads/${id}/outreach/generate`, {
      method: "POST",
      body: JSON.stringify({ channels: channels ?? null }),
    }),
  download: downloadExport,
};

export function priorityColor(priority: string | null): string {
  switch (priority) {
    case "Hot Lead":
      return "bg-red-100 text-red-700 border-red-200";
    case "Warm Lead":
      return "bg-orange-100 text-orange-700 border-orange-200";
    case "Medium Lead":
      return "bg-yellow-100 text-yellow-700 border-yellow-200";
    default:
      return "bg-slate-100 text-slate-600 border-slate-200";
  }
}
