import Link from "next/link";
import { priorityColor } from "@/lib/api";

export function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number | string;
  accent?: string;
}) {
  return (
    <div className="card p-5">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-bold ${accent ?? "text-slate-900"}`}>{value}</div>
    </div>
  );
}

export function PriorityBadge({ priority }: { priority: string | null }) {
  if (!priority) return <span className="text-slate-400">—</span>;
  return <span className={`badge ${priorityColor(priority)}`}>{priority}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "Qualified Lead"
      ? "bg-emerald-100 text-emerald-700 border-emerald-200"
      : status === "Website Found"
      ? "bg-slate-100 text-slate-600 border-slate-200"
      : "bg-blue-100 text-blue-700 border-blue-200";
  return <span className={`badge ${cls}`}>{status}</span>;
}

export function ScoreRing({ score }: { score: number | null }) {
  const s = score ?? 0;
  const color = s >= 80 ? "#dc2626" : s >= 60 ? "#ea580c" : s >= 40 ? "#ca8a04" : "#94a3b8";
  return (
    <div
      className="grid h-12 w-12 place-items-center rounded-full text-sm font-bold text-white"
      style={{ background: `conic-gradient(${color} ${s * 3.6}deg, #e2e8f0 0deg)` }}
    >
      <span className="grid h-9 w-9 place-items-center rounded-full bg-white" style={{ color }}>
        {score ?? "—"}
      </span>
    </div>
  );
}

export function LeadRow({ lead }: { lead: import("@/lib/api").LeadSummary }) {
  return (
    <Link
      href={`/leads/${lead.id}`}
      className="flex items-center gap-4 border-b border-slate-100 px-4 py-3 last:border-0 hover:bg-slate-50"
    >
      <ScoreRing score={lead.score} />
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium text-slate-900">{lead.business_name}</div>
        <div className="truncate text-xs text-slate-500">
          {[lead.category, lead.city].filter(Boolean).join(" • ") || "—"}
        </div>
      </div>
      <div className="hidden sm:block">
        <PriorityBadge priority={lead.priority} />
      </div>
      <div className="hidden md:block">
        <StatusBadge status={lead.status} />
      </div>
    </Link>
  );
}
