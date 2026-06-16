"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";

/**
 * Client-side auth gate. Redirects to /login when no token is present.
 * Returns `ready=true` once we've confirmed a token exists (render content then).
 */
export function useRequireAuth(): { ready: boolean } {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (auth.isAuthed()) {
      setReady(true);
    } else {
      router.replace("/login");
    }
  }, [router]);

  return { ready };
}
