"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, auth } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@leadhunter.tz");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (auth.isAuthed()) router.replace("/");
  }, [router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      await api.login(email.trim(), password);
      router.replace("/");
    } catch {
      setErr("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto mt-10 max-w-sm">
      <div className="mb-6 text-center">
        <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-xl bg-brand text-xl font-bold text-white">
          L
        </div>
        <h1 className="text-xl font-bold">
          LeadHunter <span className="text-brand">TZ</span>
        </h1>
        <p className="mt-1 text-sm text-slate-500">Sign in to your account</p>
      </div>

      <form onSubmit={submit} className="card space-y-4 p-6">
        <div>
          <label className="mb-1 block text-sm font-medium">Email</label>
          <input
            className="input"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Password</label>
          <input
            className="input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {err && <p className="text-sm text-red-600">{err}</p>}
        <button className="btn-primary w-full" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="mt-4 text-center text-xs text-slate-400">
        Demo: <code>admin@leadhunter.tz</code> / the <code>ADMIN_PASSWORD</code> you set
        (default <code>changeme</code>).
      </p>
    </div>
  );
}
