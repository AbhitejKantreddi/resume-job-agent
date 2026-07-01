import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agentic Resume & Job-Match Assistant",
  description:
    "Upload a resume and an AI agent researches live jobs, scores skill gaps, rewrites your resume, and drafts a cover letter.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">{children}</div>
      </body>
    </html>
  );
}
