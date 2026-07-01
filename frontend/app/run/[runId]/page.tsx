"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AgentProgress from "@/components/AgentProgress";
import JobMatchCard from "@/components/JobMatchCard";
import ResumePreview from "@/components/ResumePreview";
import CoverLetterPreview from "@/components/CoverLetterPreview";
import { downloadPdf, getResult } from "@/lib/api";
import { subscribeToRun, type StepState } from "@/lib/sse";

interface Match {
  job_title: string;
  company: string;
  match_score: number;
  missing_skills: string[];
  matching_skills: string[];
}

export default function RunPage() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;
  const [steps, setSteps] = useState<StepState[]>([]);
  const [status, setStatus] = useState("running");
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!runId) return;
    const unsub = subscribeToRun(
      runId,
      (evt) => {
        setSteps(evt.steps);
        setStatus(evt.status);
      },
      async (finalStatus) => {
        try {
          setResult(await getResult(runId));
        } catch {
          /* ignore fetch error; status still updates */
        }
        setStatus(finalStatus);
      },
    );
    return unsub;
  }, [runId]);

  const matches: Match[] = result?.gap_analysis_json?.matches ?? [];
  const jobs: any[] = result?.jobs_json?.jobs ?? [];
  const urlFor = (company: string) => jobs.find((j) => j.company === company)?.url;

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-2xl font-bold">Agent run</h1>
      <p className="mb-6 font-mono text-sm text-gray-500">Run ID: {runId}</p>

      <section className="mb-10 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-semibold">Progress</h2>
        <AgentProgress steps={steps} />
      </section>

      {status === "failed" && (
        <div className="rounded-lg bg-red-50 p-4 text-red-700">
          <p className="font-semibold">The run failed.</p>
          {result?.error ? (
            <pre className="mt-2 whitespace-pre-wrap break-words font-mono text-xs text-red-800">
              {result.error}
            </pre>
          ) : (
            <p className="mt-1 text-sm">Check the backend terminal logs for details.</p>
          )}
        </div>
      )}

      {result && status === "completed" && (
        <div className="space-y-10">
          <section>
            <h2 className="mb-4 text-lg font-semibold">Top job matches</h2>
            <div className="grid gap-4">
              {matches.map((m, i) => (
                <JobMatchCard key={i} match={m} url={urlFor(m.company)} />
              ))}
            </div>
          </section>

          {result.rewritten_resume_json && (
            <section>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold">Tailored resume</h2>
                <button
                  onClick={() =>
                    downloadPdf("resume", {
                      rewritten_resume_json: result.rewritten_resume_json,
                      resume_json: result.resume_json,
                    })
                  }
                  className="rounded-lg bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
                >
                  Download PDF
                </button>
              </div>
              <ResumePreview rewrite={result.rewritten_resume_json} />
            </section>
          )}

          {result.cover_letter_json?.cover_letter && (
            <section>
              <h2 className="mb-4 text-lg font-semibold">Cover letter</h2>
              <CoverLetterPreview
                coverLetter={result.cover_letter_json.cover_letter}
                resumeJson={result.resume_json ?? {}}
              />
            </section>
          )}
        </div>
      )}
    </main>
  );
}
