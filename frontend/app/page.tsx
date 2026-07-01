"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import ResumeUpload from "@/components/ResumeUpload";
import { runAgent, uploadResume } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [location, setLocation] = useState("Remote");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      const { resume_id, raw_text } = await uploadResume(file);
      const { run_id } = await runAgent(raw_text, location, resume_id);
      router.push(`/run/${run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-16">
      <h1 className="text-3xl font-bold tracking-tight">Agentic Resume &amp; Job-Match Assistant</h1>
      <p className="mt-3 leading-relaxed text-gray-600">
        Upload your resume. An AI agent will parse it, search live job postings, score your skill gaps,
        rewrite your resume for the best match, and draft a tailored cover letter — as a visible,
        step-by-step run.
      </p>

      <div className="mt-8">
        <label className="mb-1 block text-sm font-medium text-gray-700">Preferred location</label>
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="mb-6 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
          placeholder="e.g. Remote, Bangalore, New York"
        />

        <ResumeUpload onFile={handleFile} disabled={busy} />

        {busy && <p className="mt-4 text-center text-sm text-gray-500">Uploading and starting the agent…</p>}
        {error && <p className="mt-4 text-center text-sm text-red-600">{error}</p>}
      </div>

      <p className="mt-10 text-center text-xs text-gray-400">
        Runs in demo mode without API keys. Add Groq + Tavily keys to the backend for live results.
      </p>
    </main>
  );
}
