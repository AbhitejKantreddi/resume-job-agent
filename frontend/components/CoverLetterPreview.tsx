"use client";

import { downloadPdf } from "@/lib/api";

interface Props {
  coverLetter: string;
  resumeJson: Record<string, unknown>;
}

export default function CoverLetterPreview({ coverLetter, resumeJson }: Props) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Cover letter</h4>
        <button
          onClick={() =>
            downloadPdf("cover_letter", {
              cover_letter_json: { cover_letter: coverLetter },
              resume_json: resumeJson,
            })
          }
          className="rounded-lg bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
        >
          Download PDF
        </button>
      </div>
      <div className="whitespace-pre-wrap leading-relaxed text-gray-800">{coverLetter}</div>
    </div>
  );
}
