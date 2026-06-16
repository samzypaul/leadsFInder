"use client";

import { useEffect, useState } from "react";
import { api, User } from "@/lib/api";
import { useRequireAuth } from "@/lib/useRequireAuth";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-6">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">{title}</h2>
      {children}
    </div>
  );
}

export default function ProfilePage() {
  const { ready } = useRequireAuth();
  const [user, setUser] = useState<User | null>(null);
  const [form, setForm] = useState<Partial<User>>({});
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [pw, setPw] = useState({ current: "", next: "", confirm: "" });
  const [pwMsg, setPwMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (ready) api.me().then((u) => { setUser(u); setForm(u); });
  }, [ready]);

  if (!ready) return null;
  if (!user) return <div className="text-slate-400">Loading…</div>;

  const set = (k: keyof User) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm({ ...form, [k]: e.target.value });

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setSavedMsg(null);
    try {
      const updated = await api.updateProfile({
        full_name: form.full_name,
        brand_name: form.brand_name,
        business_info: form.business_info,
        brand_website: form.brand_website,
        brand_phone: form.brand_phone,
        brand_email: form.brand_email,
      });
      setUser(updated);
      setSavedMsg("Saved ✓");
    } finally {
      setBusy(false);
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwMsg(null);
    if (pw.next.length < 8) return setPwMsg({ ok: false, text: "New password must be ≥ 8 characters." });
    if (pw.next !== pw.confirm) return setPwMsg({ ok: false, text: "Passwords do not match." });
    setBusy(true);
    try {
      await api.changePassword(pw.current, pw.next);
      setPwMsg({ ok: true, text: "Password changed ✓" });
      setPw({ current: "", next: "", confirm: "" });
    } catch (err) {
      setPwMsg({ ok: false, text: String(err).includes("400") ? "Current password is incorrect." : "Failed to change password." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My profile</h1>
        <p className="mt-1 text-sm text-slate-500">
          Signed in as <span className="font-medium">{user.email}</span>
          {user.is_admin && <span className="badge ml-2 border-violet-200 bg-violet-100 text-violet-700">admin</span>}
        </p>
      </div>

      <form onSubmit={saveProfile}>
        <Section title="Brand & business info">
          <p className="mb-4 text-xs text-slate-400">
            Your brand name is used to sign outreach messages and proposals.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Your name</span>
              <input className="input" value={form.full_name ?? ""} onChange={set("full_name")} />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Brand / company name</span>
              <input className="input" value={form.brand_name ?? ""} onChange={set("brand_name")} placeholder="e.g. Kunonu Digital" />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Business email</span>
              <input className="input" value={form.brand_email ?? ""} onChange={set("brand_email")} />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Business phone</span>
              <input className="input" value={form.brand_phone ?? ""} onChange={set("brand_phone")} />
            </label>
            <label className="text-sm sm:col-span-2">
              <span className="mb-1 block text-slate-500">Website</span>
              <input className="input" value={form.brand_website ?? ""} onChange={set("brand_website")} placeholder="https://" />
            </label>
            <label className="text-sm sm:col-span-2">
              <span className="mb-1 block text-slate-500">Business info / tagline</span>
              <textarea className="input min-h-[80px]" value={form.business_info ?? ""} onChange={set("business_info")} placeholder="What you offer, your pitch, etc." />
            </label>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <button className="btn-primary" disabled={busy}>Save profile</button>
            {savedMsg && <span className="text-sm text-emerald-600">{savedMsg}</span>}
          </div>
        </Section>
      </form>

      <form onSubmit={changePassword}>
        <Section title="Change password">
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Current password</span>
              <input className="input" type="password" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} required />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">New password</span>
              <input className="input" type="password" value={pw.next} onChange={(e) => setPw({ ...pw, next: e.target.value })} required />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-500">Confirm new</span>
              <input className="input" type="password" value={pw.confirm} onChange={(e) => setPw({ ...pw, confirm: e.target.value })} required />
            </label>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <button className="btn-ghost" disabled={busy}>Update password</button>
            {pwMsg && <span className={`text-sm ${pwMsg.ok ? "text-emerald-600" : "text-red-600"}`}>{pwMsg.text}</span>}
          </div>
        </Section>
      </form>
    </div>
  );
}
