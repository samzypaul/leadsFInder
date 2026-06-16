"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, Lead } from "@/lib/api";
import { PriorityBadge, StatusBadge, ScoreRing } from "@/components/ui";
import { useRequireAuth } from "@/lib/useRequireAuth";

const OUTREACH_STATES = ["new", "contacted", "replied", "meeting", "won", "lost"];
const CHANNEL_ICON: Record<string, string> = {
  email: "✉️",
  whatsapp: "💬",
  instagram: "📷",
  facebook: "👍",
  linkedin: "in",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-6">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">{title}</h2>
      {children}
    </div>
  );
}

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { ready } = useRequireAuth();
  const [lead, setLead] = useState<Lead | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = () => api.lead(Number(id)).then(setLead).catch((e) => setErr(String(e)));
  useEffect(() => {
    if (ready) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, ready]);

  if (!ready) return null;
  if (err) return <div className="card p-6 text-red-600">{err}</div>;
  if (!lead) return <div className="text-slate-400">Loading lead…</div>;

  async function setOutreach(status: string) {
    setLead(await api.updateLead(Number(id), { outreach_status: status }));
  }
  async function reenrich() {
    setBusy(true);
    try {
      setLead(await api.reenrich(Number(id)));
    } finally {
      setBusy(false);
    }
  }
  async function regenOutreach() {
    setBusy(true);
    try {
      await api.generateOutreach(Number(id));
      await load();
    } finally {
      setBusy(false);
    }
  }
  async function del() {
    if (!confirm("Delete this lead permanently? (GDPR / TZ DPA erasure)")) return;
    await api.deleteLead(Number(id));
    router.push("/leads");
  }

  const contacts: [string, string | null][] = [
    ["Phone", lead.phone],
    ["WhatsApp", lead.whatsapp],
    ["Email", lead.email],
    ["Address", lead.address],
    ["City / Region", [lead.city, lead.region].filter(Boolean).join(", ") || null],
  ];
  const links: [string, string | null][] = [
    ["Instagram", lead.instagram_url],
    ["Facebook", lead.facebook_url],
    ["Google Business", lead.google_business_url],
    ["Website", lead.website_url],
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <ScoreRing score={lead.score} />
          <div>
            <h1 className="text-2xl font-bold">{lead.business_name}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
              <PriorityBadge priority={lead.priority} />
              <StatusBadge status={lead.status} />
              <span>{[lead.industry, lead.city].filter(Boolean).join(" • ")}</span>
              {lead.ai_generated && <span className="badge bg-violet-100 text-violet-700 border-violet-200">AI-generated</span>}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={reenrich} disabled={busy}>
            ↻ Re-enrich
          </button>
          <button className="btn-ghost text-red-600" onClick={del}>
            Delete
          </button>
        </div>
      </div>

      {/* Outreach status pipeline */}
      <div className="card flex flex-wrap items-center gap-2 p-4">
        <span className="mr-2 text-sm font-medium text-slate-500">Outreach:</span>
        {OUTREACH_STATES.map((s) => (
          <button
            key={s}
            onClick={() => setOutreach(s)}
            className={`badge capitalize ${
              lead.outreach_status === s
                ? "bg-brand text-white border-brand"
                : "bg-white text-slate-500 border-slate-200 hover:bg-slate-50"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Section title="AI business summary">
            <p className="text-slate-700">{lead.ai_summary || "—"}</p>
          </Section>

          <Section title="Why they need a website">
            <ul className="space-y-2">
              {lead.opportunity_analysis?.reasons?.map((r, i) => (
                <li key={i} className="flex gap-2 text-slate-700">
                  <span className="text-brand">✗</span> {r}
                </li>
              ))}
            </ul>
          </Section>

          {lead.marketing_strategy && (
            <Section title="Marketing strategy">
              <div className="grid gap-4 sm:grid-cols-3">
                {(["website", "ai", "marketing"] as const).map((k) => (
                  <div key={k}>
                    <h3 className="mb-2 font-medium capitalize text-slate-900">{k} opportunity</h3>
                    <ul className="space-y-1 text-sm text-slate-600">
                      {lead.marketing_strategy![k]?.map((x, i) => (
                        <li key={i}>• {x}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </Section>
          )}

          <Section title="Competitor analysis">
            <p className="mb-4 text-slate-700">{lead.competitor_comparison}</p>
            <div className="divide-y divide-slate-100">
              {lead.competitors.map((c) => (
                <div key={c.id} className="py-2">
                  <div className="font-medium">
                    {c.name}{" "}
                    {c.website_url && (
                      <a href={c.website_url} target="_blank" className="text-xs text-brand hover:underline">
                        {c.website_url}
                      </a>
                    )}
                  </div>
                  {c.key_services && <div className="text-sm text-slate-500">{c.key_services}</div>}
                </div>
              ))}
            </div>
          </Section>

          {lead.proposal && (
            <Section title="Proposal">
              <div className="space-y-4 text-sm">
                <div>
                  <h3 className="font-semibold text-slate-900">Executive summary</h3>
                  <p className="text-slate-600">{lead.proposal.executive_summary}</p>
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">Current situation</h3>
                  <p className="text-slate-600">{lead.proposal.current_situation}</p>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <h3 className="font-semibold text-slate-900">Recommended solution</h3>
                    <ul className="text-slate-600">
                      {lead.proposal.recommended_solution.map((x, i) => (
                        <li key={i}>• {x}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Expected benefits</h3>
                    <ul className="text-slate-600">
                      {lead.proposal.expected_benefits.map((x, i) => (
                        <li key={i}>• {x}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <div className="text-slate-600">
                  <span className="font-semibold text-slate-900">Timeline:</span>{" "}
                  {lead.proposal.estimated_timeline.website} ·{" "}
                  {lead.proposal.estimated_timeline.chatbot}
                </div>
                <div className="rounded-lg bg-brand/10 p-3 font-medium text-brand-dark">
                  {lead.proposal.call_to_action}
                </div>
              </div>
            </Section>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Section title="Contact">
            <dl className="space-y-2 text-sm">
              {contacts.map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2">
                  <dt className="text-slate-400">{k}</dt>
                  <dd className="text-right text-slate-700">{v || "—"}</dd>
                </div>
              ))}
            </dl>
          </Section>

          <Section title="Presence">
            <ul className="space-y-1 text-sm">
              {links.map(([k, v]) => (
                <li key={k} className="flex justify-between gap-2">
                  <span className="text-slate-400">{k}</span>
                  {v ? (
                    <a href={v} target="_blank" className="truncate text-brand hover:underline">
                      open ↗
                    </a>
                  ) : (
                    <span className="text-slate-300">none</span>
                  )}
                </li>
              ))}
            </ul>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs text-slate-500">
              <div>
                <div className="text-lg font-bold text-slate-900">{lead.followers ?? "—"}</div>
                followers
              </div>
              <div>
                <div className="text-lg font-bold text-slate-900">{lead.reviews_count ?? "—"}</div>
                reviews
              </div>
              <div>
                <div className="text-lg font-bold text-slate-900">{lead.rating ?? "—"}</div>
                rating
              </div>
            </div>
          </Section>

          {lead.score_breakdown && (
            <Section title={`Lead score · ${lead.score}`}>
              <div className="space-y-2">
                {Object.entries(lead.score_breakdown).map(([k, v]) => (
                  <div key={k}>
                    <div className="flex justify-between text-xs">
                      <span className="capitalize text-slate-500">{k}</span>
                      <span className="font-medium">{v}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-slate-100">
                      <div className="h-1.5 rounded-full bg-brand" style={{ width: `${Math.min(100, (v / 22) * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          <Section title="Outreach drafts">
            <div className="space-y-3">
              {lead.outreach_messages.map((m) => (
                <details key={m.id} className="rounded-lg border border-slate-200">
                  <summary className="cursor-pointer px-3 py-2 text-sm font-medium capitalize">
                    {CHANNEL_ICON[m.channel] ?? "•"} {m.channel}
                  </summary>
                  <div className="border-t border-slate-100 px-3 py-2 text-sm text-slate-600">
                    {m.subject && <div className="mb-1 font-medium text-slate-800">{m.subject}</div>}
                    <pre className="whitespace-pre-wrap font-sans">{m.body}</pre>
                  </div>
                </details>
              ))}
              <button className="btn-ghost w-full" onClick={regenOutreach} disabled={busy}>
                ↻ Regenerate all
              </button>
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}
