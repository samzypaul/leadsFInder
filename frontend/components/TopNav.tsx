"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, auth } from "@/lib/api";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/discover", label: "Discover" },
  { href: "/scan", label: "Single Scan" },
  { href: "/leads", label: "Leads" },
];

export function TopNav() {
  const pathname = usePathname();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(auth.isAuthed());
  }, [pathname]);

  const onLogin = pathname === "/login";

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <Link href={authed ? "/" : "/login"} className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand font-bold text-white">
            L
          </span>
          <span className="text-lg font-semibold">
            LeadHunter <span className="text-brand">TZ</span>
          </span>
        </Link>

        {authed && !onLogin && (
          <nav className="flex items-center gap-1">
            {NAV.map((n) => {
              const active = n.href === "/" ? pathname === "/" : pathname.startsWith(n.href);
              return (
                <Link
                  key={n.href}
                  href={n.href}
                  className={`rounded-lg px-3 py-2 text-sm font-medium ${
                    active ? "bg-brand/10 text-brand-dark" : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {n.label}
                </Link>
              );
            })}
            <button
              onClick={() => api.logout()}
              className="ml-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-500 hover:bg-slate-100 hover:text-red-600"
            >
              Logout
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}
