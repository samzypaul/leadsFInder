"use client";

import { useRef, useState } from "react";
import { api, Attachment } from "@/lib/api";

export function Attachments({ leadId, initial }: { leadId: number; initial: Attachment[] }) {
  const [items, setItems] = useState<Attachment[]>(initial);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const proposalFile = useRef<HTMLInputElement>(null);
  const contractFile = useRef<HTMLInputElement>(null);

  const refresh = async () => setItems(await api.listAttachments(leadId));

  async function upload(kind: "proposal" | "contract", file?: File | null) {
    if (!file) return;
    setBusy(true);
    setErr(null);
    try {
      await api.uploadAttachment(leadId, kind, file);
      await refresh();
    } catch (e) {
      setErr(String(e).includes("415") ? "File type not allowed for this slot." : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function saveProposalText() {
    if (!text.trim()) return;
    setBusy(true);
    try {
      await api.uploadProposalText(leadId, text.trim());
      setText("");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function del(id: number) {
    if (!confirm("Delete this attachment?")) return;
    await api.deleteAttachment(id);
    await refresh();
  }

  const proposals = items.filter((a) => a.kind === "proposal");
  const contracts = items.filter((a) => a.kind === "contract");

  const Row = ({ a }: { a: Attachment }) => (
    <div className="flex items-center justify-between gap-2 border-b border-slate-100 py-2 text-sm last:border-0">
      <div className="min-w-0">
        <div className="truncate font-medium text-slate-700">{a.filename}</div>
        <div className="text-xs text-slate-400">
          {a.content_type} · {(a.size / 1024).toFixed(1)} KB
        </div>
      </div>
      <div className="flex shrink-0 gap-2">
        <button className="text-brand hover:underline" onClick={() => api.downloadAttachment(a)}>download</button>
        <button className="text-red-500 hover:underline" onClick={() => del(a.id)}>delete</button>
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      {err && <p className="text-sm text-red-600">{err}</p>}

      {/* Proposal */}
      <div>
        <h3 className="mb-2 font-medium text-slate-900">Sent proposal</h3>
        {proposals.map((a) => <Row key={a.id} a={a} />)}
        <div className="mt-2 space-y-2">
          <textarea
            className="input min-h-[70px]"
            placeholder="Paste the proposal text you sent…"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="flex flex-wrap items-center gap-2">
            <button className="btn-ghost" onClick={saveProposalText} disabled={busy || !text.trim()}>
              Save proposal text
            </button>
            <input
              ref={proposalFile}
              type="file"
              accept=".pdf,.txt,.doc,.docx"
              className="hidden"
              onChange={(e) => upload("proposal", e.target.files?.[0])}
            />
            <button className="btn-ghost" onClick={() => proposalFile.current?.click()} disabled={busy}>
              Upload proposal (PDF)
            </button>
          </div>
        </div>
      </div>

      {/* Contract */}
      <div>
        <h3 className="mb-2 font-medium text-slate-900">Signed contract</h3>
        {contracts.map((a) => <Row key={a.id} a={a} />)}
        <input
          ref={contractFile}
          type="file"
          accept=".pdf,image/*"
          className="hidden"
          onChange={(e) => upload("contract", e.target.files?.[0])}
        />
        <button className="btn-ghost mt-2" onClick={() => contractFile.current?.click()} disabled={busy}>
          Upload contract (PDF / image)
        </button>
      </div>
    </div>
  );
}
