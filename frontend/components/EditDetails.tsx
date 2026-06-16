"use client";

import { useState } from "react";
import { api, Lead } from "@/lib/api";

const FIELDS: { key: keyof Lead; label: string; full?: boolean }[] = [
  { key: "business_name", label: "Business name" },
  { key: "industry", label: "Industry / niche" },
  { key: "email", label: "Email" },
  { key: "phone", label: "Phone" },
  { key: "whatsapp", label: "WhatsApp" },
  { key: "website_url", label: "Website" },
  { key: "city", label: "City" },
  { key: "region", label: "Region" },
  { key: "address", label: "Address", full: true },
  { key: "description", label: "Description", full: true },
];

export function EditDetails({ lead, onSaved }: { lead: Lead; onSaved: (l: Lead) => void }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  function start() {
    const init: Record<string, string> = {};
    for (const f of FIELDS) init[f.key as string] = (lead[f.key] as string) ?? "";
    setForm(init);
    setEditing(true);
  }

  async function save() {
    setBusy(true);
    try {
      const updated = await api.updateLead(lead.id, form);
      onSaved(updated);
      setEditing(false);
    } finally {
      setBusy(false);
    }
  }

  if (!editing) {
    return (
      <button className="btn-ghost text-sm" onClick={start}>
        ✎ Edit details
      </button>
    );
  }

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        {FIELDS.map((f) => (
          <label key={f.key as string} className={`text-sm ${f.full ? "sm:col-span-2" : ""}`}>
            <span className="mb-1 block text-slate-500">{f.label}</span>
            <input
              className="input"
              value={form[f.key as string] ?? ""}
              onChange={(e) => setForm({ ...form, [f.key as string]: e.target.value })}
            />
          </label>
        ))}
      </div>
      <div className="flex gap-2">
        <button className="btn-primary" onClick={save} disabled={busy}>Save</button>
        <button className="btn-ghost" onClick={() => setEditing(false)} disabled={busy}>Cancel</button>
      </div>
    </div>
  );
}
