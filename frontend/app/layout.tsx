import type { Metadata } from "next";
import "./globals.css";
import { TopNav } from "@/components/TopNav";

export const metadata: Metadata = {
  title: "LeadHunter TZ",
  description: "Tanzania business lead generation & website opportunity scraper",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <TopNav />
          <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
          <footer className="mx-auto max-w-7xl px-6 py-8 text-xs text-slate-400">
            LeadHunter TZ — for legitimate B2B lead generation on publicly available business
            information. Respect platform ToS, GDPR &amp; the Tanzania Data Protection Act.
          </footer>
        </div>
      </body>
    </html>
  );
}
