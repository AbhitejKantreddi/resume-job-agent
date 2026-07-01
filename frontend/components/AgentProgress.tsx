"use client";

import type { StepState } from "@/lib/sse";

const ICONS: Record<string, string> = {
  done: "✓",
  in_progress: "●",
  error: "✕",
  pending: "○",
};

export default function AgentProgress({ steps }: { steps: StepState[] }) {
  if (steps.length === 0) {
    return <p className="text-sm text-gray-400">Starting agent…</p>;
  }

  return (
    <ol className="space-y-3">
      {steps.map((s) => (
        <li key={s.node} className="flex items-center gap-3">
          <span
            className={`flex h-7 w-7 flex-none items-center justify-center rounded-full text-sm font-bold
              ${
                s.status === "done"
                  ? "bg-green-100 text-green-700"
                  : s.status === "in_progress"
                    ? "animate-pulse bg-blue-100 text-blue-700"
                    : s.status === "error"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-400"
              }`}
          >
            {ICONS[s.status] ?? "○"}
          </span>
          <span className={s.status === "pending" ? "text-gray-400" : "text-gray-900"}>{s.label}</span>
        </li>
      ))}
    </ol>
  );
}
