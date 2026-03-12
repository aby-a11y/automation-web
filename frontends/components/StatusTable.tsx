type Job = {
  id: string;
  url: string;
  status: "queued" | "running" | "success" | "failed" | "skipped";
  message: string;
};

const statusConfig = {
  queued:  { label: "⏳ Queued",  className: "text-gray-500" },
  running: { label: "🔄 Running", className: "text-blue-500 animate-pulse" },
  success: { label: "✅ Success", className: "text-green-600 font-bold" },
  failed:  { label: "❌ Failed",  className: "text-red-500" },
  skipped: { label: "⚠️ Skipped", className: "text-yellow-500" },
};

export default function StatusTable({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) return null;

  const total   = jobs.length;
  const success = jobs.filter((j) => j.status === "success").length;
  const failed  = jobs.filter((j) => j.status === "failed").length;
  const running = jobs.filter((j) => j.status === "running").length;
  const queued  = jobs.filter((j) => j.status === "queued").length;

  return (
    <div className="mt-8">

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { label: "Total",   value: total,   color: "bg-gray-100" },
          { label: "Success", value: success, color: "bg-green-100 text-green-700" },
          { label: "Failed",  value: failed,  color: "bg-red-100 text-red-700" },
          { label: "Pending", value: running + queued, color: "bg-blue-100 text-blue-700" },
        ].map((card) => (
          <div key={card.label} className={`${card.color} rounded-xl p-4 text-center`}>
            <div className="text-2xl font-bold">{card.value}</div>
            <div className="text-sm mt-1">{card.label}</div>
          </div>
        ))}
      </div>

      {/* Results Table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left p-3 text-gray-600">#</th>
              <th className="text-left p-3 text-gray-600">Website URL</th>
              <th className="text-center p-3 text-gray-600">Status</th>
              <th className="text-left p-3 text-gray-600">Message</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job, index) => (
              <tr key={job.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="p-3 text-gray-400">{index + 1}</td>
                <td className="p-3">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline truncate block max-w-xs"
                  >
                    {job.url}
                  </a>
                </td>
                <td className={`p-3 text-center ${statusConfig[job.status]?.className}`}>
                  {statusConfig[job.status]?.label}
                </td>
                <td className="p-3 text-gray-500 text-xs max-w-sm truncate">
                  {job.message || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
