interface Match {
  job_title: string;
  company: string;
  match_score: number;
  missing_skills: string[];
  matching_skills: string[];
}

export default function JobMatchCard({ match, url }: { match: Match; url?: string }) {
  const color =
    match.match_score >= 80
      ? "text-green-600"
      : match.match_score >= 60
        ? "text-amber-600"
        : "text-red-600";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold">{match.job_title}</h3>
          <p className="text-sm text-gray-500">{match.company}</p>
        </div>
        <div className={`text-2xl font-bold ${color}`}>{match.match_score}%</div>
      </div>

      {match.matching_skills?.length > 0 && (
        <p className="mt-3 text-sm">
          <span className="font-medium text-green-700">Matching:</span> {match.matching_skills.join(", ")}
        </p>
      )}
      {match.missing_skills?.length > 0 && (
        <p className="mt-1 text-sm">
          <span className="font-medium text-red-700">Missing:</span> {match.missing_skills.join(", ")}
        </p>
      )}

      {url && (
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-block text-sm text-blue-600 hover:underline"
        >
          View posting →
        </a>
      )}
    </div>
  );
}
