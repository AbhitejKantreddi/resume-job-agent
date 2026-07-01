import { Fragment } from "react";

interface Bullet {
  original: string;
  improved: string;
}

interface Rewrite {
  tailored_summary: string;
  tailored_bullets: Bullet[];
}

/** Render **bold** markdown segments as <strong>. */
function renderBold(text: string) {
  const parts = (text ?? "").split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) =>
    p.startsWith("**") && p.endsWith("**") ? (
      <strong key={i}>{p.slice(2, -2)}</strong>
    ) : (
      <Fragment key={i}>{p}</Fragment>
    ),
  );
}

export default function ResumePreview({ rewrite }: { rewrite: Rewrite }) {
  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          Tailored summary
        </h4>
        <p className="leading-relaxed">{renderBold(rewrite.tailored_summary || "")}</p>
      </div>

      <div className="space-y-3">
        {(rewrite.tailored_bullets ?? []).map((b, i) => (
          <div
            key={i}
            className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 md:grid-cols-2"
          >
            <div>
              <p className="mb-1 text-xs font-semibold uppercase text-gray-400">Before</p>
              <p className="text-sm text-gray-600">{b.original}</p>
            </div>
            <div>
              <p className="mb-1 text-xs font-semibold uppercase text-blue-500">After</p>
              <p className="text-sm text-gray-900">{renderBold(b.improved)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
