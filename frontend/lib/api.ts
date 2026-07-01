const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface UploadResponse {
  resume_id: string;
  raw_text: string;
}

export interface RunResponse {
  run_id: string;
}

async function asError(res: Response, fallback: string): Promise<Error> {
  try {
    const body = await res.json();
    return new Error(body.detail ?? fallback);
  } catch {
    return new Error(fallback);
  }
}

export async function uploadResume(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/api/upload-resume`, { method: "POST", body: form });
  if (!res.ok) throw await asError(res, "Upload failed");
  return res.json();
}

export async function runAgent(rawText: string, location: string, resumeId?: string): Promise<RunResponse> {
  const res = await fetch(`${API_URL}/api/run-agent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText, location, resume_id: resumeId }),
  });
  if (!res.ok) throw await asError(res, "Failed to start agent run");
  return res.json();
}

export async function getResult(runId: string) {
  const res = await fetch(`${API_URL}/api/run-result/${runId}`);
  if (!res.ok) throw await asError(res, "Failed to fetch result");
  return res.json();
}

export async function downloadPdf(kind: "resume" | "cover_letter", payload: Record<string, unknown>) {
  const res = await fetch(`${API_URL}/api/generate-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind, ...payload }),
  });
  if (!res.ok) throw await asError(res, "Failed to generate PDF");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = kind === "resume" ? "tailored_resume.pdf" : "cover_letter.pdf";
  a.click();
  URL.revokeObjectURL(url);
}

export { API_URL };
